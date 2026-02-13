from sqlalchemy import Column, Integer, String
from .database import Base


class User(Base):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String, unique=True)
    email = Column(String, unique=True)
    password = Column(String)

    linkedin = Column(String, nullable=True)
    github = Column(String, nullable=True)
    resume = Column(String, nullable=True)

    avatar = Column(String, default="Male1.png")
