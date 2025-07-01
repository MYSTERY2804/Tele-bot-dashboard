import json
import logging
from typing import Dict, Any, Optional
import google.generativeai as genai
from config.config import Config

logger = logging.getLogger(__name__)

class GeminiService:
    """Service class for Google Gemini AI integration"""
    
    def __init__(self):
        """Initialize Gemini AI client"""
        try:
            genai.configure(api_key=Config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('models/gemini-1.5-flash')
            logger.info("Gemini AI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise
    
    def generate_workout(self, user_profile: Dict[str, Any], workout_history: Optional[list] = None) -> Dict[str, Any]:
        """
        Generate a personalized workout plan based on user profile and history
        
        Args:
            user_profile: Dictionary containing user details (age, height, weight, level, goals)
            workout_history: List of previous workouts (optional)
        
        Returns:
            Dictionary containing structured workout plan
        """
        try:
            # Define available muscle groups for rotation
            muscle_groups = ["Arms", "Chest", "Back", "Legs", "Shoulders", "Abs", "Cardio"]
            
            # Determine next muscle group based on history
            next_muscle_group = self._determine_next_muscle_group(workout_history, muscle_groups)
            
            # Prepare workout history context with rotation info
            history_context = ""
            if workout_history:
                recent_workouts = workout_history[:3]  # Last 3 workouts
                recent_types = [w.get('workout_type', 'General') for w in recent_workouts]
                history_context = f"Recent workout history: {recent_types}\n"
                history_context += f"Next workout should focus on: {next_muscle_group}"
            
            # Create structured prompt for workout generation
            prompt = self._create_workout_prompt(user_profile, history_context, next_muscle_group)
            
            # Generate workout using Gemini
            response = self.model.generate_content(prompt)
            
            # Parse and validate response
            workout_data = self._parse_workout_response(response.text)
            
            # Ensure the workout type matches our rotation
            workout_data['workout_type'] = next_muscle_group
            
            logger.info(f"Generated {next_muscle_group} workout for user with goals: {user_profile.get('goals', 'Unknown')}")
            return workout_data
            
        except Exception as e:
            logger.error(f"Error generating workout: {e}")
            return self._get_fallback_workout(user_profile, next_muscle_group if 'next_muscle_group' in locals() else "Full Body")
    
    def answer_fitness_question(self, question: str, user_profile: Optional[Dict] = None) -> str:
        """
        Answer fitness and nutrition related questions
        
        Args:
            question: User's fitness question
            user_profile: Optional user profile for personalized answers
        
        Returns:
            AI-generated answer to the fitness question
        """
        try:
            # Create context-aware prompt
            prompt = self._create_qa_prompt(question, user_profile)
            
            # Generate response using Gemini
            response = self.model.generate_content(prompt)
            
            # Clean and format response
            answer = self._format_qa_response(response.text)
            
            logger.info(f"Answered fitness question: {question[:50]}...")
            return answer
            
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return "I'm sorry, I'm having trouble processing your question right now. Please try again later or rephrase your question."
    
    def extract_user_details(self, message: str) -> Dict[str, Any]:
        """
        Extract user details from natural language message
        
        Args:
            message: User's message containing personal details
        
        Returns:
            Dictionary with extracted details (age, height, weight, level, goals)
        """
        try:
            prompt = self._create_extraction_prompt(message)
            
            response = self.model.generate_content(prompt)
            
            # Parse JSON response
            extracted_data = json.loads(response.text.strip())
            
            logger.info(f"Extracted user details from message")
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error extracting details: {e}")
            return {}
    
    def _create_workout_prompt(self, user_profile: Dict[str, Any], history_context: str, target_muscle_group: str) -> str:
        """Create structured prompt for daily workout generation"""
        prompt = f"""
    You are a professional fitness trainer. Generate a daily workout plan for the following user profile:

    USER PROFILE:
    - Age: {user_profile.get('age')} years
    - Height: {user_profile.get('height')} cm
    - Weight: {user_profile.get('weight')} kg
    - Fitness Level: {user_profile.get('fitness_level', 'beginner')}
    - Goals: {user_profile.get('goals')}

    {history_context}

    IMPORTANT: Create a workout focused specifically on {target_muscle_group}.
    Include:
    1. 2 warm-up movements specific to {target_muscle_group}
    2. 4–6 main exercises targeting {target_muscle_group}
    3. 2 cool-down stretches for {target_muscle_group}
    4. Tracking-friendly structure with exercise index and name

    Respond ONLY with valid JSON in this exact format:
    {{
    "workout_type": "{target_muscle_group}",
    "duration_minutes": 30,
    "difficulty": "Beginner/Intermediate/Advanced",
    "exercises": [
        {{
        "name": "Exercise Name",
        "type": "strength/cardio/flexibility",
        "sets": 3,
        "reps": "10-12",
        "rest_seconds": 60,
        "instructions": "How to perform",
        "modifications": "Easier/harder variation"
        }}
    ],
    "warmup": [
        {{
        "name": "Warm-up Exercise",
        "duration_seconds": 30,
        "instructions": "How to perform"
        }}
    ],
    "cooldown": [
        {{
        "name": "Cool-down Stretch",
        "duration_seconds": 30,
        "instructions": "How to perform"
        }}
    ],
    "tips": ["Safety tip", "Form cue", "Motivation"],
    "calories_estimate": 200
    }}

    Make the workout personalized, practical, and safe for their goals.
    Focus ALL exercises on {target_muscle_group} development.
    """
        return prompt
    
    def generate_diet_plan(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a personalized diet plan based on user's profile"""
        try:
            # Get diet history for variety
            diet_history = self._get_diet_history(user_profile.get('user_id'))
            
            # Determine cuisine preference and variety
            cuisine_preference = self._determine_cuisine_preference(diet_history)
            
            prompt = f"""
You are a certified nutritionist specializing in both Western and Indian cuisine. Generate a structured daily diet plan for this user.

USER PROFILE:
- Age: {user_profile.get('age')} years
- Height: {user_profile.get('height')} cm
- Weight: {user_profile.get('weight')} kg
- Fitness Level: {user_profile.get('fitness_level')}
- Goals: {user_profile.get('goals')}

DIET HISTORY:
{diet_history}

CUISINE PREFERENCE: {cuisine_preference}

IMPORTANT GUIDELINES:
1. Include a mix of {cuisine_preference} dishes
2. Ensure variety in meals (avoid repeating recent meals)
3. Include traditional Indian breakfast options like:
   - Idli/Dosa with sambar
   - Poha/Upma
   - Paratha with curd
   - Besan chilla
4. Include Indian lunch/dinner options like:
   - Dal/Rice combinations
   - Roti/Sabzi combinations
   - Curries with protein
   - Biryani/Pulao (occasionally)
5. Include healthy Indian snacks like:
   - Sprouts chaat
   - Makhana
   - Roasted chana
   - Fruit chaat
6. Maintain proper protein, carb, and fat balance
7. Consider user's fitness goals for portion sizes

IMPORTANT: You MUST return ONLY a valid JSON object with the following EXACT structure. Do not include any other text, explanations, or markdown formatting:

{{
  "total_calories": number,
  "cuisine_type": "Indian/Western/Mixed",
  "meals": [
    {{
      "name": "Breakfast",
      "time": "7:00 AM",
      "items": [
        {{
          "name": "Example: Masala Oats with Vegetables",
          "portion": "1 bowl",
          "calories": 250,
          "cuisine": "Indian",
          "nutrition": {{
            "protein": "8g",
            "carbs": "45g",
            "fats": "5g"
          }}
        }},
        {{
          "name": "Example: Greek Yogurt with Berries",
          "portion": "1 cup",
          "calories": 150,
          "cuisine": "Western",
          "nutrition": {{
            "protein": "12g",
            "carbs": "15g",
            "fats": "3g"
          }}
        }}
      ],
      "total_calories": 400,
      "cuisine": "Mixed"
    }},
    {{
      "name": "Lunch",
      "time": "12:30 PM",
      "items": [
        {{
          "name": "Example: Roti with Dal and Sabzi",
          "portion": "2 rotis, 1 bowl dal, 1 bowl sabzi",
          "calories": 450,
          "cuisine": "Indian",
          "nutrition": {{
            "protein": "15g",
            "carbs": "60g",
            "fats": "8g"
          }}
        }}
      ],
      "total_calories": 450,
      "cuisine": "Indian"
    }},
    {{
      "name": "Dinner",
      "time": "7:00 PM",
      "items": [
        {{
          "name": "Example: Grilled Chicken with Quinoa",
          "portion": "150g chicken, 1 cup quinoa",
          "calories": 400,
          "cuisine": "Western",
          "nutrition": {{
            "protein": "35g",
            "carbs": "45g",
            "fats": "10g"
          }}
        }}
      ],
      "total_calories": 400,
      "cuisine": "Western"
    }}
  ],
  "snacks": [
    {{
      "time": "10:00 AM",
      "items": [
        {{
          "name": "Example: Sprouts Chaat",
          "portion": "1 bowl",
          "calories": 150,
          "cuisine": "Indian",
          "nutrition": {{
            "protein": "8g",
            "carbs": "25g",
            "fats": "3g"
          }}
        }}
      ],
      "total_calories": 150,
      "cuisine": "Indian"
    }},
    {{
      "time": "4:00 PM",
      "items": [
        {{
          "name": "Example: Apple with Almonds",
          "portion": "1 medium apple, 10 almonds",
          "calories": 200,
          "cuisine": "Western",
          "nutrition": {{
            "protein": "5g",
            "carbs": "25g",
            "fats": "10g"
          }}
        }}
      ],
      "total_calories": 200,
      "cuisine": "Western"
    }}
  ],
  "hydration": {{
    "water": "8-10 glasses",
    "other_beverages": [
      "Green tea",
      "Herbal tea",
      "Buttermilk (chaas)",
      "Coconut water"
    ]
  }},
  "nutritional_summary": {{
    "protein": "120g",
    "carbs": "200g",
    "fats": "60g",
    "fiber": "25g"
  }},
  "notes": [
    "Eat every 3-4 hours",
    "Stay hydrated throughout the day",
    "Adjust portions based on activity level",
    "Include both Indian and Western options for variety"
  ]
}}

Remember:
1. Return ONLY the JSON object, no other text
2. Include a mix of Indian and Western dishes
3. Each meal must have detailed items with portions, calories, and nutrition info
4. Include at least 2 snacks
5. Total calories should match the sum of all meals and snacks
6. Avoid repeating meals from recent history
"""

            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            # Clean the response text
            if response_text.startswith("```"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            
            # Remove any text before or after the JSON object
            try:
                start_idx = response_text.find("{")
                end_idx = response_text.rfind("}") + 1
                if start_idx == -1 or end_idx == 0:
                    raise ValueError("No JSON object found in response")
                response_text = response_text[start_idx:end_idx]
            except Exception as e:
                logger.error(f"Error extracting JSON from response: {e}")
                raise

            try:
                diet_data = json.loads(response_text)
                
                # Validate required structure
                required_keys = ["meals", "snacks", "hydration", "total_calories", "cuisine_type"]
                for key in required_keys:
                    if key not in diet_data:
                        raise ValueError(f"Missing required key: {key}")
                
                # Validate meals structure
                if not isinstance(diet_data["meals"], list) or len(diet_data["meals"]) < 3:
                    raise ValueError("Must have at least 3 meals (breakfast, lunch, dinner)")
                
                # Validate each meal has required fields
                for meal in diet_data["meals"]:
                    if not all(k in meal for k in ["name", "time", "items", "total_calories", "cuisine"]):
                        raise ValueError(f"Invalid meal structure: {meal}")
                
                return diet_data

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in diet response: {response_text}")
                raise
            except ValueError as e:
                logger.error(f"Invalid diet plan structure: {e}")
                raise

        except Exception as e:
            logger.error(f"Error generating diet plan: {e}")
            return self._get_fallback_diet_plan(user_profile)

    def _get_diet_history(self, user_id: Optional[int]) -> str:
        """Get recent diet history for the user"""
        if not user_id:
            return "No diet history available"
        
        try:
            # Get last 5 diet plans
            recent_diets = DietPlan.get_user_diets(user_id, limit=5)
            if not recent_diets:
                return "No diet history available"
            
            history = "Recent meals:\n"
            for diet in recent_diets:
                if diet.diet_content and isinstance(diet.diet_content, dict):
                    for meal in diet.diet_content.get('meals', []):
                        history += f"- {meal.get('name')}: {[item.get('name') for item in meal.get('items', [])]}\n"
            
            return history
        except Exception as e:
            logger.error(f"Error getting diet history: {e}")
            return "Error retrieving diet history"

    def _determine_cuisine_preference(self, diet_history: str) -> str:
        """Determine cuisine preference based on history and variety"""
        if "No diet history" in diet_history:
            return "Mixed (Indian and Western)"
        
        # Count cuisine types in history
        indian_count = diet_history.lower().count("indian")
        western_count = diet_history.lower().count("western")
        
        if indian_count > western_count:
            return "Mixed (More Western options)"
        elif western_count > indian_count:
            return "Mixed (More Indian options)"
        else:
            return "Mixed (Equal Indian and Western)"

    def _get_fallback_diet_plan(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Return a basic fallback diet plan if AI generation fails"""
        return {
            "total_calories": 2000,
            "cuisine_type": "Mixed",
            "meals": [
                {
                    "name": "Breakfast",
                    "time": "7:00 AM",
                    "items": [
                        {
                            "name": "Masala Oats with Vegetables",
                            "portion": "1 bowl",
                            "calories": 300,
                            "cuisine": "Indian",
                            "nutrition": {"protein": "10g", "carbs": "50g", "fats": "6g"}
                        }
                    ],
                    "total_calories": 300,
                    "cuisine": "Indian"
                },
                {
                    "name": "Lunch",
                    "time": "12:30 PM",
                    "items": [
                        {
                            "name": "Roti with Dal and Sabzi",
                            "portion": "2 rotis, 1 bowl dal, 1 bowl sabzi",
                            "calories": 450,
                            "cuisine": "Indian",
                            "nutrition": {"protein": "15g", "carbs": "60g", "fats": "8g"}
                        }
                    ],
                    "total_calories": 450,
                    "cuisine": "Indian"
                },
                {
                    "name": "Dinner",
                    "time": "7:00 PM",
                    "items": [
                        {
                            "name": "Grilled Chicken with Quinoa",
                            "portion": "150g chicken, 1 cup quinoa",
                            "calories": 400,
                            "cuisine": "Western",
                            "nutrition": {"protein": "35g", "carbs": "45g", "fats": "10g"}
                        }
                    ],
                    "total_calories": 400,
                    "cuisine": "Western"
                }
            ],
            "snacks": [
                {
                    "time": "10:00 AM",
                    "items": [
                        {
                            "name": "Sprouts Chaat",
                            "portion": "1 bowl",
                            "calories": 150,
                            "cuisine": "Indian",
                            "nutrition": {"protein": "8g", "carbs": "25g", "fats": "3g"}
                        }
                    ],
                    "total_calories": 150,
                    "cuisine": "Indian"
                },
                {
                    "time": "4:00 PM",
                    "items": [
                        {
                            "name": "Apple with Almonds",
                            "portion": "1 medium apple, 10 almonds",
                            "calories": 200,
                            "cuisine": "Western",
                            "nutrition": {"protein": "5g", "carbs": "25g", "fats": "10g"}
                        }
                    ],
                    "total_calories": 200,
                    "cuisine": "Western"
                }
            ],
            "hydration": {
                "water": "8-10 glasses",
                "other_beverages": ["Green tea", "Buttermilk (chaas)", "Coconut water"]
            },
            "nutritional_summary": {
                "protein": "100g",
                "carbs": "180g",
                "fats": "50g",
                "fiber": "25g"
            },
            "notes": [
                "Eat every 3-4 hours",
                "Stay hydrated throughout the day",
                "Include both Indian and Western options for variety",
                "Consult a nutritionist for personalized advice"
            ]
        }
    
    def generate_daily_schedule(self, user_profile: Dict[str, Any], date: str) -> Dict[str, Any]:
        """Generate both workout and diet for a specific day"""
        try:
            prompt = f"""
    You are a combined fitness coach and nutritionist. For this user:

    PROFILE:
    - Age: {user_profile.get('age')}
    - Height: {user_profile.get('height')}
    - Weight: {user_profile.get('weight')}
    - Fitness Level: {user_profile.get('fitness_level')}
    - Goals: {user_profile.get('goals')}

    DATE: {date}

    Create both:
    1. A 30-min targeted workout (see structure below)
    2. A full-day diet plan

    Return JSON in this format:
    {{
    "workout": {{ ...same structure as generate_workout... }},
    "diet": {{ ...same structure as generate_diet_plan... }}
    }}
    """
            response = self.model.generate_content(prompt)
            return json.loads(response.text.strip())
        except Exception as e:
            logger.error(f"Error generating full daily schedule: {e}")
            return {}
    
    def _create_qa_prompt(self, question: str, user_profile: Optional[Dict] = None) -> str:
        """Create prompt for fitness Q&A"""
        
        profile_context = ""
        if user_profile:
            profile_context = f"""
CONTEXT - User Profile:
- Age: {user_profile.get('age')} years
- Fitness Level: {user_profile.get('fitness_level', 'unknown')}
- Goals: {user_profile.get('goals', 'general fitness')}
"""
        
        prompt = f"""
You are a certified fitness trainer and nutritionist. Answer the following fitness/health question accurately and helpfully.

{profile_context}

QUESTION: {question}

GUIDELINES:
- Use the user profile above for context, but do NOT repeat the profile details (age, goals, etc.) in your answer unless the user specifically asks for them.
- Keep your answer concise, friendly, and actionable (aim for 4-8 sentences).
- Avoid unnecessary repetition or generic encouragement.
- If it's a medical concern, recommend consulting a healthcare professional.
- Use emojis sparingly for readability.

ANSWER:
"""
        return prompt
    
    def _create_extraction_prompt(self, message: str) -> str:
        """Create prompt for extracting user details"""
        
        prompt = f"""
Extract user fitness details from this message: "{message}"

Return ONLY valid JSON in this exact format:
{{
    "age": null_or_number,
    "height": null_or_number_in_cm,
    "weight": null_or_number_in_kg,
    "fitness_level": null_or_"beginner"_or_"intermediate"_or_"advanced",
    "goals": null_or_"extracted_goals_text"
}}

Rules:
- Return null for any detail not mentioned or unclear
- Convert heights to centimeters (e.g., 5'10" = 178 cm)
- Convert weights to kilograms (e.g., 150 lbs = 68 kg)  
- Infer fitness level from context (workout frequency, experience mentioned)
- Extract goals as concise text describing what they want to achieve

Message: "{message}"
"""
        return prompt
    
    def _parse_workout_response(self, response_text: str) -> Dict[str, Any]:
        """Parse and validate workout response from Gemini"""
        try:
            # Clean response text (remove markdown formatting if present)
            clean_text = response_text.strip()
            if clean_text.startswith('```json'):
                clean_text = clean_text[7:]
            if clean_text.endswith('```'):
                clean_text = clean_text[:-3]
            
            # Parse JSON
            workout_data = json.loads(clean_text.strip())
            
            # Validate required fields
            required_fields = ['workout_type', 'exercises', 'duration_minutes']
            for field in required_fields:
                if field not in workout_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Ensure exercises is a list
            if not isinstance(workout_data['exercises'], list) or len(workout_data['exercises']) == 0:
                raise ValueError("Exercises must be a non-empty list")
            
            return workout_data
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Error parsing workout response: {e}")
            raise
    
    def _format_qa_response(self, response_text: str) -> str:
        """Format and clean Q&A response"""
        # Remove any markdown formatting and clean up
        formatted = response_text.strip()
        
        # Remove common AI response prefixes
        prefixes_to_remove = [
            "ANSWER:",
            "Answer:",
            "Response:",
            "Here's the answer:",
            "Here's my response:"
        ]
        
        for prefix in prefixes_to_remove:
            if formatted.startswith(prefix):
                formatted = formatted[len(prefix):].strip()
        
        return formatted
    
    def _get_fallback_workout(self, user_profile: Dict[str, Any], target_muscle_group: str = "Full Body") -> Dict[str, Any]:
        """Return a basic fallback workout if AI generation fails"""
        
        fitness_level = user_profile.get('fitness_level', 'beginner')
        
        # Basic workout based on fitness level
        if fitness_level == 'advanced':
            reps = "12-15"
            rest = 45
            exercises_count = 6
        elif fitness_level == 'intermediate':
            reps = "10-12"
            rest = 60
            exercises_count = 5
        else:  # beginner
            reps = "8-10"
            rest = 90
            exercises_count = 4
        
        # Define exercises for each muscle group
        muscle_group_exercises = {
            "Arms": [
                {
                    "name": "Bicep Curls",
                    "type": "strength",
                    "sets": 3,
                    "reps": reps,
                    "rest_seconds": rest,
                    "instructions": "Stand with dumbbells, curl weights up while keeping elbows close to body.",
                    "modifications": "Use resistance bands (easier) or increase weight (harder)"
                },
                {
                    "name": "Tricep Dips",
                    "type": "strength",
                    "sets": 3,
                    "reps": reps,
                    "rest_seconds": rest,
                    "instructions": "Use a chair or bench, lower body by bending elbows, push back up.",
                    "modifications": "Bend knees (easier) or straighten legs (harder)"
                }
            ],
            "Chest": [
                {
                    "name": "Push-ups",
                    "type": "strength",
                    "sets": 3,
                    "reps": reps,
                    "rest_seconds": rest,
                    "instructions": "Start in plank position, lower chest to ground, push back up.",
                    "modifications": "Do on knees (easier) or elevate feet (harder)"
                },
                {
                    "name": "Incline Push-ups",
                    "type": "strength",
                    "sets": 3,
                    "reps": reps,
                    "rest_seconds": rest,
                    "instructions": "Place hands on elevated surface, perform push-up.",
                    "modifications": "Use higher surface (easier) or lower surface (harder)"
                }
            ],
            "Back": [
                {
                    "name": "Bent Over Rows",
                    "type": "strength",
                    "sets": 3,
                    "reps": reps,
                    "rest_seconds": rest,
                    "instructions": "Bend at hips, pull weights to chest while squeezing shoulder blades.",
                    "modifications": "Use lighter weights (easier) or heavier weights (harder)"
                },
                {
                    "name": "Superman",
                    "type": "strength",
                    "sets": 3,
                    "reps": "12-15",
                    "rest_seconds": rest,
                    "instructions": "Lie face down, lift arms and legs while squeezing back muscles.",
                    "modifications": "Lift only upper body (easier) or add arm/leg pulses (harder)"
                }
            ],
            "Legs": [
                {
                    "name": "Bodyweight Squats",
                    "type": "strength",
                    "sets": 3,
                    "reps": reps,
                    "rest_seconds": rest,
                    "instructions": "Stand with feet shoulder-width apart, lower down as if sitting back into a chair.",
                    "modifications": "Hold onto support (easier) or add jump (harder)"
                },
                {
                    "name": "Lunges",
                    "type": "strength",
                    "sets": 3,
                    "reps": reps,
                    "rest_seconds": rest,
                    "instructions": "Step forward, lower back knee toward ground, push back to start.",
                    "modifications": "Hold onto support (easier) or add weights (harder)"
                }
            ],
            "Shoulders": [
                {
                    "name": "Shoulder Press",
                    "type": "strength",
                    "sets": 3,
                    "reps": reps,
                    "rest_seconds": rest,
                    "instructions": "Press weights overhead while keeping core engaged.",
                    "modifications": "Use lighter weights (easier) or heavier weights (harder)"
                },
                {
                    "name": "Lateral Raises",
                    "type": "strength",
                    "sets": 3,
                    "reps": reps,
                    "rest_seconds": rest,
                    "instructions": "Raise arms to sides until parallel to ground.",
                    "modifications": "Use lighter weights (easier) or heavier weights (harder)"
                }
            ],
            "Abs": [
                {
                    "name": "Crunches",
                    "type": "strength",
                    "sets": 3,
                    "reps": reps,
                    "rest_seconds": rest,
                    "instructions": "Lie on back, lift shoulders while engaging core.",
                    "modifications": "Cross arms on chest (easier) or add weights (harder)"
                },
                {
                    "name": "Plank",
                    "type": "strength",
                    "sets": 3,
                    "reps": "30-45 seconds",
                    "rest_seconds": rest,
                    "instructions": "Hold straight line from head to heels, engage core.",
                    "modifications": "Drop to knees (easier) or add leg lifts (harder)"
                }
            ],
            "Cardio": [
                {
                    "name": "Jumping Jacks",
                    "type": "cardio",
                    "sets": 3,
                    "reps": "30-45 seconds",
                    "rest_seconds": rest,
                    "instructions": "Jump while raising arms and legs out to sides.",
                    "modifications": "Step instead of jump (easier) or add arm circles (harder)"
                },
                {
                    "name": "High Knees",
                    "type": "cardio",
                    "sets": 3,
                    "reps": "30-45 seconds",
                    "rest_seconds": rest,
                    "instructions": "Run in place while bringing knees up high.",
                    "modifications": "March in place (easier) or add arm movements (harder)"
                }
            ],
            "Full Body": [
                {
                    "name": "Bodyweight Squats",
                    "type": "strength",
                    "sets": 3,
                    "reps": reps,
                    "rest_seconds": rest,
                    "instructions": "Stand with feet shoulder-width apart, lower down as if sitting back into a chair.",
                    "modifications": "Hold onto support (easier) or add jump (harder)"
                },
                {
                    "name": "Push-ups",
                    "type": "strength",
                    "sets": 3,
                    "reps": reps,
                    "rest_seconds": rest,
                    "instructions": "Start in plank position, lower chest to ground, push back up.",
                    "modifications": "Do on knees (easier) or elevate feet (harder)"
                },
                {
                    "name": "Plank",
                    "type": "strength",
                    "sets": 3,
                    "reps": "30-45 seconds",
                    "rest_seconds": rest,
                    "instructions": "Hold straight line from head to heels, engage core.",
                    "modifications": "Drop to knees (easier) or add leg lifts (harder)"
                }
            ]
        }
        
        # Get exercises for the target muscle group
        exercises = muscle_group_exercises.get(target_muscle_group, muscle_group_exercises["Full Body"])
        
        fallback_workout = {
            "workout_type": target_muscle_group,
            "duration_minutes": 30,
            "difficulty": fitness_level.title(),
            "exercises": exercises,
            "warmup": [
                {
                    "name": "Arm Circles",
                    "duration_seconds": 30,
                    "instructions": "Make large circles with your arms forward then backward"
                },
                {
                    "name": "March in Place",
                    "duration_seconds": 60,
                    "instructions": "Lift knees high while marching in place"
                }
            ],
            "cooldown": [
                {
                    "name": "Forward Fold",
                    "duration_seconds": 30,
                    "instructions": "Reach toward your toes, let your back round naturally"
                },
                {
                    "name": "Shoulder Stretch",
                    "duration_seconds": 30,
                    "instructions": "Pull arm across chest, hold with other arm"
                }
            ],
            "tips": [
                "Focus on proper form over speed",
                "Listen to your body and rest when needed",
                "Stay hydrated throughout your workout"
            ],
            "calories_estimate": 150
        }
        
        return fallback_workout

    def _determine_next_muscle_group(self, workout_history: Optional[list], muscle_groups: list) -> str:
        """Determine the next muscle group to target based on workout history"""
        if not workout_history:
            # If no history, start with a balanced full-body workout
            return "Full Body"
        
        # Get the last 5 workouts (or fewer if not available)
        recent_workouts = workout_history[:5]
        recent_types = [w.get('workout_type', '') for w in recent_workouts]
        
        # Count frequency of each muscle group in recent workouts
        muscle_group_counts = {group: recent_types.count(group) for group in muscle_groups}
        
        # Find the least frequently worked muscle group
        min_count = min(muscle_group_counts.values())
        least_worked = [group for group, count in muscle_group_counts.items() if count == min_count]
        
        # If multiple groups are tied for least worked, choose one that hasn't been done recently
        if len(least_worked) > 1:
            for group in least_worked:
                if group not in recent_types[:2]:  # Not done in last 2 workouts
                    return group
        
        # Return the first least worked group
        return least_worked[0]

def list_available_gemini_models():
    import google.generativeai as genai
    from config.config import Config
    import logging
    logger = logging.getLogger(__name__)
    try:
        genai.configure(api_key=Config.GEMINI_API_KEY)
        models = genai.list_models()
        logger.info(f"Available Gemini models: {models}")
        print("Available Gemini models:")
        for model in models:
            print(model)
    except Exception as e:
        logger.error(f"Error listing Gemini models: {e}")
        print(f"Error listing Gemini models: {e}")