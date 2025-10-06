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
@router.get("/session-status/{session_id}", status_code=status.HTTP_200_OK)
async def get_session_status(
    session_id: str,
    current_user: models.User = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific session information and database connection status"""
    # Validate session belongs to user
    session = oauth2.get_current_session_by_id(session_id, current_user, db)
    
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

@router.post("/disconnect-session/{session_id}", status_code=status.HTTP_200_OK)
async def disconnect_session(
    session_id: str,
    current_user: models.User = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
):
    """Disconnect database for the specified session"""
    # Validate session belongs to user
    session = oauth2.get_current_session_by_id(session_id, current_user, db)
    
    try:
        from src.Tools.Tools import cleanup_session
        
        # Use the cleanup function from Tools
        cleanup_success = cleanup_session(session_id)
        
        if not cleanup_success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="Failed to cleanup session resources"
            )
        
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


  
@router.delete("/delete_all_sessions", status_code=status.HTTP_200_OK)
async def delete_all_sessions(
    current_user: models.User = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
):
    """Delete all sessions for the current user"""
    
    # Query sessions directly from database
    sessions = db.query(models.Session).filter(models.Session.user_id == current_user.id).all()
    
    if not sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="No sessions found for the user"
        )
    
    # Clean up session resources before deleting from database
    try:
        from src.Tools.Tools import cleanup_session
        for session in sessions:
            cleanup_session(session.session_token)
    except ImportError:
        pass  # Tools cleanup is optional
    
    # Delete all sessions from database
    session_count = len(sessions)
    for session in sessions:
        db.delete(session)
    
    db.commit()
    
    return {
        "message": "All sessions deleted successfully",
        "user_id": current_user.id,
        "deleted_sessions_count": session_count
    }

@router.delete("/delete_session/{session_id}", status_code=status.HTTP_200_OK)
async def delete_session(
    session_id: str,
    current_user: models.User = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a specific session for the current user"""
    
    session = db.query(models.Session).filter(
        models.Session.session_token == session_id,
        models.Session.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Session not found or does not belong to the user"
        )
    
    # Clean up session resources before deleting from database
    try:
        from src.Tools.Tools import cleanup_session
        cleanup_session(session_id)
    except ImportError:
        pass  # Tools cleanup is optional
    
    db.delete(session)
    db.commit()
        
    return {
            "message": "Session deleted successfully",
            "session_id": session_id,
            "user_id": current_user.id
        }





@router.get("/new_session", status_code=status.HTTP_201_CREATED)
async def create_new_session(
    current_user: models.User = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new session for the current user"""
    import uuid
    
    # Generate a new UUID for the session
    new_session_token = str(uuid.uuid4())
    
    new_session = models.Session(
        session_token=new_session_token,
        user_id=current_user.id
    )
    
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return {
        "message": "New session created successfully",
        "session_id": new_session.session_token,  # UUID serving as session identifier
        "thread_id": new_session.session_token,   # Same UUID serving as conversation thread identifier
        "user_id": current_user.id
    }


@router.get("/select_session/{session_id}", status_code=status.HTTP_200_OK)
async def select_session(
    session_id: str,
    user_session: models.User = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
):
    
    session = db.query(models.Session).filter(
        models.Session.session_token == session_id,
        models.Session.user_id == user_session.id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or does not belong to the user"
        )

    return {
        "message": "Session selected successfully",
        "session_id": session.session_token,
        "thread_id": session.session_token,
        "user_id": user_session.id
    }
