from .master_agent import master_handle_message
from .history import get_history, update_history, get_conversation_summary

def handle_message(message, user_id=None):
    if not user_id:
        user_id = "guest"
    
    # Check if this is the first message in the conversation
    history = get_history(user_id)
    is_first_message = len(history) == 0
    
    # If this is the first message and it's just a greeting like "hi", 
    # respond with a greeting and prompt about tracking
    lower_message = message.lower().strip()
    if is_first_message and lower_message in ["hi", "hello", "hey", "greetings"]:
        greeting = "Hi there! 👋 How can I help you today?"
        update_history(user_id, message, is_user=True)
        update_history(user_id, greeting, is_user=False)
        return greeting
    
    # Save the user's message to history
    update_history(user_id, message, is_user=True)
    
    # Get response from the master agent
    response = master_handle_message(message, user_id)
    
    # Save the agent's response
    update_history(user_id, response, is_user=False)
    
    return response 