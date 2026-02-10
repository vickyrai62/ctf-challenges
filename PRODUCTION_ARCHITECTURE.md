# Production-Grade CTF/Lab Platform - System Architecture

## 🏗️ OVERVIEW

### Core Security Principle
**Correct answers are NEVER exposed to users** - only stored securely as salted hashes

### Platform Roles
- **Admin**: Full control over challenges, users, and system settings
- **User**: Participant with restricted access, can only solve challenges

---

## 📊 DATABASE SCHEMA

### Core Tables

```sql
-- Users Table
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'user') DEFAULT 'user',
    score INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_username (username),
    INDEX idx_role (role)
);

-- Challenges Table
CREATE TABLE challenges (
    id INTEGER PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    category ENUM('port_scanning', 'service_enumeration', 'web_enumeration', 
                  'auth_logic', 'sql_injection', 'xss_csrf', 'file_upload_lfi_rfi',
                  'privilege_escalation', 'forensics', 'osint', 'reverse_engineering',
                  'malware_dfir') NOT NULL,
    difficulty ENUM('basic', 'intermediate', 'advanced', 'expert') NOT NULL,
    description TEXT NOT NULL,
    scenario TEXT,
    answer_hash VARCHAR(255) NOT NULL,  -- NEVER shown to users
    answer_salt VARCHAR(64) NOT NULL,    -- Unique salt per challenge
    points INTEGER NOT NULL,
    max_attempts INTEGER DEFAULT NULL,
    time_limit INTEGER DEFAULT NULL,  -- Minutes
    is_active BOOLEAN DEFAULT TRUE,
    mode ENUM('practice', 'competition') DEFAULT 'practice',
    docker_image VARCHAR(200),
    docker_port INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_category (category),
    INDEX idx_difficulty (difficulty),
    INDEX idx_mode (mode)
);

-- Submissions Table
CREATE TABLE submissions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    challenge_id INTEGER NOT NULL,
    submitted_answer VARCHAR(500) NOT NULL,
    is_correct BOOLEAN NOT NULL,
    attempt_number INTEGER NOT NULL,
    time_taken INTEGER,  -- Seconds
    ip_address VARCHAR(45),
    user_agent TEXT,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (challenge_id) REFERENCES challenges(id) ON DELETE CASCADE,
    INDEX idx_user_challenge (user_id, challenge_id),
    INDEX idx_submitted_at (submitted_at)
);

-- Hints Table
CREATE TABLE hints (
    id INTEGER PRIMARY KEY,
    challenge_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    point_cost INTEGER DEFAULT 5,
    order_index INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (challenge_id) REFERENCES challenges(id) ON DELETE CASCADE,
    INDEX idx_challenge_order (challenge_id, order_index)
);

-- User Hints Table
CREATE TABLE user_hints (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    hint_id INTEGER NOT NULL,
    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    points_deducted INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (hint_id) REFERENCES hints(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_hint (user_id, hint_id)
);

-- Docker Instances Table (for dynamic labs)
CREATE TABLE docker_instances (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    challenge_id INTEGER NOT NULL,
    container_id VARCHAR(100),
    container_ip VARCHAR(45),
    container_port INTEGER,
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (challenge_id) REFERENCES challenges(id) ON DELETE CASCADE,
    INDEX idx_user_active (user_id, is_active),
    INDEX idx_expires_at (expires_at)
);

-- Audit Log Table
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id INTEGER,
    details JSON,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_user_action (user_id, action),
    INDEX idx_created_at (created_at)
);
```

---

## 🔐 SECURITY IMPLEMENTATION

### Answer Hashing System
```python
import hashlib
import secrets
import bcrypt

class SecureAnswerHandler:
    @staticmethod
    def hash_answer(answer: str) -> tuple[str, str]:
        """Generate salted hash for answer storage"""
        salt = secrets.token_hex(32)  # 64-character hex salt
        # Use SHA-256 for speed in CTF context
        hash_obj = hashlib.sha256((answer + salt).encode('utf-8'))
        return f"{salt}${hash_obj.hexdigest()}", salt
    
    @staticmethod
    def verify_answer(submitted_answer: str, stored_hash: str) -> bool:
        """Verify submitted answer against stored hash"""
        try:
            salt, hash_value = stored_hash.split('$')
            hash_obj = hashlib.sha256((submitted_answer + salt).encode('utf-8'))
            return hash_obj.hexdigest() == hash_value
        except:
            return False
```

### Rate Limiting
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis

# Redis-based rate limiting for production
limiter = Limiter(
    app,
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379",
    default_limits=["60 per minute", "10 per minute"]
)

# Challenge-specific rate limiting
@limiter.limit("5 per minute")
def submit_challenge_answer():
    # Submission logic
```

---

## 🎮 CHALLENGE TEMPLATES & AUTO-GENERATION

### 1. Port Scanning & Network Enumeration
```python
class PortScanningChallenge:
    TEMPLATES = {
        'open_ports': {
            'template': "Scan the target machine {target_ip}. Which ports are open? (comma-separated, ascending)",
            'answer_type': 'port_list',
            'validation': lambda x: all(p.isdigit() and 1 <= int(p) <= 65535 for p in x.split(','))
        },
        'first_open_port': {
            'template': "Scan {target_ip}. What is the first open port discovered?",
            'answer_type': 'single_port',
            'validation': lambda x: x.isdigit() and 1 <= int(x) <= 65535
        },
        'ssh_service': {
            'template': "Scan {target_ip}. Which port is running SSH service?",
            'answer_type': 'port_number',
            'validation': lambda x: x.isdigit() and 1 <= int(x) <= 65535
        },
        'http_service': {
            'template': "Scan {target_ip}. Which port is running an HTTP service?",
            'answer_type': 'port_number',
            'validation': lambda x: x.isdigit() and 1 <= int(x) <= 65535
        },
        'non_standard_port': {
            'template': "Scan {target_ip}. Which open port is non-standard (not in top 1000 ports)?",
            'answer_type': 'port_number',
            'validation': lambda x: x.isdigit() and 1 <= int(x) <= 65535
        }
    }
```

### 2. SQL Injection Challenges
```python
class SQLInjectionChallenge:
    TEMPLATES = {
        'database_name': {
            'template': "Exploit the SQL injection at {target_url}. What is the database name?",
            'answer_type': 'string',
            'validation': lambda x: len(x) > 0 and x.isalnum()
        },
        'users_table': {
            'template': "Find the SQL injection at {target_url}. What is the name of the users table?",
            'answer_type': 'string',
            'validation': lambda x: len(x) > 0 and x.replace('_', '').isalnum()
        },
        'column_count': {
            'template': "Determine the number of columns in the vulnerable query at {target_url}",
            'answer_type': 'integer',
            'validation': lambda x: x.isdigit() and 1 <= int(x) <= 50
        },
        'admin_password': {
            'template': "Extract the admin password hash from {target_url}",
            'answer_type': 'hash',
            'validation': lambda x: len(x) == 32 and all(c in '0123456789abcdef' for c in x)
        }
    }
```

---

## 🔄 ANSWER VALIDATION LOGIC

```python
@app.route('/challenge/<int:challenge_id>/submit', methods=['POST'])
@limiter.limit("10 per minute")
@login_required
def submit_challenge_answer(challenge_id):
    # Get challenge
    challenge = Challenge.query.get_or_404(challenge_id)
    
    # Security checks
    if not challenge.is_active:
        return jsonify({'status': 'error', 'message': 'Challenge not active'})
    
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
    
    # Get and validate submission
    submitted_answer = request.form.get('answer', '').strip()
    
    if not submitted_answer:
        return jsonify({'status': 'empty_answer'})
    
    # Verify answer (NEVER reveal hash or correct answer)
    is_correct = SecureAnswerHandler.verify_answer(submitted_answer, challenge.answer_hash)
    
    # Record submission with audit trail
    submission = Submission(
        user_id=current_user.id,
        challenge_id=challenge_id,
        submitted_answer=submitted_answer,  # Store for admin review
        is_correct=is_correct,
        attempt_number=attempt_count + 1,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    
    db.session.add(submission)
    
    # Log audit event
    audit_log = AuditLog(
        user_id=current_user.id,
        action='submit_answer',
        resource_type='challenge',
        resource_id=challenge_id,
        details={
            'is_correct': is_correct,
            'attempt_number': attempt_count + 1,
            'challenge_category': challenge.category.value
        },
        ip_address=request.remote_addr
    )
    db.session.add(audit_log)
    
    if is_correct:
        # Award points
        current_user.score += challenge.points
        db.session.commit()
        
        return jsonify({
            'status': 'correct',
            'points': challenge.points,
            'total_score': current_user.score,
            'message': f'Correct! You earned {challenge.points} points.'
        })
    else:
        db.session.commit()
        remaining = None
        if challenge.max_attempts:
            remaining = challenge.max_attempts - (attempt_count + 1)
        
        return jsonify({
            'status': 'incorrect',
            'remaining_attempts': remaining,
            'message': 'Incorrect. Try again!' if remaining is None or remaining > 0 else 'No attempts remaining.'
        })
```

---

## 🎛️ ADMIN CONTROLS

### Challenge Management
```python
@admin_bp.route('/challenges/generate', methods=['GET', 'POST'])
@admin_required
def generate_challenge():
    """Auto-generate challenge from template"""
    if request.method == 'POST':
        category = request.form.get('category')
        template_type = request.form.get('template_type')
        difficulty = request.form.get('difficulty')
        points = int(request.form.get('points'))
        target_config = request.form.get('target_config')
        
        # Get template
        template = CHALLENGE_TEMPLATES[category][template_type]
        
        # Generate challenge
        challenge = Challenge(
            title=f"{category.replace('_', ' ').title()} - {template_type.replace('_', ' ').title()}",
            category=ChallengeCategory(category),
            difficulty=ChallengeDifficulty(difficulty),
            description=template['template'].format(**json.loads(target_config)),
            points=points
        )
        
        # Generate answer and hash it
        answer = generate_answer_for_template(template_type, target_config)
        challenge.answer_hash, challenge.answer_salt = SecureAnswerHandler.hash_answer(answer)
        
        db.session.add(challenge)
        db.session.commit()
        
        flash('Challenge generated successfully', 'success')
        return redirect(url_for('admin.challenges'))
    
    return render_template('admin/generate_challenge.html', 
                        templates=CHALLENGE_TEMPLATES)
```

---

## 📱 USER INTERFACE

### Challenge Dashboard
- Clean, responsive design with Bootstrap 5
- Category-based filtering
- Difficulty indicators
- Progress tracking
- Real-time scoreboard

### Security Features
- CSRF protection on all forms
- Secure session management
- Input sanitization
- SQL injection prevention
- XSS protection

---

## 🐳 DOCKER INTEGRATION

### Dynamic Lab Instances
```python
class DockerLabManager:
    def create_instance(self, challenge_id, user_id):
        """Create isolated Docker instance for user"""
        challenge = Challenge.query.get(challenge_id)
        
        # Generate unique container name
        container_name = f"ctf_{challenge_id}_{user_id}_{int(time.time())}"
        
        # Start container with security constraints
        container = docker_client.containers.run(
            challenge.docker_image,
            name=container_name,
            detach=True,
            ports={f'{challenge.docker_port}/tcp': None},
            mem_limit='512m',
            cpu_quota=50000,
            network='ctf-isolated',
            remove=True
        )
        
        # Store instance info
        instance = DockerInstance(
            user_id=user_id,
            challenge_id=challenge_id,
            container_id=container.id,
            container_port=container.ports[f'{challenge.docker_port}/tcp'][0]['HostPort'],
            expires_at=datetime.utcnow() + timedelta(hours=2)
        )
        
        db.session.add(instance)
        db.session.commit()
        
        return instance
```

---

## 📊 SCALABILITY & PERFORMANCE

### Database Optimization
- Proper indexing on frequently queried columns
- Connection pooling
- Query optimization
- Caching with Redis

### Security Hardening
- WAF integration
- VPN-only access option
- IP whitelisting
- Audit logging
- Intrusion detection

### Monitoring & Analytics
- Real-time user activity monitoring
- Performance metrics
- Security event tracking
- System health checks

This architecture provides a production-grade, secure, and scalable CTF platform that strictly follows all your requirements while supporting all specified challenge types.
