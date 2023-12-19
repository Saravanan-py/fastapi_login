# from fastapi import FastAPI, HTTPException
# from enum import Enum
# from typing import Optional
# from pydantic import BaseModel, Field
# from uuid import UUID


# @app.get('/')
# async def home():
#     return {"name": "saravanan"}
#
#
# @app.put('/')
# async def index():
#     return {"sample": "data"}
#
#
# @app.get('/item/me')
# async def item():
#     return {"data": "Hey this is me!"}
#
#
# @app.get('/item/{item_id}')
# async def item(item_id: str):
#     return {"item": item_id}
#
#
# class FoodEnum(str, Enum):
#     vegetables = "vegetables"
#     fruits = "fruits"
#
#
# @app.get('/foods/{food_name}')
# async def food(food_name: FoodEnum):
#     if food_name == FoodEnum.vegetables:
#         return {"food_name": food_name, "message": "You are healthy"}
#     if food_name.value == "fruits":
#         return {"food_name": food_name, "message": "You are healthy, but it is sweety"}
#     return {"message": "nothing"}
#
#
# # query parameters
# dic = [{"a": 1}, {"b": 2}, {"c": 3}]
#
#
# @app.get('/items')
# async def items(skip: int = 0, limit: int = 10):
#     return dic[skip: skip + limit]
#
#
# # optional queryparameters
#
# @app.get('/items/{phn_no}')
# async def items(item_id: str, q: Optional[str] = None):
#     if q:
#         return {"item_id": item_id, "q": q}
#     return {"item_id": item_id}
#
#
# @app.get('/i/b/s/{item_id}')
# async def get_item(item_id: str, q: Optional[str] = None, short: bool = True):
#     items = {"item_id": item_id}
#     # if q:
#     #     item.update({"q": q})
#     if short == True:
#         items.update({'description': 'Hello Everyone....'})
#     return items

#
# class Books(BaseModel):
#     id: UUID
#     title: str = Field(min_length=1)
#     author: str = Field(min_length=1, max_length=100)
#     description: str = Field(min_length=1, max_length=100)
#     rating: int = Field(gt=-1, lt=101)
#
#
# BOOKS = []
#
#
# @app.get('/books')
# def booksss():
#     return BOOKS
#
#
# @app.post('/books')
# def create_book(book: Books):
#     BOOKS.append(book)
#     return book
#
#
# @app.put('/{book_id}')
# def update(book_id: UUID, book: Books):
#     count = 0
#     for x in BOOKS:
#         count += 1
#         if x.id == book_id:
#             BOOKS[count - 1] = book
#             return BOOKS[count - 1]
#     raise HTTPException(
#         status_code=404,
#         detail=f"ID {book_id} does not exist"
#     )
#
#
# @app.delete('/{book_id}')
# def update(book_id: UUID, book: Books):
#     count = 0
#     for x in BOOKS:
#         count += 1
#         if x.id == book_id:
#             del BOOKS[count - 1]
#             return f" {book_id} is Deleted"
#     raise HTTPException(
#         status_code=404,
#         detail=f"ID {book_id} does not exist"
#     )

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
import models1
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from twilio.rest import Client
import random
import logging
from datetime import datetime

app = FastAPI()

from auth import AuthHandler

auth_handler = AuthHandler()

models1.Base.metadata.create_all(bind=engine)

account_sid = "ACfb2e9d76da8709d16651db3a409e71ae"
auth_token = "46e2d17a0a26befc2146e664ca8d606a"
twilio_phone_number = "+12057749667"


def generate_otp():
    return str(random.randint(1000, 9999))


def send_otp_via_twilio(to_phone_number, otp):
    client = Client(account_sid, auth_token)

    message_body = f"Your OTP is: {otp}"

    message = client.messages.create(
        body=message_body,
        from_=twilio_phone_number,
        to=to_phone_number
    )

    return otp


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


class Book(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    author: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=100)
    rating: int = Field(gt=-1, lt=101)


class OTPModel(BaseModel):
    phone_number: str = Field(min_length=1, max_length=20)


class UserModel(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=200)
    phone_number: str = Field(min_length=1, max_length=20)


class LoginModel(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=200)


BOOKS = []


@app.post('/get_otp')
def get_otp(otp: OTPModel, db: Session = Depends(get_db)):
    try:
        otp_model = models1.OTP()
        otp_model.phone_number = otp.phone_number
        otp_num = send_otp_via_twilio("+91" + str(otp.phone_number), str(generate_otp()))
        otp_model.otp = str(otp_num)

        db.add(otp_model)
        db.commit()

        # Return a JSON response indicating success
        return {"message": "OTP sent successfully"}
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.get('/{otp_check}')
def otp_check(otp_check: str, db: Session = Depends(get_db)):
    otp_table = db.query(models1.OTP).filter(models1.OTP.otp == otp_check).first()
    if otp_table is None:
        raise HTTPException(
            status_code=404,
            detail=f"ID {otp_check} : Does not exist"
        )
    otp_table.auth = 1
    db.add(otp_table)
    db.commit()
    return {"message": "you are successfully verified"}


users = []


@app.post('/register')
def Register(auth_details: UserModel, db: Session = Depends(get_db)):
    if any(x['username'] == auth_details.username for x in users):
        raise HTTPException(status_code=400, detail='Username is taken')

    hashed_password = auth_handler.get_password_hash(auth_details.password)
    otp_data = db.query(models1.OTP).filter(models1.OTP.phone_number == auth_details.phone_number).first()
    if otp_data.auth == 1:
        db_user = models1.User(
            username=auth_details.username,
            password=hashed_password,
            phn_num=auth_details.phone_number,
            # Include other user attributes based on your model
        )
        db.add(db_user)
        db.commit()
        users.append({
            'username': auth_details.username,
            'password': hashed_password
        })
        return 'Success'
    else:
        raise HTTPException(status_code=400, detail='Invalid OTP authentication status')


@app.post('/login')
def login(auth_details: LoginModel, db: Session = Depends(get_db)):
    user = db.query(models1.User).filter(models1.User.username == auth_details.username).first()
    if (user is None) or (not auth_handler.verify_password(auth_details.password, user.password)):
        raise HTTPException(status_code=401, detail='Invalid username and/or password')
    token = auth_handler.encode_token(user.username)
    login_table = models1.Login()
    login_table.username = auth_details.username
    login_table.token = token
    login_table.created_time = str(datetime.now())

    db.add(login_table)
    db.commit()

    return {'token': token}


@app.get('/unprotected/auth')
async def sample():
    return {"message": "hello world"}


@app.get('/protected/auth')
def protected(username=Depends(auth_handler.auth_wrapper)):
    return {'name': username,
            'message': "successfully authorized"}

# @app.get("/")
# def read_api(db: Session = Depends(get_db)):
#     return db.query(models1.Books).all()
#
#
# @app.post("/")
# def create_book(book: Book, db: Session = Depends(get_db)):
#     book_model = models1.Books()
#     book_model.title = book.title
#     book_model.author = book.author
#     book_model.description = book.description
#     book_model.rating = book.rating
#
#     db.add(book_model)
#     db.commit()
#
#     return book
#
#
# @app.put("/{book_id}")
# def update_book(book_id: int, book: Book, db: Session = Depends(get_db)):
#     book_model = db.query(models1.Books).filter(models1.Books.id == book_id).first()
#
#     if book_model is None:
#         raise HTTPException(
#             status_code=404,
#             detail=f"ID {book_id} : Does not exist"
#         )
#
#     book_model.title = book.title
#     book_model.author = book.author
#     book_model.description = book.description
#     book_model.rating = book.rating
#
#     db.add(book_model)
#     db.commit()
#
#     return {
#         "message": "Data is Updated",
#         "data": book
#     }
#
#
# @app.delete("/{book_id}")
# def delete_book(book_id: int, db: Session = Depends(get_db)):
#     book_model = db.query(models1.Books).filter(models1.Books.id == book_id).first()
#
#     if book_model is None:
#         raise HTTPException(
#             status_code=404,
#             detail=f"ID {book_id} : Does not exist"
#         )
#
#     db.query(models1.Books).filter(models1.Books.id == book_id).delete()
#
#     db.commit()
#     return f"ID {book_id} is Deleted"
