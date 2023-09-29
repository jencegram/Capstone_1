import os
import requests

from dotenv import load_dotenv

load_dotenv()

from flask import (
    Flask,
    render_template,
    url_for,
    request,
    flash,
    session,
    redirect,
    jsonify,
)
from extensions import db
from models import User, Moodboard, Mood, Photo
from forms import RegistrationForm, CreateMoodboardForm
from flask_bcrypt import Bcrypt
from decouple import config

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config["SECRET_KEY"] = config("FLASK_SECRET_KEY")

app.config["SQLALCHEMY_DATABASE_URI"] = config("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


@app.route("/")
def index():
    """Shows the welcome page. If logged in: shows the welcome page. Otherwise: shows the login/signup page."""
    if "user_id" in session:
        return render_template("home.html", message="Welcome!")
    else:
        return render_template("index.html")


@app.route("/home")
def home():
    """Displays the homepage. If not logged in, redirects to login"""
    if "user_id" not in session:
        flash("Please log in first!", "danger")
        return redirect(url_for("login"))
    return render_template("home.html", message="Welcome!")


@app.route("/dashboard")
def dashboard():
    """User's dashboard. Shows all moodboards created by user. Redirects if not authenticated."""
    if "user_id" not in session:
        flash("Please log in first!", "danger")
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])

    # Fetch all moodboards created by the logged-in user
    moodboards = Moodboard.query.filter_by(user_id=session["user_id"]).all()

    return render_template("dashboard.html", user_name=user.name, moodboards=moodboards)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Handles user registration."""
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if email already exists
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            error_message = "Email already taken. Please choose a different email."
            return render_template("error.html", error_message=error_message)

        hashed_password = bcrypt.generate_password_hash(form.password.data).decode(
            "utf-8"
        )
        new_user = User(
            name=form.name.data, email=form.email.data, password=hashed_password
        )
        try:
            db.session.add(new_user)
            db.session.commit()
            session[
                "user_id"
            ] = new_user.id  # Log the user in by saving their id in session
            flash("Registration successful! Welcome to your dashboard.", "success")
            return redirect(url_for("dashboard"))
        except:
            db.session.rollback()
            flash("Registration failed. Please try again later.", "danger")
            return render_template("register.html", form=form)

    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Handles user login. Checks credeintials."""
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            session["user_id"] = user.id
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))

        else:
            flash(
                "Login failed! Please check your login details and try again.", "danger"
            )
    return render_template("login.html")


@app.route("/create_moodboard", methods=["GET", "POST"])
def create_moodboard():
    """Creates a new moodboard."""
    moods = Mood.query.all()
    mood_choices = [(mood.mood_name, mood.mood_name.capitalize()) for mood in moods]

    form = CreateMoodboardForm()
    form.mood.choices = mood_choices

    if form.validate_on_submit():
        title = form.title.data
        description = form.description.data
        mood_name = form.mood.data

        user_id = session["user_id"]

        moodboard = Moodboard(title=title, description=description, user_id=user_id)

        for image_url in request.form.getlist("selected_images[]"):
            image = Photo(photo_url=image_url)
            moodboard.photos.append(image)

        mood = Mood.query.filter_by(mood_name=mood_name).first()
        moodboard.mood = mood

        try:
            db.session.add(moodboard)
            db.session.commit()
            flash("Moodboard created successfully!", "success")
            return redirect(url_for("dashboard"))


        except Exception as e:
            db.session.rollback()
            print("Error adding moodboard:", e)
            flash("Error creating moodboard. Please try again later.", "danger")
    else:
        if form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"Error in {field}: {error}", "danger")

    return render_template("create_moodboard.html", form=form)


@app.route("/moodboard/<int:moodboard_id>/edit", methods=["GET", "POST"])
def edit_moodboard(moodboard_id):
    """Edit an existing moodboard."""
    moodboard = Moodboard.query.get_or_404(moodboard_id)
    selected_images = moodboard.photos
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

        # Handling the images:
        current_images = {photo.photo_url for photo in selected_images}
        submitted_images = set(request.form.getlist("selected_images[]"))

        # Remove images that are not in the submitted list
        for image in current_images - submitted_images:
            photo = Photo.query.filter_by(photo_url=image).first()
            if photo:
                moodboard.photos.remove(photo)
                db.session.delete(photo)  # Deleting the photo

        # Add new images that are not in the current list
        for image in submitted_images - current_images:
            existing_photo = Photo.query.filter_by(photo_url=image).first()
            if not existing_photo:
                new_photo = Photo(photo_url=image)
                moodboard.photos.append(new_photo)
                db.session.add(new_photo)
            else:
                moodboard.photos.append(
                    existing_photo
                )  # Attach the existing image to the moodboard

        try:
            db.session.commit()
            flash("Moodboard updated successfully!", "success")
            return redirect(
                url_for("view_moodboard_with_images", moodboard_id=moodboard.id)
            )
        except Exception as e:
            db.session.rollback()
            print("Error updating moodboard:", e)
            flash("Error updating moodboard. Please try again later.", "danger")

    return render_template(
        "edit_moodboard_images.html",
        moodboard=moodboard,
        selected_images=selected_images,
        form=form,
    )


@app.route("/search_photos", methods=["GET"])
def search_photos():
    """Search for photos using Unsplash API. Returns photos based on query"""
    query = request.args.get("query")
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=10, type=int)

    # Make request to the Unsplash API to search for photos
    unsplash_access_key = os.environ.get("UNSPLASH_API_KEY")

    if not unsplash_access_key:
        return jsonify({"error": "Unsplash API key not found"}), 500

    url = f"https://api.unsplash.com/search/photos?page={page}&per_page={per_page}&query={query}"
    headers = {
        "Authorization": f"Client-ID {unsplash_access_key}",
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        photos = data["results"]
        return jsonify(photos=photos)  # Return photos as JSON data
    else:
        return jsonify({"error": "Error fetching photos from Unsplash"}), 500


@app.route("/add_image_to_moodboard/<int:moodboard_id>", methods=["POST"])
def add_image_to_moodboard(moodboard_id):
    """Add an image to specific moodboard. Image identified by url"""
    moodboard = Moodboard.query.get_or_404(moodboard_id)
    image_url = request.json.get("image_url")

    if not image_url:
        return jsonify({"error": "No image URL provided"}), 400

    # Check if image already exists
    existing_image = Photo.query.filter_by(photo_url=image_url).first()
    if not existing_image:
        new_image = Photo(photo_url=image_url)
        moodboard.photos.append(new_image)
        db.session.add(new_image)
    else:
        if existing_image not in moodboard.photos:
            moodboard.photos.append(existing_image)

    db.session.commit()

    return jsonify({"message": "Image added successfully"}), 200


@app.route("/moodboard/<int:moodboard_id>/view", methods=["GET"])
def view_moodboard_with_images(moodboard_id):
    """View a moodboard display"""
    moodboard = Moodboard.query.get_or_404(moodboard_id)
    print(moodboard)
    selected_images = moodboard.photos
    print(selected_images)
    return render_template(
        "moodboard_with_images.html",
        moodboard=moodboard,
        selected_images=selected_images,
    )


@app.route("/moodboard/<int:moodboard_id>/delete_image/<int:photo_id>", methods=["GET"])
def delete_image(moodboard_id, photo_id):
    """Delete a specific image from a moodboard."""
    photo = Photo.query.get_or_404(photo_id)
    if not photo:
        flash("Photo not found", "danger")
        return redirect(url_for("edit_moodboard", moodboard_id=moodboard_id))

    try:
        db.session.delete(photo)
        db.session.commit()
        flash("Photo deleted successfully", "success")
    except Exception as e:
        print(e)
        db.session.rollback()
        flash("An error occurred while deleting the photo", "danger")

    return redirect(url_for("edit_moodboard", moodboard_id=moodboard_id))


@app.route("/delete_moodboard/<int:moodboard_id>", methods=["GET", "POST"])
def delete_moodboard(moodboard_id):
    """Deletes moodboard and all it's images"""
    # Check if user is logged in
    if "user_id" not in session:
        flash("Please login first.", "danger")
        return redirect(url_for("login"))

    # Fetch the moodboard
    moodboard = Moodboard.query.get_or_404(moodboard_id)

    # Check if the logged in user has permissions to delete the moodboard
    if session["user_id"] != moodboard.user_id:
        flash("You do not have permissions to delete this moodboard.", "danger")
        return redirect(url_for("index"))

    for photo in moodboard.photos:
        db.session.delete(photo)

    db.session.delete(moodboard)
    db.session.commit()

    flash("Moodboard deleted successfully.", "success")
    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    """Logs out the user and clears the session"""
    session.pop("user_id", None)
    flash("You've been logged out!", "success")
    return redirect(url_for("index"))

@app.cli.command("seed-db")
def seed_db():
    """Seed database with predefined moods."""
    moods = ["Happy", "Sad", "Joyful", "Inspired", "Angry", "Anxious"]

    for mood_name in moods:
        # Check if the mood already exists 
        existing_mood = Mood.query.filter_by(mood_name=mood_name).first()
        if not existing_mood:
            mood = Mood(mood_name=mood_name)
            db.session.add(mood)
    
    db.session.commit()
    print("Database seeded")

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.debug = True
    app.run()
