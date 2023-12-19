from sqlalchemy import Column, Integer, String
from database import Base


class Books(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100))
    author = Column(String(100))
    description = Column(String(100))
    rating = Column(Integer)
    otp = Column(Integer)


class OTP(Base):
    __tablename__ = "otp"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, index=True)
    otp = Column(Integer)
    auth = Column(Integer, default=0)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(40), index=True)
    password = Column(String(100), index=True)
    phn_num = Column(String(20), index=True)


class Login(Base):
    __tablename__ = "login"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(40), index=True)
    token = Column(String(255), index=True)
    created_time = Column(String(50), index=True)
