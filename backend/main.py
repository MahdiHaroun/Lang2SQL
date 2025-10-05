from fastapi import FastAPI , HTTPException , status 
from schemas import DBConfig , QueryRequest
from contextlib import asynccontextmanager
from langchain_core.messages import HumanMessage
import models
from database import engine, get_db
from sqlalchemy.orm import Session
import logging
import os
import sys
from datetime import datetime
from routers import user, auth, google_auth , databases
import oauth2
from fastapi import Depends

# Add parent directory to path to allow importing from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.Graph.graph import get_session_graph, save_session_graph

from src.Tools_Functions.db_connector import DBConnector
from src.Graph.graph import Graph_builder
from src.Agent.agent import SQLAgent
from src.LLM.llm_with_tools import llm_with_tools
import redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


global_graph = None 
global_agent = None
global_main_llm = None
global_db_connector = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global global_graph
    global global_agent
    global global_main_llm
    logger.info("Building the graph")
    global_graph = Graph_builder().get_compiled_graph()
    logger.info("Initializing the main LLM")
    global_main_llm = llm_with_tools().llm_with_tools()
    logger.info("Creating the SQL agent")
    global_agent = SQLAgent().get_agent(global_main_llm) 
    logger.info("Agent is online") 
    logger.info("connecting to redis...")
    try:
        # Use our Redis client module for consistency
        from src.redis_client import redis_client
        if not redis_client.is_connected():
            redis_client.reconnect()
        
        if redis_client.is_connected():
            logger.info("Connected to Redis successfully")
        else:
            raise redis.ConnectionError("Failed to connect to Redis")
    except redis.ConnectionError as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise e
    
    yield
    
    # Cleanup when shutting down
    logger.info("Shutting down application...")
    try:
        # Clear session connectors cache
        logger.info("Clearing session connectors cache...")
        from src.Tools.Tools import session_connectors
        session_connectors.clear()
        logger.info("Session connectors cache cleared")
        
        # Clear Redis database
        logger.info("Clearing Redis database...")
        from src.redis_client import redis_client
        if redis_client.is_connected():
            # Clear all session data
            keys = redis_client.keys("session:*")
            if keys:
                redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} session keys from Redis")
            else:
                logger.info("No session keys found in Redis")
            
            # Close the Redis connection
            if hasattr(redis_client, 'redis_client') and redis_client.redis_client:
                redis_client.redis_client.close()
                logger.info("Redis connection closed")
        else:
            logger.info("Redis was not connected during shutdown")
    except Exception as e:
        logger.error(f"Error during Redis cleanup: {e}")
    
    logger.info("Application shutdown complete")
        

models.Base.metadata.create_all(bind=engine)  # Create tables in the database
app = FastAPI(lifespan=lifespan , title="SQLAgent API", description="API for SQLAgent using FastAPI")
app.include_router(user.router)
app.include_router(auth.router)
app.include_router(google_auth.router)
app.include_router(databases.router )







@app.get("/health")
async def health_check():
    """Health check endpoint with Redis status"""
    global global_graph
    global global_agent
    global global_main_llm
    
    health_status = {
        "status": "healthy",
        "message": "Service is up and running",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
    
    # Check core components
    if global_graph is None:
        health_status.update({"status": "unhealthy", "message": "Graph not initialized"})
        return health_status
    if global_agent is None:
        health_status.update({"status": "unhealthy", "message": "Agent not initialized"})
        return health_status
    if global_main_llm is None:
        health_status.update({"status": "unhealthy", "message": "Main LLM not initialized"})
        return health_status
    
    # Check Redis connection
    try:
        from src.redis_client import redis_client
        redis_status = "healthy" if redis_client.is_connected() else "unhealthy"
        health_status["redis"] = redis_status
        
        if redis_status == "unhealthy":
            health_status.update({
                "status": "degraded", 
                "message": "Service running but Redis unavailable"
            })
    except Exception as e:
        health_status["redis"] = "error"
        health_status.update({
            "status": "degraded",
            "message": f"Service running but Redis check failed: {e}"
        })
    
    return health_status

@app.get("/health/session")
async def session_health_check(user_session: tuple = Depends(oauth2.get_current_user_and_session)):
    """Health check endpoint with session information"""
    current_user, session_id = user_session
    
    try:
        from src.Tools.Tools import is_database_connected
        db_connected = is_database_connected(session_id)
    except:
        db_connected = False
    
    return {
        "status": "healthy",
        "message": "Service is up and running",
        "user_id": current_user.id,
        "session_id": session_id,      # UUID serving as session identifier
        "thread_id": session_id,       # Same UUID serving as conversation thread
        "database_connected": db_connected
    }



@app.post("/ask", response_model=str, status_code=status.HTTP_200_OK)
async def ask_question(
    query_request: QueryRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    try:
        # -----------------------------
        # Validate user
        # -----------------------------
        if query_request.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User ID in payload does not match authenticated user"
            )

        # -----------------------------
        # Validate session in DB
        # -----------------------------
        user_session = db.query(models.Session).filter(
            models.Session.session_token == query_request.session_id,
            models.Session.user_id == current_user.id
        ).first()
        
        if not user_session:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Session ID does not belong to the authenticated user or session not found"
            )

        # -----------------------------
        # Load or create session-specific graph (Redis-backed)
        # -----------------------------
        session_graph = get_session_graph(query_request.session_id)

        logger.info(f"Received question from user {current_user.id}, session/thread {query_request.session_id}: {query_request.question}")

        # -----------------------------
        # Invoke the graph
        # -----------------------------
        config = {"configurable": {"thread_id": query_request.session_id}}
        response = await session_graph.ainvoke(
            {"messages": [HumanMessage(content=query_request.question)]},
            config=config
        )

        # -----------------------------
        # Persist updated graph state to Redis
        # -----------------------------
        save_session_graph(query_request.session_id, session_graph)

        # -----------------------------
        # Extract final message
        # -----------------------------
        if response and "messages" in response and response["messages"]:
            final_message = response["messages"][-1]
            if hasattr(final_message, 'content'):
                return final_message.content
            else:
                return str(final_message)
        
        return "No response generated"

    except Exception as e:
        logger.error(f"Error occurred: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error occurred with exception: {e}")



