import models, schemas, utils
from database import get_db
from fastapi import FastAPI , status , HTTPException , Depends , APIRouter
from sqlalchemy.orm import Session 
import oauth2



router = APIRouter(
    prefix="/databases",
    tags=["databases"]
)

@router.post("/add_db_connection", status_code=status.HTTP_201_CREATED)
async def add_db_connection(
    new_db: schemas.DBConfig, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    # Ensure the database connection is owned by the current user
    new_db.owner_id = current_user.id
    new_database = models.DB_Connection_Details(**new_db.dict())
    db.add(new_database)
    db.commit()
    db.refresh(new_database)
    return {
        "message": "Database added successfully",
        "db_connection": new_database
    }




@router.post("/connect_db/{db_id}", status_code=status.HTTP_200_OK)
async def connect_db(
    db_id: int, 
    db: Session = Depends(get_db),
    user_session: tuple = Depends(oauth2.get_current_user_and_session)
): 
    try:
        current_user, session_id = user_session
        
        # Get the database connection details and ensure it belongs to the current user
        db_details = db.query(models.DB_Connection_Details).filter(
            models.DB_Connection_Details.id == db_id,
            models.DB_Connection_Details.owner_id == current_user.id
        ).first()
        
        if not db_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Database connection not found or you don't have permission to access it"
            )
        
        # Build the connection string (using psycopg2 for synchronous operations)
        connection_string = f"postgresql+psycopg2://{db_details.username}:{db_details.db_password}@{db_details.host}:{db_details.port}/{db_details.database_name}"
        
        # Test the connection by creating a DBConnector and attempting to connect
        from src.Tools_Functions.db_connector import DBConnector
        db_connector = DBConnector(connection_string)
        connection = db_connector.connect()
        
        # If successful, close the test connection
        connection.close()
        
        # Update the session-specific database connector in Tools system
        try:
            from src.Tools.Tools import update_db_connector
            update_success = update_db_connector(connection_string, session_id)
            if not update_success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                    detail="Database connection successful but failed to update tools system"
                )
        except ImportError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Could not import tools system: {e}"
            )
        
        return {
            "message": "Database connection successful and tools updated",
            "session_id": session_id,  # This UUID serves as both session_id and thread_id
            "thread_id": session_id,   # Same as session_id for conversation continuity
            "db_id": db_id,
            "database_name": db_details.database_name,
            "user_id": current_user.id
        }
     
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error occurred with exception: {e}")
    


@router.get("/databases", status_code=status.HTTP_200_OK)
async def get_user_dbs(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    # Get databases for the currently authenticated user only
    db_connections = db.query(models.DB_Connection_Details).filter(
        models.DB_Connection_Details.owner_id == current_user.id
    ).all()
    
    return {
        "user_id": current_user.id,
        "databases": db_connections
    }

@router.get("/session-status", status_code=status.HTTP_200_OK)
async def get_session_status(
    user_session: tuple = Depends(oauth2.get_current_user_and_session)
):
    """Get current session information and database connection status"""
    current_user, session_id = user_session
    
    # Check if database is connected for this session
    try:
        from src.Tools.Tools import is_database_connected
        db_connected = is_database_connected(session_id)
    except ImportError:
        db_connected = False
    
    return {
        "user_id": current_user.id,
        "session_id": session_id,      # UUID serving as session identifier  
        "thread_id": session_id,       # Same UUID serving as conversation thread identifier
        "database_connected": db_connected
    }

@router.post("/disconnect-session", status_code=status.HTTP_200_OK)
async def disconnect_session(
    user_session: tuple = Depends(oauth2.get_current_user_and_session)
):
    """Disconnect database for the current session and clean up Redis data"""
    current_user, session_id = user_session
    
    try:
        # Clean up Redis session data
        from src.Tools.Tools import cleanup_session
        redis_cleanup_success = cleanup_session(session_id)
        
        # Clean up in-memory session graphs
        try:
            from src.Graph.graph import session_graphs
            if session_id in session_graphs:
                del session_graphs[session_id]
        except ImportError:
            pass  # Graph module might not be available
        
        return {
            "message": "Session disconnected successfully",
            "session_id": session_id,  # UUID that was serving as both session and thread ID
            "thread_id": session_id,   # Same UUID for thread continuity (now disconnected)
            "user_id": current_user.id,
            "redis_cleanup": redis_cleanup_success
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error disconnecting session: {e}"
        )

@router.get("/session-info/{session_id}", status_code=status.HTTP_200_OK)
async def get_detailed_session_info(
    session_id: str,
    current_user: models.User = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed session information including Redis data"""
    try:
        # Validate session belongs to user
        user_session = db.query(models.Session).filter(
            models.Session.session_token == session_id,
            models.Session.user_id == current_user.id
        ).first()
        
        if not user_session:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Session not found or does not belong to user"
            )
        
        # Get Redis session information
        from src.Tools.Tools import get_session_info, is_database_connected
        redis_info = get_session_info(session_id)
        db_connected = is_database_connected(session_id)
        
        return {
            "session_id": session_id,
            "thread_id": session_id,
            "user_id": current_user.id,
            "database_connected": db_connected,
            "redis_data": redis_info,
            "db_session_created_at": user_session.created_at.isoformat() if user_session.created_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving session info: {e}"
        )