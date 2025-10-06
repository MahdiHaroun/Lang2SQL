from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
import models, schemas, database, utils 
import oauth2
from database import get_db

router = APIRouter(
    tags=["Sessions"],
    prefix="/sessions"
)
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

@router.get("/disconnect-session/{session_id}", status_code=status.HTTP_200_OK)
async def disconnect_session(
    session_id: str,
    user_session: tuple = Depends(oauth2.get_current_user_and_session)
):
    """Disconnect database for the current session"""
    current_user, session_id = user_session
    
    try:
        from src.Tools.Tools import session_db_connectors, session_fetch_db, session_execute_sql
        
        # Remove session-specific connectors
        if session_id in session_db_connectors:
            del session_db_connectors[session_id]
        if session_id in session_fetch_db:
            del session_fetch_db[session_id]
        if session_id in session_execute_sql:
            del session_execute_sql[session_id]
            
        # Also remove session graph
        from src.Graph.graph import session_graphs
        if session_id in session_graphs:
            del session_graphs[session_id]
        
        return {
            "message": "Session disconnected successfully",
            "session_id": session_id,  # UUID that was serving as both session and thread ID
            "thread_id": session_id,   # Same UUID for thread continuity (now disconnected)
            "user_id": current_user.id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error disconnecting session: {e}"
        )
    
@router.get("/all_sessions", status_code=status.HTTP_200_OK)
async def get_all_sessions(
    current_user: models.User = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
):
    """Get all active sessions for the current user"""
    sessions = db.query(models.Session).filter(models.Session.user_id == current_user.id).all()
    
    session_list = [{"session_id": s.session_token} for s in sessions]
    
    return {
        "user_id": current_user.id,
        "active_sessions": session_list
    }


  


@router.delete("/delete_session/{session_id}", status_code=status.HTTP_200_OK)
async def delete_session(
    session_id: str , 
    current_user: models.User = Depends(oauth2.get_current_user),
):
    """Delete a specific session for the current user"""
    db: Session = next(database.get_db())
    
    session = db.query(models.Session).filter(
        models.Session.session_token == session_id,
        models.Session.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Session not found or does not belong to the user"
        )
    
    db.delete(session)
    db.commit()
        
    return {
            "message": "Session deleted successfully",
            "session_id": session_id,
            "user_id": current_user.id
        }





  