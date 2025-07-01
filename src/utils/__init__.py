import logging
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from src.database.models import ChatMessage, UserSession

logger = logging.getLogger(__name__)

def log_message(func):
    """Decorator to automatically log user and bot messages"""
    @wraps(func)
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        message_id = update.message.message_id if update.message else None
        
        # Get current session state
        session = UserSession.get_by_user_id(user_id)
        session_state = session.conversation_state if session else None
        
        # Log user message
        if update.message and update.message.text:
            # Check if it's a command
            is_command = update.message.text.startswith('/')
            command_name = update.message.text.split()[0][1:] if is_command else None
            
            ChatMessage.create_user_message(
                user_id=user_id,
                message_text=update.message.text,
                message_id=message_id,
                chat_id=chat_id,
                is_command=is_command,
                command_name=command_name,
                session_state=session_state
            )
        
        # Call the original function
        result = await func(self, update, context, *args, **kwargs)
        
        return result
    
    return wrapper

def log_bot_response(user_id: int, message_text: str, chat_id: int = None, 
                    reply_to_message_id: int = None, session_state: str = None):
    """Log a bot response message"""
    try:
        ChatMessage.create_bot_message(
            user_id=user_id,
            message_text=message_text,
            chat_id=chat_id,
            reply_to_message_id=reply_to_message_id,
            session_state=session_state
        )
    except Exception as e:
        logger.error(f"Error logging bot response: {e}")

def log_user_message(user_id: int, message_text: str, chat_id: int = None,
                    message_id: int = None, reply_to_message_id: int = None,
                    is_command: bool = False, command_name: str = None,
                    session_state: str = None):
    """Log a user message"""
    try:
        ChatMessage.create_user_message(
            user_id=user_id,
            message_text=message_text,
            message_id=message_id,
            chat_id=chat_id,
            reply_to_message_id=reply_to_message_id,
            is_command=is_command,
            command_name=command_name,
            session_state=session_state
        )
    except Exception as e:
        logger.error(f"Error logging user message: {e}")

# Chat message logging utilities
