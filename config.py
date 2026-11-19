import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    RESEND_API_KEY = os.getenv("RESEND_API_KEY")
    DOMAIN = os.getenv("DOMAIN", "http://localhost:5000")