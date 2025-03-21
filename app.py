# imports
import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response # type: ignore
from flask_jwt_extended import JWTManager, create_access_token                       # type: ignore
from DB import DB
from datetime import datetime  # Import the datetime class
from dotenv import load_dotenv                                                       # type: ignore
import random
import string

"""
===================================
    Load .env + Invoke DB 
===================================
"""
# load dotenv
load_dotenv()

# initialize db class
db = DB()

"""
===================================
      Routes + Flask App Flow
===================================
"""
# init new flask instance
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.config['JWT_SECRET_KEY'] = os.getenv("SECRET_KEY")
jwt = JWTManager(app)

@app.route('/')
def index():
    # render login form
    return render_template('login.html')

# Generate captcha
@app.route('/generate_captcha')
def generate_captcha():
    # Generate rando captcha string (5 characters)
    captcha_value = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

    # Store the captcha value in session
    session['captcha'] = captcha_value

    # Return captcha as text or image (depending on your implementation)
    return captcha_value

# login route
@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    captcha_input = request.form['captcha']

    # Get the stored captcha from the session
    stored_captcha = session.get('captcha')

    # Match captcha with user input
    if captcha_input != stored_captcha:
        flash("Login failed due to incorrect captcha.", 'error')
        return redirect(url_for('index'))

    if db.login(email, password):
        # store access token in DB
        access_token = create_access_token(identity=email)
        db.store_token(email, access_token)

        # store email in session
        session['email'] = email

        # send token as cookie
        response = make_response(redirect(url_for('dashboard')))
        response.set_cookie('access_token', access_token)

        flash("Login successful!", 'success')
        return redirect(url_for('dashboard'))
    else:
        flash("Login failed. Check your credentials.", 'error')
        return redirect(url_for('index'))

# logout from JaPi App
@app.route('/logout')
def logout():
    # retrieve user email from session 
    user_email = session.get('email')

    print("user email: %s" %(user_email))
    
    if user_email:
        # clear token from email
        db.clear_token(user_email)

    # clear entire session
    session.clear()

    # flash successfully logout!
    flash("LOGOUT SUKSES", 'success')

    # Redirect the user to the login page
    return redirect(url_for('index'))

# dashboard to invoke conversation with AI
@app.route('/dashboard')
def dashboard():
    # Fetch all users from the database
    users = db.get_all_users()

    # Convert CreateTime to datetime and format it
    for user in users:
        # Ensure 'CreateTime' is in datetime format
        if isinstance(user['created_at'], str):
            # Use the correct format for ISO 8601 with microseconds
            user['created_at'] = datetime.strptime(user['created_at'], '%Y-%m-%dT%H:%M:%S.%f')
        # Format the datetime object as 'YYYY-MM-DD'
        user['created_at'] = user['created_at'].strftime('%Y-%m-%d')

    # Render the dashboard template with users data
    return render_template('dashboard.html', users=users)

# register new user route 
@app.route('/create_user', methods=['GET', 'POST'])
def create_user():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Add the new user to the database
        db.insert_user(username, email, password)
        
        flash("BERHASIL MENAMBAHKAN USER BARU!", 'success')
        return redirect(url_for('dashboard'))

    return render_template('create_user.html')

"""
===============================
    Invoke Flask App 
===============================
"""
# checks if the current script is being run directly as the main program
# or if it's being imported as a module into another program
if __name__ == "__main__":
    # migrate and create `tbl_user`
    # db.create_table()
    
    app.run(debug=True)