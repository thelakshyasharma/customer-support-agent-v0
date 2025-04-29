import os
import sys
import logging
from agent.info_agent import handle_info

# Configure logging to show messages on the console
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_link_handling(email="test@example.com"):
    """Test that the agent properly handles link requests instead of using placeholders."""
    
    # Test cases with queries that would typically result in link references
    test_cases = [
        {
            "query": "Where can I find the documentation?",
            "expected_contains": ["which version", "specific", "share", "URL"],
            "expected_not_contains": ["www.gocomet.com", "dashboard", "link to", "[link", "http"]
        },
        {
            "query": "How do I access the dashboard?",
            "expected_contains": ["could you", "which", "using", "version"],
            "expected_not_contains": ["www.gocomet.com/dashboard", "https://", "login.gocomet"]
        },
        {
            "query": "Send me the link to download the bulk upload template",
            "expected_contains": ["which version", "could you share", "specific URL"],
            "expected_not_contains": ["www.gocomet.com/bulk", "here's the link", "https://"]
        },
        {
            "query": "I need the URL for tracking containers",
            "expected_contains": ["which platform", "version", "share"],
            "expected_not_contains": ["www.gocomet.com/tracking", "gocomet.com", "https://"]
        }
    ]
    
    # Run tests
    for idx, test_case in enumerate(test_cases):
        # Create conversation history for continuity
        if idx > 0:
            conversation_history = f"User: {test_cases[idx-1]['query']}\nAgent: {responses[idx-1]}\n"
        else:
            conversation_history = ""
        
        # Get agent response
        query = test_case["query"]
        logger.info(f"Testing query: {query}")
        
        response = handle_info(query, email, conversation_history)
        
        # Log the response
        logger.info(f"Agent response: {response[:100]}...")
        
        # Check if response contains expected phrases
        contains_expected = all(phrase.lower() in response.lower() for phrase in test_case["expected_contains"])
        
        # Check if response does not contain prohibited phrases
        contains_prohibited = any(phrase.lower() in response.lower() for phrase in test_case["expected_not_contains"])
        
        # Print result
        if contains_expected and not contains_prohibited:
            logger.info(f"✅ PASSED: Agent correctly asks for specific links without using placeholders")
        else:
            if not contains_expected:
                missing = [phrase for phrase in test_case["expected_contains"] 
                          if phrase.lower() not in response.lower()]
                logger.error(f"❌ FAILED: Missing expected phrases: {missing}")
            if contains_prohibited:
                prohibited = [phrase for phrase in test_case["expected_not_contains"] 
                             if phrase.lower() in response.lower()]
                logger.error(f"❌ FAILED: Contains prohibited phrases: {prohibited}")
                
        # Store response for conversation history in next iteration
        if idx == 0:
            responses = [response]
        else:
            responses.append(response)
            
        logger.info("-" * 50)

if __name__ == "__main__":
    # Run the test
    test_link_handling()
    logger.info("All link handling tests completed!") 