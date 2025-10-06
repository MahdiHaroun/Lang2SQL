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
from routers import user, google_auth , databases , sessions
import oauth2
from fastapi import Depends


# Add parent directory to path to allow importing from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.Tools_Functions.db_connector import DBConnector
from src.Graph.graph import Graph_builder
from src.Agent.agent import SQLAgent
from src.LLM.llm_with_tools import llm_with_tools

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
    yield
    

models.Base.metadata.create_all(bind=engine)  # Create tables in the database
app = FastAPI(lifespan=lifespan , title="SQLAgent API", description="API for SQLAgent using FastAPI")
app.include_router(user.router)
app.include_router(sessions.router)
app.include_router(google_auth.router)
app.include_router(databases.router )







@app.get("/health")
async def health_check():
    """Health check endpoint"""
    global global_graph
    global global_agent
    global global_main_llm
    if global_graph is None:
        return {"status": "unhealthy", "message": "Graph not initialized"}
    if global_agent is None:
        return {"status": "unhealthy", "message": "Agent not initialized"}
    if global_main_llm is None:
        return {"status": "unhealthy", "message": "Main LLM not initialized"}
    return {"status": "healthy", "message": "Service is up and running"}

@app.get("/health/session/{session_id}")
async def session_health_check(
    session_id: str,
    current_user: models.User = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
):
    """Health check endpoint with session information"""
    # Validate that the session belongs to the user
    session = oauth2.get_current_session_by_id(session_id, current_user, db)
    
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
        # Validate that the user in the payload matches the authenticated user
        if query_request.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="User ID in payload does not match authenticated user"
            )
        
        # Validate that the session belongs to the user by checking the database
        user_session = db.query(models.Session).filter(
            models.Session.session_token == query_request.session_id,
            models.Session.user_id == current_user.id
        ).first()
        
        if not user_session:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Session ID does not belong to the authenticated user or session not found"
            )
        
        # Get session-specific graph using the validated session_id
        from src.Graph.graph import get_session_graph
        session_graph = get_session_graph(query_request.session_id)
        
        logger.info(f"Received question from user {current_user.id}, session/thread {query_request.session_id}: {query_request.question}")
        
        # Use session_id as thread_id for conversation memory - session_id IS the thread_id (UUID)
        config = {"configurable": {"thread_id": query_request.session_id}}

        response = await session_graph.ainvoke(
            {"messages": [HumanMessage(content=query_request.question)]}, 
            config=config
        )
        logger.info(f"Agent response for session {query_request.session_id}: {response}")
        
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



