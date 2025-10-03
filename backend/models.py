from database import Base 
from sqlalchemy import Column, Integer, String, Boolean , ForeignKey 
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql import text
from sqlalchemy.orm import relationship






class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    thread_id = Column(String, unique=True, nullable=True)  # One thread per user
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)
    number_of_connections = Column(Integer, default=0, nullable=False)

    # One-to-Many: User -> DB Connections
    db_connections = relationship("DB_Connection_Details", back_populates="owner", cascade="all, delete")


class DB_Connection_Details(Base): 
    __tablename__ = 'db_connection_details'
    id = Column(Integer, primary_key=True, nullable=False)
    db_type = Column(String, nullable=False)
    host = Column(String, nullable=False)
    port = Column(Integer, nullable=False)
    database_name = Column(String, nullable=False)
    username = Column(String, nullable=False)
    db_password = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)

    owner = relationship("User", back_populates="db_connections")








  