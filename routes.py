from flask import request, jsonify, render_template, redirect, url_for, session, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from extensions import db
from models import User, Challenge, Submission
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import re
import os
from sqlalchemy import func

# Login manager setup will be done in the init_routes function

UPLOAD_FOLDER = 'static/uploads/challenges'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp', 'svg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def init_routes(app):
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('challenges'))
            
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            
            # Validate input
            if not all([username, email, password]):
                flash('All fields are required', 'danger')
                return redirect(url_for('register'))
                
            if len(username) < 3 or len(username) > 20:
                flash('Username must be between 3 and 20 characters', 'danger')
                return redirect(url_for('register'))
                
            if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                flash('Please enter a valid email address', 'danger')
                return redirect(url_for('register'))
                
            if len(password) < 8:
                flash('Password must be at least 8 characters long', 'danger')
                return redirect(url_for('register'))

            # Check for existing user
            if User.query.filter(func.lower(User.username) == func.lower(username)).first():
                flash('Username already exists', 'danger')
                return redirect(url_for('register'))

            if User.query.filter(func.lower(User.email) == email.lower()).first():
                flash('Email already registered', 'danger')
                return redirect(url_for('register'))

            # Create new user
            user = User(username=username, email=email)
            user.set_password(password)
            
            # First user is admin
            if User.query.count() == 0:
                user.role = 'admin'
                
            db.session.add(user)
            try:
                db.session.commit()
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                db.session.rollback()
                flash('An error occurred during registration. Please try again.', 'danger')
                app.logger.error(f'Registration error: {str(e)}')

        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('challenges'))
            
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            if not username or not password:
                flash('Please enter both username and password', 'danger')
                return redirect(url_for('login'))

            user = User.query.filter(func.lower(User.username) == func.lower(username)).first()
            if user and user.check_password(password):
                login_user(user)
                next_page = request.args.get('next')
                return redirect(next_page or url_for('challenges'))

            flash('Invalid username or password', 'danger')
        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('index'))

    @app.route('/challenges')
    @login_required
    def challenges():
        challenges = Challenge.query.filter_by(is_active=True).all()
        return render_template('challenges.html', challenges=challenges)

    @app.route('/challenge/<int:challenge_id>', methods=['GET', 'POST'])
    @login_required
    def challenge(challenge_id):
        challenge = Challenge.query.get_or_404(challenge_id)
        if request.method == 'POST':
            submitted_flag = request.form.get('flag', '').strip()
            if not submitted_flag:
                flash('Please enter a flag', 'danger')
                return redirect(url_for('challenge', challenge_id=challenge_id))
                
            # Check if already solved
            existing = Submission.query.filter_by(
                user_id=current_user.id, 
                challenge_id=challenge_id, 
                is_correct=True
            ).first()
            
            if existing:
                flash('You have already solved this challenge', 'info')
                return redirect(url_for('challenge', challenge_id=challenge_id))

            is_correct = submitted_flag == challenge.flag
            submission = Submission(
                user_id=current_user.id,
                challenge_id=challenge_id,
                submitted_flag=submitted_flag,
                is_correct=is_correct
            )
            db.session.add(submission)

            if is_correct:
                current_user.score += challenge.points
                flash('Correct flag! Points added to your score.', 'success')
            else:
                flash('Incorrect flag. Try again.', 'danger')

            db.session.commit()
            return redirect(url_for('challenge', challenge_id=challenge_id))

        return render_template('challenge.html', challenge=challenge)

    @app.route('/scoreboard')
    @login_required
    def scoreboard():
        if current_user.role == 'admin':
            # Admins see full leaderboard
            users = User.query.filter(User.role != 'admin').order_by(User.score.desc()).all()
            # Create list of dicts with rank
            leaderboard = []
            for idx, user in enumerate(users, start=1):
                leaderboard.append({'rank': idx, 'user': user})
            return render_template('scoreboard.html', users=leaderboard, is_admin=True)
        else:
            # Regular users see only their own entry with rank
            all_users = User.query.filter(User.role != 'admin').order_by(User.score.desc()).all()
            # Find the current user's rank
            user_rank = None
            for idx, user in enumerate(all_users, start=1):
                if user.id == current_user.id:
                    user_rank = idx
                    break
            # If user not found (shouldn't happen), default to last
            if user_rank is None:
                user_rank = len(all_users) + 1
            user_data = [{'rank': user_rank, 'user': current_user}]
            return render_template('scoreboard.html', users=user_data, is_admin=False)

    @app.route('/admin')
    @admin_required
    def admin():
        stats = {
            'total_users': User.query.count(),
            'total_challenges': Challenge.query.count(),
            'total_submissions': Submission.query.count(),
            'solved_challenges': Submission.query.filter_by(is_correct=True).count()
        }
        challenges = Challenge.query.all()
        return render_template('admin.html', challenges=challenges, stats=stats)

    @app.route('/admin/challenge/add', methods=['GET', 'POST'])
    @admin_required
    def add_challenge():
        if request.method == 'POST':
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            category = request.form.get('category', '').strip()
            flag = request.form.get('flag', '').strip()
            crypto_type = request.form.get('crypto_type', '').strip() if category == 'cryptography' else ''

            try:
                points = int(request.form.get('points', 0))
                if points < 0:
                    raise ValueError('Points must be positive')
            except (ValueError, TypeError):
                flash('Invalid points value', 'danger')
                return redirect(url_for('add_challenge'))

            if not all([title, description, category, flag]):
                flash('All fields are required', 'danger')
                return redirect(url_for('add_challenge'))

            # Handle file uploads
            uploaded_files = []
            if 'media_files' in request.files:
                files = request.files.getlist('media_files')
                for file in files:
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        # Add challenge ID prefix to avoid conflicts
                        unique_filename = f"temp_{filename}"
                        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                        file.save(file_path)
                        uploaded_files.append(unique_filename)
                    elif file:
                        flash(f'Invalid file type for {file.filename}. Allowed: {", ".join(ALLOWED_EXTENSIONS)}', 'danger')
                        return redirect(url_for('add_challenge'))

            challenge = Challenge(
                title=title,
                description=description,
                category=category,
                flag=flag,
                points=points,
                crypto_type=crypto_type
            )
            challenge.set_media_files(uploaded_files)

            db.session.add(challenge)
            try:
                db.session.commit()
                # Rename files with challenge ID
                for i, filename in enumerate(uploaded_files):
                    old_path = os.path.join(UPLOAD_FOLDER, filename)
                    new_filename = f"{challenge.id}_{filename.replace('temp_', '')}"
                    new_path = os.path.join(UPLOAD_FOLDER, new_filename)
                    os.rename(old_path, new_path)
                    uploaded_files[i] = new_filename
                challenge.set_media_files(uploaded_files)
                db.session.commit()
                flash('Challenge added successfully', 'success')
                return redirect(url_for('admin'))
            except Exception as e:
                db.session.rollback()
                # Clean up uploaded files on error
                for filename in uploaded_files:
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                flash('Error adding challenge. Please try again.', 'danger')
                app.logger.error(f'Error adding challenge: {str(e)}')

        return render_template('add_challenge.html')

    @app.route('/admin/challenge/edit/<int:challenge_id>', methods=['GET', 'POST'])
    @admin_required
    def edit_challenge(challenge_id):
        challenge = Challenge.query.get_or_404(challenge_id)
        if request.method == 'POST':
            challenge.title = request.form.get('title', '').strip()
            challenge.description = request.form.get('description', '').strip()
            challenge.category = request.form.get('category', '').strip()
            challenge.flag = request.form.get('flag', '').strip()
            challenge.crypto_type = request.form.get('crypto_type', '').strip() if challenge.category == 'cryptography' else ''

            try:
                challenge.points = int(request.form.get('points', 0))
                if challenge.points < 0:
                    raise ValueError('Points must be positive')
            except (ValueError, TypeError):
                flash('Invalid points value', 'danger')
                return redirect(url_for('edit_challenge', challenge_id=challenge_id))

            if not all([challenge.title, challenge.description, challenge.category, challenge.flag]):
                flash('All fields are required', 'danger')
                return redirect(url_for('edit_challenge', challenge_id=challenge_id))

            # Handle file uploads
            current_files = challenge.get_media_files()
            if 'media_files' in request.files:
                files = request.files.getlist('media_files')
                for file in files:
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        unique_filename = f"{challenge.id}_{filename}"
                        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                        file.save(file_path)
                        current_files.append(unique_filename)
                    elif file:
                        flash(f'Invalid file type for {file.filename}. Allowed: {", ".join(ALLOWED_EXTENSIONS)}', 'danger')
                        return redirect(url_for('edit_challenge', challenge_id=challenge_id))
            challenge.set_media_files(current_files)

            try:
                db.session.commit()
                flash('Challenge updated successfully', 'success')
                return redirect(url_for('admin'))
            except Exception as e:
                db.session.rollback()
                flash('Error updating challenge', 'danger')
                app.logger.error(f'Error updating challenge: {str(e)}')

        return render_template('edit_challenge.html', challenge=challenge)

    @app.route('/admin/challenge/delete/<int:challenge_id>', methods=['POST'])
    @admin_required
    def delete_challenge(challenge_id):
        challenge = Challenge.query.get_or_404(challenge_id)
        try:
            # Delete related submissions first
            Submission.query.filter_by(challenge_id=challenge_id).delete()
            db.session.delete(challenge)
            db.session.commit()
            flash('Challenge deleted successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error deleting challenge', 'danger')
            app.logger.error(f'Error deleting challenge: {str(e)}')
            
        return redirect(url_for('admin'))
