from flask import Flask
from extensions import db
import models  # This is for ensuring the model classes are loaded

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///moodboard_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  

db.init_app(app)

@app.route('/')
def index():
    return "Hello, there World!"

with app.app_context():
    db.create_all()
