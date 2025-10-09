import models, schemas, utils
from database import get_db
from fastapi import FastAPI , status , HTTPException , Depends , APIRouter
from sqlalchemy.orm import Session 
import oauth2
from urllib.parse import quote_plus



router = APIRouter(
    prefix="/databases",
    tags=["Databases"]
)

@router.post("/add_db_connection", status_code=status.HTTP_201_CREATED)
async def add_db_connection(
    new_db: schemas.DBConfig, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    # Create database connection with automatic owner_id from authenticated user
    db_data = new_db.dict()
    db_data["owner_id"] = current_user.id  # Automatically set owner_id from JWT token
    
    # URL-encode username and password to handle special characters like @ symbols
    encoded_username = quote_plus(db_data['username'])
    encoded_password = quote_plus(db_data['db_password'])
    connection_string = f"postgresql+psycopg2://{encoded_username}:{encoded_password}@{db_data['host']}:{db_data['port']}/{db_data['database_name']}"
    test_db = await test_db_connection(connection_string)
    if test_db["message"] != "Database connection successful":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid database connection details")
    
    new_database = models.DB_Connection_Details(**db_data)
    db.add(new_database)
    db.commit()
    db.refresh(new_database)
    
    # Return proper response with serializable data
    return {
        "message": "Database added successfully",
        "db_connection": {
            "id": new_database.id,
            "db_type": new_database.db_type,
            "host": new_database.host,
            "port": new_database.port,
            "database_name": new_database.database_name,
            "username": new_database.username,
            "owner_id": new_database.owner_id,
            "created_at": new_database.created_at.isoformat() if new_database.created_at else None
        }
    }

@router.get("/test_db_connection/{connection_string}", status_code=status.HTTP_200_OK)
async def test_db_connection(
    connection_string: str,
):
    """Test database connection using the provided connection string"""
    try:
        from src.Tools_Functions.db_connector import DBConnector
        db_connector = DBConnector(connection_string)
        connection = db_connector.connect()
        
        # Test if we can execute a simple query
        from sqlalchemy import text
        result = connection.execute(text("SELECT 1"))
        connection.close()
        
        return {"message": "Database connection successful"}
    except Exception as e:
        error_msg = str(e)
        
        # Provide more helpful error messages based on common issues
        if "password authentication failed" in error_msg:
            detail = "Database connection failed: Invalid username or password. Please verify your credentials."
        elif "does not exist" in error_msg:
            detail = "Database connection failed: Database does not exist. Please check the database name."
        elif "Connection refused" in error_msg or "could not connect to server" in error_msg:
            detail = "Database connection failed: Cannot reach the database server. Please check the host and port."
        elif "timeout" in error_msg:
            detail = "Database connection failed: Connection timeout. Please check your network connection and firewall settings."
        else:
            detail = f"Database connection failed: {error_msg}"
            
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


@router.post("/connect_db/{db_id}/{session_id}", status_code=status.HTTP_200_OK)
async def connect_db(
    db_id: int,
    session_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
): 
    try:
        # Validate that the session belongs to the current user
        session = oauth2.get_current_session_by_id(session_id, current_user, db)
        
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
        # URL-encode username and password to handle special characters like @ symbols
        encoded_username = quote_plus(db_details.username)
        encoded_password = quote_plus(db_details.db_password)
        connection_string = f"postgresql+psycopg2://{encoded_username}:{encoded_password}@{db_details.host}:{db_details.port}/{db_details.database_name}"
        
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
            "db_id": db_details.id,
            "database_name": db_details.database_name,
            "user_id": current_user.id
        }
     
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error occurred with exception: {e}")
    


@router.get("/databases/{user_id}", status_code=status.HTTP_200_OK)
async def get_user_dbs(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):  
    if current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="You do not have permission to access these databases"
            )
    # Get databases for the currently authenticated user only
    db_connections = db.query(models.DB_Connection_Details).filter(
        models.DB_Connection_Details.owner_id == user_id
    ).all()
    
    return {
        "user_id": user_id,
        "databases": db_connections
    }

