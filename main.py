from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import List, Optional


# =============================================
# НАСТРОЙКА БАЗЫ ДАННЫХ И МОДЕЛЕЙ
# =============================================

# Подключение к SQLite базе данных (файл simcards.db будет создан автоматически)
SQLALCHEMY_DATABASE_URL = "sqlite:///./sbpreports.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
