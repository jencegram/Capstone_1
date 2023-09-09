from flask import Flask, render_template, url_for, request, flash, session, redirect
from extensions import db
from models import User, Moodboard, Mood
from forms import RegistrationForm, CreateMoodboardForm
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
    
    # Fetch all moodboards created by the logged-in user
    moodboards = Moodboard.query.filter_by(user_id=session['user_id']).all()

    return render_template('dashboard.html', user_name=user.name, moodboards=moodboards)



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

# Create a moodboard
@app.route('/create_moodboard', methods=['GET', 'POST'])
def create_moodboard():
    moods = Mood.query.all()
    mood_choices = [(mood.mood_name, mood.mood_name.capitalize()) for mood in moods]
    
    form = CreateMoodboardForm()
    form.mood.choices = mood_choices  # Set the choices for the mood field dynamically

    if form.validate_on_submit():
        # Print form data for debugging purposes
        print("Form Data:", form.title.data, form.description.data, form.mood.data)

        mood = Mood.query.filter_by(mood_name=form.mood.data).first()
        new_moodboard = Moodboard(title=form.title.data, description=form.description.data, mood_id=mood.id, user_id=session['user_id'])
        
        try:
            db.session.add(new_moodboard)
            db.session.commit()
            flash("Moodboard created successfully!", "success")
            return redirect(url_for('view_moodboard', moodboard_id=new_moodboard.id))
        except Exception as e:
            db.session.rollback()
            print("Error adding moodboard:", e)
            flash("Error creating moodboard. Please try again later.", "danger")
    else:
        if form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"Error in {field}: {error}", "danger")
    return render_template('create_moodboard.html', form=form)




# Route for viewing a moodboard:
@app.route('/moodboard/<int:moodboard_id>')
def view_moodboard(moodboard_id):
    moodboard = Moodboard.query.get_or_404(moodboard_id)
    return render_template('moodboard_detail.html', moodboard=moodboard)


# Route for editing a moodboard:
@app.route('/moodboard/<int:moodboard_id>/edit', methods=['GET', 'POST'])
def edit_moodboard(moodboard_id):
    moodboard = Moodboard.query.get_or_404(moodboard_id)
    form = CreateMoodboardForm(obj=moodboard)  # Prefill form with current data

    # Query the moods to populate the dropdown
    moods = Mood.query.all()
    mood_choices = [(mood.mood_name, mood.mood_name.capitalize()) for mood in moods]
    form.mood.choices = mood_choices

    if form.validate_on_submit():
        moodboard.title = form.title.data
        moodboard.description = form.description.data
        mood = Mood.query.filter_by(mood_name=form.mood.data).first()
        moodboard.mood_id = mood.id
        db.session.commit()
        flash("Moodboard updated successfully!", "success")
        return redirect(url_for('view_moodboard', moodboard_id=moodboard.id))
    
    return render_template('edit_moodboard.html', form=form, moodboard=moodboard)




@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("You've been logged out!", "success")
    return redirect(url_for('index'))


with app.app_context():
    db.create_all()
