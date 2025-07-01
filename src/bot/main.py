import logging
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config.config import Config
from src.bot.handlers import BotHandlers
import asyncio
import threading
import time

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO if Config.DEBUG else logging.WARNING
)
logger = logging.getLogger(__name__)

class WorkoutBot:
    def __init__(self):
        """Initialize the workout bot"""
        self.application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        self.handlers = BotHandlers()
        self.reminder_service = None
        self.reminder_thread = None
        self.stop_reminders = False
    
    def setup_handlers(self):
        """Set up all bot handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", BotHandlers.start_command))
        self.application.add_handler(CommandHandler("help", BotHandlers.help_command))
        self.application.add_handler(CommandHandler("schedule", self.handlers.handle_schedule_command))
        self.application.add_handler(CommandHandler("progress", BotHandlers.handle_progress_request))
        self.application.add_handler(CommandHandler("test_reminders", BotHandlers.test_reminders_command))
        self.application.add_handler(CommandHandler("updatename", self.update_name_command))

        # Callback query handler for inline keyboards
        self.application.add_handler(CallbackQueryHandler(
            BotHandlers.handle_fitness_level, 
            pattern="^level_"
        ))
        
        # Handle both exercise completion and skip
        self.application.add_handler(CallbackQueryHandler(
            self.handlers.handle_exercise_completion,
            pattern="^exercise_(done|skip)_"
        ))

        # Handle both diet completion and skip
        self.application.add_handler(CallbackQueryHandler(
            BotHandlers.handle_diet_completion,
            pattern="^diet_(complete|skip)_"
        ))

        # Handle meal completion and skip
        self.application.add_handler(CallbackQueryHandler(
            BotHandlers.handle_meal_completion,
            pattern="^meal_(complete|skip)_"
        ))

        # Handle reminder completion and skip
        self.application.add_handler(CallbackQueryHandler(
            BotHandlers.handle_reminder_completion,
            pattern="^reminder_(complete|skip)_"
        ))

        # Handle other callback queries
        self.application.add_handler(CallbackQueryHandler(
            BotHandlers.handle_callback_queries,
            pattern="^(?!exercise_(done|skip)_|diet_(complete|skip)_|meal_(complete|skip)_|reminder_(complete|skip)_|level_)"
        ))

        # Message handlers for Gemini Q&A
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            BotHandlers.handle_general_message
        ))

        # Error handler
        self.application.add_error_handler(BotHandlers.error_handler)
        
        logger.info("All handlers set up successfully")
    
    def start_reminder_service(self):
        """Start the reminder service in a background thread"""
        try:
            from src.services.reminder_service import ReminderService
            self.reminder_service = ReminderService(self.application.bot)
            
            # Start reminder service in a separate thread
            self.reminder_thread = threading.Thread(target=self._run_reminder_service, daemon=True)
            self.reminder_thread.start()
            
            logger.info("Reminder service started successfully")
        except Exception as e:
            logger.error(f"Failed to start reminder service: {e}")
    
    def _run_reminder_service(self):
        """Run the reminder service in a separate thread"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.reminder_service.start())
        except Exception as e:
            logger.error(f"Reminder service error: {e}")
    
    def stop_reminder_service(self):
        """Stop the reminder service"""
        if self.reminder_service:
            self.reminder_service.stop()
            self.stop_reminders = True
            if self.reminder_thread:
                self.reminder_thread.join(timeout=5)
            logger.info("Reminder service stopped")
    
    async def update_name_command(self, update, context):
        """Command to manually update user name information"""
        from src.database.models import User
        
        user_id = update.effective_user.id
        first_name = update.effective_user.first_name
        last_name = update.effective_user.last_name
        username = update.effective_user.username
        
        # Get or create user
        user = User.get_by_user_id(user_id)
        if not user:
            user = User(
                user_id=user_id,
                first_name=first_name,
                last_name=last_name,
                username=username
            )
        else:
            # Update existing user's name information
            user.first_name = first_name
            user.last_name = last_name
            user.username = username
        
        user.save()
        
        await update.message.reply_text(
            f"✅ Name information updated!\n\n"
            f"First Name: {first_name or 'Not set'}\n"
            f"Last Name: {last_name or 'Not set'}\n"
            f"Username: @{username or 'Not set'}\n\n"
            f"Your name information has been saved to the database."
        )
    
    def run(self):
        """Run the bot synchronously using run_polling"""
        try:
            Config.validate_config()
            logger.info("Configuration validated successfully")
            self.setup_handlers()
            logger.info("Bot handlers set")

            # Start reminder service
            self.start_reminder_service()

            logger.info("🤖 Bot is running! Press Ctrl+C to stop.")
            
            # Start the bot
            self.application.run_polling(allowed_updates=["message", "callback_query"])

        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
            self.stop_reminder_service()
        except Exception as e:
            logger.error(f"Bot crashed: {e}")
            self.stop_reminder_service()
            raise

def main():
    """Main entry point"""
    print("🚀 Starting Workout Bot...")
    print("=" * 40)
    
    try:
        bot = WorkoutBot()
        bot.run()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped gracefully")
    except Exception as e:
        print(f"❌ Bot failed to start: {e}")
        return False

    return True

if __name__ == "__main__":
    main()
