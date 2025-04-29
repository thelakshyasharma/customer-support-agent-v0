import sys
import os
import logging
from agent.info_agent import handle_info

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_email_response(test_case):
    """Test how agent responds to an email in various contexts"""
    name = test_case["name"]
    conversation = test_case["conversation"]
    
    logger.info(f"\nTesting: {name}")
    logger.info("="*50)
    
    # Build conversation history
    history = "\n".join(conversation[:-1]) if len(conversation) > 1 else ""
    current_message = conversation[-1].replace("User: ", "")
    
    # Get response
    response = handle_info(current_message, history)
    
    logger.info(f"Input: {current_message}")
    logger.info(f"Response: {response}")
    logger.info("="*50)
    
    return response

# Test cases with various contexts
TEST_CASES = [
    {
        "name": "Email without context",
        "conversation": [
            "User: random@random.com"
        ]
    },
    {
        "name": "Email after tracking question",
        "conversation": [
            "User: I can't track my shipment",
            "Agent: I understand you're having trouble tracking your shipment. Have you already added this shipment to your dashboard, or are you trying to add it for the first time?",
            "User: random@random.com"
        ]
    },
    {
        "name": "Email after account blocked message",
        "conversation": [
            "User: I can't login",
            "Agent: Are you unable to login due to an error, or do you need help with your email or password?",
            "User: I get a message suggesting my account is blocked",
            "Agent: Your account appears to be blocked. I will escalate this to our support team and create a ticket for you. Please provide your email address so we can follow up.",
            "User: random@random.com"
        ]
    },
    {
        "name": "Email during purchase conversation",
        "conversation": [
            "User: I want to buy your tracking solution",
            "Agent: Thank you for your interest in our tracking solution. Could you please provide your email address so our sales team can contact you?",
            "User: random@random.com"
        ]
    },
    {
        "name": "Email after troubleshooting",
        "conversation": [
            "User: My data is not updating",
            "Agent: I'm sorry to hear you're having trouble with data updates. Could you please provide your container number?",
            "User: MSCU1234567",
            "Agent: Thank you. I see that container MSCU1234567 is with MSC, a P1 carrier that typically updates every 3-6 hours. If you're not seeing updates after 24 hours, this could be a synchronization issue. Could you please provide your email address so we can follow up?",
            "User: random@random.com"
        ]
    }
]

def main():
    """Run all test cases"""
    logger.info("Starting email response tests")
    
    # Run test cases
    results = {}
    for test_case in TEST_CASES:
        response = test_email_response(test_case)
        results[test_case["name"]] = response
    
    logger.info("\nTest Results Summary:")
    for name, response in results.items():
        logger.info(f"{name}: {'Related response' if response else 'Unrelated response'}")
    
    logger.info("\nAll tests completed")

if __name__ == "__main__":
    main() 