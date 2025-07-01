import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from telegram import Bot
from src.database.models import Reminder, User, Workout, DietPlan
from src.database.supabase_client import supabase_client
from config.config import Config
from src.utils.chat_logger import log_reminder_message, log_completion_message

logger = logging.getLogger(__name__)

class ReminderService:
    """Service for handling reminders and notifications"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.is_running = False
        self.check_interval = 30  # Check every 30 seconds
    
    async def start(self):
        """Start the reminder service"""
        self.is_running = True
        logger.info("Reminder service started")
        
        while self.is_running:
            try:
                await self.check_and_send_reminders()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in reminder service: {e}")
                await asyncio.sleep(self.check_interval)
    
    def stop(self):
        """Stop the reminder service"""
        self.is_running = False
        logger.info("Reminder service stopped")
    
    async def check_and_send_reminders(self):
        """Check for pending reminders and send them"""
        try:
            # Get all pending reminders that need to be sent
            pending_reminders = Reminder.get_pending_reminders()
            
            for reminder in pending_reminders:
                await self.send_reminder(reminder)
                
        except Exception as e:
            logger.error(f"Error checking reminders: {e}")
    
    async def send_reminder(self, reminder: Reminder):
        """Send a reminder message to the user"""
        try:
            # Get user details
            user = User.get_by_user_id(reminder.user_id)
            if not user:
                logger.error(f"User {reminder.user_id} not found for reminder {reminder.id}")
                return
            
            # Create reminder message based on type
            message = self.create_reminder_message(reminder)
            
            # Create keyboard based on reminder type
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            
            if reminder.reminder_type == 'workout':
                # For workout reminders, include exercise completion buttons
                keyboard = await self.create_workout_reminder_keyboard(reminder)
            elif reminder.reminder_type in ['breakfast', 'lunch', 'dinner', 'snack']:
                # For meal reminders, include meal completion buttons
                keyboard = await self.create_meal_reminder_keyboard(reminder)
            else:
                # Fallback to simple complete/skip buttons
                keyboard = [
                    [
                        InlineKeyboardButton("✅ Complete", callback_data=f"reminder_complete_{reminder.id}"),
                        InlineKeyboardButton("⏭️ Skip", callback_data=f"reminder_skip_{reminder.id}")
                    ]
                ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send the reminder
            await self.bot.send_message(
                chat_id=reminder.user_id,
                text=message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            # Log reminder message
            log_reminder_message(
                user_id=reminder.user_id,
                message_text=message,
                chat_id=reminder.user_id
            )
            
            # Mark reminder as sent
            reminder.mark_sent()
            
            logger.info(f"Sent reminder {reminder.id} to user {reminder.user_id}")
            
        except Exception as e:
            logger.error(f"Error sending reminder {reminder.id}: {e}", exc_info=True)
    
    async def create_workout_reminder_keyboard(self, reminder: Reminder):
        """Create keyboard with exercise completion buttons for workout reminders"""
        try:
            from telegram import InlineKeyboardButton
            
            # Get the workout data
            from src.database.models import Workout
            workout = None
            workouts = Workout.get_user_workouts(reminder.user_id, limit=10)
            for w in workouts:
                if w.id == reminder.related_id:
                    workout = w
                    break
            
            if not workout or not workout.workout_content:
                # Fallback to simple complete/skip buttons
                return [
                    [
                        InlineKeyboardButton("✅ Complete Workout", callback_data=f"reminder_complete_{reminder.id}"),
                        InlineKeyboardButton("⏭️ Skip Workout", callback_data=f"reminder_skip_{reminder.id}")
                    ]
                ]
            
            # Get exercises from workout content
            exercises = workout.workout_content.get('exercises', [])
            if not exercises:
                # Fallback to simple complete/skip buttons
                return [
                    [
                        InlineKeyboardButton("✅ Complete Workout", callback_data=f"reminder_complete_{reminder.id}"),
                        InlineKeyboardButton("⏭️ Skip Workout", callback_data=f"reminder_skip_{reminder.id}")
                    ]
                ]
            
            # Create exercise completion buttons
            keyboard = []
            for i, exercise in enumerate(exercises):
                exercise_name = exercise.get('name', f'Exercise {i+1}')
                # Truncate long exercise names
                if len(exercise_name) > 15:
                    exercise_name = exercise_name[:12] + "..."
                
                keyboard.append([
                    InlineKeyboardButton(
                        f"✅ Complete {i+1}",
                        callback_data=f"exercise_done_{workout.id}_{i}"
                    ),
                    InlineKeyboardButton(
                        f"⏭️ Skip {i+1}",
                        callback_data=f"exercise_skip_{workout.id}_{i}"
                    )
                ])
            
            # Add overall workout completion buttons
            keyboard.append([
                InlineKeyboardButton("🎉 Complete All", callback_data=f"reminder_complete_{reminder.id}"),
                InlineKeyboardButton("⏭️ Skip All", callback_data=f"reminder_skip_{reminder.id}")
            ])
            
            return keyboard
            
        except Exception as e:
            logger.error(f"Error creating workout reminder keyboard: {e}")
            # Fallback to simple buttons
            return [
                [
                    InlineKeyboardButton("✅ Complete", callback_data=f"reminder_complete_{reminder.id}"),
                    InlineKeyboardButton("⏭️ Skip", callback_data=f"reminder_skip_{reminder.id}")
                ]
            ]
    
    async def create_meal_reminder_keyboard(self, reminder: Reminder):
        """Create keyboard with meal completion buttons for meal reminders"""
        try:
            from telegram import InlineKeyboardButton
            
            # Get the diet data
            from src.database.models import DietPlan
            diet_data = None
            user_diets = DietPlan.get_user_diets(reminder.user_id, limit=10)
            for d in user_diets:
                if d.get('id') == reminder.related_id:
                    diet_data = d
                    break
            
            if not diet_data:
                # Fallback to simple complete/skip buttons
                return [
                    [
                        InlineKeyboardButton("✅ Complete", callback_data=f"reminder_complete_{reminder.id}"),
                        InlineKeyboardButton("⏭️ Skip", callback_data=f"reminder_skip_{reminder.id}")
                    ]
                ]
            
            # Get meal details from diet content
            diet_content = diet_data.get('diet_content', {})
            meals = diet_content.get('meals', [])
            snacks = diet_content.get('snacks', [])
            
            # Find the specific meal for this reminder
            meal_name = reminder.content.get('meal_name', reminder.reminder_type.title())
            meal_type = reminder.reminder_type
            
            # Create meal completion buttons - ONLY 2 buttons per meal
            keyboard = [
                [
                    InlineKeyboardButton(
                        f"✅ Done",
                        callback_data=f"meal_complete_{diet_data['id']}_{meal_type}"
                    ),
                    InlineKeyboardButton(
                        f"⏭️ Skip",
                        callback_data=f"meal_skip_{diet_data['id']}_{meal_type}"
                    )
                ]
            ]
            
            # Only add "View Progress" button for dinner
            if meal_type == 'dinner':
                keyboard.append([
                    InlineKeyboardButton("📊 View Progress", callback_data="show_stats")
                ])
            
            return keyboard
            
        except Exception as e:
            logger.error(f"Error creating meal reminder keyboard: {e}")
            # Fallback to simple buttons
            return [
                [
                    InlineKeyboardButton("✅ Complete", callback_data=f"reminder_complete_{reminder.id}"),
                    InlineKeyboardButton("⏭️ Skip", callback_data=f"reminder_skip_{reminder.id}")
                ]
            ]
    
    def create_reminder_message(self, reminder: Reminder) -> str:
        """Create a formatted reminder message"""
        emoji_map = {
            'workout': '💪',
            'breakfast': '🍳',
            'lunch': '🍽️',
            'dinner': '🍴',
            'snack': '🍎'
        }
        
        emoji = emoji_map.get(reminder.reminder_type, '⏰')
        
        if reminder.reminder_type == 'workout':
            # Get workout details for enhanced message
            from src.database.models import Workout
            workout = None
            workouts = Workout.get_user_workouts(reminder.user_id, limit=10)
            for w in workouts:
                if w.id == reminder.related_id:
                    workout = w
                    break
            
            base_message = (
                f"{emoji} **Workout Reminder**\n\n"
                f"Time to get moving! Your workout is scheduled for {reminder.scheduled_time}.\n\n"
                f"🎯 **Today's Focus**: {reminder.content.get('workout_type', 'Full Body')}\n"
                f"⏱️ **Duration**: {reminder.content.get('duration_minutes', 30)} minutes\n"
                f"🔥 **Est. Calories**: {reminder.content.get('calories_estimate', 'N/A')}\n\n"
            )
            
            # Add exercise details if available
            if workout and workout.workout_content:
                exercises = workout.workout_content.get('exercises', [])
                if exercises:
                    base_message += "**Today's Exercises:**\n"
                    for i, exercise in enumerate(exercises[:5], 1):  # Show first 5 exercises
                        base_message += f"{i}. {exercise.get('name', 'Exercise')} - {exercise.get('sets', 3)} sets × {exercise.get('reps', '10-12')} reps\n"
                    if len(exercises) > 5:
                        base_message += f"... and {len(exercises) - 5} more exercises\n"
                    base_message += "\n"
            
            base_message += (
                f"Get ready to crush your fitness goals! 💪\n\n"
                f"Use the buttons below to track your progress!"
            )
            
            return base_message
        else:
            meal_name = reminder.reminder_type.title()
            return (
                f"{emoji} **{meal_name} Reminder**\n\n"
                f"Time for {meal_name.lower()}! Scheduled for {reminder.scheduled_time}.\n\n"
                f"🥗 **Today's {meal_name} Plan**:\n"
                f"• {reminder.content.get('meal_name', 'Healthy meal')}\n"
                f"• {reminder.content.get('total_calories', 'N/A')} calories\n\n"
                f"Stay on track with your nutrition goals! 🎯\n\n"
                f"Tap 'Complete' when you finish your {meal_name.lower()}, or 'Skip' if you need to reschedule."
            )
    
    @staticmethod
    def create_daily_reminders(user_id: int, workout_data: dict, diet_data: dict, 
                              workout_time: str, breakfast_time: str, lunch_time: str, 
                              dinner_time: str, snack_time: str):
        """Create reminders for a user's daily schedule"""
        try:
            from datetime import datetime, timedelta
            
            logger.info(f"Creating daily reminders for user {user_id}")
            logger.info(f"Times: workout={workout_time}, breakfast={breakfast_time}, lunch={lunch_time}, dinner={dinner_time}, snack={snack_time}")
            
            # Get current time
            now = datetime.now()
            current_time = now.strftime('%H:%M')
            
            # Check if all times have passed for today
            times = [workout_time, breakfast_time, lunch_time, dinner_time, snack_time]
            times = [t for t in times if t]  # Remove None/empty times
            
            all_passed = all(t < current_time for t in times)
            
            if all_passed:
                logger.info(f"All times have passed for today. Reminders will be created for tomorrow.")
                # For now, we'll create reminders for today anyway, but they won't be pending
                # In a future version, we could create them for tomorrow
            
            # Create workout reminder
            if workout_data and workout_time:
                workout_content = {
                    'workout_type': workout_data.get('workout_type', 'Full Body'),
                    'duration_minutes': workout_data.get('duration_minutes', 30),
                    'calories_estimate': workout_data.get('calories_estimate', 'N/A')
                }
                workout_reminder = Reminder.create_reminder(
                    user_id=user_id,
                    reminder_type='workout',
                    scheduled_time=workout_time,
                    content=workout_content,
                    related_id=workout_data.get('id'),
                    related_type='workout'
                )
                logger.info(f"Created workout reminder: {workout_reminder}")
            
            # Create meal reminders
            if diet_data:
                # Extract diet_content from the database record
                diet_content = diet_data.get('diet_content', {}) if isinstance(diet_data, dict) else diet_data
                meals = diet_content.get('meals', [])
                snacks = diet_content.get('snacks', [])
                
                logger.info(f"Diet data found: {len(meals)} meals, {len(snacks)} snacks")
                logger.info(f"Diet content keys: {list(diet_content.keys()) if isinstance(diet_content, dict) else 'Not a dict'}")
                
                # Breakfast reminder
                if breakfast_time and meals:
                    # Find breakfast meal or use first meal
                    breakfast_meal = None
                    for meal in meals:
                        if 'breakfast' in meal.get('name', '').lower():
                            breakfast_meal = meal
                            break
                    if not breakfast_meal and meals:
                        breakfast_meal = meals[0]  # Use first meal as breakfast
                    
                    if breakfast_meal:
                        breakfast_reminder = Reminder.create_reminder(
                            user_id=user_id,
                            reminder_type='breakfast',
                            scheduled_time=breakfast_time,
                            content={
                                'meal_name': breakfast_meal.get('name', 'Breakfast'),
                                'total_calories': breakfast_meal.get('total_calories', 'N/A')
                            },
                            related_id=diet_data.get('id'),
                            related_type='diet'
                        )
                        logger.info(f"Created breakfast reminder: {breakfast_reminder}")
                    else:
                        logger.warning(f"No breakfast meal found in diet data")
                
                # Lunch reminder
                if lunch_time and meals:
                    # Find lunch meal or use second meal
                    lunch_meal = None
                    for meal in meals:
                        if 'lunch' in meal.get('name', '').lower():
                            lunch_meal = meal
                            break
                    if not lunch_meal and len(meals) > 1:
                        lunch_meal = meals[1]  # Use second meal as lunch
                    elif not lunch_meal and meals:
                        lunch_meal = meals[0]  # Use first meal if only one exists
                    
                    if lunch_meal:
                        lunch_reminder = Reminder.create_reminder(
                            user_id=user_id,
                            reminder_type='lunch',
                            scheduled_time=lunch_time,
                            content={
                                'meal_name': lunch_meal.get('name', 'Lunch'),
                                'total_calories': lunch_meal.get('total_calories', 'N/A')
                            },
                            related_id=diet_data.get('id'),
                            related_type='diet'
                        )
                        logger.info(f"Created lunch reminder: {lunch_reminder}")
                    else:
                        logger.warning(f"No lunch meal found in diet data")
                
                # Dinner reminder
                if dinner_time and meals:
                    # Find dinner meal or use last meal
                    dinner_meal = None
                    for meal in meals:
                        if 'dinner' in meal.get('name', '').lower():
                            dinner_meal = meal
                            break
                    if not dinner_meal and meals:
                        dinner_meal = meals[-1]  # Use last meal as dinner
                    
                    if dinner_meal:
                        dinner_reminder = Reminder.create_reminder(
                            user_id=user_id,
                            reminder_type='dinner',
                            scheduled_time=dinner_time,
                            content={
                                'meal_name': dinner_meal.get('name', 'Dinner'),
                                'total_calories': dinner_meal.get('total_calories', 'N/A')
                            },
                            related_id=diet_data.get('id'),
                            related_type='diet'
                        )
                        logger.info(f"Created dinner reminder: {dinner_reminder}")
                    else:
                        logger.warning(f"No dinner meal found in diet data")
                
                # Snack reminder
                if snack_time and snacks:
                    snack = snacks[0] if snacks else {}
                    snack_reminder = Reminder.create_reminder(
                        user_id=user_id,
                        reminder_type='snack',
                        scheduled_time=snack_time,
                        content={
                            'meal_name': snack.get('name', 'Snack'),
                            'total_calories': snack.get('total_calories', 'N/A')
                        },
                        related_id=diet_data.get('id'),
                        related_type='diet'
                    )
                    logger.info(f"Created snack reminder: {snack_reminder}")
                elif snack_time:
                    logger.warning(f"Snack time provided but no snacks found in diet data")
            else:
                logger.warning(f"No diet data provided for user {user_id}")
            
            logger.info(f"Successfully created daily reminders for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error creating daily reminders for user {user_id}: {e}", exc_info=True)
    
    @staticmethod
    async def handle_reminder_completion(bot: Bot, reminder_id: int, action: str):
        """Handle reminder completion or skip"""
        try:
            # Get the reminder by ID
            result = supabase_client.client.table('reminders').select('*').eq('id', reminder_id).execute()
            
            if not result.data:
                logger.error(f"Reminder {reminder_id} not found")
                return
            
            reminder_data = result.data[0]
            reminder = Reminder(
                id=reminder_data['id'],
                user_id=reminder_data['user_id'],
                reminder_type=reminder_data['reminder_type'],
                scheduled_time=reminder_data['scheduled_time'],
                reminder_time=reminder_data['reminder_time'],
                content=reminder_data['content'],
                status=reminder_data['status'],
                related_id=reminder_data['related_id'],
                related_type=reminder_data['related_type'],
                created_at=reminder_data['created_at'],
                sent_at=reminder_data['sent_at'],
                completed_at=reminder_data['completed_at']
            )
            
            # Handle based on reminder type
            if reminder.reminder_type == 'workout':
                await ReminderService.handle_workout_reminder_completion(bot, reminder, action)
            else:
                # Handle meal reminders
                await ReminderService.handle_meal_reminder_completion(bot, reminder, action)
            
            logger.info(f"Reminder {reminder_id} marked as {action}")
            
        except Exception as e:
            logger.error(f"Error handling reminder completion: {e}")
    
    @staticmethod
    async def handle_workout_reminder_completion(bot: Bot, reminder: Reminder, action: str):
        """Handle workout reminder completion"""
        try:
            from src.database.models import Workout
            
            # Get the workout
            workouts = Workout.get_user_workouts(reminder.user_id, limit=10)
            workout = None
            for w in workouts:
                if w.id == reminder.related_id:
                    workout = w
                    break
            
            if not workout:
                await bot.send_message(
                    chat_id=reminder.user_id,
                    text="❌ Workout not found. Please try again."
                )
                return
            
            if action == 'complete':
                # Mark workout as completed
                workout.mark_completed()
                message = f"🎉 **Workout Completed!** 💪\n\nGreat job finishing your {workout.workout_content.get('workout_type', 'workout')}!\nYou burned approximately {workout.workout_content.get('calories_estimate', 200)} calories.\n\n🏆 Keep up the amazing work! Your consistency is building strength and discipline."
            else:
                # Mark workout as skipped
                workout.status = 'skipped'
                workout.completion_date = datetime.now()
                workout.save()
                message = f"⏭️ **Workout Skipped**\n\nNo worries! You can always try again later. Remember, consistency is key to achieving your fitness goals! 💪"
            
            # Mark reminder as completed
            reminder.mark_completed()
            
            # Send confirmation message
            await bot.send_message(
                chat_id=reminder.user_id,
                text=message,
                parse_mode='Markdown'
            )
            
            # Log completion message
            log_completion_message(
                user_id=reminder.user_id,
                message_text=message,
                chat_id=reminder.user_id
            )
            
        except Exception as e:
            logger.error(f"Error handling workout reminder completion: {e}")
            await bot.send_message(
                chat_id=reminder.user_id,
                text="❌ Error processing workout completion. Please try again."
            )
    
    @staticmethod
    async def handle_meal_reminder_completion(bot: Bot, reminder: Reminder, action: str):
        """Handle meal reminder completion"""
        try:
            from src.database.models import DietPlan
            
            # Get the diet plan
            user_diets = DietPlan.get_user_diets(reminder.user_id, limit=10)
            diet_data = None
            for d in user_diets:
                if d.get('id') == reminder.related_id:
                    diet_data = d
                    break
            
            if not diet_data:
                await bot.send_message(
                    chat_id=reminder.user_id,
                    text="❌ Diet plan not found. Please try again."
                )
                return
            
            # Create diet plan object
            diet = DietPlan(
                user_id=reminder.user_id,
                diet_content=diet_data['diet_content'],
                scheduled_date=diet_data['scheduled_date'],
                status='completed' if action == 'complete' else 'skipped',
                id=diet_data['id'],
                created_date=diet_data.get('created_date'),
                completion_date=datetime.now().date().isoformat()
            )
            
            # Save the updated diet plan
            diet.save()
            
            # Mark reminder as completed
            reminder.mark_completed()
            
            # Send confirmation message
            if action == 'complete':
                message = f"✅ **{reminder.reminder_type.title()} Completed!**\n\nGreat job following your nutrition plan! Keep up the healthy eating habits! 💪"
            else:
                message = f"⏭️ **{reminder.reminder_type.title()} Skipped**\n\nNo worries! Remember to maintain a balanced diet for your health goals! 🥗"
            
            await bot.send_message(
                chat_id=reminder.user_id,
                text=message,
                parse_mode='Markdown'
            )
            
            # Log completion message
            log_completion_message(
                user_id=reminder.user_id,
                message_text=message,
                chat_id=reminder.user_id
            )
            
        except Exception as e:
            logger.error(f"Error handling meal reminder completion: {e}")
            await bot.send_message(
                chat_id=reminder.user_id,
                text="❌ Error processing meal completion. Please try again."
            ) 