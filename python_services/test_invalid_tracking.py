"""
Test script specifically for verifying the agent handles invalid tracking numbers correctly.
This focuses on the case where a tracking number has the correct format (4 letters + 7 digits)
but is still reported as invalid.
"""

import os
import sys
import logging
from agent.info_agent import handle_info, extract_container_numbers

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_invalid_tracking_with_correct_format():
    """Test the agent's response to a tracking number with correct format but reported as invalid"""
    
    # Test case: User reports a correctly formatted tracking number as invalid
    conversation = [
        "User: I can't track my container MSCU1234567",
        "Agent: I understand you're having trouble tracking your container MSCU1234567. Have you already added this shipment to your dashboard, or are you trying to add it for the first time?",
        "User: It says tracking is invalid"
    ]
    
    # Build conversation history
    history = "\n".join(conversation[:-1])
    current_message = conversation[-1].replace("User: ", "")
    
    # Get response
    print("\nTesting invalid tracking with correct format:")
    print("-" * 80)
    print(f"Conversation history:\n{history}")
    print(f"Current message: {current_message}")
    
    response = handle_info(current_message, history)
    print(f"\nResponse:\n{response}")
    
    # Check if the response contains expected information
    expected_phrases = [
        "invalid",
        "format is correct",
        "database",
        "carrier",
        "future shipment"
    ]
    
    missing_phrases = []
    for phrase in expected_phrases:
        if phrase.lower() not in response.lower():
            missing_phrases.append(phrase)
    
    if not missing_phrases:
        print("\n✅ PASS: Response contains all expected phrases")
    else:
        print(f"\n❌ FAIL: Response missing expected phrases: {missing_phrases}")
    
    # Check that the response does NOT ask if the format is correct
    incorrect_phrases = [
        "is your tracking number in this format",
        "check if your tracking number follows this format",
        "should be 4 letters followed by 7 digits"
    ]
    
    found_incorrect = []
    for phrase in incorrect_phrases:
        if phrase.lower() in response.lower():
            found_incorrect.append(phrase)
    
    if not found_incorrect:
        print("✅ PASS: Response does not ask about correct format when format is already correct")
    else:
        print(f"❌ FAIL: Response incorrectly asks about format: {found_incorrect}")
    
    # Check if container number is mentioned in response
    if "MSCU1234567" in response:
        print("✅ PASS: Response mentions the specific container number")
    else:
        print("❌ FAIL: Response does not mention the specific container number")
    
    print("-" * 80)
    
    return response

def test_with_dispatch_date_question():
    """Test the agent's response to a follow-up question about adding dispatch date"""
    
    # Test case: User asks how to add a dispatch date after being told about invalid tracking
    conversation = [
        "User: I can't track my container MSCU1234567",
        "Agent: I understand your container MSCU1234567 is showing as invalid, even though the format is correct. This typically happens for one of these reasons: 1) The container isn't in MSC's database yet (future shipment), 2) There might be a carrier mismatch, or 3) This could be a booking reference rather than a container number. Did you select MSC as the carrier when adding this tracking?",
        "User: Yes, I selected MSC", 
        "Agent: Thank you for confirming. Since you selected the correct carrier but it's still showing as invalid, this likely means the container MSCU1234567 is not yet in MSC's database. This commonly happens with future shipments. I recommend editing the shipment to add a dispatch date or estimated departure date - this tells our system it's a future shipment and prevents it from being marked invalid.",
        "User: How do I add a dispatch date?"
    ]
    
    # Build conversation history
    history = "\n".join(conversation[:-1])
    current_message = conversation[-1].replace("User: ", "")
    
    # Get response
    print("\nTesting follow-up about adding dispatch date:")
    print("-" * 80)
    print(f"Current message: {current_message}")
    
    response = handle_info(current_message, history)
    print(f"\nResponse:\n{response}")
    
    # Check if the response contains expected information
    expected_phrases = [
        "dashboard",
        "edit",
        "click",
        "dispatch date"
    ]
    
    missing_phrases = []
    for phrase in expected_phrases:
        if phrase.lower() not in response.lower():
            missing_phrases.append(phrase)
    
    if not missing_phrases:
        print("\n✅ PASS: Response contains all expected phrases")
    else:
        print(f"\n❌ FAIL: Response missing expected phrases: {missing_phrases}")
    
    print("-" * 80)
    
    return response

def main():
    """Run all tests"""
    test_invalid_tracking_with_correct_format()
    test_with_dispatch_date_question()

if __name__ == "__main__":
    main() 