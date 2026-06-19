from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# 1. Safe API Key Check
if not os.environ.get("OPENAI_API_KEY"):
    print("Error: OPENAI_API_KEY environment variable is not set.")
    print("Please check your .env file in the workspace root.")
    exit(1)

client = OpenAI()
deployment = "gpt-3.5-turbo"

# 2. Ask for the character and sanitize/validate input length
character_input = input("What historical character would you like to speak with? (e.g., Julius Caesar, Cleopatra, Abe Lincoln): ")
character = character_input.strip()[:50]  # Limit input length to prevent abuse

if not character:
    print("No character specified. Exiting.")
    exit(1)

print(f"\n--- Starting conversation with {character}. Type 'quit' to exit. ---\n")

# Initialize the conversation history with the system persona
messages = [
    {
        "role": "system", 
        "content": f"You are the historical figure {character}. Speak in the first person, stay in character, and answer the user's questions based on your history, perspective, and accomplishments."
    }
]

# Max history turns to keep (excluding the system prompt)
# 10 turns = 10 user messages + 10 assistant responses
MAX_HISTORY_MESSAGES = 20

# Chat loop
while True:
    user_message = input("You: ")
    if user_message.strip().lower() == "quit":
        print(f"\nEnding conversation with {character}. Goodbye!\n")
        break
    
    # Append user turn to history
    messages.append({"role": "user", "content": user_message})
    
    # Send history to OpenAI
    completion = client.chat.completions.create(
        model=deployment,
        messages=messages,
        temperature=0.7
    )
    
    response = completion.choices[0].message.content
    print(f"\n{character}: {response}\n")
    
    # Append assistant turn to history so the bot remembers the context
    messages.append({"role": "assistant", "content": response})
    
    # 3. Sliding Context Window to prevent API context limits & token/billing exhaustion
    # Retain the system instruction (messages[0]) and slide the rest of the history
    if len(messages) > MAX_HISTORY_MESSAGES + 1:
        # Keep index 0 (system prompt) and slice from the end to keep the latest messages
        messages = [messages[0]] + messages[-(MAX_HISTORY_MESSAGES):]


