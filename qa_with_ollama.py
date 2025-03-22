from langchain_ollama import OllamaLLM                 # type: ignore
from langchain_core.prompts import ChatPromptTemplate  # type: ignore
import json

# Template for the conversation
template = """
Answer the question below.

Here is the conversation history: {context}

Question: {question}

Answer:
"""
model = OllamaLLM(model="llama3")
prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model

# Dummy database for storing user information
user_data = {}

def handle_conversation():
    context = ""
    print("Welcome to the AI ChatBot, Type 'exit' to quit.")

    # Simulating user login
    user_name = input("Enter your name: ")
    
    # Check if user exists (for simplicity, we use a dummy database here)
    if user_name not in user_data:
        print(f"Hi {user_name}! Welcome to Japi. Let's start your onboarding.")
        user_data[user_name] = {"goals": "", "skill_level": "", "conversation": []}

        # Step 1: Ask for learning goal
        learning_goal = input(f"{user_name}, what's your English learning goal? ")
        user_data[user_name]["goals"] = learning_goal
        context += f"AI: Hi {user_name}! Welcome to Japi. What's your English learning goal?\nUser: {learning_goal}\n"

        # Step 2: Ask for current skill level
        skill_level = input(f"{user_name}, what is your current English level? ")
        user_data[user_name]["skill_level"] = skill_level
        context += f"AI: That's a great goal, {user_name}! What is your current English level?\nUser: {skill_level}\n"

        # Step 3: Acknowledge and store conversation
        context += f"AI: Got it! Let's begin with a practice conversation.\n"
        user_data[user_name]["conversation"].append({"role": "AI", "message": f"Hi {user_name}! Welcome to Japi. What's your English learning goal?"})
        user_data[user_name]["conversation"].append({"role": "User", "message": learning_goal})
        user_data[user_name]["conversation"].append({"role": "AI", "message": f"That's a great goal, {user_name}! What is your current English level?"})
        user_data[user_name]["conversation"].append({"role": "User", "message": skill_level})
        user_data[user_name]["conversation"].append({"role": "AI", "message": "Got it! Let's begin with a practice conversation."})

        # Step 4: Output structured conversation history
        print(json.dumps({"conversation": user_data[user_name]["conversation"]}, indent=2))

    else:
        print(f"Welcome back, {user_name}! Let's continue your learning journey.")
        # Continue with previous conversation if any.
        print(json.dumps({"conversation": user_data[user_name]["conversation"]}, indent=2))
    
    # Continue with further interactions if necessary (this can be expanded)
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break

        # Format the prompt string using the template with context and user_input
        prompt_string = prompt.format(context=context, question=user_input)

        # Pass the formatted prompt string to the model
        result = model.invoke(prompt_string)
        print("Bot: ", result)

        # Update context with new input and response
        context += f"\nUser: {user_input}\nAI: {result}"

if __name__ == "__main__":
    handle_conversation()