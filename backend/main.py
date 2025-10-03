from fastapi import FastAPI , HTTPException , status 
from schemas import DBConfig , QueryRequest
from contextlib import asynccontextmanager
from langchain_core.messages import HumanMessage
import models
from database import engine
import logging
import os
import sys
from routers import user, auth, google_auth , databases
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
app.include_router(auth.router)
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



@app.post("/ask", response_model=str, status_code=status.HTTP_200_OK)
async def ask_question(query_request: QueryRequest , user_id :int = Depends(oauth2.get_current_user)):
    try:
        global global_graph
        if global_graph is None:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Graph not initialized")
        
        logger.info(f"Received question: {query_request.question}")
        
        # Provide thread_id for conversation memory
        thread_id = getattr(query_request, 'thread_id', 'default-thread')
        config = {"configurable": {"thread_id": thread_id}}
        
        response = await global_graph.ainvoke(
            {"messages": [HumanMessage(content=query_request.question)]}, 
            config=config
        )
        logger.info(f"Agent response: {response}")
        
        
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



