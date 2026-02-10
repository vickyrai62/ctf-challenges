# Professional CTF / Cyber Lab Platform - System Architecture

## 🏗️ SYSTEM OVERVIEW

### Platform Roles
- **Admin**: Full control over challenges, users, and system settings
- **User**: Participant who can solve challenges and earn points

### Core Security Principle
**Correct answers are NEVER exposed to users** - only stored securely as hashes

---

## 📊 DATABASE SCHEMA

### Core Tables

```sql
-- Users Table
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',  -- 'admin' or 'user'
    score INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Challenges Table
CREATE TABLE challenges (
    id INTEGER PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,  -- Network, Web, Crypto, Forensics, etc.
    difficulty VARCHAR(20) NOT NULL,  -- Basic, Intermediate, Advanced, Expert
    description TEXT NOT NULL,
    story TEXT,  -- Optional story/scenario
    answer_hash VARCHAR(256) NOT NULL,  -- NEVER shown to users
    points INTEGER NOT NULL,
    max_attempts INTEGER DEFAULT NULL,  -- Optional retry limit
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Submissions Table
CREATE TABLE submissions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    challenge_id INTEGER REFERENCES challenges(id),
    submitted_answer VARCHAR(200) NOT NULL,
    is_correct BOOLEAN NOT NULL,
    attempt_number INTEGER NOT NULL,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Hints Table (Optional)
CREATE TABLE hints (
    id INTEGER PRIMARY KEY,
    challenge_id INTEGER REFERENCES challenges(id),
    content TEXT NOT NULL,
    point_cost INTEGER DEFAULT 5,
    order_index INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE
);

-- User Hints Table (Track unlocked hints)
CREATE TABLE user_hints (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    hint_id INTEGER REFERENCES hints(id),
    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    points_deducted INTEGER NOT NULL
);
```

---

## 🔐 SECURITY IMPLEMENTATION

### Answer Hashing System
```python
import hashlib
import secrets

def hash_answer(answer: str) -> str:
    """Hash answer with salt for secure storage"""
    salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256((answer + salt).encode())
    return f"{salt}${hash_obj.hexdigest()}"

def verify_answer(submitted_answer: str, stored_hash: str) -> bool:
    """Verify submitted answer against stored hash"""
    try:
        salt, hash_value = stored_hash.split('$')
        hash_obj = hashlib.sha256((submitted_answer + salt).encode())
        return hash_obj.hexdigest() == hash_value
    except:
        return False
```

### Rate Limiting
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["60 per minute"]
)

@app.route('/submit', methods=['POST'])
@limiter.limit("10 per minute")
@login_required
def submit_answer():
    # Submission logic here
```

---

## 🔄 ANSWER VALIDATION LOGIC FLOW

```python
@app.route('/challenge/<int:challenge_id>/submit', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
def submit_challenge_answer(challenge_id):
    challenge = Challenge.query.get_or_404(challenge_id)
    
    # Check if already solved
    existing = Submission.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge_id,
        is_correct=True
    ).first()
    
    if existing:
        return jsonify({'status': 'already_solved'})
    
    # Check attempt limit
    attempt_count = Submission.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge_id
    ).count()
    
    if challenge.max_attempts and attempt_count >= challenge.max_attempts:
        return jsonify({'status': 'max_attempts_reached'})
    
    # Get submitted answer
    submitted_answer = request.form.get('answer', '').strip()
    
    if not submitted_answer:
        return jsonify({'status': 'empty_answer'})
    
    # Verify answer (NEVER reveal the hash or correct answer)
    is_correct = verify_answer(submitted_answer, challenge.answer_hash)
    
    # Record submission
    submission = Submission(
        user_id=current_user.id,
        challenge_id=challenge_id,
        submitted_answer=submitted_answer,  # Store for admin review
        is_correct=is_correct,
        attempt_number=attempt_count + 1
    )
    
    db.session.add(submission)
    
    if is_correct:
        # Award points
        current_user.score += challenge.points
        db.session.commit()
        
        return jsonify({
            'status': 'correct',
            'points': challenge.points,
            'total_score': current_user.score
        })
    else:
        db.session.commit()
        return jsonify({'status': 'incorrect'})
```

---

## 🎛️ ADMIN CONTROLS

### Challenge Management
```python
@admin_bp.route('/challenges/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_challenge():
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title')
        category = request.form.get('category')
        difficulty = request.form.get('difficulty')
        description = request.form.get('description')
        story = request.form.get('story')
        answer = request.form.get('answer')  # Plain text answer
        points = int(request.form.get('points'))
        max_attempts = request.form.get('max_attempts')
        
        # Hash the answer immediately - NEVER store plain text
        answer_hash = hash_answer(answer)
        
        # Create challenge (NEVER include plain answer)
        challenge = Challenge(
            title=title,
            category=category,
            difficulty=difficulty,
            description=description,
            story=story,
            answer_hash=answer_hash,  # Only store hash
            points=points,
            max_attempts=int(max_attempts) if max_attempts else None
        )
        
        db.session.add(challenge)
        db.session.commit()
        
        flash('Challenge created successfully', 'success')
        return redirect(url_for('admin.challenges'))
    
    return render_template('admin/create_challenge.html')

@admin_bp.route('/challenges/<int:challenge_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_challenge(challenge_id):
    challenge = Challenge.query.get_or_404(challenge_id)
    
    if request.method == 'POST':
        # Update challenge fields
        challenge.title = request.form.get('title')
        challenge.category = request.form.get('category')
        challenge.difficulty = request.form.get('difficulty')
        challenge.description = request.form.get('description')
        challenge.story = request.form.get('story')
        challenge.points = int(request.form.get('points'))
        challenge.max_attempts = request.form.get('max_attempts')
        
        # Update answer if provided
        new_answer = request.form.get('answer')
        if new_answer:
            challenge.answer_hash = hash_answer(new_answer)
        
        db.session.commit()
        flash('Challenge updated successfully', 'success')
        return redirect(url_for('admin.challenges'))
    
    return render_template('admin/edit_challenge.html', challenge=challenge)
```

### Admin Dashboard
```python
@admin_bp.route('/dashboard')
@login_required
@admin_required
def admin_dashboard():
    # Get statistics
    total_users = User.query.filter_by(role='user').count()
    total_challenges = Challenge.query.count()
    total_submissions = Submission.query.count()
    correct_submissions = Submission.query.filter_by(is_correct=True).count()
    
    # Get recent submissions
    recent_submissions = Submission.query\
        .join(User).join(Challenge)\
        .order_by(Submission.submitted_at.desc())\
        .limit(10).all()
    
    return render_template('admin/dashboard.html',
        total_users=total_users,
        total_challenges=total_challenges,
        total_submissions=total_submissions,
        correct_submissions=correct_submissions,
        recent_submissions=recent_submissions
    )
```

---

## 👤 USER FLOW

### Challenge Listing
```python
@app.route('/challenges')
@login_required
def list_challenges():
    # Get all active challenges
    challenges = Challenge.query.filter_by(is_active=True).all()
    
    # Get user's solved challenges
    solved_challenges = db.session.query(Submission.challenge_id)\
        .filter_by(user_id=current_user.id, is_correct=True)\
        .distinct().all()
    solved_ids = [challenge[0] for challenge in solved_challenges]
    
    return render_template('challenges/list.html',
        challenges=challenges,
        solved_challenges=solved_ids
    )
```

### Challenge View
```python
@app.route('/challenge/<int:challenge_id>')
@login_required
def view_challenge(challenge_id):
    challenge = Challenge.query.get_or_404(challenge_id)
    
    # Check if already solved
    is_solved = Submission.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge_id,
        is_correct=True
    ).first() is not None
    
    # Get attempt count
    attempt_count = Submission.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge_id
    ).count()
    
    # Get available hints
    hints = Hint.query.filter_by(challenge_id=challenge_id, is_active=True)\
        .order_by(Hint.order_index).all()
    
    # Get unlocked hints
    unlocked_hints = UserHint.query.filter_by(user_id=current_user.id)\
        .join(Hint).filter(Hint.challenge_id == challenge_id).all()
    unlocked_ids = [uh.hint_id for uh in unlocked_hints]
    
    return render_template('challenges/view.html',
        challenge=challenge,
        is_solved=is_solved,
        attempt_count=attempt_count,
        hints=hints,
        unlocked_hints=unlocked_ids
    )
```

---

## 🏆 SCORING SYSTEM

### Scoreboard
```python
@app.route('/scoreboard')
def scoreboard():
    # Get top users by score
    users = User.query.filter_by(role='user')\
        .order_by(User.score.desc(), User.created_at.asc())\
        .limit(100).all()
    
    # Get user's rank
    user_rank = None
    if current_user.is_authenticated:
        user_rank = User.query.filter_by(role='user')\
            .filter(User.score > current_user.score)\
            .count() + 1
    
    return render_template('scoreboard.html',
        users=users,
        user_rank=user_rank
    )
```

### Points Calculation
```python
def calculate_user_score(user_id):
    """Calculate user's total score from solved challenges"""
    total_score = db.session.query(
        db.func.sum(Challenge.points)
    ).join(Submission).filter(
        Submission.user_id == user_id,
        Submission.is_correct == True
    ).scalar() or 0
    
    return total_score
```

---

## 🛡️ SECURITY MEASURES

### Input Validation
```python
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, SelectField
from wtforms.validators import DataRequired, Length, NumberRange

class ChallengeForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=200)])
    category = SelectField('Category', choices=[
        ('network', 'Network'),
        ('web', 'Web'),
        ('crypto', 'Cryptography'),
        ('forensics', 'Forensics'),
        ('osint', 'OSINT'),
        ('reverse', 'Reverse Engineering'),
        ('malware', 'Malware Analysis'),
        ('privilege_escalation', 'Privilege Escalation')
    ], validators=[DataRequired()])
    
    difficulty = SelectField('Difficulty', choices=[
        ('basic', 'Basic'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert')
    ], validators=[DataRequired()])
    
    description = TextAreaField('Description', validators=[DataRequired()])
    story = TextAreaField('Story')
    answer = StringField('Correct Answer', validators=[DataRequired()])
    points = IntegerField('Points', validators=[DataRequired(), NumberRange(min=1)])
    max_attempts = IntegerField('Max Attempts', validators=[NumberRange(min=1)])
```

### CSRF Protection
```python
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)

# All forms automatically include CSRF protection
```

### Session Security
```python
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=1)
)
```

---

## 📱 UI/UX STRUCTURE

### User Dashboard
- **Navigation**: Challenges, Scoreboard, Profile, Logout
- **Challenge Cards**: Title, Category, Difficulty, Points, Status
- **Progress Indicators**: Visual completion status
- **Mobile Responsive**: Bootstrap/Tailwind CSS

### Admin Panel
- **Dashboard**: System statistics, recent activity
- **Challenge Management**: CRUD operations
- **User Management**: View users, reset progress
- **Submission Review**: Monitor all submissions
- **System Settings**: Configuration options

---

## 🐳 DOCKER INTEGRATION (Optional Advanced Feature)

### Docker Challenge Support
```python
class DockerChallenge(Challenge):
    __tablename__ = 'docker_challenges'
    
    id = db.Column(db.Integer, db.ForeignKey('challenge.id'), primary_key=True)
    docker_image = db.Column(db.String(200))
    docker_port = db.Column(db.Integer)
    container_timeout = db.Column(db.Integer, default=3600)  # 1 hour
    
    __mapper_args__ = {
        'polymorphic_identity': 'docker'
    }

def start_docker_challenge(challenge_id, user_id):
    """Start Docker container for challenge"""
    challenge = DockerChallenge.query.get(challenge_id)
    
    # Create unique container name
    container_name = f"challenge_{challenge_id}_{user_id}_{int(time.time())}"
    
    # Start container
    container = docker_client.containers.run(
        challenge.docker_image,
        name=container_name,
        ports={f'{challenge.docker_port}/tcp': None},
        detach=True,
        remove=True
    )
    
    # Store container info
    instance = DockerInstance(
        challenge_id=challenge_id,
        user_id=user_id,
        container_id=container.id,
        container_port=container.ports[f'{challenge.docker_port}/tcp'][0]['HostPort'],
        expires_at=datetime.utcnow() + timedelta(seconds=challenge.container_timeout)
    )
    
    db.session.add(instance)
    db.session.commit()
    
    return instance
```

---

## 📊 IMPLEMENTATION PLAN

### Phase 1: Core System
1. Database schema implementation
2. User authentication and roles
3. Basic challenge CRUD
4. Answer validation with hashing
5. Simple scoring system

### Phase 2: Security & UI
1. Rate limiting implementation
2. CSRF protection
3. Input validation
4. Responsive UI design
5. Admin dashboard

### Phase 3: Advanced Features
1. Hint system with point deduction
2. Docker integration
3. Advanced analytics
4. Competition modes
5. Time-based challenges

### Phase 4: Production Ready
1. Security audit
2. Performance optimization
3. Monitoring and logging
4. Backup and recovery
5. Documentation

---

## 🔒 CRITICAL SECURITY RULES

1. **NEVER** expose correct answers to users
2. **ALWAYS** hash answers before storage
3. **NEVER** reveal hashes to users
4. **ALWAYS** implement rate limiting
5. **NEVER** store plain text answers
6. **ALWAYS** validate all inputs
7. **NEVER** trust user submissions
8. **ALWAYS** use secure session management

This architecture ensures a secure, scalable, and professional CTF platform that meets all your strict requirements while maintaining the highest security standards.
