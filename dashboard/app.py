from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
from datetime import datetime, timedelta
import json
from src.database.supabase_client import supabase_client
from src.database.models import User, Workout, DietPlan, ChatMessage, UserSession, Trainer, Payment
from functools import wraps
from supabase import create_client, Client
import hashlib
from src.database.auth import verify_auth_user, create_user_session, hash_password

app = Flask(__name__)
app.secret_key = os.environ.get('DASHBOARD_SECRET_KEY', 'your-secret-key-change-this-in-production')

# Configure login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Admin credentials
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

# Trainer credentials (in production, use proper authentication)
TRAINER_USERNAME = os.environ.get('TRAINER_USERNAME', 'trainer')
TRAINER_PASSWORD = os.environ.get('TRAINER_PASSWORD', 'trainer123')

# Supabase configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", SUPABASE_KEY)

def init_supabase():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Supabase connection failed: {e}")
        return None

def init_supabase_service():
    try:
        return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    except Exception as e:
        print(f"Supabase service connection failed: {e}")
        return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_role' not in session or session['user_role'] != 'admin':
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

class AdminUser(UserMixin):
    def __init__(self, user_id):
        self.id = user_id

class TrainerUser(UserMixin):
    def __init__(self, user_id):
        self.id = user_id
        self.is_trainer = True

@login_manager.user_loader
def load_user(user_id):
    if user_id.startswith('trainer:'):
        return TrainerUser(user_id)
    return AdminUser(user_id)

@app.route('/')
@login_required
def dashboard():
    if session.get('user_role') == 'admin':
        return redirect(url_for('admin_dashboard'))
    return render_template('user_dashboard.html')

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower().replace(' ', '')
        password = request.form.get('password', '').strip()
        supabase = init_supabase_service()
        if not supabase:
            flash("Database connection error", "error")
            return render_template('login.html')
        password_hash = hash_password(password)
        # Admin login
        if username == 'admin' and password == 'admin123':
            response = supabase.table('users').select('*').eq('username', 'admin').execute()
            if response.data:
                user = response.data[0]
                session['user_id'] = user['id']
                session['user_role'] = 'admin'
                session['user_email'] = user['email']
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Admin user not found in database.', 'error')
                return render_template('login.html')
        # User login
        response = supabase.table('users').select('*').eq('username', username).eq('password_hash', password_hash).execute()
        if response.data:
            user = response.data[0]
            session['user_id'] = user['id']
            session['user_email'] = user['email']
            session['user_role'] = 'user'
            session['user_name'] = f"{user.get('first_name', '')} {user.get('last_name', '')}"
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials. Username is your first name, password is first name + 123.", "error")
            return render_template('login.html')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/trainer')
@login_required
def trainer_dashboard():
    if not (hasattr(current_user, 'is_trainer') and current_user.is_trainer):
        return redirect(url_for('dashboard'))
    return render_template('trainer_dashboard.html')

@app.route('/api/stats')
@login_required
def get_stats():
    """Get overall statistics for the dashboard"""
    try:
        # Get all users
        users_result = supabase_client.client.table('users').select('*').execute()
        all_users = users_result.data or []
        
        # Get all workouts
        workouts_result = supabase_client.client.table('workouts').select('*').execute()
        all_workouts = workouts_result.data or []
        
        # Get all messages
        messages_result = supabase_client.client.table('chat_messages').select('*').execute()
        all_messages = messages_result.data or []
        
        # Calculate active users (users with workouts in last 30 days)
        thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
        active_users = len(set([w['user_id'] for w in all_workouts if w.get('created_date', '') >= thirty_days_ago]))
        
        # Calculate workout completion rate
        completed_workouts = len([w for w in all_workouts if w['status'] == 'completed'])
        workout_completion_rate = (completed_workouts / len(all_workouts) * 100) if all_workouts else 0
        
        return jsonify({
            'total_users': len(all_users),
            'total_workouts': len(all_workouts),
            'total_messages': len(all_messages),
            'active_users': active_users,
            'workout_completion_rate': workout_completion_rate
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users')
@login_required
def get_users():
    """Get all users with their complete statistics"""
    try:
        # Get all users
        users_result = supabase_client.client.table('users').select('*').execute()
        users = users_result.data or []

        # Get all workouts for statistics
        workouts_result = supabase_client.client.table('workouts').select('*').execute()
        all_workouts = workouts_result.data or []

        # Calculate 30 days ago for recent activity
        thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()

        # Add statistics to each user
        for user in users:
            user_id = user.get('user_id')
            
            # Get user's workouts
            user_workouts = [w for w in all_workouts if w.get('user_id') == user_id]
            total_workouts = len(user_workouts)
            completed_workouts = len([w for w in user_workouts if w.get('status') == 'completed'])
            
            # Recent workouts (last 30 days)
            recent_workouts = [w for w in user_workouts if w.get('created_date', '') >= thirty_days_ago]
            recent_total = len(recent_workouts)
            recent_completed = len([w for w in recent_workouts if w.get('status') == 'completed'])
            
            # Calculate completion rates
            overall_rate = (completed_workouts / total_workouts * 100) if total_workouts > 0 else 0
            
            # Calculate average completion rate from individual workout completion rates
            workout_rates = []
            for workout in user_workouts:
                if workout.get('total_exercises', 0) > 0:
                    rate = (workout.get('exercises_completed', 0) / workout.get('total_exercises', 1)) * 100
                    workout_rates.append(rate)
            avg_completion = sum(workout_rates) / len(workout_rates) if workout_rates else 0
            
            # Add stats to user object
            user['total_workouts'] = total_workouts
            user['completed_workouts'] = completed_workouts
            user['recent_workouts'] = recent_total
            user['recent_completed'] = recent_completed
            user['overall_completion_rate'] = overall_rate
            user['avg_completion_rate'] = avg_completion

        return jsonify({'users': users})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/<user_id>')
@login_required
def get_user_details(user_id):
    """Get detailed information about a specific user"""
    try:
        # Get user info
        user_result = supabase_client.client.table('users').select('*').eq('user_id', user_id).execute()
        if not user_result.data:
            return jsonify({'error': 'User not found'}), 404
        
        user = user_result.data[0]
        
        # Get user's workouts
        workouts_result = supabase_client.client.table('workouts').select('*').eq('user_id', user_id).order('created_date', desc=True).limit(30).execute()
        workouts = workouts_result.data or []
        
        # Calculate workout stats
        total_workouts = len(workouts)
        completed_workouts = len([w for w in workouts if w['status'] == 'completed'])
        completion_rate = (completed_workouts / total_workouts * 100) if total_workouts > 0 else 0
        
        # Calculate exercise completion rates
        for workout in workouts:
            workout['completion_rate'] = (workout.get('exercises_completed', 0) / workout.get('total_exercises', 1) * 100) if workout.get('total_exercises', 0) > 0 else 0
        
        return jsonify({
            'user': user,
            'workouts': workouts,
            'stats': {
                'total_workouts': total_workouts,
                'completed_workouts': completed_workouts,
                'completion_rate': completion_rate
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversation/<user_id>')
@login_required
def get_conversation(user_id):
    """Get chat history for a specific user"""
    try:
        messages_result = supabase_client.client.table('chat_messages').select('*').eq('user_id', user_id).order('timestamp', desc=True).limit(100).execute()
        return jsonify({'messages': messages_result.data or []})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/profile')
@login_required
def get_user_profile():
    supabase = init_supabase_service()
    if not supabase:
        return jsonify({"error": "Database connection error"})
    try:
        user_response = supabase.table('users').select('*').eq('id', session['user_id']).execute()
        if not user_response.data:
            return jsonify({"error": "User not found"})
        user = user_response.data[0]
        return jsonify({
            'id': user['id'],
            'email': user['email'],
            'first_name': user['first_name'],
            'last_name': user['last_name'],
            'age': user.get('age'),
            'height': user.get('height'),
            'weight': user.get('weight'),
            'fitness_level': user.get('fitness_level'),
            'goals': user.get('goals')
        })
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/user/stats')
@login_required
def get_user_stats():
    try:
        # Fetch user object using session['user_id']
        user_response = supabase_client.client.table('users').select('*').eq('id', session['user_id']).execute()
        if not user_response.data:
            return jsonify({"error": "User not found"})
        user = user_response.data[0]
        user_id = user.get('user_id')  # Use the correct user_id for workouts

        workouts_response = supabase_client.client.table('workouts').select('*').eq('user_id', user_id).execute()
        workouts = workouts_response.data or []
        total_workouts = len(workouts)
        completed_workouts = len([w for w in workouts if w.get('status') == 'completed'])
        # Recent (last 30 days)
        thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
        recent_workouts = [w for w in workouts if w.get('created_date', '') >= thirty_days_ago]
        recent_total = len(recent_workouts)
        recent_completed = len([w for w in recent_workouts if w.get('status') == 'completed'])
        # Calculate completion rates
        overall_completion_rate = (completed_workouts / total_workouts * 100) if total_workouts > 0 else 0
        workout_rates = []
        for workout in workouts:
            if workout.get('total_exercises', 0) > 0:
                rate = (workout.get('exercises_completed', 0) / workout.get('total_exercises', 1)) * 100
                workout_rates.append(rate)
        avg_completion_rate = sum(workout_rates) / len(workout_rates) if workout_rates else 0
        # Streak
        streak = 0
        if workouts:
            sorted_workouts = sorted([w for w in workouts if w.get('status') == 'completed' and w.get('created_date')], key=lambda x: x['created_date'], reverse=True)
            today = datetime.now().date()
            for w in sorted_workouts:
                w_date = datetime.fromisoformat(w['created_date']).date()
                if (today - w_date).days == streak:
                    streak += 1
                else:
                    break
        return jsonify({
            'total_workouts': total_workouts,
            'completed_workouts': completed_workouts,
            'completion_rate': overall_completion_rate,
            'current_streak': streak,
            'avg_completion_rate': avg_completion_rate,
            'recent_workouts': recent_total,
            'recent_completed': recent_completed
        })
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/user/workouts')
@login_required
def get_user_workouts():
    period = request.args.get('period', 'week')
    try:
        # Fetch user object using session['user_id']
        user_response = supabase_client.client.table('users').select('*').eq('id', session['user_id']).execute()
        if not user_response.data:
            return jsonify({"error": "User not found"})
        user = user_response.data[0]
        user_id = user.get('user_id')  # Use the correct user_id for workouts

        now = datetime.now()
        if period == 'week':
            start_date = (now - timedelta(days=7)).isoformat()
        elif period == 'month':
            start_date = (now - timedelta(days=30)).isoformat()
        else:
            start_date = '1970-01-01'
        workouts_response = supabase_client.client.table('workouts').select('*').eq('user_id', user_id).gte('created_date', start_date).order('created_date', desc=True).execute()
        workouts = workouts_response.data or []
        # Add completion_rate to each workout
        for w in workouts:
            if w.get('total_exercises', 0) > 0:
                w['completion_rate'] = (w.get('exercises_completed', 0) / w.get('total_exercises', 1)) * 100
            else:
                w['completion_rate'] = 0
        return jsonify({'workouts': workouts})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/new_user_dashboard')
def new_user_dashboard():
    # Example data for plans and testimonials
    plans = [
        {"name": "Basic", "price": 499, "features": ["Workout Plan", "Diet Plan"]},
        {"name": "Premium", "price": 999, "features": ["All Basic Features", "1-on-1 Trainer", "Progress Tracking"]},
    ]
    testimonials = [
        {"user": "Alice", "text": "Great app! Helped me get fit."},
        {"user": "Bob", "text": "The trainer support is amazing!"},
    ]
    return render_template('new_user_dashboard.html', plans=plans, testimonials=testimonials, razorpay_key=os.environ.get("RAZORPAY_KEY_ID"))

@app.route('/Photos/<path:filename>')
def photos(filename):
    return send_from_directory('../Photos', filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 