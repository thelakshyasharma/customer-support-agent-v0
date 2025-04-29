"""
Negative test script for the customer support agent to validate proper behavior.
Tests focus on what the agent should NOT do in specific scenarios.
"""

import os
import sys
import logging
import re
from agent.info_agent import handle_info, extract_container_numbers
import unittest

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestNegativeCases(unittest.TestCase):
    """Test cases for ensuring the agent doesn't give inappropriate responses."""
    
    def test_no_carrier_website_redirection(self):
        """Test that the agent doesn't direct users to carrier websites."""
        test_messages = [
            "My container MSCU1234567 is not updating",
            "I can't see any updates for my shipment",
            "The data for my MSC container seems outdated"
        ]
        
        # Patterns to check for in responses
        carrier_website_patterns = [
            r"check.*carrier('s)?\s+website",
            r"visit.*shipping line('s)?\s+website",
            r"go\s+to\s+(the\s+)?(MSC|Maersk|CMA CGM|OOCL|Hapag-Lloyd)('s)?\s+website",
            r"check\s+on\s+(the\s+)?(carrier|shipping line)('s)?\s+site",
            r"carrier('s)?\s+website\s+directly",
            r"check\s+directly\s+with\s+(the\s+)?carrier"
        ]
        
        for message in test_messages:
            response = handle_info(message, "test@example.com")
            
            for pattern in carrier_website_patterns:
                matches = re.search(pattern, response.lower())
                self.assertIsNone(
                    matches, 
                    f"Response should not direct users to carrier websites. Found: '{matches.group(0) if matches else ''}' in response: {response}"
                )
    
    def test_no_email_format(self):
        """Test that the agent doesn't format responses as emails."""
        test_messages = [
            "I have a question about my shipment",
            "Can you help me with tracking?",
            "My container is delayed"
        ]
        
        # Patterns that would indicate email formatting
        email_patterns = [
            r"subject:",
            r"dear\s+.*,",
            r"to\s*:",
            r"from\s*:",
            r"sincerely,",
            r"best\s+regards",
            r"regards,",
            r"thank\s+you\s+for\s+your\s+email"
        ]
        
        for message in test_messages:
            response = handle_info(message, "test@example.com")
            
            for pattern in email_patterns:
                matches = re.search(pattern, response.lower())
                self.assertIsNone(
                    matches, 
                    f"Response should not be formatted as an email. Found: '{matches.group(0) if matches else ''}' in response: {response}"
                )
    
    def test_no_links(self):
        """Test that the agent doesn't include links in its responses."""
        test_messages = [
            "How do I track my shipment?",
            "Where can I find the tracking dashboard?",
            "How do I add a shipment?"
        ]
        
        # Patterns that would indicate links
        link_patterns = [
            r"\[.*\]\(.*\)",  # Markdown links [text](url)
            r"https?://\S+",  # Raw URLs
            r"www\.\S+"       # www URLs
        ]
        
        for message in test_messages:
            response = handle_info(message, "test@example.com")
            
            for pattern in link_patterns:
                matches = re.search(pattern, response.lower())
                self.assertIsNone(
                    matches, 
                    f"Response should not include links. Found: '{matches.group(0) if matches else ''}' in response: {response}"
                )

def test_invalid_tracking_response():
    """
    Test that the agent doesn't ask for format when user reports invalid tracking.
    Instead, it should provide specific information about causes of invalid tracking
    and possible solutions from the documentation.
    """
    # Test case: User says "It says tracking is invalid" without specific error details
    conversation = [
        "User: I can't track my shipment",
        "Agent: I understand you're having trouble tracking your shipment. Have you already added this shipment to your dashboard, or are you trying to add it for the first time?",
        "User: It says shipment invalid"
    ]
    
    # Build conversation history
    history = "\n".join(conversation[:-1])
    current_message = conversation[-1].replace("User: ", "")
    
    # Get response
    print("\nTesting invalid tracking response - agent should ask for specific issue:")
    print("-" * 80)
    print(f"Conversation history:\n{history}")
    print(f"Current message: {current_message}")
    
    response = handle_info(current_message, history)
    print(f"\nResponse:\n{response}")
    
    # The agent SHOULD NOT immediately ask about format
    incorrect_phrases = [
        "is your tracking number in this format",
        "check if your tracking number follows this format",
        "container numbers must be"
    ]
    
    # The agent SHOULD ask about specific error messages or what kind of "invalid" issue
    expected_phrases = [
        "specific error",
        "exact message",
        "what kind of"
    ]
    
    found_incorrect = False
    for phrase in incorrect_phrases:
        if phrase.lower() in response.lower():
            found_incorrect = True
            print(f"❌ FAIL: Response incorrectly mentions format: '{phrase}'")
    
    if not found_incorrect:
        print("✅ PASS: Response does not ask about format unnecessarily")
        
    has_expected = False
    for phrase in expected_phrases:
        if phrase.lower() in response.lower():
            has_expected = True
            print(f"✅ PASS: Response asks for more details about the error: '{phrase}'")
            break
            
    if not has_expected:
        print("❌ FAIL: Response doesn't ask for specific error details")
    
    print("-" * 80)
    return response

def test_dont_mention_carrier_sla_for_simple_container():
    """
    Test that the agent doesn't provide unsolicited carrier SLA information
    when a user just mentions a container number without update issues.
    """
    # Test case: User simply enters a container number without update issues
    conversation = [
        "User: I need to track container MSCU8765435"
    ]
    
    # No history for this test
    history = ""
    current_message = conversation[0].replace("User: ", "")
    
    # Get response
    print("\nTesting container response - agent should not give unsolicited SLA info:")
    print("-" * 80)
    print(f"Current message: {current_message}")
    
    response = handle_info(current_message, history)
    print(f"\nResponse:\n{response}")
    
    # The agent SHOULD NOT mention carrier update times/SLAs without user asking
    incorrect_phrases = [
        "updates every 3-6 hours",
        "P1 carrier",
        "update frequency"
    ]
    
    found_incorrect = []
    for phrase in incorrect_phrases:
        if phrase.lower() in response.lower():
            found_incorrect.append(phrase)
    
    if not found_incorrect:
        print("✅ PASS: Response does not mention unsolicited carrier SLA info")
    else:
        print(f"❌ FAIL: Response gives unsolicited carrier SLA info: {found_incorrect}")
    
    print("-" * 80)
    return response

def test_outdated_data_response():
    """
    Test that the agent correctly provides SLA/update info
    ONLY when user mentions outdated/non-updated data.
    """
    # Test case: User mentions outdated data
    conversation = [
        "User: My container MSCU8765435 shows outdated information",
    ]
    
    # No history for this test
    history = ""
    current_message = conversation[0].replace("User: ", "")
    
    # Get response
    print("\nTesting outdated data response - agent SHOULD give SLA info:")
    print("-" * 80)
    print(f"Current message: {current_message}")
    
    response = handle_info(current_message, history)
    print(f"\nResponse:\n{response}")
    
    # The agent SHOULD mention carrier update times/SLAs here
    expected_phrases = [
        "updates every",
        "carrier",
        "frequency"
    ]
    
    missing_phrases = []
    for phrase in expected_phrases:
        if phrase.lower() not in response.lower():
            missing_phrases.append(phrase)
    
    if not missing_phrases:
        print("✅ PASS: Response does mention appropriate SLA info for outdated data")
    else:
        print(f"❌ FAIL: Response missing important SLA info: {missing_phrases}")
    
    print("-" * 80)
    return response

def test_initial_tracking_issue_question():
    """
    Test that when a user says they can't track their shipment, 
    the agent asks specifically what issue they're facing.
    """
    # Test case: User says they can't track shipment
    conversation = [
        "User: I can't track my shipment"
    ]
    
    # No history for this test
    history = ""
    current_message = conversation[0].replace("User: ", "")
    
    # Get response
    print("\nTesting initial tracking issue - agent should ask what specific issue:")
    print("-" * 80)
    print(f"Current message: {current_message}")
    
    response = handle_info(current_message, history)
    print(f"\nResponse:\n{response}")
    
    # The agent SHOULD ask what specific issue the user is facing, not just if they've added it
    incorrect_phrase = "have you already added this shipment"
    expected_phrases = [
        "what issue",
        "specific error",
        "specific problem",
        "what happens when",
        "what's the problem"
    ]
    
    if incorrect_phrase.lower() in response.lower():
        print(f"❌ FAIL: Response only asks if shipment has been added without asking about specific issue")
    else:
        print("✅ PASS: Response doesn't just ask if shipment has been added")
        
    found_expected = False
    for phrase in expected_phrases:
        if phrase.lower() in response.lower():
            found_expected = True
            print(f"✅ PASS: Response asks about specific issue: '{phrase}'")
            break
            
    if not found_expected:
        print("❌ FAIL: Response doesn't ask about specific issue user is facing")
    
    print("-" * 80)
    return response

def test_handle_type_errors():
    """
    Test that the agent doesn't crash with type errors when processing past conversations.
    This ensures robustness against different return types from load_past_conversations.
    """
    # Test case: Simple greeting to test general conversation flow
    conversation = [
        "User: Hi there"
    ]
    
    # No history for this test
    history = ""
    current_message = conversation[0].replace("User: ", "")
    
    # Get response
    print("\nTesting robustness against type errors:")
    print("-" * 80)
    print(f"Current message: {current_message}")
    
    try:
        response = handle_info(current_message, "test@example.com")
        print(f"\nResponse:\n{response}")
        print("✅ PASS: Agent successfully responded without type errors")
    except (AttributeError, TypeError) as e:
        print(f"❌ FAIL: Agent crashed with error: {str(e)}")
    except Exception as e:
        print(f"❌ FAIL: Agent crashed with unexpected error: {str(e)}")
    
    # Test with email address in the message to verify email handling
    email_message = "Please contact me at user@example.com"
    print("\nTesting with email in message:")
    print(f"Current message: {email_message}")
    
    try:
        response = handle_info(email_message, "test@example.com")
        print(f"\nResponse:\n{response}")
        print("✅ PASS: Agent successfully handled message containing email")
    except (AttributeError, TypeError) as e:
        print(f"❌ FAIL: Agent crashed with error when handling email: {str(e)}")
    except Exception as e:
        print(f"❌ FAIL: Agent crashed with unexpected error: {str(e)}")
    
    print("-" * 80)
    return response

def test_handle_context_confirmation():
    """
    Test the agent's ability to understand when a user is confirming an option from a previous agent message,
    especially short responses like 'one by one' or 'yes'.
    """
    # Test case 1: User confirms a previously presented option "one by one"
    conversation1 = [
        "User: I can't track my shipment",
        "Agent: I understand you're having trouble tracking your shipment. Could you please tell me if you've already added the shipment to your dashboard? If not, I can guide you through the process.",
        "User: I have added it",
        "Agent: Great! To ensure you can track your shipments effectively, could you please tell me if you added them one by one or used a bulk upload? Knowing this will help me assist you further.",
        "User: one by one"
    ]
    
    # Build conversation history
    history1 = "\n".join(conversation1[:-1])
    current_message1 = conversation1[-1].replace("User: ", "")
    
    # Get response
    print("\nTesting context confirmation - option selection:")
    print("-" * 80)
    print(f"Conversation history:\n{history1}")
    print(f"Current message: {current_message1}")
    
    response1 = handle_info(current_message1, "test@example.com", history1)
    print(f"\nResponse:\n{response1}")
    
    # The agent SHOULD acknowledge the "one by one" selection and continue appropriately
    acknowledgment_phrases = [
        "added one by one",
        "individual shipments",
        "manually added",
        "one at a time"
    ]
    
    found_acknowledgment = False
    for phrase in acknowledgment_phrases:
        if phrase.lower() in response1.lower():
            found_acknowledgment = True
            print(f"✅ PASS: Response acknowledges user's 'one by one' selection: '{phrase}'")
            break
            
    if not found_acknowledgment:
        print("❌ FAIL: Response doesn't acknowledge user's selection of 'one by one'")
    
    # Test case 2: Simple "yes" confirmation
    conversation2 = [
        "User: I'm trying to track my container",
        "Agent: I understand you want to track your container. Have you already added this shipment to your dashboard?",
        "User: yes"
    ]
    
    # Build conversation history
    history2 = "\n".join(conversation2[:-1])
    current_message2 = conversation2[-1].replace("User: ", "")
    
    # Get response
    print("\nTesting context confirmation - simple yes:")
    print("-" * 80)
    print(f"Conversation history:\n{history2}")
    print(f"Current message: {current_message2}")
    
    response2 = handle_info(current_message2, "test@example.com", history2)
    print(f"\nResponse:\n{response2}")
    
    # The agent SHOULD acknowledge the "yes" confirmation and continue with the next step
    continuation_phrases = [
        "great",
        "excellent",
        "good",
        "please provide",
        "what's the",
        "container number",
        "tracking number"
    ]
    
    found_continuation = False
    for phrase in continuation_phrases:
        if phrase.lower() in response2.lower():
            found_continuation = True
            print(f"✅ PASS: Response properly continues from 'yes' confirmation: '{phrase}'")
            break
            
    if not found_continuation:
        print("❌ FAIL: Response doesn't properly continue from 'yes' confirmation")
    
    print("-" * 80)
    return response1, response2

def test_casual_conversation_handling():
    """
    Test that the agent responds appropriately to casual conversation
    without steering back to business topics too aggressively.
    """
    # Test case 1: Weather question
    conversation1 = ["User: How's the weather today?"]
    
    # No history for this test
    history1 = ""
    current_message1 = conversation1[0].replace("User: ", "")
    
    # Get response
    print("\nTesting casual conversation - weather question:")
    print("-" * 80)
    print(f"Current message: {current_message1}")
    
    response1 = handle_info(current_message1, "test@example.com")
    print(f"\nResponse:\n{response1}")
    
    # The agent SHOULD be friendly and not forcefully redirect to shipping
    friendly_phrase = False
    if re.search(r"(weather|sunny|rainy|cloudy|forecast)", response1.lower()):
        print("✅ PASS: Response acknowledges weather question")
        friendly_phrase = True
    else:
        print("❌ FAIL: Response doesn't acknowledge weather question")
        
    business_redirect = False
    if re.search(r"(track|shipment|container|cargo|freight|package|dashboard)", response1.lower()):
        if re.search(r"(can I help you with|do you need help with|assist you with) (tracking|shipment)", response1.lower()):
            print("✅ PASS: Response gently transitions to business")
            business_redirect = True
        else:
            print("❌ FAIL: Response redirects to business too aggressively")
    
    if friendly_phrase and not re.search(r"(sorry|can't|unable|don't have access)", response1.lower()):
        print("✅ PASS: Response is friendly without apologies")
    else:
        print("❌ FAIL: Response has unnecessary apologies or limitations")
    
    # Test case 2: Joke request
    conversation2 = ["User: Tell me a joke"]
    
    # No history for this test
    history2 = ""
    current_message2 = conversation2[0].replace("User: ", "")
    
    # Get response
    print("\nTesting casual conversation - joke request:")
    print("-" * 80)
    print(f"Current message: {current_message2}")
    
    response2 = handle_info(current_message2, "test@example.com")
    print(f"\nResponse:\n{response2}")
    
    # The agent SHOULD respond with humor
    if re.search(r"(ha|haha|funny|laugh|joke|humor|shipping|cargo|container)", response2.lower()):
        print("✅ PASS: Response includes humor")
    else:
        print("❌ FAIL: Response doesn't include any humor")
        
    if not re.search(r"(sorry|can't|unable|don't have access|not programmed)", response2.lower()):
        print("✅ PASS: Response doesn't have unnecessary limitations")
    else:
        print("❌ FAIL: Response includes unnecessary limitations")
    
    # Test case 3: Rude request that should still get polite response
    conversation3 = ["User: Are you stupid?"]
    
    # No history for this test
    history3 = ""
    current_message3 = conversation3[0].replace("User: ", "")
    
    # Get response
    print("\nTesting casual conversation - rude question:")
    print("-" * 80)
    print(f"Current message: {current_message3}")
    
    response3 = handle_info(current_message3, "test@example.com")
    print(f"\nResponse:\n{response3}")
    
    # The agent SHOULD be polite despite the rude question
    if not re.search(r"(stupid|dumb|idiot|rude)", response3.lower()):
        print("✅ PASS: Response doesn't repeat or escalate rudeness")
    else:
        print("❌ FAIL: Response repeats or escalates rudeness")
        
    if re.search(r"(help|assist|support|question|answer)", response3.lower()):
        print("✅ PASS: Response steers toward constructive interaction")
    else:
        print("❌ FAIL: Response doesn't steer toward constructive interaction")
    
    print("-" * 80)
    return response1, response2, response3

def test_no_placeholder_links():
    """
    Test that the agent doesn't use placeholder URLs or make up links.
    Instead, it should ask the user for specific URLs or navigate without links.
    """
    # Test cases where the agent might be tempted to use placeholder links
    test_cases = [
        "How do I access the dashboard?",
        "Send me a link to the bulk upload page",
        "Where can I find documentation about tracking?",
        "Give me the URL for the carrier settings page"
    ]
    
    print("\nTesting that agent doesn't use placeholder links:")
    print("-" * 80)
    
    for test_query in test_cases:
        print(f"Testing query: {test_query}")
        
        # Get response
        response = handle_info(test_query, "test@example.com")
        print(f"First 100 chars of response:\n{response[:100]}...")
        
        # Check for placeholder links and URLs
        placeholder_patterns = [
            r'\[link to.*?\]',
            r'https?://(?:www\.)?gocomet\.com',
            r'<link>',
            r'https?://example\.com',
            r'click here:',
            r'login\.gocomet'
        ]
        
        found_placeholders = []
        for pattern in placeholder_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            if matches:
                found_placeholders.extend(matches)
        
        if found_placeholders:
            print(f"❌ FAIL: Response contains placeholder links/URLs: {found_placeholders}")
        else:
            # Check that it asks for information instead
            asking_patterns = [
                r'which version',
                r'could you share',
                r'specific url',
                r'screenshot'
            ]
            
            asks_properly = False
            for pattern in asking_patterns:
                if re.search(pattern, response, re.IGNORECASE):
                    asks_properly = True
                    break
                    
            if asks_properly:
                print("✅ PASS: Agent properly asks for information instead of using placeholder links")
            else:
                print("⚠️ WARNING: Agent doesn't use placeholders but also doesn't ask for specifics")
        
        print("-" * 50)
    
    return True

def main():
    """Run all tests"""
    print("Starting negative test cases")
    test_invalid_tracking_response()
    test_dont_mention_carrier_sla_for_simple_container()
    test_outdated_data_response()
    test_initial_tracking_issue_question()
    test_handle_type_errors()
    test_handle_context_confirmation()
    test_casual_conversation_handling()
    test_no_placeholder_links()
    print("\nAll negative tests completed")

if __name__ == "__main__":
    unittest.main() 