from fastapi import FastAPI
from .database import engine, Base
from . import models

app = FastAPI()

# 데이터베이스에 테이블 생성
Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}
