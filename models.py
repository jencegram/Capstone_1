from extensions import db

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    moodboards = db.relationship('Moodboard', backref='user', lazy=True)



# Mood Model
class Mood(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mood_name = db.Column(db.String(255), nullable=False)
    moodboards = db.relationship('Moodboard', backref='mood', lazy=True)  # This will allow mood.moodboards querying

# Moodboard Model
class Moodboard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)  # Add description field
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    mood_id = db.Column(db.Integer, db.ForeignKey('mood.id'), nullable=False)
    
    photos = db.relationship('Photo', backref='moodboard', lazy=True)


# Photo Model
class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    photo_url = db.Column(db.String(255), nullable=False)
    moodboard_id = db.Column(db.Integer, db.ForeignKey('moodboard.id'), nullable=False)
