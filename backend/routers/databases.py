import models, schemas, utils
from database import get_db
from fastapi import FastAPI , status , HTTPException , Depends , APIRouter
from sqlalchemy.orm import Session 



router = APIRouter(
    prefix="/databases",
    tags=["databases"]
)

@router.post("/add_db_connection", status_code=status.HTTP_201_CREATED)
async def add_db_connection(new_db:schemas.DBConfig , db:Session = Depends(get_db)):
    new_database = models.DB_Connection_Details(**new_db.dict())
    db.add(new_database)
    db.commit()
    db.refresh(new_database)
    return {
        "message": "Database added successfully",
        "db_connection": new_database
    }




@router.post("/connect_db/{db_id}", status_code=status.HTTP_200_OK)
async def connect_db(db_id: int , db:Session = Depends(get_db)): 
    try: 
        # Get the database connection details
        db_details = db.query(models.DB_Connection_Details).filter(models.DB_Connection_Details.id == db_id).first()
        
        if not db_details:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Database connection not found")
        
        # Build the connection string (using psycopg2 for synchronous operations)
        connection_string = f"postgresql+psycopg2://{db_details.username}:{db_details.db_password}@{db_details.host}:{db_details.port}/{db_details.database_name}"
        
        # Test the connection by creating a DBConnector and attempting to connect
        from src.Tools_Functions.db_connector import DBConnector
        db_connector = DBConnector(connection_string)
        connection = db_connector.connect()
        
        # If successful, close the test connection
        connection.close()
        
        # Update the global database connector in Tools system
        try:
            from src.Tools.Tools import update_db_connector
            update_success = update_db_connector(connection_string)
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
            "db_id": db_id,
            "database_name": db_details.database_name
        }
     
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error occurred with exception: {e}")
    


@router.get("/databases/{user_id}", status_code=status.HTTP_200_OK)
async def get_user_dbs(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    db_connections = db.query(models.DB_Connection_Details).filter(models.DB_Connection_Details.owner_id == user_id).all()
    
    return {
        "user_id": user_id,
        "databases": db_connections
    }