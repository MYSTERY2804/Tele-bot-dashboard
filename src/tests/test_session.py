import logging
from src.database.models import UserSession
from src.database.supabase_client import SupabaseClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_session_handling():
    """Test session creation and retrieval"""
    test_user_id = 1362163381
    
    # First refresh schema
    try:
        SupabaseClient.refresh_schema()
        logger.info("Schema cache refreshed successfully")
    except Exception as e:
        logger.error(f"Failed to refresh schema: {e}")
        return False
    
    # Test session retrieval
    session = UserSession.get_by_user_id(test_user_id)
    if session:
        logger.info(f"Session loaded successfully: {session.__dict__}")
    else:
        logger.info("Creating new session...")
        session = UserSession(user_id=test_user_id)
        if session.save():
            logger.info("New session created successfully")
        else:
            logger.error("Failed to create new session")
            return False
    
    # Verify session attributes
    assert hasattr(session, 'current_exercise_index'), "Missing current_exercise_index"
    assert hasattr(session, 'current_workout_id'), "Missing current_workout_id"
    assert hasattr(session, 'last_updated'), "Missing last_updated"
    
    logger.info("Session verification completed successfully")
    return True

if __name__ == "__main__":
    if test_session_handling():
        logger.info("All session tests passed!")
    else:
        logger.error("Session tests failed!") 