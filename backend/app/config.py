import os

from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__),'../../.env')

load_dotenv(dotenv_path)

class Config:
    POSTGRES_USER = os.getenv('POSTGRES_USER')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
    POSTGRES_PORT=os.getenv('POSTGRES_PORT')
    POSTGRES_HOST=os.getenv('POSTGRES_HOST')
    POSTGRES_DATABASE=os.getenv('POSTGRES_DATABASE')
    
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DATABASE}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False