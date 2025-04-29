import os
import sys
import logging
from agent.info_agent import handle_info

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_scenario(message, context_hint, email="test@example.com"):
    """Test the agent with a specific message and expected context"""
    logging.info(f"\n\n=== Testing scenario: {context_hint} ===")
    logging.info(f"Message: {message}")
    
    # Call the agent's handle_info function
    response = handle_info(message, email)
    
    # Log the response
    logging.info(f"Response: {response}")
    
    # Check if response contains links
    if "[" in response and "](" in response:
        logging.info("SUCCESS: Response contains links!")
    else:
        logging.info("NOTICE: Response does not contain links")
    
    return response

def main():
    """Test the agent's ability to provide links in different contexts"""
    
    # Test tracking context
    test_scenario(
        "I can't track my shipment",
        "Tracking issue"
    )
    
    # Test invalid tracking context
    test_scenario(
        "My tracking number MSCU1234567 is invalid",
        "Invalid tracking"
    )
    
    # Test bulk upload context
    test_scenario(
        "How do I add multiple containers at once?",
        "Bulk upload"
    )
    
    # Test account context
    test_scenario(
        "I can't login to my account",
        "Account issue"
    )
    
    # Test port congestion context
    test_scenario(
        "Is there congestion at the port of Shanghai?",
        "Port congestion"
    )
    
    # Test team management
    test_scenario(
        "How do I add a team member?",
        "Team management"
    )
    
    # Test adding existing users to new team
    test_scenario(
        "How can I add an existing user to a new team?",
        "Team management - existing users"
    )

if __name__ == "__main__":
    main() 