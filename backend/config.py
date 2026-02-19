"""
Configuration Settings
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application settings"""
    
    # API Settings
    API_HOST = '127.0.0.1'
    API_PORT = 5000
    SECRET_KEY = os.getenv('SECRET_KEY', 'finguard-ai-secret-key-2024-hackathon')
    DEBUG = True
    
    # MongoDB Settings
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
    DATABASE_NAME = 'finguard_ai'
    
    # File Upload Settings
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'tiff'}
    
    # AML Thresholds
    LARGE_TRANSACTION_THRESHOLD = 200000.0
    RAPID_MOVEMENT_COUNT = 3
    RAPID_MOVEMENT_HOURS = 1
    STRUCTURING_THRESHOLD = 49999.0
    
    # OpenAI (optional)
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

settings = Settings()