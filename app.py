from flask import Flask, render_template, url_for, request, flash, session, redirect
from extensions import db
from models import User
from forms import RegistrationForm
from flask_bcrypt import Bcrypt

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config['SECRET_KEY'] = '5300749'

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///moodboard_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  

db.init_app(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    if 'user_id' not in session:
        flash("Please log in first!", "danger")
        return redirect(url_for('login'))
    return render_template('home.html', message="Welcome!")

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("Please log in first!", "danger")
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    return render_template('dashboard.html', user_name=user.name)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if email already exists
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            error_message = "Email already taken. Please choose a different email."
            return render_template('error.html', error_message=error_message)
        
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(name=form.name.data, email=form.email.data, password=hashed_password)
        try:
            db.session.add(new_user)
            db.session.commit()
            session['user_id'] = new_user.id  # Log the user in by saving their id in session
            flash("Registration successful! Welcome to your dashboard.", "success")
            return redirect(url_for('dashboard'))  # Redirect to dashboard
        except:
            db.session.rollback()
            flash("Registration failed. Please try again later.", "danger")
            return render_template('register.html', form=form)
                
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))  # redirect to dashboard

        else:
            flash("Login failed! Please check your login details and try again.", "danger")
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("You've been logged out!", "success")
    return redirect(url_for('index'))


with app.app_context():
    db.create_all()
