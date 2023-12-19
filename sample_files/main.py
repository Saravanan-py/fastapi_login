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
        return {"message": "OTP sent successfully"}
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Check your number >>>")


@app.get('/{otp_check}')
def otp_check(otp_check: str, db: Session = Depends(get_db)):
    otp_table = db.query(models1.OTP).filter(models1.OTP.otp == otp_check).first()
    if otp_table is None:
        raise HTTPException(
            status_code=404,
            detail=f"{otp_check} : Does not exist. You ID is Expired"
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

        )
        db.add(db_user)
        db.commit()
        users.append({
            'username': auth_details.username,
            'password': hashed_password
        })
        return {
            'message': 'User is successfully registered'
        }
    else:
        raise HTTPException(status_code=400, detail='Invalid OTP authentication status')


login_users = []


@app.post('/login')
def login(auth_details: LoginModel, db: Session = Depends(get_db)):
    user = db.query(models1.User).filter(models1.User.username == auth_details.username).first()
    if (user is None) or (not auth_handler.verify_password(auth_details.password, user.password)):
        raise HTTPException(status_code=401, detail='Invalid username and/or password')
    if any(x['username'] == auth_details.username for x in login_users):
        login_table = db.query(models1.Login).filter(models1.Login.username == auth_details.username).first()
        token = auth_handler.encode_token(auth_details.username)
        login_table.token = token
        login_table.created_time = str(datetime.now())
        db.add(login_table)
        db.commit()
    else:
        token = auth_handler.encode_token(auth_details.username)
        login_table = models1.Login()
        login_table.username = auth_details.username
        login_table.token = token
        login_table.created_time = str(datetime.now())
        db.add(login_table)
        db.commit()



    login_users.append({
        'username': auth_details.username,
    })

    return {'token': token}


@app.post('/logout/{username}')
def logout(username: str, db: Session = Depends(get_db)):
    login_table = db.query(models1.Login).filter(models1.Login.username == username).first()


    if login_table is None:
            raise HTTPException(
                status_code=404,
                detail=f"Name {username} : Does not exist"
            )
    db.query(models1.Login).filter(models1.Login.username == username).delete()
    db.commit()
    return {'message': 'You are Logged Out'}

@app.get('/unprotected/auth')
def sample():
    return {"message": "hello world"}


@app.get('/protected/auth')
def protected(username=Depends(auth_handler.auth_wrapper)):
    return {'name': username,
            'message': "successfully authorized"}
