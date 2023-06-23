from cs50 import SQL


from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session

from add import Add

from werkzeug.security import check_password_hash, generate_password_hash


# app name
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///project.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
def index():
    """Show portfolio of stocks"""


    coursess = db.execute("SELECT * FROM courses")

    if session.get("user_id") is None:
            return render_template("index2.html",courses=coursess)


    user_id = session["user_id"]
    username = db.execute("SELECT username FROM users WHERE id = ?", int(user_id))

    return render_template("index.html", courses=coursess, username=username[0]["username"])


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            flash("Enter Username !!!!")
            return render_template("login.html")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("Enter Password !!!!")
            return render_template("login.html")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash("invalid username or password !!!!")
            return render_template("login.html")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signin():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username:
            flash("Enter Username !!!!")
            return render_template("signup.html")

        # Ensure password was submitted
        elif not password:
            flash("Enter Password !!!!")
            return render_template("signup.html")

        elif not confirmation:
            flash("Enter Password Again !!!!")
            return render_template("signup.html")

        elif password != confirmation:
            flash("Password Not Match !!!!")
            return render_template("signup.html")

        # hash password
        hash = generate_password_hash(password)

        try:
            newuser = db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash)

        except:
            flash("user already have an account !!!!")
            return render_template("login.html")

        session["user_id"] = newuser

        return redirect("/")


    else:
        return render_template("signup.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/courses", methods=["GET", "POST"])
def courses():
    """Show portfolio of stocks"""



    if session.get("user_id") is None:
            return redirect("/login")

    coursess = db.execute("SELECT * FROM courses")

    if request.method == "POST":
        course_id = request.form.get("enroll")

        id = db.execute("SELECT * FROM courses WHERE course_id = ?", int(course_id))

        if not id:
            flash("This course not Here !!!!")
            return render_template("courses.html", courses=coursess)


        user_id = session["user_id"]

        # check is course enrolled
        check = db.execute("SELECT * FROM usercourse WHERE user_id = ? AND course_id = ?", user_id, course_id)
        if check:
            flash("This course You Already Enroll !!!!")
            return render_template("courses.html", courses=coursess)

        # Add course to user
        db.execute("INSERT INTO usercourse (user_id, course_id) VALUES (?, ?)", user_id, course_id)

        # render page
        flash("You Enroll Now Go to /mycourses to check")
        return render_template("courses.html", courses=coursess)

    else:

        return render_template("courses.html", courses=coursess)


@app.route("/mycourses", methods=["GET", "POST"])
def mycourses():
    """Show portfolio of stocks"""

    # check user is login
    if session.get("user_id") is None:
            return redirect("/login")

    user_id = session["user_id"]

    usercourses = db.execute("SELECT * FROM courses JOIN usercourse ON usercourse.course_id = courses.course_id WHERE user_id = ?", user_id)

    return render_template("mycourses.html", courses=usercourses)


@app.route("/addcourse", methods=["GET", "POST"])
def addcourse():
    """Show portfolio of stocks"""



    if session.get("user_id") is None:
            return redirect("/login")

    coursess = db.execute("SELECT * FROM courses")

    if request.method == "POST":

        newcourse = request.form.get("playlist")

        # check is course in courses
        check = db.execute("SELECT * FROM courses WHERE playlist_link = ?", newcourse)

        if check:
            flash("This course You Already in Courses !!!!")
            return render_template("addcourse.html")


        try:
            Add(newcourse)
        except:
            flash("Check link is correct !!!!")
            return render_template("addcourse.html")

        flash("Course Added  !!!!")
        return render_template("addcourse.html")

    else:
        return render_template("addcourse.html")


# Define the dynamic route for course pages
@app.route('/course/<int:id>', methods=["GET", "POST"])
def course(id):
    # Find the course with the given ID

    coursess = db.execute("SELECT * FROM courses")

    for cours in coursess:
        if cours['course_id'] == id:
            videos = db.execute("SELECT * FROM videos WHERE course_id = ? ORDER BY 	video_num", id)
            
            return render_template('course.html', course=cours, videos=videos)
    # If no course was found with the given ID, return a 404 error
    return render_template('404.html'), 404


# Define the dynamic route for course pages
@app.route('/course/<int:id>/<int:num>')
def coursev(id, num):
    # Find the course with the given ID

    coursess = db.execute("SELECT * FROM courses")

    for cours in coursess:
        if cours['course_id'] == id:
            if num <= cours['count'] and num > 0:
                try:
                    video = db.execute("SELECT link FROM videos WHERE course_id = ? AND video_num = ?", id, num)
                except:
                    return render_template('404.html'), 404


                nextvideo = num + 1
                if nextvideo <= cours['count']+1 and nextvideo > 0:
                    videos = db.execute("SELECT * FROM videos WHERE course_id = ? ORDER BY 	video_num", id)

                    video=video[0]["link"]
                    if nextvideo == cours['count']+1:
                        nextvideo -=1

                    return render_template('video.html', video=video[32:], course=cours, videos=videos,nextvideo=nextvideo)
    # If no course was found with the given ID, return a 404 error
    return render_template('404.html'), 404







from flask import render_template

@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    # Ensure username was submitted
    if session.get("user_id") is None:
            return redirect("/login")
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run()