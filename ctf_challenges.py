"""
CTF Challenges Module
Educational Security Training Platform
"""

from flask import Blueprint, request, render_template, redirect, url_for, session, flash, jsonify
from flask_login import login_required, current_user
import sqlite3
import os
import json
from werkzeug.utils import secure_filename
from functools import wraps

# Create blueprint for CTF challenges
ctf_bp = Blueprint('ctf', __name__, url_prefix='/challenge')

# Challenge configuration
CHALLENGES = {
    'sqli': {
        'title': 'SQL Injection',
        'description': 'Find the SQL injection vulnerability to extract the hidden flag',
        'difficulty': 'Medium',
        'points': 100,
        'flag': 'FLAG{SQL_INJECTION_MASTER}',
        'category': 'Database Security'
    },
    'xss': {
        'title': 'Cross-Site Scripting',
        'description': 'Exploit the XSS vulnerability to retrieve the flag',
        'difficulty': 'Easy',
        'points': 50,
        'flag': 'FLAG{XSS_EXPLOIT_SUCCESS}',
        'category': 'Client-Side Security'
    },
    'auth': {
        'title': 'Broken Authentication',
        'description': 'Bypass the authentication mechanism to access admin panel',
        'difficulty': 'Medium',
        'points': 150,
        'flag': 'FLAG{AUTH_BYPASS_ACHIEVED}',
        'category': 'Authentication'
    },
    'upload': {
        'title': 'File Upload Vulnerability',
        'description': 'Upload a malicious file to read the hidden flag',
        'difficulty': 'Hard',
        'points': 200,
        'flag': 'FLAG{FILE_UPLOAD_PWNED}',
        'category': 'File Security'
    },
    'lfi': {
        'title': 'Local File Inclusion',
        'description': 'Exploit path traversal to read the flag file',
        'difficulty': 'Medium',
        'points': 120,
        'flag': 'FLAG{LFI_TRAVERSAL_SUCCESS}',
        'category': 'File System'
    }
}

def init_ctf_database():
    """Initialize CTF challenge database with vulnerable data"""
    conn = sqlite3.connect('ctf_challenges.db')
    cursor = conn.cursor()
    
    # Create vulnerable users table for SQL injection challenge
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            password TEXT,
            role TEXT,
            flag TEXT
        )
    ''')
    
    # Insert sample data with hidden flag
    cursor.execute('''
        INSERT OR REPLACE INTO users (id, username, password, role, flag) VALUES
        (1, 'admin', 'password123', 'admin', 'FLAG{SQL_INJECTION_MASTER}'),
        (2, 'user1', 'pass123', 'user', NULL),
        (3, 'guest', 'guest123', 'guest', NULL)
    ''')
    
    # Create products table for SQLi practice
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT,
            price REAL,
            description TEXT,
            flag TEXT
        )
    ''')
    
    cursor.execute('''
        INSERT OR REPLACE INTO products (id, name, price, description, flag) VALUES
        (1, 'Laptop', 999.99, 'High-performance laptop', NULL),
        (2, 'Mouse', 29.99, 'Wireless mouse', NULL),
        (3, 'Keyboard', 79.99, 'Mechanical keyboard', 'FLAG{SQL_INJECTION_MASTER}')
    ''')
    
    conn.commit()
    conn.close()

def create_flag_files():
    """Create flag files for file-based challenges"""
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('flags', exist_ok=True)
    
    # Create flag file for LFI challenge
    with open('flags/secret.txt', 'w') as f:
        f.write('FLAG{LFI_TRAVERSAL_SUCCESS}')
    
    # Create flag file for upload challenge
    with open('flags/upload_flag.txt', 'w') as f:
        f.write('FLAG{FILE_UPLOAD_PWNED}')
    
    # Create .htaccess for upload directory (vulnerable)
    with open('uploads/.htaccess', 'w') as f:
        f.write('# Vulnerable configuration\n')

# SQL Injection Challenge
@ctf_bp.route('/sqli')
@login_required
def sqli_challenge():
    """SQL Injection Challenge - Only accessible to authenticated users"""
    # Check if user has permission to access challenges
    if current_user.role not in ['user', 'admin']:
        flash('You do not have permission to access challenges', 'danger')
        return redirect(url_for('ctf.challenge_list'))
    return render_template('ctf/sqli.html')

@ctf_bp.route('/sqli/search', methods=['POST'])
@login_required
def sqli_search():
    """Vulnerable search endpoint - SQL Injection point"""
    search_query = request.form.get('query', '')
    
    conn = sqlite3.connect('ctf_challenges.db')
    cursor = conn.cursor()
    
    # VULNERABLE: Direct string concatenation - SQL Injection point
    query = f"SELECT * FROM products WHERE name LIKE '%{search_query}%' OR description LIKE '%{search_query}%'"
    
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        
        # Get column names
        cursor.execute("PRAGMA table_info(products)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Convert results to list of dicts
        products = []
        for row in results:
            product = dict(zip(columns, row))
            products.append(product)
        
        return render_template('ctf/sqli_results.html', products=products, query=search_query)
    
    except Exception as e:
        return render_template('ctf/sqli.html', error=f"Error: {str(e)}", query=search_query)
    finally:
        conn.close()

@ctf_bp.route('/sqli/login', methods=['GET', 'POST'])
def sqli_login():
    """Vulnerable login endpoint - SQL Injection point"""
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        conn = sqlite3.connect('ctf_challenges.db')
        cursor = conn.cursor()
        
        # VULNERABLE: Direct string concatenation - SQL Injection point
        query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
        
        try:
            cursor.execute(query)
            user = cursor.fetchone()
            
            if user:
                # Get column names
                cursor.execute("PRAGMA table_info(users)")
                columns = [column[1] for column in cursor.fetchall()]
                user_dict = dict(zip(columns, user))
                
                if user_dict.get('flag'):
                    flash(f'Flag found: {user_dict["flag"]}', 'success')
                    return render_template('ctf/sqli_success.html', flag=user_dict['flag'])
                else:
                    flash('Login successful but no flag found. Try extracting more data!', 'info')
                    return render_template('ctf/sqli_login.html', success=True)
            else:
                flash('Invalid credentials', 'error')
                
        except Exception as e:
            flash(f'Database error: {str(e)}', 'error')
        finally:
            conn.close()
    
    return render_template('ctf/sqli_login.html')

# XSS Challenge
@ctf_bp.route('/xss')
@login_required
def xss_challenge():
    """XSS Challenge - Only accessible to authenticated users"""
    if current_user.role not in ['user', 'admin']:
        flash('You do not have permission to access challenges', 'danger')
        return redirect(url_for('ctf.challenge_list'))
    return render_template('ctf/xss.html')

@ctf_bp.route('/xss/search', methods=['POST'])
@login_required
def xss_search():
    """Vulnerable search endpoint - XSS point"""
    search_query = request.form.get('query', '')
    
    # VULNERABLE: Direct reflection without sanitization - XSS point
    results = []
    if search_query:
        # Simulate search results
        results = [
            {'title': f'Result for {search_query}', 'description': f'Matching content for {search_query}'},
            {'title': f'Another {search_query} result', 'description': f'More content about {search_query}'}
        ]
    
    return render_template('ctf/xss_results.html', query=search_query, results=results)

@ctf_bp.route('/xss/comment', methods=['POST'])
@login_required
def xss_comment():
    """Vulnerable comment endpoint - Stored XSS point"""
    comment = request.form.get('comment', '')
    username = request.form.get('username', 'Anonymous')
    
    # VULNERABLE: Store without sanitization - Stored XSS point
    comments = session.get('comments', [])
    comments.append({'username': username, 'comment': comment, 'timestamp': 'Just now'})
    session['comments'] = comments
    
    # Check if flag is in comment
    if 'FLAG{XSS_EXPLOIT_SUCCESS}' in comment:
        flash('Flag submitted via XSS!', 'success')
    
    return render_template('ctf/xss_comments.html', comments=comments)

# Broken Authentication Challenge
@ctf_bp.route('/auth')
@login_required
def auth_challenge():
    """Broken Authentication Challenge - Only accessible to authenticated users"""
    if current_user.role not in ['user', 'admin']:
        flash('You do not have permission to access challenges', 'danger')
        return redirect(url_for('ctf.challenge_list'))
    return render_template('ctf/auth.html')

@ctf_bp.route('/auth/login', methods=['POST'])
def auth_login():
    """Vulnerable authentication - Logic flaw"""
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    role = request.form.get('role', 'user')
    
    # VULNERABLE: Role parameter can be manipulated - Authentication bypass
    if username and password:
        # Logic flaw: role is accepted from user input
        if role == 'admin':
            # Admin access granted
            session['is_admin'] = True
            session['username'] = username
            flash('Admin access granted!', 'success')
            return render_template('ctf/auth_admin.html', flag='FLAG{AUTH_BYPASS_ACHIEVED}')
        else:
            # Normal user access
            session['is_admin'] = False
            session['username'] = username
            flash('User access granted', 'info')
            return render_template('ctf/auth_user.html')
    
    flash('Invalid credentials', 'error')
    return render_template('ctf/auth.html')

@ctf_bp.route('/auth/profile')
@login_required
def auth_profile():
    """Profile page with privilege escalation"""
    is_admin = session.get('is_admin', False)
    username = session.get('username', '')
    
    if is_admin:
        return render_template('ctf/auth_admin.html', flag='FLAG{AUTH_BYPASS_ACHIEVED}')
    else:
        return render_template('ctf/auth_user.html')

# File Upload Challenge
@ctf_bp.route('/upload')
@login_required
def upload_challenge():
    """File Upload Challenge - Only accessible to authenticated users"""
    if current_user.role not in ['user', 'admin']:
        flash('You do not have permission to access challenges', 'danger')
        return redirect(url_for('ctf.challenge_list'))
    return render_template('ctf/upload.html')

@ctf_bp.route('/upload/file', methods=['POST'])
@login_required
def upload_file():
    """Vulnerable file upload endpoint"""
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('ctf.upload_challenge'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('ctf.upload_challenge'))
    
    # VULNERABLE: Insufficient file validation - Upload vulnerability
    filename = secure_filename(file.filename)
    
    # Weak validation - can be bypassed
    allowed_extensions = ['jpg', 'png', 'gif', 'txt']
    if '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions:
        file.save(os.path.join('uploads', filename))
        flash(f'File {filename} uploaded successfully!', 'success')
        
        # Check if uploaded file contains flag
        try:
            with open(os.path.join('uploads', filename), 'r') as f:
                content = f.read()
                if 'FLAG{FILE_UPLOAD_PWNED}' in content:
                    flash('Flag found in uploaded file!', 'success')
        except:
            pass
        
        return render_template('ctf/upload_success.html', filename=filename)
    else:
        flash('Invalid file type. Allowed: jpg, png, gif, txt', 'error')
        return redirect(url_for('ctf.upload_challenge'))

@ctf_bp.route('/upload/view/<filename>')
@login_required
def view_uploaded_file(filename):
    """View uploaded file - Directory traversal possible"""
    # VULNERABLE: Path traversal possible
    filepath = os.path.join('uploads', filename)
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        return render_template('ctf/file_view.html', content=content, filename=filename)
    except:
        flash('File not found', 'error')
        return redirect(url_for('ctf.upload_challenge'))

# Local File Inclusion Challenge
@ctf_bp.route('/lfi')
@login_required
def lfi_challenge():
    """Local File Inclusion Challenge - Only accessible to authenticated users"""
    if current_user.role not in ['user', 'admin']:
        flash('You do not have permission to access challenges', 'danger')
        return redirect(url_for('ctf.challenge_list'))
    return render_template('ctf/lfi.html')

@ctf_bp.route('/lfi/view', methods=['POST'])
@login_required
def lfi_view():
    """Vulnerable file inclusion endpoint"""
    page = request.form.get('page', 'home')
    
    # VULNERABLE: Direct file inclusion without validation - LFI point
    try:
        # Construct file path
        filepath = os.path.join('templates', 'ctf', f'{page}.html')
        
        # Check if file exists
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                content = f.read()
            return render_template('ctf/lfi_result.html', content=content, page=page)
        else:
            # Try path traversal
            if '../' in page:
                try:
                    with open(page, 'r') as f:
                        content = f.read()
                    return render_template('ctf/lfi_result.html', content=content, page=page)
                except:
                    pass
            
            return render_template('ctf/lfi.html', error='Page not found')
            
    except Exception as e:
        return render_template('ctf/lfi.html', error=f'Error: {str(e)}')

# Flag validation endpoint
@ctf_bp.route('/submit_flag', methods=['POST'])
@login_required
def submit_flag():
    """Validate submitted flags"""
    flag = request.form.get('flag', '')
    challenge_id = request.form.get('challenge_id', '')
    
    if challenge_id in CHALLENGES:
        expected_flag = CHALLENGES[challenge_id]['flag']
        if flag == expected_flag:
            # Award points to user
            current_user.score += CHALLENGES[challenge_id]['points']
            from extensions import db
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Correct flag! {CHALLENGES[challenge_id]["points"]} points awarded.',
                'points': CHALLENGES[challenge_id]['points']
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Incorrect flag. Try again!'
            })
    
    return jsonify({
        'success': False,
        'message': 'Invalid challenge ID'
    })

# Reset challenges
@ctf_bp.route('/reset')
@login_required
def reset_challenges():
    """Reset all challenges to initial state"""
    init_ctf_database()
    create_flag_files()
    
    # Clear session data
    session.pop('comments', None)
    session.pop('is_admin', None)
    session.pop('username', None)
    
    flash('All challenges have been reset!', 'success')
    return redirect(url_for('ctf.challenge_list'))

# File upload list endpoint
@ctf_bp.route('/upload/list')
@login_required
def upload_list():
    """List uploaded files"""
    try:
        files = []
        if os.path.exists('uploads'):
            files = [f for f in os.listdir('uploads') if os.path.isfile(os.path.join('uploads', f))]
        return jsonify({'files': files})
    except:
        return jsonify({'files': []})

# Challenge list
@ctf_bp.route('/')
@login_required
def challenge_list():
    """List all available challenges - only for authenticated users"""
    # Check if user is admin or regular user
    if current_user.role == 'admin':
        # Admins can see all challenges
        return render_template('ctf/challenge_list.html', challenges=CHALLENGES, is_admin=True)
    else:
        # Regular users can see challenges but with limited access
        return render_template('ctf/challenge_list.html', challenges=CHALLENGES, is_admin=False)
