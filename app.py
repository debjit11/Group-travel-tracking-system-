from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date

app = Flask(__name__)

# Configure app
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///travel_tracking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==================== ACCOUNTS MODEL ====================
class Account(db.Model):
    __tablename__ = 'accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password, password)

# ==================== REGISTRATIONS MODEL ====================
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False)  # Store username instead of account_id
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
            'notes': self.notes
        }

# Create database tables
with app.app_context():
    db.drop_all()  # Drop all existing tables
    db.create_all()  # Create fresh tables

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
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        
        # Validation
        if not all([username, email, password, confirm_password]):
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        if password != confirm_password:
            return jsonify({'success': False, 'message': 'Passwords do not match'}), 400
        
        if len(password) < 6:
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400
        
        # Check if user exists
        if Account.query.filter_by(username=username).first():
            return jsonify({'success': False, 'message': 'Username already exists'}), 400
        
        if Account.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': 'Email already registered'}), 400
        
        # Create new account
        try:
            account = Account(username=username, email=email)
            account.set_password(password)
            db.session.add(account)
            db.session.commit()
            
            print(f"✓ Account created in accounts.db: {username}")
            return jsonify({'success': True, 'message': 'Account created successfully! Please login.'}), 201
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error creating account: {str(e)}")
            return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password required'}), 400
        
        account = Account.query.filter_by(username=username).first()
        
        if account and account.check_password(password):
            session['user_id'] = account.id
            session['username'] = account.username
            session['email'] = account.email
            print(f"✓ Login successful: {username}")
            return jsonify({'success': True, 'message': 'Login successful!'}), 200
        
        print(f"✗ Login failed: {username}")
        return jsonify({'success': False, 'message': 'Invalid username or password'}), 401
    
    return render_template('login.html')

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
        username = session['username']  # Use username instead of account_id
        
        # Convert joined_date string to date object
        joined_date = None
        if data.get('joined_date'):
            try:
                joined_date = datetime.strptime(data.get('joined_date'), '%Y-%m-%d').date()
            except:
                return jsonify({'success': False, 'message': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Create new user registration
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
            notes=data.get('notes')
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        print(f"✓ Registration saved to registrations.db: {new_user.name} (User: {username})")
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
        print(f"✓ Retrieved {len(users)} registrations for user {username} from registrations.db")
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
            print(f"✓ Registration deleted from registrations.db: {user.name}")
            return jsonify({'success': True, 'message': 'Registration deleted successfully'}), 200
        
        return jsonify({'success': False, 'message': 'Registration not found'}), 404
    except Exception as e:
        db.session.rollback()
        print(f"✗ Error deleting registration: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)