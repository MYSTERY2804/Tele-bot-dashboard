import logging
from src.database.models import ChatMessage

logger = logging.getLogger(__name__)

def log_bot_message(user_id: int, message_text: str, chat_id: int = None, 
                   reply_to_message_id: int = None, session_state: str = None, 
                   message_category: str = None):
    """
    Log a bot message to chat history
    
    Args:
        user_id: Telegram user ID
        message_text: The message text to save
        chat_id: Telegram chat ID
        reply_to_message_id: ID of the message this is replying to
        session_state: Current session state
        message_category: Category of the message ('workout', 'diet', 'reminder', 'progress', etc.)
    """
    try:
        ChatMessage.create_bot_message(
            user_id=user_id,
            message_text=message_text,
            chat_id=chat_id,
            reply_to_message_id=reply_to_message_id,
            session_state=session_state,
            message_category=message_category
        )
        logger.debug(f"Logged bot message for user {user_id}, category: {message_category}")
    except Exception as e:
        logger.error(f"Error logging bot message: {e}")

def log_workout_message(user_id: int, message_text: str, chat_id: int = None, 
                       reply_to_message_id: int = None, session_state: str = None):
    """Log a workout-related bot message"""
    log_bot_message(user_id, message_text, chat_id, reply_to_message_id, session_state, 'workout')

def log_diet_message(user_id: int, message_text: str, chat_id: int = None, 
                    reply_to_message_id: int = None, session_state: str = None):
    """Log a diet-related bot message"""
    log_bot_message(user_id, message_text, chat_id, reply_to_message_id, session_state, 'diet')

def log_reminder_message(user_id: int, message_text: str, chat_id: int = None, 
                        reply_to_message_id: int = None, session_state: str = None):
    """Log a reminder-related bot message"""
    log_bot_message(user_id, message_text, chat_id, reply_to_message_id, session_state, 'reminder')

def log_progress_message(user_id: int, message_text: str, chat_id: int = None, 
                        reply_to_message_id: int = None, session_state: str = None):
    """Log a progress-related bot message"""
    log_bot_message(user_id, message_text, chat_id, reply_to_message_id, session_state, 'progress')

def log_completion_message(user_id: int, message_text: str, chat_id: int = None, 
                          reply_to_message_id: int = None, session_state: str = None):
    """Log a completion-related bot message"""
    log_bot_message(user_id, message_text, chat_id, reply_to_message_id, session_state, 'completion')

def log_general_message(user_id: int, message_text: str, chat_id: int = None, 
                       reply_to_message_id: int = None, session_state: str = None):
    """Log a general bot message"""
    log_bot_message(user_id, message_text, chat_id, reply_to_message_id, session_state, 'general') 