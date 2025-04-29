import os
import logging
from .info_agent import handle_info
from .troubleshooting_agent import handle_troubleshoot
from .escalation_agent import handle_escalation
from .history import get_conversation_summary
from .conversation_monitor import ConversationMonitor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize conversation monitor
conversation_monitor = ConversationMonitor()

# User conversation histories (in-memory for simplicity)
conversation_histories = {}

def save_history(user_id, role, message):
    """Save a message to the conversation history"""
    if user_id not in conversation_histories:
        conversation_histories[user_id] = []
    
    conversation_histories[user_id].append(f"{role}: {message}")

def get_history(user_id, max_messages=10):
    """Get the conversation history for a user"""
    if user_id not in conversation_histories:
        return ""
    
    # Get the last N messages
    messages = conversation_histories[user_id][-max_messages:]
    return "\n".join(messages)

def get_conversation_summary(user_id):
    """Generate a summary of the conversation"""
    if user_id not in conversation_histories:
        return "No conversation history available."
    
    # For now, just return the number of exchanges
    num_messages = len(conversation_histories[user_id])
    return f"Conversation with {num_messages} messages."

# Communication guidelines wrapper
COMM_GUIDELINES = "(Friendly, brief, empathetic, no jargon)"

def master_handle_message(message, user_id=None):
    """Process a user message and return an appropriate response"""
    logging.info(f"Processing message from user {user_id}: {message}")
    
    # Simple triage logic (stub):
    if not user_id:
        user_id = "default"
        
    # Get conversation history
    history = get_history(user_id)
    
    # Save user message to history
    save_history(user_id, "User", message)
    
    # Monitor user message for loops and progress
    status = conversation_monitor.add_message(user_id, "user", message)
    
    # Get conversation summary for context
    summary = get_conversation_summary(user_id)
    
    # Check if intervention is needed
    needs_intervention = status.get("needs_intervention", False)
    
    # Get context for the conversation
    context = None
    try:
        from .info_agent import parse_intent, determine_context
        intent_analysis = parse_intent(message)
        context = determine_context(intent_analysis, message, history)
    except (ImportError, AttributeError) as e:
        # If functions aren't available, continue without context
        logging.warning(f"Context detection unavailable: {str(e)}")
    
    # Simple routing logic based on message content and history
    if "escalate" in message.lower() or "manager" in message.lower():
        # Route to escalation agent
        response = handle_escalation(message, user_id)
    elif "error" in message.lower() or "bug" in message.lower() or "not working" in message.lower():
        # Route to troubleshooting agent
        response = handle_troubleshoot(message, user_id)
    else:
        if needs_intervention:
            try:
                # Try to use intervention system
                from .info_agent import get_gemini_response
                intervention_prompt = conversation_monitor.get_intervention_prompt(user_id)
                
                logging.info(f"Using intervention for user {user_id}: {status['guidance']['issue']}")
                
                # Create intervention prompt
                intervention_context = f"""
User message: {message}

Conversation history:
{history}

{intervention_prompt}

Respond directly to the user without mentioning that you're intervening.
"""
                response = get_gemini_response(intervention_context)
            except (ImportError, AttributeError) as e:
                # Fallback to regular info agent
                logging.warning(f"Intervention failed, using regular response: {str(e)}")
                response = handle_info(message, user_id, history)
        else:
            # Default to info agent
            response = handle_info(message, user_id, history)
        
    # Save agent response to history
    save_history(user_id, "Agent", response)
    
    # Monitor agent response
    conversation_monitor.add_message(user_id, "agent", response, context)
    
    # Log conversation status
    status = conversation_monitor.conversation_states.get(user_id, {})
    if status:
        logging.info(f"Conversation status: stage={status.get('stage', 'unknown')}, " +
                   f"progress_score={status.get('progress_score', 0)}, " +
                   f"loops_detected={status.get('loops_detected', 0)}")
    
    return response

def determine_intent(self, user_message):
    # Check for conversation closing signals when user indicates they don't need help
    if user_message.lower() in ["no", "nope", "I'm good", "all good", "I'm all set"]:
        # Check if the last agent message was asking if they need further assistance
        if self.conversation and len(self.conversation) >= 2:
            last_agent_message = self.conversation[-2].get("content", "").lower()
            if "assistance" in last_agent_message or "help" in last_agent_message or "further" in last_agent_message:
                return "conversation_end"
    
    # Continue with existing intent determination logic
    # ... rest of the method ...

async def get_response(self, user_message):
    # ... existing code ...
    
    intent = self.determine_intent(user_message)
    
    if intent == "conversation_end":
        # Handle conversation ending with a thank you message
        response = "Thank you for using our customer support service! Your chat has been marked as resolved. Feel free to reach out again if you need any assistance in the future."
        return response
    
    # ... existing code ... 