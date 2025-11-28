from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configure app
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///travel_tracking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Gmail Configuration
GMAIL_ADDRESS = os.getenv('GMAIL_ADDRESS', 'your-email@gmail.com')
GMAIL_PASSWORD = os.getenv('GMAIL_PASSWORD', 'your-app-password')

# ==================== ACCOUNTS MODEL ====================
class Account(db.Model):
    __tablename__ = 'accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password, password)

# ==================== OTP MODEL ====================
class OTP(db.Model):
    __tablename__ = 'otps'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False)
    otp_code = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    verified = db.Column(db.Boolean, default=False)
    
    def is_valid(self):
        return not self.verified and datetime.utcnow() < self.expires_at
    
    def verify_otp(self, code):
        if self.is_valid() and self.otp_code == code:
            self.verified = True
            db.session.commit()
            return True
        return False

# ==================== REGISTRATIONS MODEL ====================
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    group_id = db.Column(db.Integer, nullable=False)
    joined_date = db.Column(db.Date)
    emergency_contact_name = db.Column(db.String(100))
    emergency_contact_phone = db.Column(db.String(20))
    id_proof_type = db.Column(db.String(50))
    id_proof_number = db.Column(db.String(100))
    location_link = db.Column(db.String(500))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'age': self.age,
            'gender': self.gender,
            'city': self.city,
            'state': self.state,
            'group_id': self.group_id,
            'joined_date': self.joined_date.isoformat() if self.joined_date else None,
            'emergency_contact_name': self.emergency_contact_name,
            'emergency_contact_phone': self.emergency_contact_phone,
            'id_proof_type': self.id_proof_type,
            'id_proof_number': self.id_proof_number,
            'location_link': self.location_link,
            'notes': self.notes
        }

# Create database tables
with app.app_context():
    db.drop_all()
    db.create_all()

# ==================== OTP FUNCTIONS ====================
def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(email, otp):
    try:
        subject = "Your OTP for Group Travel Tracking System"
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #667eea;">Group Travel Tracking System</h2>
                <p>Your One-Time Password (OTP) is:</p>
                <h1 style="color: #764ba2; letter-spacing: 5px;">{otp}</h1>
                <p><strong>This OTP will expire in 5 minutes.</strong></p>
                <p>If you didn't request this OTP, please ignore this email.</p>
                <hr>
                <p style="color: #999; font-size: 12px;">Do not share this OTP with anyone.</p>
            </body>
        </html>
        """
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = GMAIL_ADDRESS
        msg['To'] = email
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, email, msg.as_string())
        server.quit()
        
        print(f"✓ OTP sent to {email}")
        return True
    except Exception as e:
        print(f"✗ Error sending OTP email: {str(e)}")
        return False

# ==================== AUTHENTICATION ROUTES ====================

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        email = data.get('email')
        
        # Validation
        if not all([username, email]):
            return jsonify({'success': False, 'message': 'Username and email are required'}), 400
        
        # Check if user exists
        if Account.query.filter_by(username=username).first():
            return jsonify({'success': False, 'message': 'Username already exists'}), 400
        
        if Account.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': 'Email already registered'}), 400
        
        try:
            # Generate and send OTP
            otp_code = generate_otp()
            otp = OTP(
                email=email,
                otp_code=otp_code,
                expires_at=datetime.utcnow() + timedelta(minutes=5)
            )
            db.session.add(otp)
            db.session.commit()
            
            # Send OTP email
            if send_otp_email(email, otp_code):
                # Store signup data in session temporarily
                session['signup_username'] = username
                session['signup_email'] = email
                return jsonify({'success': True, 'message': 'OTP sent to your email!'}), 200
            else:
                return jsonify({'success': False, 'message': 'Failed to send OTP email'}), 500
                
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error during signup: {str(e)}")
            return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    
    return render_template('signup.html')

@app.route('/verify-otp-signup', methods=['POST'])
def verify_otp_signup():
    data = request.json
    otp_code = data.get('otp')
    
    if 'signup_email' not in session:
        return jsonify({'success': False, 'message': 'Session expired. Please signup again'}), 400
    
    try:
        email = session.get('signup_email')
        otp_record = OTP.query.filter_by(email=email).order_by(OTP.created_at.desc()).first()
        
        if otp_record and otp_record.verify_otp(otp_code):
            # Create account
            username = session.get('signup_username')
            account = Account(username=username, email=email)
            db.session.add(account)
            db.session.commit()
            
            # Clean up session
            session.pop('signup_username', None)
            session.pop('signup_email', None)
            
            print(f"✓ Account created: {username}")
            return jsonify({'success': True, 'message': 'Account created successfully!'}), 201
        else:
            return jsonify({'success': False, 'message': 'Invalid or expired OTP'}), 400
            
    except Exception as e:
        db.session.rollback()
        print(f"✗ Error verifying OTP: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json
        email = data.get('email')
        
        if not email:
            return jsonify({'success': False, 'message': 'Email is required'}), 400
        
        account = Account.query.filter_by(email=email).first()
        
        if not account:
            return jsonify({'success': False, 'message': 'Email not registered'}), 401
        
        try:
            # Generate and send OTP
            otp_code = generate_otp()
            otp = OTP(
                email=email,
                otp_code=otp_code,
                expires_at=datetime.utcnow() + timedelta(minutes=5)
            )
            db.session.add(otp)
            db.session.commit()
            
            # Send OTP email
            if send_otp_email(email, otp_code):
                session['login_email'] = email
                return jsonify({'success': True, 'message': 'OTP sent to your email!'}), 200
            else:
                return jsonify({'success': False, 'message': 'Failed to send OTP email'}), 500
                
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error sending login OTP: {str(e)}")
            return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    
    return render_template('login.html')

@app.route('/verify-otp-login', methods=['POST'])
def verify_otp_login():
    data = request.json
    otp_code = data.get('otp')
    
    if 'login_email' not in session:
        return jsonify({'success': False, 'message': 'Session expired. Please login again'}), 400
    
    try:
        email = session.get('login_email')
        otp_record = OTP.query.filter_by(email=email).order_by(OTP.created_at.desc()).first()
        
        if otp_record and otp_record.verify_otp(otp_code):
            account = Account.query.filter_by(email=email).first()
            
            session['user_id'] = account.id
            session['username'] = account.username
            session['email'] = account.email
            session.pop('login_email', None)
            
            print(f"✓ Login successful: {account.username}")
            return jsonify({'success': True, 'message': 'Login successful!'}), 200
        else:
            return jsonify({'success': False, 'message': 'Invalid or expired OTP'}), 400
            
    except Exception as e:
        print(f"✗ Error verifying login OTP: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/logout')
def logout():
    username = session.get('username')
    session.clear()
    print(f"✓ Logout: {username}")
    return redirect(url_for('login'))

# ==================== HOME & REGISTRATION ROUTES ====================

@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('home.html', username=session.get('username'))

@app.route('/api/register', methods=['POST'])
def register():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    try:
        data = request.form
        username = session['username']
        
        joined_date = None
        if data.get('joined_date'):
            try:
                joined_date = datetime.strptime(data.get('joined_date'), '%Y-%m-%d').date()
            except:
                return jsonify({'success': False, 'message': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        new_user = User(
            user_id=username,
            name=data.get('name'),
            email=data.get('email'),
            phone=data.get('phone'),
            age=int(data.get('age')) if data.get('age') else None,
            gender=data.get('gender'),
            city=data.get('city'),
            state=data.get('state'),
            group_id=int(data.get('group_id')),
            joined_date=joined_date,
            emergency_contact_name=data.get('emergency_contact_name'),
            emergency_contact_phone=data.get('emergency_contact_phone'),
            id_proof_type=data.get('id_proof_type'),
            id_proof_number=data.get('id_proof_number'),
            location_link=data.get('location_link'),
            notes=data.get('notes')
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        print(f"✓ Registration saved: {new_user.name} (User: {username})")
        return jsonify({'success': True, 'message': 'Registration successful!', 'user_id': new_user.id}), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"✗ Error during registration: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/api/users', methods=['GET'])
def get_users():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    try:
        username = session['username']
        users = User.query.filter_by(user_id=username).all()
        print(f"✓ Retrieved {len(users)} registrations for user {username}")
        return jsonify({'success': True, 'users': [user.to_dict() for user in users]}), 200
    except Exception as e:
        print(f"✗ Error fetching users: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    try:
        username = session['username']
        user = User.query.filter_by(id=user_id, user_id=username).first()
        
        if user:
            db.session.delete(user)
            db.session.commit()
            print(f"✓ Registration deleted: {user.name}")
            return jsonify({'success': True, 'message': 'Registration deleted successfully'}), 200
        
        return jsonify({'success': False, 'message': 'Registration not found'}), 404
    except Exception as e:
        db.session.rollback()
        print(f"✗ Error deleting registration: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)