from datetime import datetime, date
from typing import Optional, Dict, Any
import json
import logging
from src.database.supabase_client import supabase_client

logger = logging.getLogger(__name__)

class User:
    def __init__(self, user_id: int, age: Optional[int] = None, height: Optional[float] = None, 
                 weight: Optional[float] = None, fitness_level: Optional[str] = None, 
                 goals: Optional[str] = None, id: Optional[int] = None, 
                 created_at: Optional[datetime] = None, updated_at: Optional[datetime] = None,
                 workout_time: Optional[str] = None, breakfast_time: Optional[str] = None,
                 lunch_time: Optional[str] = None, dinner_time: Optional[str] = None,
                 snack_time: Optional[str] = None, first_name: Optional[str] = None,
                 last_name: Optional[str] = None, username: Optional[str] = None,
                 trainer_id: Optional[int] = None):
        self.id = id
        self.user_id = user_id
        self.age = age
        self.height = height
        self.weight = weight
        self.fitness_level = fitness_level
        self.goals = goals
        self.created_at = created_at
        self.updated_at = updated_at
        self.workout_time = workout_time
        self.breakfast_time = breakfast_time
        self.lunch_time = lunch_time
        self.dinner_time = dinner_time
        self.snack_time = snack_time
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.trainer_id = trainer_id
    
    def save(self):
        """Save user to database"""
        try:
            user_data = {
                'user_id': self.user_id,
                'age': self.age,
                'height': self.height,
                'weight': self.weight,
                'fitness_level': self.fitness_level,
                'goals': self.goals,
                'workout_time': self.workout_time,
                'breakfast_time': self.breakfast_time,
                'lunch_time': self.lunch_time,
                'dinner_time': self.dinner_time,
                'snack_time': self.snack_time,
                'first_name': self.first_name,
                'last_name': self.last_name,
                'username': self.username,
                'trainer_id': self.trainer_id,
                'updated_at': datetime.now().isoformat()
            }
            
            # Check if user already exists
            existing = supabase_client.client.table('users').select('*').eq('user_id', self.user_id).execute()
            
            if existing.data:
                # Update existing user
                result = supabase_client.client.table('users').update(user_data).eq('user_id', self.user_id).execute()
                logger.info(f"Updated user {self.user_id}")
            else:
                # Create new user
                result = supabase_client.client.table('users').insert(user_data).execute()
                logger.info(f"Created new user {self.user_id}")
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Error saving user {self.user_id}: {e}")
            return None
    
    @classmethod
    def get_by_user_id(cls, user_id: int):
        """Get user by Telegram user ID"""
        try:
            result = supabase_client.client.table('users').select('*').eq('user_id', user_id).execute()
            
            if result.data:
                data = result.data[0]
                return cls(
                    id=data['id'],
                    user_id=data['user_id'],
                    age=data['age'],
                    height=data['height'],
                    weight=data['weight'],
                    fitness_level=data['fitness_level'],
                    goals=data['goals'],
                    created_at=data['created_at'],
                    updated_at=data['updated_at'],
                    workout_time=data.get('workout_time'),
                    breakfast_time=data.get('breakfast_time'),
                    lunch_time=data.get('lunch_time'),
                    dinner_time=data.get('dinner_time'),
                    snack_time=data.get('snack_time'),
                    first_name=data.get('first_name'),
                    last_name=data.get('last_name'),
                    username=data.get('username'),
                    trainer_id=data.get('trainer_id')
                )
            return None
            
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    def is_complete_profile(self) -> bool:
        """Check if user has completed their profile"""
        required_fields = [self.age, self.height, self.weight, self.fitness_level, self.goals]
        time_fields = [self.workout_time, self.breakfast_time, self.lunch_time, self.dinner_time, self.snack_time]
        return all(field is not None for field in required_fields) and all(field is not None for field in time_fields)

class Workout:
    def __init__(self, user_id, workout_content=None, status='generated',
                 trainer_feedback=None, id=None, created_date=None, 
                 completion_date=None, scheduled_date=None,
                 workout_type='daily', exercises_completed=0, total_exercises=0,
                 skipped_exercises=0):
        self.id = id
        self.user_id = user_id
        self.workout_content = workout_content or {}
        self.status = status
        self.trainer_feedback = trainer_feedback
        self.created_date = created_date
        self.completion_date = completion_date
        self.scheduled_date = scheduled_date
        self.workout_type = workout_type
        self.exercises_completed = exercises_completed
        self.total_exercises = total_exercises
        self.skipped_exercises = skipped_exercises

    def save(self):
        """Save workout to database"""
        try:
            # Handle completion_date properly
            completion_date = self.completion_date
            if isinstance(completion_date, datetime):
                completion_date = completion_date.isoformat()
            elif isinstance(completion_date, date):
                completion_date = completion_date.isoformat()
            
            # Handle scheduled_date properly
            scheduled_date = self.scheduled_date
            if isinstance(scheduled_date, datetime):
                scheduled_date = scheduled_date.isoformat()
            elif isinstance(scheduled_date, date):
                scheduled_date = scheduled_date.isoformat()
            
            workout_data = {
                'user_id': self.user_id,
                'workout_content': self.workout_content,
                'status': self.status,
                'trainer_feedback': self.trainer_feedback,
                'completion_date': completion_date,
                'scheduled_date': scheduled_date,
                'workout_type': self.workout_type,
                'exercises_completed': self.exercises_completed,
                'total_exercises': self.total_exercises,
                'skipped_exercises': self.skipped_exercises,
            }
                        
            if self.id:
                result = supabase_client.client.table('workouts').update(workout_data).eq('id', self.id).execute()
            else:
                result = supabase_client.client.table('workouts').insert(workout_data).execute()
            
            if result.data:
                self.id = result.data[0]['id']
                logger.info(f"Saved workout {self.id} for user {self.user_id}")
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Error saving workout for user {self.user_id}: {e}", exc_info=True)
            return None
    
    @classmethod
    def get_user_workouts(cls, user_id: int, limit: int = 10):
        """Get recent workouts for a user"""
        try:
            result = supabase_client.client.table('workouts').select('*').eq('user_id', user_id).order('created_date', desc=True).limit(limit).execute()
            
            workouts = []
            for data in result.data:
                workout = cls(
                    id=data['id'],
                    user_id=data['user_id'],
                    workout_content=data['workout_content'],
                    status=data['status'],
                    trainer_feedback=data['trainer_feedback'],
                    created_date=data['created_date'],
                    completion_date=data['completion_date'],
                    scheduled_date=data.get('scheduled_date'),
                    workout_type=data.get('workout_type', 'daily'),
                    exercises_completed=data.get('exercises_completed', 0),
                    total_exercises=data.get('total_exercises', 0),
                    skipped_exercises=data.get('skipped_exercises', 0)
                )
                workouts.append(workout)
            
            return workouts
            
        except Exception as e:
            logger.error(f"Error getting workouts for user {user_id}: {e}")
            return []
    
    def mark_completed(self):
        """Mark workout as completed"""
        self.status = 'completed'
        self.completion_date = datetime.now()
        return self.save()
    
    def get_completion_percentage(self) -> float:
        if not self.total_exercises or self.total_exercises == 0:
            return 0.0
        return round((self.exercises_completed / self.total_exercises) * 100, 1)

    def mark_exercise_completed(self, exercise_index: int) -> bool:
        """Mark one exercise as completed. If all are done, mark workout complete."""
        try:
            self.exercises_completed += 1
            if self.exercises_completed >= self.total_exercises:
                self.status = "completed"
                self.completion_date = datetime.utcnow()
            self.save()
            return True
        except Exception as e:
            logger.error(f"Failed to update workout {self.id} after exercise completion: {e}")
            return False

    @staticmethod
    def get_today_workout(user_id: int):
        try:
            today = datetime.now().date().isoformat()
            result = supabase_client.client.table('workouts').select('*') \
                .eq('user_id', user_id).eq('scheduled_date', today).limit(1).execute()
            if result.data:
                data = result.data[0]
                return Workout(
                    id=data['id'],
                    user_id=data['user_id'],
                    workout_content=data['workout_content'],
                    status=data['status'],
                    trainer_feedback=data.get('trainer_feedback'),
                    created_date=data['created_date'],
                    completion_date=data['completion_date']
                )
            return None
        except Exception as e:
            logger.error(f"Error fetching today's workout: {e}")
            return None

    @staticmethod
    def create_scheduled_workout(user_id: int, workout_content: Dict, scheduled_date: str):
        try:
            workout = Workout(
                user_id=user_id,
                workout_content=workout_content,
                status="scheduled",
            )
            workout.scheduled_date = scheduled_date
            workout.total_exercises = len(workout_content.get('exercises', []))
            return workout.save()
        except Exception as e:
            logger.error(f"Failed to create scheduled workout: {e}")
            return None

    @staticmethod
    def get_completed_exercises_count(workout_id: int) -> int:
        """Get the current count of completed exercises for a workout"""
        try:
            result = supabase_client.client.table('exercise_completions') \
                .select('id', count='exact') \
                .eq('workout_id', workout_id) \
                .execute()
            return result.count or 0
        except Exception as e:
            logger.error(f"Error getting completed exercises count: {e}")
            return 0

    def refresh_completion_count(self):
        """Refresh the exercises_completed and skipped_exercises counts from the database"""
        try:
            completions = ExerciseCompletion.get_workout_completions(self.id)
            self.exercises_completed = len([c for c in completions if c.get('status') == 'completed'])
            self.skipped_exercises = len([c for c in completions if c.get('status') == 'skipped'])
            
            # Update workout status based on completion/skip counts
            if self.exercises_completed + self.skipped_exercises >= self.total_exercises:
                # Only mark as skipped if ALL exercises are skipped
                if self.skipped_exercises == self.total_exercises and self.exercises_completed == 0:
                    self.status = "skipped"
                # Mark as completed if at least one exercise is completed
                elif self.exercises_completed > 0:
                    self.status = "completed"
                self.completion_date = datetime.utcnow()
            
            self.save()
            return True
        except Exception as e:
            logger.error(f"Error refreshing completion count: {e}")
            return False

class DietPlan:
    def __init__(self, user_id: int, diet_content: Dict[str, Any], scheduled_date: str, 
                 status: str = 'scheduled', id: Optional[int] = None, created_date: Optional[str] = None, 
                 completion_date: Optional[str] = None):
        self.id = id
        self.user_id = user_id
        self.diet_content = diet_content
        self.scheduled_date = scheduled_date
        self.status = status
        self.created_date = created_date
        self.completion_date = completion_date

    def _serialize_dates(self, obj):
        """Helper method to serialize dates for JSON storage"""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return obj

    def save(self):
        """Save diet plan to database"""
        try:
            # Serialize the diet_content to handle any date objects
            serialized_content = json.loads(json.dumps(self.diet_content, default=self._serialize_dates))
            
            diet_data = {
                'user_id': self.user_id,
                'diet_content': serialized_content,
                'scheduled_date': self.scheduled_date,
                'status': self.status,
                'completion_date': self.completion_date
            }
            
            if self.id:
                result = supabase_client.client.table('diet_plans').update(diet_data).eq('id', self.id).execute()
            else:
                result = supabase_client.client.table('diet_plans').insert(diet_data).execute()
            
            if result.data:
                self.id = result.data[0]['id']
                logger.info(f"Saved diet plan with ID {self.id} for user {self.user_id}")
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Error saving diet plan for user {self.user_id}: {e}", exc_info=True)
            return None
    
    def mark_meal_completed(self, meal_type: str, meal_name: str) -> bool:
        """Mark a specific meal as completed"""
        try:
            # Check if meal completion already exists
            if DietCompletion.exists(self.id, meal_type):
                logger.warning(f"Meal {meal_type} already completed for diet {self.id}")
                return False
            
            # Create meal completion record
            completion_result = DietCompletion.create(
                diet_id=self.id,
                meal_name=meal_name,
                meal_type=meal_type,
                status='completed'
            )
            
            if completion_result:
                # Refresh completion counts and update diet status
                self.refresh_completion_count()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error marking meal {meal_type} as completed: {e}")
            return False
    
    def mark_meal_skipped(self, meal_type: str, meal_name: str) -> bool:
        """Mark a specific meal as skipped"""
        try:
            # Check if meal completion already exists
            if DietCompletion.exists(self.id, meal_type):
                logger.warning(f"Meal {meal_type} already processed for diet {self.id}")
                return False
            
            # Create meal completion record with skipped status
            completion_result = DietCompletion.create(
                diet_id=self.id,
                meal_name=meal_name,
                meal_type=meal_type,
                status='skipped'
            )
            
            if completion_result:
                # Refresh completion counts and update diet status
                self.refresh_completion_count()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error marking meal {meal_type} as skipped: {e}")
            return False
    
    def refresh_completion_count(self):
        """Refresh the meal completion counts and update diet status"""
        try:
            completions = DietCompletion.get_diet_completions(self.id)
            completed_meals = len([c for c in completions if c.get('status') == 'completed'])
            skipped_meals = len([c for c in completions if c.get('status') == 'skipped'])
            
            # Get total expected meals from diet content
            diet_content = self.diet_content if isinstance(self.diet_content, dict) else {}
            meals = diet_content.get('meals', [])
            snacks = diet_content.get('snacks', [])
            total_meals = len(meals) + len(snacks)
            
            # Update diet status based on completion/skip counts
            if completed_meals + skipped_meals >= total_meals:
                # Only mark as skipped if ALL meals are skipped
                if skipped_meals == total_meals and completed_meals == 0:
                    self.status = "skipped"
                # Mark as completed if at least one meal is completed
                elif completed_meals > 0:
                    self.status = "completed"
                self.completion_date = datetime.now().date().isoformat()
            
            self.save()
            return True
            
        except Exception as e:
            logger.error(f"Error refreshing completion count: {e}")
            return False
    
    def get_completion_percentage(self) -> float:
        """Get the completion percentage of the diet plan"""
        try:
            completions = DietCompletion.get_diet_completions(self.id)
            total_completions = len(completions)
            
            if total_completions == 0:
                return 0.0
            
            completed_count = len([c for c in completions if c.get('status') == 'completed'])
            return round((completed_count / total_completions) * 100, 1)
            
        except Exception as e:
            logger.error(f"Error calculating completion percentage: {e}")
            return 0.0

    @staticmethod
    def get_today_diet(user_id: int):
        """Get today's diet plan for a user"""
        try:
            today = datetime.now().date().isoformat()
            result = supabase_client.client.table('diet_plans').select('*') \
                .eq('user_id', user_id).eq('scheduled_date', today).limit(1).execute()
            
            if result.data:
                data = result.data[0]
                return DietPlan(
                    id=data['id'],
                    user_id=data['user_id'],
                    diet_content=data['diet_content'],
                    scheduled_date=data['scheduled_date'],
                    status=data['status'],
                    created_date=data['created_date'],
                    completion_date=data['completion_date']
                )
            return None
            
        except Exception as e:
            logger.error(f"Error fetching today's diet: {e}")
            return None

    @staticmethod
    def get_user_diets(user_id: int, limit: int = 10):
        """Get recent diet plans for a user"""
        try:
            result = supabase_client.client.table('diet_plans').select('*') \
                .eq('user_id', user_id).order('created_date', desc=True).limit(limit).execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"Error getting diets for user {user_id}: {e}")
            return []

class ExerciseCompletion:
    def __init__(self, workout_id: int, exercise_name: str, exercise_index: int, status: str = 'completed'):
        self.workout_id = workout_id
        self.exercise_name = exercise_name
        self.exercise_index = exercise_index
        self.status = status

    @staticmethod
    def create(workout_id: int, exercise_name: str, exercise_index: int, status: str = 'completed'):
        try:
            data = {
                'workout_id': workout_id,
                'exercise_name': exercise_name,
                'exercise_index': exercise_index,
                'status': status,
                'completed_at': datetime.utcnow().isoformat()
            }
            return supabase_client.client.table('exercise_completions').insert(data).execute()
        except Exception as e:
            logger.error(f"Failed to mark exercise {status}: {e}")
            return None

    @staticmethod
    def exists(workout_id: int, exercise_index: int) -> bool:
        try:
            result = supabase_client.client.table('exercise_completions') \
                .select('id') \
                .eq('workout_id', workout_id) \
                .eq('exercise_index', exercise_index).execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error checking exercise completion: {e}")
            return False

    @staticmethod
    def get_workout_completions(workout_id: int) -> list:
        """Get all completed/skipped exercises for a workout"""
        try:
            result = supabase_client.client.table('exercise_completions') \
                .select('*') \
                .eq('workout_id', workout_id) \
                .order('exercise_index') \
                .execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting workout completions: {e}")
            return []

    @staticmethod
    def get_user_completions(user_id: int) -> list:
        """Get all exercise completions/skips for a user across all workouts"""
        try:
            workouts = Workout.get_user_workouts(user_id)
            workout_ids = [w.id for w in workouts if w.id]
            
            if not workout_ids:
                return []
            
            result = supabase_client.client.table('exercise_completions') \
                .select('*') \
                .in_('workout_id', workout_ids) \
                .order('completed_at', desc=True) \
                .execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting user completions: {e}")
            return []

class UserSession:
    def __init__(self, user_id: int, conversation_state: str = 'NEW_USER', 
                 temp_data: Optional[Dict] = None, id: Optional[int] = None, 
                 updated_at: Optional[datetime] = None):
        self.id = id
        self.user_id = user_id
        self.conversation_state = conversation_state
        self.temp_data = temp_data or {}
        self.updated_at = updated_at
    
    def save(self):
        """Save user session to database"""
        try:
            session_data = {
                'user_id': self.user_id,
                'conversation_state': self.conversation_state,
                'temp_data': self.temp_data,
                'updated_at': datetime.now().isoformat()
            }
            
            # Check if session already exists
            existing = supabase_client.client.table('user_sessions').select('*').eq('user_id', self.user_id).execute()
            
            if existing.data:
                # Update existing session
                result = supabase_client.client.table('user_sessions').update(session_data).eq('user_id', self.user_id).execute()
            else:
                # Create new session
                result = supabase_client.client.table('user_sessions').insert(session_data).execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Error saving session for user {self.user_id}: {e}")
            return None
    
    @classmethod
    def get_by_user_id(cls, user_id: int):
        """Get user session by Telegram user ID"""
        try:
            result = supabase_client.client.table('user_sessions').select('*').eq('user_id', user_id).execute()
            
            if result.data:
                data = result.data[0]
                return cls(
                    id=data['id'],
                    user_id=data['user_id'],
                    conversation_state=data['conversation_state'],
                    temp_data=data['temp_data'],
                    updated_at=data['updated_at']
                )
            return None
            
        except Exception as e:
            logger.error(f"Error getting session for user {user_id}: {e}")
            return None
    
    def update_state(self, new_state: str, temp_data: Optional[Dict] = None):
        """Update conversation state"""
        self.conversation_state = new_state
        if temp_data is not None:
            self.temp_data.update(temp_data)
        return self.save()

class Reminder:
    def __init__(self, user_id: int, reminder_type: str, scheduled_time: str, 
                 reminder_time: str, content: Dict[str, Any], related_id: int, 
                 related_type: str, status: str = 'pending', id: Optional[int] = None,
                 created_at: Optional[datetime] = None, sent_at: Optional[datetime] = None,
                 completed_at: Optional[datetime] = None):
        self.id = id
        self.user_id = user_id
        self.reminder_type = reminder_type  # 'workout', 'breakfast', 'lunch', 'dinner', 'snack'
        self.scheduled_time = scheduled_time  # Time when the activity should happen
        self.reminder_time = reminder_time    # Time when reminder should be sent (5 min before)
        self.content = content
        self.status = status  # 'pending', 'sent', 'completed', 'skipped'
        self.related_id = related_id
        self.related_type = related_type  # 'workout', 'diet'
        self.created_at = created_at
        
        # Handle sent_at - convert string to datetime if needed
        if isinstance(sent_at, str):
            try:
                from datetime import datetime
                self.sent_at = datetime.fromisoformat(sent_at.replace('Z', '+00:00'))
            except:
                self.sent_at = sent_at
        else:
            self.sent_at = sent_at
            
        # Handle completed_at - convert string to datetime if needed
        if isinstance(completed_at, str):
            try:
                from datetime import datetime
                self.completed_at = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
            except:
                self.completed_at = completed_at
        else:
            self.completed_at = completed_at
    
    def save(self):
        """Save reminder to database"""
        try:
            reminder_data = {
                'user_id': self.user_id,
                'reminder_type': self.reminder_type,
                'scheduled_time': self.scheduled_time,
                'reminder_time': self.reminder_time,
                'content': self.content,
                'status': self.status,
                'related_id': self.related_id,
                'related_type': self.related_type,
                'sent_at': self.sent_at.isoformat() if hasattr(self.sent_at, 'isoformat') else self.sent_at,
                'completed_at': self.completed_at.isoformat() if hasattr(self.completed_at, 'isoformat') else self.completed_at
            }
            
            logger.info(f"Attempting to save reminder: {reminder_data}")
            
            if self.id:
                result = supabase_client.client.table('reminders').update(reminder_data).eq('id', self.id).execute()
                logger.info(f"Update result: {result}")
            else:
                result = supabase_client.client.table('reminders').insert(reminder_data).execute()
                logger.info(f"Insert result: {result}")
            
            if result.data:
                self.id = result.data[0]['id']
                logger.info(f"Successfully saved reminder {self.id} for user {self.user_id}")
                return result.data[0]
            else:
                logger.error(f"No data returned from save operation: {result}")
                return None
            
        except Exception as e:
            logger.error(f"Error saving reminder for user {self.user_id}: {e}", exc_info=True)
            return None
    
    @classmethod
    def get_pending_reminders(cls):
        """Get all pending reminders that need to be sent"""
        try:
            from datetime import datetime, time
            now = datetime.now()
            current_time = now.strftime('%H:%M:%S')
            
            result = supabase_client.client.table('reminders') \
                .select('*') \
                .eq('status', 'pending') \
                .lte('reminder_time', current_time) \
                .execute()
            
            reminders = []
            for data in result.data:
                reminder = cls(
                    id=data['id'],
                    user_id=data['user_id'],
                    reminder_type=data['reminder_type'],
                    scheduled_time=data['scheduled_time'],
                    reminder_time=data['reminder_time'],
                    content=data['content'],
                    status=data['status'],
                    related_id=data['related_id'],
                    related_type=data['related_type'],
                    created_at=data['created_at'],
                    sent_at=data['sent_at'],
                    completed_at=data['completed_at']
                )
                reminders.append(reminder)
            
            return reminders
            
        except Exception as e:
            logger.error(f"Error getting pending reminders: {e}")
            return []
    
    @classmethod
    def get_user_reminders(cls, user_id: int, date: str = None):
        """Get reminders for a specific user and date"""
        try:
            query = supabase_client.client.table('reminders').select('*').eq('user_id', user_id)
            
            if date:
                # Filter by date if provided
                query = query.eq('scheduled_date', date)
            
            result = query.order('reminder_time').execute()
            
            reminders = []
            for data in result.data:
                reminder = cls(
                    id=data['id'],
                    user_id=data['user_id'],
                    reminder_type=data['reminder_type'],
                    scheduled_time=data['scheduled_time'],
                    reminder_time=data['reminder_time'],
                    content=data['content'],
                    status=data['status'],
                    related_id=data['related_id'],
                    related_type=data['related_type'],
                    created_at=data['created_at'],
                    sent_at=data['sent_at'],
                    completed_at=data['completed_at']
                )
                reminders.append(reminder)
            
            return reminders
            
        except Exception as e:
            logger.error(f"Error getting user reminders: {e}")
            return []
    
    def mark_sent(self):
        """Mark reminder as sent"""
        self.status = 'sent'
        self.sent_at = datetime.now()
        return self.save()
    
    def mark_completed(self):
        """Mark reminder as completed"""
        self.status = 'completed'
        self.completed_at = datetime.now()
        return self.save()
    
    def mark_skipped(self):
        """Mark reminder as skipped"""
        self.status = 'skipped'
        self.completed_at = datetime.now()
        return self.save()
    
    @staticmethod
    def create_reminder(user_id: int, reminder_type: str, scheduled_time: str, 
                       content: Dict[str, Any], related_id: int, related_type: str):
        """Create a new reminder with 5-minute advance notice"""
        try:
            from datetime import datetime, timedelta
            
            # Handle time format - remove seconds if present
            if scheduled_time.count(':') == 2:  # Format: HH:MM:SS
                scheduled_time = scheduled_time[:5]  # Take only HH:MM
            
            # Parse scheduled time
            scheduled_dt = datetime.strptime(scheduled_time, '%H:%M')
            
            # Calculate reminder time (5 minutes before)
            reminder_dt = scheduled_dt - timedelta(minutes=5)
            reminder_time = reminder_dt.strftime('%H:%M:%S')
            
            reminder = Reminder(
                user_id=user_id,
                reminder_type=reminder_type,
                scheduled_time=scheduled_time,
                reminder_time=reminder_time,
                content=content,
                related_id=related_id,
                related_type=related_type
            )
            
            result = reminder.save()
            logger.info(f"Created reminder: {reminder_type} for user {user_id} at {scheduled_time} (reminder at {reminder_time})")
            return result
            
        except Exception as e:
            logger.error(f"Error creating reminder: {e}", exc_info=True)
            return None

class DietCompletion:
    def __init__(self, diet_id: int, meal_name: str, meal_type: str, status: str = 'completed'):
        self.diet_id = diet_id
        self.meal_name = meal_name
        self.meal_type = meal_type  # 'breakfast', 'lunch', 'dinner', 'snack'
        self.status = status
        self.completed_at = datetime.now()
    
    @staticmethod
    def create(diet_id: int, meal_name: str, meal_type: str, status: str = 'completed'):
        """Create a new diet completion record"""
        try:
            completion_data = {
                'diet_id': diet_id,
                'meal_name': meal_name,
                'meal_type': meal_type,
                'status': status,
                'completed_at': datetime.now().isoformat()
            }
            
            result = supabase_client.client.table('diet_completions').insert(completion_data).execute()
            
            if result.data:
                logger.info(f"Created diet completion: {meal_type} for diet {diet_id}")
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error creating diet completion: {e}")
            return None
    
    @staticmethod
    def exists(diet_id: int, meal_type: str) -> bool:
        """Check if a meal completion already exists"""
        try:
            result = supabase_client.client.table('diet_completions') \
                .select('id') \
                .eq('diet_id', diet_id) \
                .eq('meal_type', meal_type) \
                .execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Error checking diet completion existence: {e}")
            return False
    
    @staticmethod
    def get_diet_completions(diet_id: int) -> list:
        """Get all completions for a specific diet"""
        try:
            result = supabase_client.client.table('diet_completions') \
                .select('*') \
                .eq('diet_id', diet_id) \
                .order('completed_at') \
                .execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"Error getting diet completions: {e}")
            return []
    
    @staticmethod
    def get_user_completions(user_id: int) -> list:
        """Get all diet completions for a user"""
        try:
            # First get user's diet plans
            diet_plans = DietPlan.get_user_diets(user_id, limit=100)
            diet_ids = [diet.get('id') for diet in diet_plans if diet.get('id')]
            
            if not diet_ids:
                return []
            
            # Get completions for all diet plans
            result = supabase_client.client.table('diet_completions') \
                .select('*') \
                .in_('diet_id', diet_ids) \
                .order('completed_at') \
                .execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"Error getting user diet completions: {e}")
            return []

class ChatMessage:
    def __init__(self, user_id: int, message_text: str, message_type: str, 
                 message_id: Optional[int] = None, chat_id: Optional[int] = None,
                 reply_to_message_id: Optional[int] = None, is_command: bool = False,
                 command_name: Optional[str] = None, session_state: Optional[str] = None,
                 id: Optional[int] = None, timestamp: Optional[datetime] = None,
                 message_category: Optional[str] = None):
        self.id = id
        self.user_id = user_id
        self.message_text = message_text
        self.message_type = message_type  # 'user' or 'bot'
        self.message_id = message_id
        self.chat_id = chat_id
        self.reply_to_message_id = reply_to_message_id
        self.is_command = is_command
        self.command_name = command_name
        self.session_state = session_state
        self.timestamp = timestamp or datetime.now()
        self.message_category = message_category  # 'workout', 'diet', 'reminder', 'progress', etc.
    
    def save(self):
        """Save chat message to database"""
        try:
            message_data = {
                'user_id': self.user_id,
                'message_text': self.message_text,
                'message_type': self.message_type,
                'message_id': self.message_id,
                'chat_id': self.chat_id,
                'reply_to_message_id': self.reply_to_message_id,
                'is_command': self.is_command,
                'command_name': self.command_name,
                'session_state': self.session_state,
                'timestamp': self.timestamp.isoformat(),
                'message_category': self.message_category
            }
            
            result = supabase_client.client.table('chat_messages').insert(message_data).execute()
            
            if result.data:
                self.id = result.data[0]['id']
                logger.info(f"Saved chat message {self.id} for user {self.user_id}")
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Error saving chat message for user {self.user_id}: {e}")
            return None
    
    @classmethod
    def create_user_message(cls, user_id: int, message_text: str, message_id: int = None,
                           chat_id: int = None, reply_to_message_id: int = None,
                           is_command: bool = False, command_name: str = None,
                           session_state: str = None):
        """Create and save a user message"""
        message = cls(
            user_id=user_id,
            message_text=message_text,
            message_type='user',
            message_id=message_id,
            chat_id=chat_id,
            reply_to_message_id=reply_to_message_id,
            is_command=is_command,
            command_name=command_name,
            session_state=session_state
        )
        return message.save()
    
    @classmethod
    def create_bot_message(cls, user_id: int, message_text: str, message_id: int = None,
                          chat_id: int = None, reply_to_message_id: int = None,
                          session_state: str = None, message_category: str = None):
        """Create and save a bot message with optional category"""
        message = cls(
            user_id=user_id,
            message_text=message_text,
            message_type='bot',
            message_id=message_id,
            chat_id=chat_id,
            reply_to_message_id=reply_to_message_id,
            session_state=session_state
        )
        # Add category to message data if provided
        if message_category:
            message.message_category = message_category
        return message.save()
    
    @classmethod
    def get_user_messages(cls, user_id: int, limit: int = 50, offset: int = 0):
        """Get recent messages for a user"""
        try:
            result = supabase_client.client.table('chat_messages')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('timestamp', desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()
            
            messages = []
            for data in result.data:
                message = cls(
                    id=data['id'],
                    user_id=data['user_id'],
                    message_text=data['message_text'],
                    message_type=data['message_type'],
                    message_id=data.get('message_id'),
                    chat_id=data.get('chat_id'),
                    reply_to_message_id=data.get('reply_to_message_id'),
                    is_command=data.get('is_command', False),
                    command_name=data.get('command_name'),
                    session_state=data.get('session_state'),
                    timestamp=data['timestamp'],
                    message_category=data.get('message_category')
                )
                messages.append(message)
            
            return messages
            
        except Exception as e:
            logger.error(f"Error getting messages for user {user_id}: {e}")
            return []
    
    @classmethod
    def get_conversation_history(cls, user_id: int, limit: int = 100):
        """Get conversation history for a user in chronological order"""
        try:
            result = supabase_client.client.table('chat_messages')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('timestamp', desc=False)\
                .limit(limit)\
                .execute()
            
            messages = []
            for data in result.data:
                message = cls(
                    id=data['id'],
                    user_id=data['user_id'],
                    message_text=data['message_text'],
                    message_type=data['message_type'],
                    message_id=data.get('message_id'),
                    chat_id=data.get('chat_id'),
                    reply_to_message_id=data.get('reply_to_message_id'),
                    is_command=data.get('is_command', False),
                    command_name=data.get('command_name'),
                    session_state=data.get('session_state'),
                    timestamp=data['timestamp'],
                    message_category=data.get('message_category')
                )
                messages.append(message)
            
            return messages
            
        except Exception as e:
            logger.error(f"Error getting conversation history for user {user_id}: {e}")
            return []
    
    @classmethod
    def get_all_messages(cls, limit: int = 100, offset: int = 0):
        """Get all messages across all users (for admin dashboard)"""
        try:
            result = supabase_client.client.table('chat_messages')\
                .select('*')\
                .order('timestamp', desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()
            
            messages = []
            for data in result.data:
                message = cls(
                    id=data['id'],
                    user_id=data['user_id'],
                    message_text=data['message_text'],
                    message_type=data['message_type'],
                    message_id=data.get('message_id'),
                    chat_id=data.get('chat_id'),
                    reply_to_message_id=data.get('reply_to_message_id'),
                    is_command=data.get('is_command', False),
                    command_name=data.get('command_name'),
                    session_state=data.get('session_state'),
                    timestamp=data['timestamp'],
                    message_category=data.get('message_category')
                )
                messages.append(message)
            
            return messages
            
        except Exception as e:
            logger.error(f"Error getting all messages: {e}")
            return []

class Trainer:
    def __init__(self, trainer_id: int, first_name: str = None, last_name: str = None, email: str = None, phone: str = None, id: int = None, created_at=None, updated_at=None):
        self.id = id
        self.trainer_id = trainer_id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.phone = phone
        self.created_at = created_at
        self.updated_at = updated_at

    def save(self):
        try:
            trainer_data = {
                'trainer_id': self.trainer_id,
                'first_name': self.first_name,
                'last_name': self.last_name,
                'email': self.email,
                'phone': self.phone,
                'updated_at': datetime.now().isoformat()
            }
            existing = supabase_client.client.table('trainers').select('*').eq('trainer_id', self.trainer_id).execute()
            if existing.data:
                result = supabase_client.client.table('trainers').update(trainer_data).eq('trainer_id', self.trainer_id).execute()
            else:
                result = supabase_client.client.table('trainers').insert(trainer_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error saving trainer {self.trainer_id}: {e}")
            return None

    @classmethod
    def get_by_trainer_id(cls, trainer_id: int):
        try:
            result = supabase_client.client.table('trainers').select('*').eq('trainer_id', trainer_id).execute()
            if result.data:
                data = result.data[0]
                return cls(
                    id=data['id'],
                    trainer_id=data['trainer_id'],
                    first_name=data.get('first_name'),
                    last_name=data.get('last_name'),
                    email=data.get('email'),
                    phone=data.get('phone'),
                    created_at=data.get('created_at'),
                    updated_at=data.get('updated_at')
                )
            return None
        except Exception as e:
            logger.error(f"Error getting trainer {trainer_id}: {e}")
            return None

    @classmethod
    def get_all(cls):
        try:
            result = supabase_client.client.table('trainers').select('*').execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting all trainers: {e}")
            return []

    @classmethod
    def get_users(cls, trainer_id: int):
        try:
            result = supabase_client.client.table('users').select('*').eq('trainer_id', trainer_id).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting users for trainer {trainer_id}: {e}")
            return []

class Payment:
    def __init__(self, user_id: int, amount: float, status: str, payment_date=None, plan_name=None, transaction_id=None, method=None, id=None):
        self.id = id
        self.user_id = user_id
        self.amount = amount
        self.status = status
        self.payment_date = payment_date
        self.plan_name = plan_name
        self.transaction_id = transaction_id
        self.method = method

    def save(self):
        try:
            payment_data = {
                'user_id': self.user_id,
                'amount': self.amount,
                'status': self.status,
                'payment_date': self.payment_date or datetime.now().isoformat(),
                'plan_name': self.plan_name,
                'transaction_id': self.transaction_id,
                'method': self.method
            }
            if self.id:
                result = supabase_client.client.table('payments').update(payment_data).eq('id', self.id).execute()
            else:
                result = supabase_client.client.table('payments').insert(payment_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error saving payment for user {self.user_id}: {e}")
            return None

    @classmethod
    def get_by_user_id(cls, user_id: int):
        try:
            result = supabase_client.client.table('payments').select('*').eq('user_id', user_id).order('payment_date', desc=True).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting payments for user {user_id}: {e}")
            return []

    @classmethod
    def get_all(cls):
        try:
            result = supabase_client.client.table('payments').select('*').order('payment_date', desc=True).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting all payments: {e}")
            return []