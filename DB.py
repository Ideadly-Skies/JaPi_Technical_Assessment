import os
from supabase import create_client, Client # type: ignore
from dotenv import load_dotenv             # type: ignore
import psycopg2                            # type: ignore

# bcrypt to encrypt the password
import bcrypt                              # type: ignore 

# load .env file when connecting to the DB 
load_dotenv()

class DB:
    def __init__(self):
        """
        Initialize the database connection. All of the code here aren't GPT Generated and are generated personally by me :) 
        Visit this documentation to learn more about how to connect to the postgresql db using python: 
        https://supabase.com/docs/reference/python/update.
        """
        # derive url and key from .env to connect to db
        url: str = os.getenv("SUPABASE_URL")
        key: str = os.getenv("SUPABASE_KEY")
        self.supabase: Client = create_client(url, key)

        # output successful connection message
        print("DB Connected Successfully!")

    """
    ================================================== 
                USER RELATED METHODS 
    ================================================== 
    """
    def create_table_user(self):
        """
        Create `tbl_user` in Supabase PostgreSQL.
        """
        try:
            # Get credentials from environment variables
            DATABASE_URL = os.getenv("SUPABASE_DB_URL")

            # Connect to the database
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()

            # Drop the table if it exists query
            drop_table_sql = "DROP TABLE IF EXISTS tbl_user CASCADE;"

            # SQL command to create the table with more comprehensive user details
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS tbl_user (
                id SERIAL PRIMARY KEY,
                username VARCHAR(128) UNIQUE NOT NULL,
                email VARCHAR(128) UNIQUE NOT NULL,
                password_hash VARCHAR(256) NOT NULL,
                learning_goal TEXT,
                skill_level TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                role VARCHAR(50) DEFAULT 'user',
                jwt_token TEXT
            );
            """

            # Execute SQL statements
            cur.execute(drop_table_sql)
            cur.execute(create_table_sql)
            conn.commit()

            print("Table 'tbl_user' created successfully!")

            # close connection
            cur.close()
            conn.close()

        except Exception as e:
            print("Error creating table: %s" % (e))

    # instance method to login into system 
    def login(self, email, password):
        """Verify the email and password against the database."""
        # Fetch the user by email
        response = self.supabase.table("tbl_user").select("*").eq("email", email).execute()
        
        if response.data:
            user = response.data[0]
            # Compare the hashed password
            if bcrypt.checkpw(password.encode('utf-8'), user["password_hash"].encode('utf-8')):
                # Update last_login timestamp
                self.supabase.table("tbl_user").update({"last_login": "now()"}).eq("id", user["id"]).execute()
                return True
            else:
                return False
        else:
            return False

    # store token when logging in        
    def store_token(self, email, token):
        """Store the JWT token in the database."""
        self.supabase.table("tbl_user").update({"jwt_token": token}).eq("email", email).execute()

    # clear token when logging out
    def clear_token(self, email):
        """Clear the JWT token in the database for a given user."""
        self.supabase.table("tbl_user").update({"jwt_token": None}).eq("email", email).execute()

    # CRUD Operations for users
    def insert_user(self, username, email, password):
        """Insert a new user into the tbl_user table."""
        # Hash the password with bcrypt
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Insert user with email and hashed password
        response = self.supabase.table("tbl_user").insert({
            "username": username,
            "email": email,
            "password_hash": hashed_password
        }).execute()
        
        return response.data
    
    # Select all users
    def get_all_users(self):
        """Retrieve all users from tbl_user."""
        response = self.supabase.table("tbl_user").select("*").execute()
        return response.data 
    
    # Select a user by ID
    def get_user_by_id(self, user_id):
        """Retrieve a single user by ID."""
        response = self.supabase.table("tbl_user").select("*").eq("id", user_id).execute()
        return response.data 
    
    # selet a user by email
    def get_user_by_email(self, email):
        """Retrieve a single user by email."""
        response = self.supabase.table("tbl_user").select("*").eq("email", email).execute()
        return response.data

    # Update user
    def update_user(self, user_id, new_username, new_password):
        """Update username and password of an existing user."""
        # Hash the new password
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

        # Decode the hashed password to store it as a string in the database
        decoded_password = hashed_password.decode('utf-8')

        response = self.supabase.table("tbl_user").update({
            "username": new_username,
            "password": decoded_password 
        }).eq("id", user_id).execute()
        return response.data
    
    # Delete user
    def delete_user(self, user_id):
        """Delete a user from tbl_user by ID."""
        response = self.supabase.table("tbl_user").delete().eq("id", user_id).execute()
        return response.data
    
    """
    ================================================== 
                    LLAMA RELATED METHODS 
    ==================================================  
    """
    def create_table_conversation(self):
        """
        Create `tbl_conversation` to store user and AI conversations.
        """
        try:
            DATABASE_URL = os.getenv("SUPABASE_DB_URL")
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()

            # Drop table if it exists and create a new one
            drop_table_sql = "DROP TABLE IF EXISTS tbl_conversation CASCADE;"
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS tbl_conversation (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES tbl_user(id),
                role VARCHAR(50) NOT NULL,  -- AI or User
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            # Execute SQL commands
            cur.execute(drop_table_sql)
            cur.execute(create_table_sql)
            conn.commit()
            print("Table 'tbl_conversation' created successfully!")

            # Close connection
            cur.close()
            conn.close()

        except Exception as e:
            print("Error creating table: %s" % (e))

    def check_user_conversation_exists(self, user_id):
        """Check if the user has a conversation history."""
        response = self.supabase.table("tbl_conversation").select("id").eq("user_id", user_id).execute()
        return len(response.data) > 0
    
    def insert_user_message(self, user_id, message):
        """Insert the user's message into the conversation table."""
        self.supabase.table("tbl_conversation").insert({
            "user_id": user_id,
            "role": "User",
            "message": message
        }).execute()

    def insert_ai_response(self, user_id, message):
        """Insert the AI's response into the conversation table."""
        self.supabase.table("tbl_conversation").insert({
            "user_id": user_id,
            "role": "AI",
            "message": message
        }).execute()

    def get_conversation_history(self, user_id):
        """Get the conversation history for a user."""
        response = self.supabase.table("tbl_conversation").select("*").eq("user_id", user_id).execute()
        return response.data

    def check_user_conversation_exists(self, user_id):
        """Check if the user has a conversation history."""
        response = self.supabase.table("tbl_conversation").select("id").eq("user_id", user_id).execute()
        return len(response.data) > 0  
