import models, schemas, utils
from database import get_db
from fastapi import FastAPI , status , HTTPException , Depends , APIRouter
from sqlalchemy.orm import Session 
import uuid


router = APIRouter(
    prefix="/users",
    tags=["users"]
)




@router.post("/createuser", status_code=status.HTTP_201_CREATED , response_model=schemas.User_Response)  # Use response_model to return UserResponse schema
async def create_user(new_user: schemas.User_create, db: Session = Depends(get_db)): 

    # Check if email already exists BEFORE creating the user
    existing_user = db.query(models.User).filter(models.User.email == new_user.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

    # Hash the password before storing it
    hashed_password = utils.hash(new_user.password)
    new_user.password = hashed_password  # Update the password with the hashed value
    new_user.thread_id = str(uuid.uuid4())  # Generate a unique thread_id for the user
    


    new_user = models.User(**new_user.dict())  # Create User model from dict
    db.add(new_user)
    db.commit()  # Commit the transaction to save changes
    db.refresh(new_user)  # Refresh the instance to get the updated data

    return new_user


@router.get("/{id}", response_model=schemas.User_Response)
async def get_user(id:int , db :Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == id).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return user