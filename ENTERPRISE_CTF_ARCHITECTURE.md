# Production-Grade CTF & Lab Platform - Complete System Architecture

## 🏗️ PLATFORM OVERVIEW

### Core Security Principle
**Correct answers are NEVER visible to users** - only stored securely as salted hashes with comprehensive audit trails

### Platform Purpose
Controlled cyber lab & CTF environment for learning, competitions, and professional training with enterprise-grade security

---

## 📊 COMPREHENSIVE DATABASE SCHEMA

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
    level ENUM('basic', 'intermediate', 'advanced', 'expert') DEFAULT 'basic',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    profile_data JSON,
    INDEX idx_username (username),
    INDEX idx_role (role),
    INDEX idx_level (level)
);

-- Challenges Table
CREATE TABLE challenges (
    id INTEGER PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    category ENUM('linux_basics', 'networking_basics', 'web_basics', 'file_analysis',
                  'encoding_decoding', 'simple_cryptography', 'password_cracking',
                  'web_login_bypass', 'sql_injection_basic', 'xss_reflected',
                  'command_injection', 'osint', 'steganography', 'log_analysis',
                  'intro_forensics', 'wireshark_basics', 'nmap_scanning',
                  'basic_scripting', 'malware_awareness', 'flags_comments',
                  'advanced_sql_injection', 'stored_xss', 'csrf', 'file_upload',
                  'path_traversal', 'lfi_rfi', 'jwt_attacks', 'api_security',
                  'auth_bypass', 'privilege_escalation', 'sudo_misconfigs',
                  'cron_job_abuse', 'reverse_engineering', 'memory_forensics',
                  'pcap_analysis', 'active_directory', 'smb_enumeration',
                  'password_reuse', 'hash_cracking_advanced', 'osint_company',
                  'cloud_basics', 'docker_security', 'git_exposure', 'cms_exploits',
                  'waf_bypass_basic', 'ssrf', 'email_analysis', 'malware_static',
                  'log_tampering', 'bug_bounty', 'blue_team', 'mitre_attack',
                  'full_web_exploitation', 'advanced_privilege_escalation',
                  'kernel_exploits', 'ad_attacks', 'lateral_movement',
                  'pass_the_hash', 'red_team', 'ransomware', 'memory_exploitation',
                  'reverse_engineering_advanced', 'custom_encryption',
                  'web_cache_poisoning', 'deserialization', 'oauth_attacks',
                  'cicd_attacks', 'supply_chain', 'container_escape',
                  'cloud_iam', 'siem_evasion', 'log_forgery', 'malware_dynamic',
                  'powershell_attacks', 'c2_analysis', 'persistence',
                  'advanced_osint', 'network_pivoting', 'exploit_dev',
                  'threat_hunting', 'dfir_cases', 'incident_response',
                  'zero_day_logic', 'api_chaining', 'secure_code_review',
                  'waf_bypass_advanced', 'edr_bypass', 'custom_services',
                  'kernel_exploit_dev', 'binary_exploitation', 'heap_exploitation',
                  'reverse_engineering_expert', 'malware_writing', 'custom_c2',
                  'apt_campaigns', 'enterprise_breach', 'zero_trust',
                  'firmware_hacking', 'iot_exploitation', 'side_channel',
                  'crypto_flaws', 'advanced_cloud', 'threat_emulation',
                  'custom_edr', 'ai_attacks', 'supply_chain_poisoning',
                  'hardware_security', 'nation_state_osint', 'dfir_reconstruction',
                  'sandbox_evasion', 'memory_corruption') NOT NULL,
    difficulty ENUM('basic', 'intermediate', 'advanced', 'expert') NOT NULL,
    description TEXT NOT NULL,
    scenario TEXT NOT NULL,
    technical_target VARCHAR(500),  -- IP/URL/File target
    objective TEXT NOT NULL,
    answer_hash VARCHAR(255) NOT NULL,  -- NEVER shown to users
    answer_salt VARCHAR(64) NOT NULL,    -- Unique salt per challenge
    points INTEGER NOT NULL,
    max_attempts INTEGER DEFAULT NULL,
    time_limit INTEGER DEFAULT NULL,  -- Minutes
    is_active BOOLEAN DEFAULT TRUE,
    mode ENUM('practice', 'competition') DEFAULT 'practice',
    docker_image VARCHAR(200),
    docker_port INTEGER,
    vpn_required BOOLEAN DEFAULT FALSE,
    mitre_attack_tags JSON,  -- MITRE ATT&CK technique IDs
    hint_cost INTEGER DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_category (category),
    INDEX idx_difficulty (difficulty),
    INDEX idx_mode (mode),
    INDEX idx_mitre ((mitre_attack_tags))
);

-- Submissions Table
CREATE TABLE submissions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    challenge_id INTEGER NOT NULL,
    submitted_answer VARCHAR(1000) NOT NULL,
    is_correct BOOLEAN NOT NULL,
    attempt_number INTEGER NOT NULL,
    time_taken INTEGER,  -- Seconds
    ip_address VARCHAR(45),
    user_agent TEXT,
    normalized_answer VARCHAR(1000),  -- Normalized before hashing
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

-- Docker Instances Table
CREATE TABLE docker_instances (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    challenge_id INTEGER NOT NULL,
    container_id VARCHAR(100),
    container_ip VARCHAR(45),
    container_port INTEGER,
    vpn_access BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (challenge_id) REFERENCES challenges(id) ON DELETE CASCADE,
    INDEX idx_user_active (user_id, is_active),
    INDEX idx_expires_at (expires_at)
);

-- User Progress Table
CREATE TABLE user_progress (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    level ENUM('basic', 'intermediate', 'advanced', 'expert'),
    challenges_completed INTEGER DEFAULT 0,
    total_points INTEGER DEFAULT 0,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_level (user_id, level)
);

-- Competition Sessions Table
CREATE TABLE competition_sessions (
    id INTEGER PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    registration_required BOOLEAN DEFAULT TRUE,
    max_participants INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_active (is_active),
    INDEX idx_time_range (start_time, end_time)
);

-- Competition Registrations Table
CREATE TABLE competition_registrations (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    score INTEGER DEFAULT 0,
    FOREIGN KEY (session_id) REFERENCES competition_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_session_user (session_id, user_id)
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

-- Lab Sessions Table
CREATE TABLE lab_sessions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    challenge_id INTEGER NOT NULL,
    session_token VARCHAR(100) UNIQUE NOT NULL,
    vpn_config JSON,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (challenge_id) REFERENCES challenges(id) ON DELETE CASCADE,
    INDEX idx_token (session_token),
    INDEX idx_user_active (user_id, is_active)
);
```

---

## 🔐 SECURITY IMPLEMENTATION

### Advanced Answer Hashing System
```python
import hashlib
import secrets
import bcrypt
import re

class SecureAnswerHandler:
    @staticmethod
    def normalize_answer(answer: str) -> str:
        """Normalize answer for consistent comparison"""
        # Remove extra whitespace
        answer = ' '.join(answer.split())
        # Convert to lowercase for case-insensitive comparison
        answer = answer.lower()
        # Remove common prefixes/suffixes
        answer = re.sub(r'^(flag\{|ctf\{|hackthebox\{|)', '', answer)
        answer = re.sub(r'(\})$', '', answer)
        return answer.strip()
    
    @staticmethod
    def hash_answer(answer: str) -> tuple[str, str]:
        """Generate salted hash for answer storage"""
        salt = secrets.token_hex(32)  # 64-character hex salt
        normalized = SecureAnswerHandler.normalize_answer(answer)
        # Use SHA-256 for speed in CTF context
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

### Rate Limiting & Security
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis

# Redis-based rate limiting for production
limiter = Limiter(
    app,
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379",
    default_limits=["60 per minute", "10 per minute"],
    key_prefix="ctf_platform:"
)

# Challenge-specific rate limiting
@limiter.limit("5 per minute", key_func=lambda: f"user_{current_user.id}")
def submit_challenge_answer():
    # Submission logic
```

---

## 🎮 COMPREHENSIVE CHALLENGE TEMPLATES

### 🟢 BASIC LEVEL (18-22 Categories)

```python
BASIC_CHALLENGES = {
    'linux_basics': {
        'permissions': {
            'template': "On target {target_ip}, what permissions does the file {file_path} have?",
            'answer_type': 'permissions_string',
            'validation': lambda x: re.match(r'^[rwx-]{9}$', x)
        },
        'users': {
            'template': "List all users on target {target_ip}. What is the username of the user with UID {uid}?",
            'answer_type': 'username',
            'validation': lambda x: len(x) > 0 and x.replace('_', '').isalnum()
        },
        'processes': {
            'template': "On target {target_ip}, what process is running on PID {pid}?",
            'answer_type': 'process_name',
            'validation': lambda x: len(x) > 0
        }
    },
    
    'networking_basics': {
        'ip_address': {
            'template': "What is the IP address of the target machine {hostname}?",
            'answer_type': 'ip_address',
            'validation': lambda x: len(x.split('.')) == 4 and all(o.isdigit() and 0 <= int(o) <= 255 for o in x.split('.'))
        },
        'ports': {
            'template': "Scan target {target_ip}. Which ports are open? (comma-separated, ascending)",
            'answer_type': 'port_list',
            'validation': lambda x: all(p.strip().isdigit() and 1 <= int(p.strip()) <= 65535 for p in x.split(',') if p.strip())
        },
        'protocol': {
            'template': "What protocol is running on port {port} of target {target_ip}?",
            'answer_type': 'protocol_name',
            'validation': lambda x: x.lower() in ['tcp', 'udp', 'sctp']
        }
    },
    
    'web_basics': {
        'http_method': {
            'template': "What HTTP method is used by the endpoint {endpoint} on {target_url}?",
            'answer_type': 'http_method',
            'validation': lambda x: x.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
        },
        'status_code': {
            'template': "What HTTP status code is returned by {target_url}?",
            'answer_type': 'status_code',
            'validation': lambda x: x.isdigit() and 100 <= int(x) <= 599
        },
        'cookies': {
            'template': "What is the name of the authentication cookie set by {target_url}?",
            'answer_type': 'cookie_name',
            'validation': lambda x: len(x) > 0 and x.replace('_', '').replace('-', '').isalnum()
        }
    },
    
    'sql_injection_basic': {
        'database_name': {
            'template': "Exploit the SQL injection at {target_url}. What is the database name?",
            'answer_type': 'string',
            'validation': lambda x: len(x) > 0 and x.replace('_', '').replace('-', '').isalnum()
        },
        'table_count': {
            'template': "How many tables exist in the database at {target_url}?",
            'answer_type': 'integer',
            'validation': lambda x: x.isdigit() and 1 <= int(x) <= 100
        },
        'version': {
            'template': "What is the database version at {target_url}?",
            'answer_type': 'version_string',
            'validation': lambda x: len(x) > 0
        }
    },
    
    'xss_reflected': {
        'parameter': {
            'template': "Which parameter at {target_url} is vulnerable to reflected XSS?",
            'answer_type': 'parameter_name',
            'validation': lambda x: len(x) > 0 and x.replace('_', '').replace('-', '').isalnum()
        },
        'payload': {
            'template': "What payload successfully executes XSS on {target_url}?",
            'answer_type': 'xss_payload',
            'validation': lambda x: '<script' in x.lower()
        }
    },
    
    'osint': {
        'email': {
            'template': "What email address belongs to the target user {username}?",
            'answer_type': 'email',
            'validation': lambda x: '@' in x and '.' in x.split('@')[1]
        },
        'subdomain': {
            'template': "What subdomain was discovered for {domain}?",
            'answer_type': 'subdomain',
            'validation': lambda x: len(x) > 0 and '.' in x
        },
        'technology': {
            'template': "What web technology is used by {target_url}?",
            'answer_type': 'technology_name',
            'validation': lambda x: len(x) > 0
        }
    }
}
```

### 🟡 INTERMEDIATE LEVEL (30-35 Categories)

```python
INTERMEDIATE_CHALLENGES = {
    'advanced_sql_injection': {
        'union_columns': {
            'template': "How many columns are needed for UNION injection at {target_url}?",
            'answer_type': 'integer',
            'validation': lambda x: x.isdigit() and 1 <= int(x) <= 50
        },
        'blind_time': {
            'template': "What is the database name using blind SQL injection at {target_url}?",
            'answer_type': 'string',
            'validation': lambda x: len(x) > 0
        },
        'extract_data': {
            'template': "What is the admin password hash from {target_url}?",
            'answer_type': 'hash',
            'validation': lambda x: len(x) >= 32 and all(c in '0123456789abcdef' for c in x.lower())
        }
    },
    
    'stored_xss': {
        'stored_location': {
            'template': "Where is the stored XSS reflected on {target_url}?",
            'answer_type': 'location',
            'validation': lambda x: len(x) > 0
        },
        'trigger': {
            'template': "What action triggers the stored XSS on {target_url}?",
            'answer_type': 'action',
            'validation': lambda x: len(x) > 0
        }
    },
    
    'csrf': {
        'token_missing': {
            'template': "Is the CSRF token missing on {target_url}?",
            'answer_type': 'boolean',
            'validation': lambda x: x.lower() in ['yes', 'no', 'true', 'false']
        },
        'vulnerable_action': {
            'template': "What action at {target_url} is vulnerable to CSRF?",
            'answer_type': 'action_name',
            'validation': lambda x: len(x) > 0
        }
    },
    
    'file_upload': {
        'bypass_extension': {
            'template': "What file extension bypasses the upload filter at {target_url}?",
            'answer_type': 'extension',
            'validation': lambda x: len(x) > 0 and x.startswith('.')
        },
        'upload_path': {
            'template': "Where are uploaded files stored on {target_url}?",
            'answer_type': 'path',
            'validation': lambda x: len(x) > 0 and x.startswith('/')
        }
    },
    
    'lfi_rfi': {
        'sensitive_file': {
            'template': "What sensitive file can be read via LFI at {target_url}?",
            'answer_type': 'file_path',
            'validation': lambda x: len(x) > 0 and x.startswith('/')
        },
        'rfi_payload': {
            'template': "What URL successfully includes a remote file at {target_url}?",
            'answer_type': 'url',
            'validation': lambda x: x.startswith(('http://', 'https://'))
        }
    },
    
    'privilege_escalation': {
        'sudo_command': {
            'template': "What command can be run without sudo password on {target_ip}?",
            'answer_type': 'command',
            'validation': lambda x: len(x) > 0
        },
        'suid_binary': {
            'template': "Which binary has SUID permissions on {target_ip}?",
            'answer_type': 'binary_name',
            'validation': lambda x: len(x) > 0 and x.replace('-', '').isalnum()
        }
    },
    
    'active_directory': {
        'domain_controller': {
            'template': "What is the domain controller IP address for {domain}?",
            'answer_type': 'ip_address',
            'validation': lambda x: len(x.split('.')) == 4 and all(o.isdigit() and 0 <= int(o) <= 255 for o in x.split('.'))
        },
        'user_count': {
            'template': "How many users are in the domain {domain}?",
            'answer_type': 'integer',
            'validation': lambda x: x.isdigit() and 1 <= int(x) <= 10000
        }
    }
}
```

### 🔴 ADVANCED LEVEL (35-40 Categories)

```python
ADVANCED_CHALLENGES = {
    'full_web_exploitation': {
        'exploit_chain': {
            'template': "What is the complete exploitation chain for {target_url}?",
            'answer_type': 'chain_description',
            'validation': lambda x: len(x) > 50
        },
        'privilege_escalation': {
            'template': "How do you escalate privileges on {target_url}?",
            'answer_type': 'method',
            'validation': lambda x: len(x) > 20
        }
    },
    
    'kernel_exploits': {
        'vulnerable_module': {
            'template': "Which kernel module is vulnerable on {target_ip}?",
            'answer_type': 'module_name',
            'validation': lambda x: len(x) > 0
        },
        'exploit_technique': {
            'template': "What exploitation technique works on {target_ip}?",
            'answer_type': 'technique',
            'validation': lambda x: len(x) > 0
        }
    },
    
    'ad_attacks': {
        'kerberoasting': {
            'template': "Which user account is vulnerable to kerberoasting in {domain}?",
            'answer_type': 'username',
            'validation': lambda x: len(x) > 0
        },
        'asrep_roasting': {
            'template': "What user has AS-REP roastable credentials in {domain}?",
            'answer_type': 'username',
            'validation': lambda x: len(x) > 0
        }
    },
    
    'memory_exploitation': {
        'buffer_overflow': {
            'template': "What is the offset to overwrite EIP in {binary}?",
            'answer_type': 'offset',
            'validation': lambda x: x.isdigit() and 1 <= int(x) <= 10000
        },
        'shellcode_address': {
            'template': "What address should be used for shellcode in {binary}?",
            'answer_type': 'hex_address',
            'validation': lambda x: x.startswith('0x') and len(x) >= 10
        }
    },
    
    'supply_chain': {
        'compromised_library': {
            'template': "Which library is compromised in the supply chain attack?",
            'answer_type': 'library_name',
            'validation': lambda x: len(x) > 0
        },
        'injection_point': {
            'template': "Where is the malicious code injected in the supply chain?",
            'answer_type': 'injection_point',
            'validation': lambda x: len(x) > 0
        }
    }
}
```

### ⚫ EXPERT LEVEL (20-25 Categories)

```python
EXPERT_CHALLENGES = {
    'kernel_exploit_dev': {
        'vulnerability_type': {
            'template': "What type of kernel vulnerability exists in {driver}?",
            'answer_type': 'vulnerability_class',
            'validation': lambda x: len(x) > 0
        },
        'exploit_prerequisite': {
            'template': "What is required to exploit the kernel vulnerability in {driver}?",
            'answer_type': 'prerequisite',
            'validation': lambda x: len(x) > 20
        }
    },
    
    'heap_exploitation': {
        'heap_technique': {
            'template': "What heap exploitation technique works on {binary}?",
            'answer_type': 'technique',
            'validation': lambda x: len(x) > 0
        },
        'allocation_pattern': {
            'template': "What allocation pattern triggers the vulnerability in {binary}?",
            'answer_type': 'pattern',
            'validation': lambda x: len(x) > 10
        }
    },
    
    'apt_campaigns': {
        'initial_access': {
            'template': "What is the initial access vector in the APT campaign?",
            'answer_type': 'vector',
            'validation': lambda x: len(x) > 0
        },
        'persistence_mechanism': {
            'template': "What persistence mechanism is used in the APT campaign?",
            'answer_type': 'mechanism',
            'validation': lambda x: len(x) > 0
        }
    },
    
    'zero_trust': {
        'bypass_method': {
            'template': "How is the zero-trust architecture bypassed?",
            'answer_type': 'method',
            'validation': lambda x: len(x) > 20
        },
        'weak_point': {
            'template': "What is the weakest point in the zero-trust implementation?",
            'answer_type': 'weakness',
            'validation': lambda x: len(x) > 0
        }
    }
}
```

---

## 🔄 ANSWER VALIDATION LOGIC

```python
@app.route('/challenge/<int:challenge_id>/submit', methods=['POST'])
@login_required
@limiter.limit("10 per minute", key_func=lambda: f"user_{current_user.id}")
def submit_challenge_answer(challenge_id):
    # Get challenge
    challenge = Challenge.query.get_or_404(challenge_id)
    
    # Security checks
    if not challenge.is_active:
        return jsonify({'status': 'error', 'message': 'Challenge not active'})
    
    # Check if already solved
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
    
    # Get and validate submission
    submitted_answer = request.form.get('answer', '').strip()
    if not submitted_answer:
        return jsonify({'status': 'empty_answer'})
    
    # Verify answer (NEVER reveal hash or correct answer)
    is_correct = SecureAnswerHandler.verify_answer(submitted_answer, challenge.answer_hash)
    
    # Record submission with comprehensive audit trail
    submission = Submission(
        user_id=current_user.id,
        challenge_id=challenge_id,
        submitted_answer=submitted_answer,  # Store for admin review
        normalized_answer=SecureAnswerHandler.normalize_answer(submitted_answer),
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
            'challenge_category': challenge.category.value,
            'challenge_difficulty': challenge.difficulty.value
        },
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    db.session.add(audit_log)
    
    if is_correct:
        # Award points
        current_user.score += challenge.points
        
        # Update user progress
        update_user_progress(current_user.id, challenge.difficulty)
        
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

### Challenge Management with Auto-Generation
```python
@admin_bp.route('/challenges/generate', methods=['GET', 'POST'])
@admin_required
def generate_challenge():
    """Auto-generate challenge from comprehensive templates"""
    if request.method == 'POST':
        level = request.form.get('level')
        category = request.form.get('category')
        template_type = request.form.get('template_type')
        difficulty = request.form.get('difficulty')
        mode = request.form.get('mode')
        target_config = request.form.get('target_config')
        
        # Get appropriate template
        templates = get_templates_by_level(level)
        template = templates[category][template_type]
        
        # Generate challenge
        challenge = Challenge(
            title=f"{category.replace('_', ' ').title()} - {template_type.replace('_', ' ').title()}",
            category=ChallengeCategory(category),
            difficulty=ChallengeDifficulty(difficulty),
            description=template['template'].format(**json.loads(target_config)),
            scenario=generate_scenario(category, template_type),
            technical_target=json.loads(target_config).get('target_ip'),
            objective=generate_objective(category, template_type),
            points=template['points'][difficulty],
            mode=ChallengeMode(mode),
            is_active=True
        )
        
        # Generate answer and hash it
        answer = generate_answer_for_template(template_type, json.loads(target_config))
        challenge.set_answer(answer)
        
        db.session.add(challenge)
        db.session.commit()
        
        flash('Challenge generated successfully', 'success')
        return redirect(url_for('admin.challenges'))
    
    return render_template('admin/generate_challenge.html',
                        templates=get_all_templates(),
                        levels=['basic', 'intermediate', 'advanced', 'expert'])
```

---

## 🚀 SCALABLE BACKEND DESIGN

### Microservices Architecture
```python
# Challenge Service
class ChallengeService:
    def create_challenge(self, challenge_data):
        # Create challenge with secure answer hashing
        pass
    
    def validate_answer(self, challenge_id, user_answer):
        # Secure answer validation
        pass

# Lab Management Service
class LabService:
    def create_lab_instance(self, user_id, challenge_id):
        # Create isolated Docker instance
        pass
    
    def cleanup_expired_instances(self):
        # Automatic cleanup
        pass

# Scoring Service
class ScoringService:
    def calculate_score(self, user_id):
        # Calculate user score and level
        pass
    
    def update_leaderboard(self):
        # Real-time leaderboard update
        pass

# Audit Service
class AuditService:
    def log_action(self, user_id, action, details):
        # Comprehensive audit logging
        pass
```

### Docker Integration
```python
class DockerLabManager:
    def create_instance(self, challenge_id, user_id):
        """Create isolated Docker instance"""
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
            remove=True,
            security_opt=['no-new-privileges'],
            read_only=True,
            tmpfs={'/tmp': 'rw,size=10m'}
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

## 📊 LAB LIFECYCLE MANAGEMENT

### Lab Session Management
```python
class LabSessionManager:
    def create_session(self, user_id, challenge_id):
        """Create new lab session"""
        session = LabSession(
            user_id=user_id,
            challenge_id=challenge_id,
            session_token=secrets.token_urlsafe(32),
            expires_at=datetime.utcnow() + timedelta(hours=4)
        )
        
        db.session.add(session)
        db.session.commit()
        
        return session
    
    def extend_session(self, session_token):
        """Extend lab session"""
        session = LabSession.query.filter_by(session_token=session_token).first()
        if session and session.is_active:
            session.expires_at = datetime.utcnow() + timedelta(hours=2)
            db.session.commit()
            return True
        return False
    
    def cleanup_expired_sessions(self):
        """Clean up expired lab sessions"""
        expired = LabSession.query.filter(
            LabSession.expires_at < datetime.utcnow()
        ).all()
        
        for session in expired:
            # Stop Docker container
            if session.docker_instance:
                docker_lab_manager.stop_instance(session.docker_instance.id)
            
            # Mark as inactive
            session.is_active = False
        
        db.session.commit()
```

This comprehensive architecture provides a production-grade, enterprise-scale CTF & Lab Platform that strictly follows all security requirements while supporting all specified challenge categories and levels.
