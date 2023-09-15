import os

import sqlite3
from flask import Flask, redirect, render_template, request, session, url_for
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import json

from helpers import apology, login_required

# Constants
DATABASE = "database.db"

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def homepage():
    """Homepage"""
    return render_template("homepage.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()
    con = sqlite3.connect(DATABASE)

    # User reached route via GET (as by getting the link)
    if request.method == "GET":
        return render_template("login.html")
    
    # User reached route via POST (as by submitting a form via POST)
    # Ensure username was submitted
    if not request.form.get("email"):
        return apology("email non valida", 400)

    # Ensure password was submitted
    elif not request.form.get("password"):
        return apology("password non valida", 400)

    # Query db for id and hash from email
    cur = con.cursor()
    # query_result is like [(id, pw_hash)] 
    query_result = cur.execute("SELECT id, hash FROM students WHERE email = ?;", (request.form.get("email"),)).fetchall()
    if not query_result:
        return apology("email e/o password invalidi", 400)
    
    id, pw_hash = query_result[0]

    # Check password against hash
    if not check_password_hash(pw_hash, request.form.get("password")):
        return apology("email e/o password invalidi", 400)

    # Remember which user has logged in
    session["user_id"] = id

    # Redirect user to home page
    return redirect("/")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # If called from the form
    if request.method == "POST":
        # Check if form fields are filled
        name = request.form.get("name")
        surname = request.form.get("surname")
        student_class = request.form.get("class")
        email = request.form.get("email")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Checks if name filed was filled
        if not name:
            return apology("Nome non valido", 400)

        # Checks if surname field was filled
        elif not surname:
            return apology("Cognome non valido", 400)

        # Checks if class field was filled
        elif not student_class:
            return apology("Classe non valida", 400)
        
        # Checks if email field was filled
        elif not email:
            return apology("Email non valida", 400)
        
        # Checks if password field was filled
        elif not password:
            return apology("Password non valida", 400)

        # Checks if the confirmation field wass filled
        elif not confirmation:
            return apology("Conferma non valida", 400)

        # Cheks if the password and confirmation match
        elif password != confirmation:
            return apology("password e conferma non coincidono", 400)

        # Checks if email is not taken
        con = sqlite3.connect(DATABASE)
        cur = con.cursor()
        
        # cur.execute returns a list like [(el1,), (el2,)] etc
        emails = map(lambda x: x[0], cur.execute("SELECT email FROM students").fetchall())
        if email in emails:
            return apology("email registrata", 400)

        # Save the new user
        cur.execute("INSERT INTO students (name, surname, class, email, hash) VALUES (?, ?, ?, ?, ?)",
                    (name, surname, student_class, email, generate_password_hash(password)))
        
        con.commit()

        # Redirect to the homepage
        return redirect("/")

    # If called to get the page
    else:
        # Render the page
        return render_template("register.html")


@app.route("/activities", methods=["GET", "POST"])
@login_required
def activities():
    """List of all activities"""
    
    if request.method == "POST":
        activity_id = request.form.get("activity_id")

        return redirect(url_for(".activity", id=activity_id))
    
    # If method is GET
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    query_output = cur.execute("SELECT id, title, type FROM activities").fetchall()
    
    if not query_output:
        return apology("Nessuna attività disponibile al momento")
    
    activities_list = [{"id": activity_id,
                        "title": activity_title,
                        "type": activity_type}
                    for activity_id, activity_title, activity_type in query_output]
    
    return render_template("activities.html", activities=activities_list)
    
    
@app.route("/activity", methods=["GET", "POST"])
@login_required
def activity():
    """Activity page w/ details"""
    
    if request.method == "GET":
        con = sqlite3.connect(DATABASE)
        cur = con.cursor()
        
        activity_id = request.args["id"]
        cur.execute("SELECT title, abstract, type, availability FROM activities WHERE id = ?;", (activity_id,))
        activity_title, activity_abstract, activity_type, activity_availability = cur.fetchone()
        
        # Factors of the activity
        activity_dict = {"title": activity_title,
                        "abstract": activity_abstract,
                        "type": activity_type,
                        }
        
        # Days and hours the course is available on
        activity_availability = json.loads(activity_availability)
        days = activity_availability.keys()
        timespans = activity_availability[next(iter(activity_availability))].keys()
        
        return render_template("activity.html", activity=activity_dict, days=days, timespans=timespans)
    
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()


@app.route("/me")
@login_required
def me():
    """Me page w/ your bookings"""
    return render_template("me.html")