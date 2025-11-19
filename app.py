from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

app = Flask(__name__)

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///travel_tracking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define the User model
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
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
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.form
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=data.get('email')).first()
        if existing_user:
            return jsonify({'success': False, 'message': 'Email already registered'}), 400
        
        # Convert joined_date string to date object
        joined_date = None
        if data.get('joined_date'):
            try:
                joined_date = datetime.strptime(data.get('joined_date'), '%Y-%m-%d').date()
            except:
                return jsonify({'success': False, 'message': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Create new user
        new_user = User(
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
        
        print(f"✓ User registered successfully: {new_user.name} (ID: {new_user.id})")
        
        return jsonify({'success': True, 'message': 'Registration successful!', 'user_id': new_user.id}), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"✗ Error during registration: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/api/users', methods=['GET'])
def get_users():
    try:
        users = User.query.all()
        print(f"✓ Retrieved {len(users)} users from database")
        return jsonify({'success': True, 'users': [user.to_dict() for user in users]}), 200
    except Exception as e:
        print(f"✗ Error fetching users: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        user = User.query.get(user_id)
        if user:
            print(f"✓ Retrieved user: {user.name}")
            return jsonify({'success': True, 'user': user.to_dict()}), 200
        print(f"✗ User not found: {user_id}")
        return jsonify({'success': False, 'message': 'User not found'}), 404
    except Exception as e:
        print(f"✗ Error fetching user: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        user = User.query.get(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()
            print(f"✓ User deleted: {user.name}")
            return jsonify({'success': True, 'message': 'User deleted successfully'}), 200
        return jsonify({'success': False, 'message': 'User not found'}), 404
    except Exception as e:
        db.session.rollback()
        print(f"✗ Error deleting user: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)