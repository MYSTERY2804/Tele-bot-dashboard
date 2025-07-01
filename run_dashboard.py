#!/usr/bin/env python3
"""
Admin Dashboard Runner for Fitness Bot
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dashboard.app import app

if __name__ == '__main__':
    print("🏋️ Starting Fitness Bot Admin Dashboard...")
    print("📊 Dashboard will be available at: http://localhost:5000")
    print("🔐 Default credentials: admin / admin123")
    print("⚠️  Remember to change default credentials in production!")
    print()
    
    # Set default environment variables if not set
    if not os.environ.get('DASHBOARD_SECRET_KEY'):
        os.environ['DASHBOARD_SECRET_KEY'] = 'your-secret-key-change-this-in-production'
    
    if not os.environ.get('ADMIN_USERNAME'):
        os.environ['ADMIN_USERNAME'] = 'admin'
    
    if not os.environ.get('ADMIN_PASSWORD'):
        os.environ['ADMIN_PASSWORD'] = 'admin123'
    
    app.run(debug=True, host='0.0.0.0', port=5000) 