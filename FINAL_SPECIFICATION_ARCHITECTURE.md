# Production-Grade CTF & Lab Platform - Final Specification Architecture

## 🎯 CORE OBJECTIVE

Build a production-grade Cyber Security CTF & Lab Platform with:
- Strict level-based challenges
- Admin-only correct answers
- Points awarded ONLY on exact answer match
- Zero answer exposure to users

---

## 📊 DATABASE SCHEMA (STRICT COMPLIANCE)

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
    current_level ENUM('basic', 'intermediate', 'advanced', 'expert') DEFAULT 'basic',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_username (username),
    INDEX idx_role (role),
    INDEX idx_level (current_level)
);

-- Challenges Table
CREATE TABLE challenges (
    id INTEGER PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    level ENUM('basic', 'intermediate', 'advanced', 'expert') NOT NULL,
    category VARCHAR(100) NOT NULL,
    scenario TEXT NOT NULL,
    description TEXT NOT NULL,
    answer_hash VARCHAR(255) NOT NULL,  -- NEVER shown to users
    answer_salt VARCHAR(64) NOT NULL,    -- Unique salt per challenge
    points INTEGER NOT NULL,
    max_attempts INTEGER DEFAULT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_level (level),
    INDEX idx_category (category),
    INDEX idx_active (is_active)
);

-- Submissions Table
CREATE TABLE submissions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    challenge_id INTEGER NOT NULL,
    submitted_answer VARCHAR(1000) NOT NULL,
    is_correct BOOLEAN NOT NULL,
    attempt_number INTEGER NOT NULL,
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

## 🔐 SECURITY IMPLEMENTATION (ABSOLUTE COMPLIANCE)

### Answer Hashing System
```python
import hashlib
import secrets
import re

class SecureAnswerHandler:
    @staticmethod
    def normalize_answer(answer: str) -> str:
        """Normalize answer for exact comparison"""
        # Remove extra whitespace
        answer = ' '.join(answer.split())
        # Convert to lowercase for case-insensitive comparison
        answer = answer.lower()
        # Remove common CTF prefixes/suffixes
        answer = re.sub(r'^(flag\{|ctf\{|hackthebox\{|)', '', answer)
        answer = re.sub(r'(\})$', '', answer)
        return answer.strip()
    
    @staticmethod
    def hash_answer(answer: str) -> tuple[str, str]:
        """Generate salted hash for answer storage"""
        salt = secrets.token_hex(32)  # 64-character hex salt
        normalized = SecureAnswerHandler.normalize_answer(answer)
        # Use SHA-256 for consistent hashing
        hash_obj = hashlib.sha256((normalized + salt).encode('utf-8'))
        return f"{salt}${hash_obj.hexdigest()}", salt
    
    @staticmethod
    def verify_answer(submitted_answer: str, stored_hash: str) -> bool:
        """Verify submitted answer against stored hash"""
        try:
            salt, hash_value = stored_hash.split('$')
            normalized = SecureAnswerHandler.normalize_answer(submitted_answer)
            hash_obj = hashlib.sha256((normalized + salt).encode('utf-8'))
            return hash_obj.hexdigest() == hash_value
        except:
            return False
```

---

## 🎮 LEVEL-BASED CHALLENGE ENGINE (STRICT COMPLIANCE)

### 🟢 BASIC LEVEL - FUNDAMENTALS ONLY

```python
BASIC_CHALLENGES = {
    'linux_basics': {
        'open_port': {
            'template': "Which port is open on the target machine {target_ip}?",
            'answer_type': 'port_number',
            'validation': lambda x: x.isdigit() and 1 <= int(x) <= 65535,
            'points': 10
        },
        'target_ip': {
            'template': "What is the IP address of the target {hostname}?",
            'answer_type': 'ip_address',
            'validation': lambda x: len(x.split('.')) == 4 and all(o.isdigit() and 0 <= int(o) <= 255 for o in x.split('.')),
            'points': 5
        },
        'service_port80': {
            'template': "What service is running on port 80 of {target_ip}?",
            'answer_type': 'service_name',
            'validation': lambda x: x.lower() in ['http', 'apache', 'nginx', 'iis'],
            'points': 10
        },
        'http_response': {
            'template': "What is the HTTP response code from {target_url}?",
            'answer_type': 'status_code',
            'validation': lambda x: x.isdigit() and 100 <= int(x) <= 599,
            'points': 5
        },
        'source_comment': {
            'template': "What value is found in the source code comment of {target_url}?",
            'answer_type': 'string',
            'validation': lambda x: len(x) > 0,
            'points': 15
        },
        'base64_decode': {
            'template': "What is the decoded Base64 string: {encoded_string}?",
            'answer_type': 'string',
            'validation': lambda x: len(x) > 0,
            'points': 10
        },
        'system_user': {
            'template': "What username exists on the system {target_ip}?",
            'answer_type': 'username',
            'validation': lambda x: len(x) > 0 and x.replace('_', '').isalnum(),
            'points': 10
        },
        'file_permission': {
            'template': "What file permission is set on {file_path}?",
            'answer_type': 'permissions',
            'validation': lambda x: re.match(r'^[rwx-]{9}$', x),
            'points': 10
        },
        'robots_flag': {
            'template': "What flag is found in robots.txt of {target_url}?",
            'answer_type': 'string',
            'validation': lambda x: len(x) > 0,
            'points': 15
        }
    },
    
    'networking_basics': {
        'ping_ip': {
            'template': "What IP responds to ping from {target_network}?",
            'answer_type': 'ip_address',
            'validation': lambda x: len(x.split('.')) == 4 and all(o.isdigit() and 0 <= int(o) <= 255 for o in x.split('.')),
            'points': 10
        },
        'dns_record': {
            'template': "What is the A record for {domain}?",
            'answer_type': 'ip_address',
            'validation': lambda x: len(x.split('.')) == 4 and all(o.isdigit() and 0 <= int(o) <= 255 for o in x.split('.')),
            'points': 10
        }
    },
    
    'web_basics': {
        'page_title': {
            'template': "What is the title of the page at {target_url}?",
            'answer_type': 'string',
            'validation': lambda x: len(x) > 0,
            'points': 5
        },
        'cookie_name': {
            'template': "What is the name of the session cookie at {target_url}?",
            'answer_type': 'string',
            'validation': lambda x: len(x) > 0 and x.replace('_', '').replace('-', '').isalnum(),
            'points': 10
        }
    },
    
    'sql_injection_basic': {
        'database_version': {
            'template': "What is the database version at {target_url}?",
            'answer_type': 'version_string',
            'validation': lambda x: len(x) > 0,
            'points': 20
        },
        'table_count': {
            'template': "How many tables exist in the database at {target_url}?",
            'answer_type': 'integer',
            'validation': lambda x: x.isdigit() and 1 <= int(x) <= 100,
            'points': 15
        }
    },
    
    'xss_reflected': {
        'vulnerable_param': {
            'template': "Which parameter is vulnerable to reflected XSS at {target_url}?",
            'answer_type': 'parameter_name',
            'validation': lambda x: len(x) > 0 and x.replace('_', '').replace('-', '').isalnum(),
            'points': 20
        }
    },
    
    'simple_osint': {
        'email_address': {
            'template': "What email address belongs to {username}?",
            'answer_type': 'email',
            'validation': lambda x: '@' in x and '.' in x.split('@')[1],
            'points': 15
        },
        'subdomain': {
            'template': "What subdomain exists for {domain}?",
            'answer_type': 'subdomain',
            'validation': lambda x: len(x) > 0 and '.' in x,
            'points': 15
        }
    },
    
    'simple_forensics': {
        'hidden_file': {
            'template': "What hidden file is in the provided archive?",
            'answer_type': 'filename',
            'validation': lambda x: len(x) > 0,
            'points': 20
        },
        'file_hash': {
            'template': "What is the MD5 hash of the suspicious file?",
            'answer_type': 'hash',
            'validation': lambda x: len(x) == 32 and all(c in '0123456789abcdef' for c in x.lower()),
            'points': 15
        }
    }
}
```

### 🟡 INTERMEDIATE LEVEL - MULTI-STEP LOGIC

```python
INTERMEDIATE_CHALLENGES = {
    'advanced_sql_injection': {
        'hidden_directory': {
            'template': "What hidden directory contains the admin panel at {target_url}?",
            'answer_type': 'directory',
            'validation': lambda x: len(x) > 0 and x.startswith('/'),
            'points': 30
        },
        'database_name': {
            'template': "What database name was extracted using SQL injection at {target_url}?",
            'answer_type': 'string',
            'validation': lambda x: len(x) > 0 and x.replace('_', '').replace('-', '').isalnum(),
            'points': 35
        },
        'users_table': {
            'template': "What is the name of the users table at {target_url}?",
            'answer_type': 'table_name',
            'validation': lambda x: len(x) > 0 and x.replace('_', '').isalnum(),
            'points': 30
        },
        'admin_hash': {
            'template': "What hash belongs to the admin user at {target_url}?",
            'answer_type': 'hash',
            'validation': lambda x: len(x) >= 32 and all(c in '0123456789abcdef' for c in x.lower()),
            'points': 40
        }
    },
    
    'stored_xss': {
        'vulnerable_param': {
            'template': "Which parameter is vulnerable to stored XSS at {target_url}?",
            'answer_type': 'parameter_name',
            'validation': lambda x: len(x) > 0 and x.replace('_', '').replace('-', '').isalnum(),
            'points': 35
        },
        'xss_location': {
            'template': "Where is the stored XSS reflected on {target_url}?",
            'answer_type': 'location',
            'validation': lambda x: len(x) > 0,
            'points': 30
        }
    },
    
    'csrf': {
        'vulnerable_action': {
            'template': "What action at {target_url} is vulnerable to CSRF?",
            'answer_type': 'action',
            'validation': lambda x: len(x) > 0,
            'points': 30
        },
        'token_status': {
            'template': "Is the CSRF token missing or invalid at {target_url}?",
            'answer_type': 'status',
            'validation': lambda x: x.lower() in ['missing', 'invalid'],
            'points': 25
        }
    },
    
    'file_upload': {
        'bypass_extension': {
            'template': "What file extension bypasses the upload filter at {target_url}?",
            'answer_type': 'extension',
            'validation': lambda x: len(x) > 0 and x.startswith('.'),
            'points': 35
        },
        'upload_path': {
            'template': "Where are uploaded files stored on {target_url}?",
            'answer_type': 'path',
            'validation': lambda x: len(x) > 0 and x.startswith('/'),
            'points': 30
        }
    },
    
    'lfi_rfi': {
        'sensitive_file': {
            'template': "What sensitive file was accessed using path traversal at {target_url}?",
            'answer_type': 'file_path',
            'validation': lambda x: len(x) > 0 and x.startswith('/'),
            'points': 40
        },
        'etc_content': {
            'template': "What file was read from /etc/ at {target_url}?",
            'answer_type': 'filename',
            'validation': lambda x: len(x) > 0,
            'points': 35
        }
    },
    
    'jwt_attacks': {
        'secret_key': {
            'template': "What JWT secret key was discovered at {target_url}?",
            'answer_type': 'string',
            'validation': lambda x: len(x) > 0,
            'points': 40
        },
        'algorithm_none': {
            'template': "Can the JWT algorithm be set to 'none' at {target_url}?",
            'answer_type': 'boolean',
            'validation': lambda x: x.lower() in ['yes', 'no'],
            'points': 30
        }
    },
    
    'privilege_escalation': {
        'sudo_command': {
            'template': "What command can be run without sudo password on {target_ip}?",
            'answer_type': 'command',
            'validation': lambda x: len(x) > 0,
            'points': 35
        },
        'suid_binary': {
            'template': "What binary has SUID permissions on {target_ip}?",
            'answer_type': 'binary_name',
            'validation': lambda x: len(x) > 0 and x.replace('-', '').isalnum(),
            'points': 30
        },
        'cron_job': {
            'template': "What cron job runs as root on {target_ip}?",
            'answer_type': 'command',
            'validation': lambda x: len(x) > 0,
            'points': 35
        }
    },
    
    'pcap_analysis': {
        'suspicious_ip': {
            'template': "What suspicious IP address was found in the PCAP file?",
            'answer_type': 'ip_address',
            'validation': lambda x: len(x.split('.')) == 4 and all(o.isdigit() and 0 <= int(o) <= 255 for o in x.split('.')),
            'points': 30
        },
        'protocol_port': {
            'template': "What protocol and port were used for data exfiltration?",
            'answer_type': 'protocol_port',
            'validation': lambda x: len(x) > 0,
            'points': 25
        }
    },
    
    'git_exposure': {
        'secret_file': {
            'template': "What secret file was exposed in the Git repository?",
            'answer_type': 'filename',
            'validation': lambda x: len(x) > 0,
            'points': 35
        },
        'commit_hash': {
            'template': "What commit hash contains sensitive data?",
            'answer_type': 'hash',
            'validation': lambda x: len(x) == 40 and all(c in '0123456789abcdef' for c in x.lower()),
            'points': 30
        }
    }
}
```

### 🔴 ADVANCED LEVEL - REAL-WORLD ATTACK CHAINS

```python
ADVANCED_CHALLENGES = {
    'full_web_exploitation': {
        'exploit_chain': {
            'template': "What vulnerability chain led to full system compromise on {target_url}?",
            'answer_type': 'chain_description',
            'validation': lambda x: len(x) > 50,
            'points': 60
        },
        'final_payload': {
            'template': "What final payload achieved system compromise on {target_url}?",
            'answer_type': 'payload_description',
            'validation': lambda x: len(x) > 30,
            'points': 50
        }
    },
    
    'active_directory': {
        'kerberos_ticket': {
            'template': "What Kerberos ticket was extracted from {domain}?",
            'answer_type': 'ticket_type',
            'validation': lambda x: x.lower() in ['krbtgt', 'service', 'user'],
            'points': 55
        },
        'domain_admin': {
            'template': "What domain admin account was compromised in {domain}?",
            'answer_type': 'username',
            'validation': lambda x: len(x) > 0 and x.replace('_', '').isalnum(),
            'points': 60
        }
    },
    
    'lateral_movement': {
        'pivot_command': {
            'template': "What command achieved lateral movement from {source_ip} to {target_ip}?",
            'answer_type': 'command',
            'validation': lambda x: len(x) > 0,
            'points': 55
        },
        'credential_theft': {
            'template': "What credentials were stolen for lateral movement?",
            'answer_type': 'credential_type',
            'validation': lambda x: len(x) > 0,
            'points': 50
        }
    },
    
    'memory_exploitation': {
        'buffer_offset': {
            'template': "What buffer overflow offset was used in {binary}?",
            'answer_type': 'offset',
            'validation': lambda x: x.isdigit() and 1 <= int(x) <= 10000,
            'points': 65
        },
        'shellcode_address': {
            'template': "What address was used for shellcode in {binary}?",
            'answer_type': 'hex_address',
            'validation': lambda x: x.startswith('0x') and len(x) >= 10,
            'points': 70
        }
    },
    
    'container_escape': {
        'escape_method': {
            'template': "What container escape method worked on {target_container}?",
            'answer_type': 'method',
            'validation': lambda x: len(x) > 0,
            'points': 60
        },
        'host_access': {
            'template': "What host file was accessed after container escape?",
            'answer_type': 'file_path',
            'validation': lambda x: len(x) > 0 and x.startswith('/'),
            'points': 55
        }
    },
    
    'cloud_iam': {
        'abused_role': {
            'template': "What IAM role was abused in the cloud environment?",
            'answer_type': 'role_name',
            'validation': lambda x: len(x) > 0,
            'points': 60
        },
        'privilege_escalation': {
            'template': "How was privilege escalation achieved in the cloud environment?",
            'answer_type': 'method',
            'validation': lambda x: len(x) > 20,
            'points': 65
        }
    },
    
    'malware_dynamic': {
        'c2_server': {
            'template': "What C2 server does the malware communicate with?",
            'answer_type': 'ip_address',
            'validation': lambda x: len(x.split('.')) == 4 and all(o.isdigit() and 0 <= int(o) <= 255 for o in x.split('.')),
            'points': 55
        },
        'persistence_method': {
            'template': "What persistence mechanism does the malware use?",
            'answer_type': 'method',
            'validation': lambda x: len(x) > 0,
            'points': 50
        }
    }
}
```

### ⚫ EXPERT LEVEL - RESEARCH & ELITE

```python
EXPERT_CHALLENGES = {
    'kernel_exploit_dev': {
        'vulnerability_type': {
            'template': "What vulnerability type exists in kernel module {module_name}?",
            'answer_type': 'vulnerability_class',
            'validation': lambda x: len(x) > 0,
            'points': 100
        },
        'exploit_prerequisite': {
            'template': "What is required to exploit the kernel vulnerability in {module_name}?",
            'answer_type': 'prerequisite',
            'validation': lambda x: len(x) > 20,
            'points': 120
        }
    },
    
    'heap_exploitation': {
        'heap_technique': {
            'template': "What heap exploitation technique works on {binary}?",
            'answer_type': 'technique',
            'validation': lambda x: len(x) > 0,
            'points': 110
        },
        'allocation_pattern': {
            'template': "What allocation pattern triggers the vulnerability in {binary}?",
            'answer_type': 'pattern',
            'validation': lambda x: len(x) > 10,
            'points': 100
        }
    },
    
    'advanced_reverse_engineering': {
        'obfuscation_method': {
            'template': "What obfuscation method was used in {binary}?",
            'answer_type': 'method',
            'validation': lambda x: len(x) > 0,
            'points': 90
        },
        'encryption_algorithm': {
            'template': "What encryption algorithm protects the data in {binary}?",
            'answer_type': 'algorithm',
            'validation': lambda x: len(x) > 0,
            'points': 95
        }
    },
    
    'malware_development': {
        'evasion_technique': {
            'template': "What evasion technique does the custom malware use?",
            'answer_type': 'technique',
            'validation': lambda x: len(x) > 0,
            'points': 100
        },
        'injection_method': {
            'template': "What injection method does the malware use?",
            'answer_type': 'method',
            'validation': lambda x: len(x) > 0,
            'points': 95
        }
    },
    
    'custom_c2': {
        'protocol_type': {
            'template': "What protocol does the custom C2 framework use?",
            'answer_type': 'protocol',
            'validation': lambda x: len(x) > 0,
            'points': 90
        },
        'communication_pattern': {
            'template': "What communication pattern does the C2 use?",
            'answer_type': 'pattern',
            'validation': lambda x: len(x) > 10,
            'points': 100
        }
    },
    
    'firmware_hacking': {
        'vulnerability_location': {
            'template': "Where is the vulnerability located in the firmware?",
            'answer_type': 'location',
            'validation': lambda x: len(x) > 0,
            'points': 120
        },
        'exploit_vector': {
            'template': "What exploit vector works against the firmware?",
            'answer_type': 'vector',
            'validation': lambda x: len(x) > 0,
            'points': 110
        }
    }
}
```

---

## 🔄 ANSWER VALIDATION & SCORING LOGIC (EXACT COMPLIANCE)

```python
@app.route('/challenge/<int:challenge_id>/submit', methods=['POST'])
@login_required
def submit_challenge_answer(challenge_id):
    """Strict answer validation with exact match requirement"""
    challenge = Challenge.query.get_or_404(challenge_id)
    
    # Security checks
    if not challenge.is_active:
        return jsonify({'status': 'error', 'message': 'Challenge not active'})
    
    # Check if already solved (lock further submissions)
    if Submission.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge_id,
        is_correct=True
    ).first():
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
    
    # Verify answer (NEVER reveal hash or correct answer)
    is_correct = SecureAnswerHandler.verify_answer(submitted_answer, challenge.answer_hash)
    
    # Record submission
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
    
    if is_correct:
        # Award points ONLY on exact match
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

## 🎛️ ADMIN CONTROLS (MANDATORY FEATURES)

### Challenge Management
```python
@admin_bp.route('/challenges/create', methods=['GET', 'POST'])
@admin_required
def create_challenge():
    """Create challenge with admin-only correct answer"""
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title', '').strip()
        level = request.form.get('level')
        category = request.form.get('category')
        scenario = request.form.get('scenario', '').strip()
        description = request.form.get('description', '').strip()
        correct_answer = request.form.get('correct_answer', '').strip()  # Admin-only
        points = request.form.get('points', type=int)
        max_attempts = request.form.get('max_attempts', type=int)
        is_active = request.form.get('is_active') == 'on'
        
        # Validation
        if not all([title, level, category, scenario, description, correct_answer, points]):
            flash('All required fields must be filled', 'danger')
            return render_template('admin/create_challenge.html')
        
        # Create challenge
        challenge = Challenge(
            title=title,
            level=level,
            category=category,
            scenario=scenario,
            description=description,
            points=points,
            max_attempts=max_attempts if max_attempts else None,
            is_active=is_active
        )
        
        # Hash the correct answer immediately - NEVER store plain text
        challenge.set_answer(correct_answer)
        
        db.session.add(challenge)
        db.session.commit()
        
        flash('Challenge created successfully', 'success')
        return redirect(url_for('admin.challenges'))
    
    return render_template('admin/create_challenge.html')
```

---

## 📱 USER PANEL (MANDATORY FEATURES)

### Level-Based Challenge Viewing
```python
@app.route('/challenges')
@login_required
def view_challenges():
    """View challenges grouped STRICTLY by level"""
    # Get challenges grouped by level
    basic_challenges = Challenge.query.filter_by(level='basic', is_active=True).all()
    intermediate_challenges = Challenge.query.filter_by(level='intermediate', is_active=True).all()
    advanced_challenges = Challenge.query.filter_by(level='advanced', is_active=True).all()
    expert_challenges = Challenge.query.filter_by(level='expert', is_active=True).all()
    
    # Get user's solved challenges
    solved_ids = db.session.query(Submission.challenge_id)\
        .filter_by(user_id=current_user.id, is_correct=True)\
        .distinct().all()
    solved_ids = [challenge[0] for challenge in solved_ids]
    
    return render_template('challenges/index.html',
        basic_challenges=basic_challenges,
        intermediate_challenges=intermediate_challenges,
        advanced_challenges=advanced_challenges,
        expert_challenges=expert_challenges,
        solved_ids=solved_ids
    )
```

---

## 🚀 SCALABLE BACKEND DESIGN

### Level-Based Challenge Engine
```python
class LevelBasedChallengeEngine:
    def __init__(self):
        self.basic_challenges = BASIC_CHALLENGES
        self.intermediate_challenges = INTERMEDIATE_CHALLENGES
        self.advanced_challenges = ADVANCED_CHALLENGES
        self.expert_challenges = EXPERT_CHALLENGES
    
    def get_challenges_by_level(self, level):
        """Get challenges strictly by level - NO MIXING"""
        if level == 'basic':
            return self.basic_challenges
        elif level == 'intermediate':
            return self.intermediate_challenges
        elif level == 'advanced':
            return self.advanced_challenges
        elif level == 'expert':
            return self.expert_challenges
        else:
            raise ValueError(f"Invalid level: {level}")
    
    def validate_answer_by_level(self, level, category, template_type, answer):
        """Validate answer according to level rules"""
        challenges = self.get_challenges_by_level(level)
        if category in challenges and template_type in challenges[category]:
            return challenges[category][template_type]['validation'](answer)
        return False
```

This architecture provides a production-grade CTF & Lab Platform that **strictly follows** all your specifications with zero interpretation freedom.
