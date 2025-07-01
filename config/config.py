import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    BOT_USERNAME = os.getenv('BOT_USERNAME')
    
    # Gemini AI Configuration
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # Supabase Configuration
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    SUPABASE_DB_URL = os.getenv('SUPABASE_DB_URL')
    
    # Bot Settings
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Conversation States
    class States:
        NEW_USER = "NEW_USER"
        COLLECTING_FIRST_NAME = "COLLECTING_FIRST_NAME"
        COLLECTING_LAST_NAME = "COLLECTING_LAST_NAME"
        COLLECTING_AGE = "COLLECTING_AGE"
        COLLECTING_HEIGHT = "COLLECTING_HEIGHT"
        COLLECTING_WEIGHT = "COLLECTING_WEIGHT"
        COLLECTING_FITNESS_LEVEL = "COLLECTING_FITNESS_LEVEL"
        COLLECTING_GOALS = "COLLECTING_GOALS"
        COLLECTING_WORKOUT_TIME = "COLLECTING_WORKOUT_TIME"
        COLLECTING_BREAKFAST_TIME = "COLLECTING_BREAKFAST_TIME"
        COLLECTING_LUNCH_TIME = "COLLECTING_LUNCH_TIME"
        COLLECTING_DINNER_TIME = "COLLECTING_DINNER_TIME"
        COLLECTING_SNACK_TIME = "COLLECTING_SNACK_TIME"
        ACTIVE = "ACTIVE"
        SCHEDULE_GENERATION = "SCHEDULE_GENERATION"
        EXERCISE_TRACKING = "EXERCISE_TRACKING"
        TRAINER_REVIEW = "TRAINER_REVIEW"

    
    @classmethod
    def validate_config(cls):
        """Validate that all required configuration is present"""
        required_vars = [
            'TELEGRAM_BOT_TOKEN',
            'GEMINI_API_KEY',
            'SUPABASE_URL',
            'SUPABASE_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True