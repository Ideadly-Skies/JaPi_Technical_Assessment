# imports
import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response, session, jsonify # type: ignore
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity                        # type: ignore
from DB import DB
from datetime import datetime    
from dotenv import load_dotenv                                                                                        # type: ignore
import random
import string
from langchain_ollama import OllamaLLM                                                                                # type: ignore
from langchain_core.prompts import ChatPromptTemplate                                                                 # type: ignore
from flask_swagger_ui import get_swaggerui_blueprint

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
    Swagger Documentation 
===================================
"""
# Swagger configuration
SWAGGER_URL = '/api/docs'  # URL for exposing Swagger UI (without trailing '/')
API_URL = '/static/swagger.json'  # URL for your API specification file

# Call factory function to create the Swagger UI blueprint
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,  # Swagger UI static files will be served at {SWAGGER_URL}
    API_URL,
    config={  # Swagger UI config overrides
        'app_name': "Japi API Documentation"
    }
)

"""
===================================
   Init Flask APP and Auth Feat 
===================================
"""
# init new flask instance
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.config['JWT_SECRET_KEY'] = os.getenv("SECRET_KEY")
jwt = JWTManager(app)

# Register the Swagger UI blueprint with the Flask app
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

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

@app.route('/login', methods=['POST'])
def login():
    # Get the data from the request JSON body
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    captcha_input = data.get('captcha')

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

        user = db.get_user_by_email(email)
    
        if not user:
            flash("User not found", "error")
            return redirect(url_for('index')) 

        # check if user is returning user or not
        learning_goal = user[0].get("learning_goal", None)
        skill_level = user[0].get("skill_level", None)

        # flag to check if user is new
        returningUser = False

        if learning_goal or skill_level:
            returningUser = True

        # send token as cookie
        response = make_response(redirect(url_for('dashboard')))
        response.set_cookie('access_token', access_token)

        flash("Login successful!", 'success')
        
        # Send token as JSON response so that it can be saved in localStorage
        return jsonify({'access_token': access_token, 'returningUser': returningUser}), 200
    else:
        flash("Login failed. Check your credentials.", 'error')
        return redirect(url_for('index'))

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
    user_email = session.get('email')
    user = db.get_user_by_email(user_email)
    
    if not user:
        flash("User not found", "error")
        return redirect(url_for('index')) 

    username = user[0]['username'] 
    
    # Convert CreateTime to datetime and format it
    if isinstance(user[0]['created_at'], str):
        user[0]['created_at'] = datetime.strptime(user[0]['created_at'], '%Y-%m-%dT%H:%M:%S.%f')
    user[0]['created_at'] = user[0]['created_at'].strftime('%Y-%m-%d')

    # Render the dashboard template with the user's username and other data
    return render_template('dashboard.html', username=username) 

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
        return redirect(url_for('index'))

    return render_template('create_user.html')

"""
=====================================================
    Update User English Goal + Proficiency Level 
=====================================================
"""
@app.route('/update_user_info', methods=['GET', 'POST'])
def update_user_info():
    flash("Successfully navigated to profile section", 'success')

    user_email = session.get('email')
 
    # Fetch the user from the database
    user = db.get_user_by_email(user_email)
    user_id = user[0]['id']

    if request.method == 'POST':
        learning_goal = request.form['learning_goal']
        skill_level = request.form['skill_level']

        # Update the user info in the database
        db.supabase.table("tbl_user").update({
            "learning_goal": learning_goal,
            "skill_level": skill_level
        }).eq("id", user_id).execute()

        # Generate a topic suggestion based on the updated info
        suggested_topic = generate_topic(learning_goal, skill_level, user[0]['username'])
        
        # Insert an AI message acknowledging the update
        ai_message = f"Great, {user[0]['username']}! Your learning goal is now set to '{learning_goal}' with a proficiency level of '{skill_level}'. Let's start with: '{suggested_topic}'."
        db.insert_ai_response(user_id, ai_message)

        flash("Your information has been updated successfully!", 'success')
        return redirect(url_for('dashboard'))  

    return render_template('onboarding.html', user=user[0]) 

"""
=====================================================
    LLama Flow to chat with Logged-In User (TBA)
=====================================================
"""
# Template for the conversation
template = """
Follow these rules:
1. Avoid repeating the same response.
2. Focus on the user's learning goal: {learning_goal} (skill level: {skill_level}).
3. If stuck, suggest a new topic like: "{example_topic}".
4. Address the user by their name ({user_name}) where relevant.

Conversation history: {context}

Question: {question}

Answer:
"""
model = OllamaLLM(model="llama3")
prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model

# Example of limiting context length
def get_conversation_history(user_id, max_messages=5):
    conversation = db.get_conversation_history(user_id)
    context = ""
    for msg in conversation[-max_messages:]:  # Only include the last 'max_messages' messages
        context += f"{msg['role']}: {msg['message']}\n"
    return context

# Example of loop detection
def detect_loop(conversation):
    if len(conversation) < 3:
        return False
    
    # Check if the last 3 AI messages are identical
    last_ai_messages = [msg['message'] for msg in conversation[-3:] if msg['role'] == 'AI']
    if len(last_ai_messages) >= 2 and len(set(last_ai_messages)) == 1:
        return True
    
    # Check if user input repeats
    user_inputs = [msg['message'] for msg in conversation[-3:] if msg['role'] == 'User']
    if len(user_inputs) >= 2 and len(set(user_inputs)) == 1:
        return True
    
    return False

# chat with ai functionality
@app.route('/chat', methods=['POST'])
@jwt_required()
def chat():
    user_email = get_jwt_identity()
    user = db.get_user_by_email(user_email)
    user_id = user[0]['id']
    user_name = user[0]['username']

    learning_goal = user[0].get("learning_goal", None)
    skill_level = user[0].get("skill_level", None)

    context = get_conversation_history(user_id)

    if not learning_goal or not skill_level:
        return jsonify({
            "role": "AI",
            "message": f"Hi {user_name}, you're new here! Please set your English learning goal and proficiency level."
        })

    user_input = request.json.get('user_input', '')

    # Retrieve the conversation history as a list of messages
    conversation = db.get_conversation_history(user_id)

    # Check if this is the start of a new conversation
    if not conversation:
        # Suggest a topic to start the conversation
        suggested_topic = generate_topic(learning_goal, skill_level, user_name)
        ai_message = f"Hi {user_name}! Let's practice your English. Based on your goal to {learning_goal}, how about discussing: '{suggested_topic}'?"
        
        # Save the AI's greeting to the database
        db.insert_ai_response(user_id, ai_message)
        
        return jsonify({"role": "AI", "message": ai_message})

    if detect_loop(conversation):
        new_topic = generate_topic(learning_goal, skill_level, user_name)
        ai_message = f"Let's shift focus, {user_name}! Based on your goal to {learning_goal}, how about discussing: '{new_topic}'?"
        
        # Save the AI's new topic to the database
        db.insert_ai_response(user_id, ai_message)  # <-- Critical fix
        
        return jsonify({"role": "AI", "message": ai_message})

    # Include user_name in the prompt string
    prompt_string = f"Here is the conversation history:\n{context}\nQuestion: {user_input}\nAnswer:"
    result = model.invoke(prompt_string)

    # Add user_name to the AI's response if it makes sense
    if "{" in result and "}" in result: 
        result = result.format(user_name=user_name, learning_goal=learning_goal, skill_level=skill_level)

    db.insert_user_message(user_id, user_input)
    db.insert_ai_response(user_id, result)

    return jsonify({"role": "AI", "message": result})

# Function to generate a new topic based on learning goal and skill level
def generate_topic(learning_goal, skill_level, user_name):
    topics = {
        "improve speaking skills": {
            "beginner": [f"basic self-introductions, {user_name}", f"asking for directions in English"],
            "intermediate": [f"discussing your career goals, {user_name}", f"describing your hometown"],
            "advanced": [f"debating ethical dilemmas, {user_name}", f"analyzing TED Talks"]
        },
        "improve writing skills": {
            "beginner": [f"writing a diary entry, {user_name}", f"describing your family"],
            "intermediate": [f"crafting a LinkedIn post, {user_name}", f"summarizing news articles"],
            "advanced": [f"writing a research abstract, {user_name}", f"drafting a legal memo"]
        }
    }
    return random.choice(topics.get(learning_goal, {}).get(skill_level, ["a topic tailored to your updated skills"]))

"""
===============================
    Invoke Flask App 
===============================
"""
# checks if the current script is being run directly as the main program
# or if it's being imported as a module into another program
if __name__ == "__main__":
    # migrate and create `tbl_user` and `tbl_conversation`
    # db.create_table_user()
    # db.create_table_conversation()

    app.run(host="0.0.0.0", port=8080)