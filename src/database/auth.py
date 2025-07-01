import hashlib
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import os
from supabase import Client

def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def create_auth_user(supabase: Client, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Create a new auth user when a new user is registered.
    
    Args:
        supabase: Supabase client
        user_data: Dictionary containing user information
            Required keys: first_name, last_name, username
            Optional keys: email (will be generated if not provided)
    
    Returns:
        Created auth user record or None if creation failed
    """
    try:
        # Generate email if not provided
        email = user_data.get('email', f"{user_data['username']}@fitness.com").lower()
        
        # Generate default password (username + "123")
        default_password = f"{user_data['username']}123"
        
        auth_user_data = {
            'email': email,
            'password_hash': hash_password(default_password),
            'role': 'user',
            'first_name': user_data['first_name'],
            'last_name': user_data['last_name'],
            'is_active': True
        }
        
        response = supabase.table('auth_users').insert(auth_user_data).execute()
        
        if response.data:
            print(f"Created auth user for {email}")
            print(f"Default password: {default_password}")
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error creating auth user: {e}")
        return None

def verify_auth_user(supabase: Client, email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Verify user credentials and return user info if valid.
    
    Args:
        supabase: Supabase client
        email: User's email
        password: User's password
    
    Returns:
        User info if credentials are valid, None otherwise
    """
    try:
        response = supabase.table('auth_users').select('*').eq('email', email.lower()).execute()
        
        if response.data:
            user = response.data[0]
            if user['password_hash'] == hash_password(password):
                return user
        return None
    except Exception as e:
        print(f"Error verifying auth user: {e}")
        return None

def create_user_session(supabase: Client, user_id: str) -> Optional[str]:
    """
    Create a new session for a user.
    
    Args:
        supabase: Supabase client
        user_id: Auth user's ID
    
    Returns:
        Session token if created successfully, None otherwise
    """
    try:
        session_data = {
            'user_id': user_id,
            'session_token': hashlib.sha256(os.urandom(32)).hexdigest(),
            'expires_at': (datetime.now() + timedelta(days=7)).isoformat()
        }
        
        response = supabase.table('user_sessions_auth').insert(session_data).execute()
        
        if response.data:
            return response.data[0]['session_token']
        return None
    except Exception as e:
        print(f"Error creating user session: {e}")
        return None

def verify_session(supabase: Client, session_token: str) -> Optional[Dict[str, Any]]:
    """
    Verify a session token and return user info if valid.
    
    Args:
        supabase: Supabase client
        session_token: Session token to verify
    
    Returns:
        User info if session is valid, None otherwise
    """
    try:
        response = supabase.table('user_sessions_auth').select(
            'user_sessions_auth.id, user_sessions_auth.expires_at, auth_users.*'
        ).eq('session_token', session_token).join(
            'auth_users', 
            'user_sessions_auth.user_id=auth_users.id'
        ).execute()
        
        if response.data:
            session = response.data[0]
            expires_at = datetime.fromisoformat(session['expires_at'].replace('Z', '+00:00'))
            
            if expires_at > datetime.now():
                return {
                    'user_id': session['id'],
                    'email': session['email'],
                    'role': session['role'],
                    'first_name': session['first_name'],
                    'last_name': session['last_name']
                }
        return None
    except Exception as e:
        print(f"Error verifying session: {e}")
        return None

def run_auth_migration(supabase: Client) -> bool:
    """
    Run the auth migration to create auth users for existing users.
    
    Args:
        supabase: Supabase client
    
    Returns:
        True if migration was successful, False otherwise
    """
    try:
        # Read and execute the migration SQL
        with open('migrations/create_auth_users.sql', 'r') as f:
            migration_sql = f.read()
        
        # Execute the migration in a transaction
        supabase.table('auth_users').select('*').execute()  # This is just to test the connection
        
        # Since we can't run raw SQL directly with supabase-py,
        # we'll need to break down the migration into separate operations
        
        # 1. Update users without usernames
        users_response = supabase.table('users').select('*').execute()
        for user in users_response.data:
            if not user.get('username') and user.get('first_name') and user.get('last_name'):
                username = f"{user['first_name'].lower()}.{user['last_name'].lower()}"
                supabase.table('users').update({'username': username}).eq('id', user['id']).execute()
        
        # 2. Create auth users for existing users
        users_response = supabase.table('users').select('*').execute()
        for user in users_response.data:
            if user.get('username'):
                email = f"{user['username']}@fitness.com".lower()
                # Check if auth user already exists
                auth_check = supabase.table('auth_users').select('*').eq('email', email).execute()
                
                if not auth_check.data:
                    auth_user_data = {
                        'email': email,
                        'password_hash': hash_password(f"{user['username']}123"),
                        'role': 'user',
                        'first_name': user.get('first_name'),
                        'last_name': user.get('last_name'),
                        'is_active': True
                    }
                    supabase.table('auth_users').insert(auth_user_data).execute()
        
        # 3. Create default admin if not exists
        admin_check = supabase.table('auth_users').select('*').eq('email', 'admin@fitness.com').execute()
        if not admin_check.data:
            admin_data = {
                'email': 'admin@fitness.com',
                'password_hash': hash_password('admin123'),
                'role': 'admin',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_active': True
            }
            supabase.table('auth_users').insert(admin_data).execute()
        
        print("Auth migration completed successfully")
        return True
    except Exception as e:
        print(f"Error running auth migration: {e}")
        return False 