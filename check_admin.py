from app import create_app
from models import User
from extensions import db

app = create_app()
with app.app_context():
    user = User.query.filter_by(username='admin').first()
    if user:
        print(f"User found: {user.username}, role: {user.role}")
        print(f"Password check for 'admin123': {user.check_password('admin123')}")
    else:
        print("Admin user not found")
