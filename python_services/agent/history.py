# Simple in-memory conversation history (not for production)
_history = {}

def get_history(user_id):
    return _history.get(user_id, [])

def update_history(user_id, message, is_user=False):
    if user_id not in _history:
        _history[user_id] = []
    
    # Add the current message
    _history[user_id].append({
        "role": "user" if is_user else "agent",
        "message": message
    })
    
    return _history[user_id]

def get_conversation_summary(user_id, last_n=5):
    """Return the last n exchanges in a format suitable for the model context"""
    history = get_history(user_id)
    if not history:
        return ""
        
    # Get the last n*2 messages (n exchanges)
    recent_history = history[-min(last_n*2, len(history)):]
    
    # Format for model context
    summary = ""
    for entry in recent_history:
        role = "User" if entry["role"] == "user" else "Agent"
        summary += f"{role}: {entry['message']}\n\n"
    
    return summary 