from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient 
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = "startuphub123"


# ---------------- DATABASE CONNECTION ----------------

MONGO_URI = "mongodb+srv://sujithak2020_db_user:MCMsX0ct2dCyiLPE@cluster0.mucs16r.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(MONGO_URI)

db = client["startuphub"]
users_collection = db["users"]
projects_collection = db["projects"]
startups_collection = db["startups"]
applications_collection = db["applications"]
contacts_collection = db["contacts"]


# ---------------- HOME ----------------

@app.route('/')
def home():
    return render_template('home.html')


# ---------------- REGISTER ----------------

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        existing_user = users_collection.find_one({
            "email": email
        })

        if existing_user:
            flash("Email already exists!", "danger")

        else:

            users_collection.insert_one({
                "name": name,
                "email": email,
                "password": password,
                "skill": "",
                "bio": "",
                "github": "",
                "linkedin": "",
                "image": ""
            })

            flash(
                "Registration successful! Please login.",
                "success"
            )

            return redirect(url_for('login'))

    return render_template('register.html')


# ---------------- LOGIN ----------------

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        user = users_collection.find_one({
            "email": email,
            "password": password
        })

        if user:

            session['user_id'] = str(user['_id'])
            session['user_name'] = user['name']

            flash("Logged in successfully!", "success")

            return redirect(url_for('dashboard'))

        else:

            flash("Invalid email or password", "danger")

    return render_template('login.html')


# ---------------- LOGOUT ----------------

@app.route('/logout')
def logout():

    session.clear()

    flash("Logged out successfully", "info")

    return redirect(url_for('home'))

# ---------------- DASHBOARD ----------------

# ---------------- DASHBOARD ----------------

@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_projects = list(
        projects_collection.find({
            "user_id": session["user_id"]
        })
    )

    all_startups = list(
        startups_collection.find().limit(5)
    )

    project_count = {
        "total_projects":
        projects_collection.count_documents({
            "user_id": session["user_id"]
        })
    }

    application_count = {
        "total_applications":
        applications_collection.count_documents({
            "user_id": session["user_id"]
        })
    }

    return render_template(
        "dashboard.html",
        projects=user_projects,
        startups=all_startups,
        project_count=project_count,
        application_count=application_count
    )


# ---------------- PROFILE ----------------

@app.route('/profile')
def profile():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = users_collection.find_one({
        "_id": ObjectId(session['user_id'])
    })

    projects = list(
        projects_collection.find({
            "user_id": session['user_id']
        })
    )

    return render_template(
        "profile.html",
        user=user,
        projects=projects
    )


# ---------------- EDIT PROFILE ----------------
@app.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':

        skill = request.form['skill']
        bio = request.form['bio']
        github = request.form['github']
        linkedin = request.form['linkedin']

        users_collection.update_one(
            {
                "_id": ObjectId(session['user_id'])
            },
            {
                "$set": {
                    "skill": skill,
                    "bio": bio,
                    "github": github,
                    "linkedin": linkedin
                }
            }
        )

        flash("Profile updated successfully", "success")

        return redirect(url_for('profile'))

    user = users_collection.find_one({
        "_id": ObjectId(session['user_id'])
    })

    return render_template(
        "edit_profile.html",
        user=user
    )

    # ---------------- ADD PROJECT ----------------
@app.route('/project/add', methods=['GET', 'POST'])
def add_project():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':

        title = request.form['title']
        description = request.form['description']
        technology = request.form['technology']

        projects_collection.insert_one({
            "user_id": session['user_id'],
            "title": title,
            "description": description,
            "technology": technology
        })

        flash("Project added successfully!", "success")

        return redirect(url_for('dashboard'))

    return render_template('add_project.html')


# ---------------- DELETE PROJECT ----------------
@app.route('/project/delete/<id>')
def delete_project(id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    projects_collection.delete_one({
        "_id": ObjectId(id),
        "user_id": session['user_id']
    })

    flash("Project deleted successfully!", "warning")

    return redirect(url_for('profile'))


# ---------------- STARTUPS ----------------

@app.route('/startups')
def startups():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    startups_list = list(startups_collection.find())

    # convert ObjectId → string
    for s in startups_list:
        s["_id"] = str(s["_id"])

    return render_template("startups.html", startups=startups_list)



# ---------------- APPLY TO STARTUP ----------------

@app.route('/apply/<startup_id>', methods=['GET', 'POST'])
def apply_startup(startup_id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Check if user has already applied to this startup
    already_applied = applications_collection.find_one({
        "user_id": session['user_id'],
        "startup_id": startup_id
    })

    if already_applied:
        flash("You have already applied to this company!", "info")
        return redirect(url_for('applications'))

    # Handle the submission from your teammate's new form page
    if request.method == 'POST':
        cover_letter = request.form.get('cover_letter', '')
        portfolio = request.form.get('portfolio', '')

        applications_collection.insert_one({
            "user_id": session['user_id'],
            "startup_id": startup_id,
            "cover_letter": cover_letter,
            "portfolio": portfolio,
            "status": "Pending"
        })

        flash("Application submitted successfully!", "success")
        return redirect(url_for('applications'))

    # GET Request: Fetch the startup details to show on the apply form
    startup = startups_collection.find_one({"_id": ObjectId(startup_id)})
    return render_template("apply.html", startup=startup)

# ---------------- APPLICATIONS ----------------

@app.route('/applications')
def applications():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_apps = []

    applications = applications_collection.find({
        "user_id": session['user_id']
    })

    for app_data in applications:

        startup = startups_collection.find_one({
            "_id": ObjectId(app_data["startup_id"])
        })

        if startup:

            user_apps.append({
                "startup_name": startup.get("startup_name", ""),
                "description": startup.get("description", ""),
                "status": app_data.get("status", "Pending")
            })

    return render_template(
        "applications.html",
        applications=user_apps
    )


# ---------------- DEVELOPERS ----------------

@app.route('/developers')
def developers():

    users = list(
        users_collection.find()
    )

    return render_template(
        "developers.html",
        users=users
    )


# ---------------- SEARCH ----------------

@app.route('/search')
def search():

    skill = request.args.get('skill', '')

    users = list(
        users_collection.find({
            "skill": {
                "$regex": skill,
                "$options": "i"
            }
        })
    )

    return render_template(
        "developers.html",
        users=users
    )


# ---------------- ABOUT ----------------

@app.route('/about')
def about():
    return render_template('about.html')


# ---------------- CONTACT ----------------

@app.route('/contact', methods=['GET', 'POST'])
def contact():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        contacts_collection.insert_one({
            "name": name,
            "email": email,
            "message": message
        })

        flash(
            "Message sent successfully!",
            "success"
        )

        return redirect(url_for('contact'))

    return render_template('contact.html')

# ---------------- MAIN ----------------

if __name__ == '__main__':
    app.run(debug=True)