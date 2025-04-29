import os
import google.generativeai as genai
from dotenv import load_dotenv
import logging
from .history import get_history, get_conversation_summary
import json
import re
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
logger.info("Current working directory: %s", os.getcwd())
logger.info("Loading .env file...")
load_dotenv(verbose=True)
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    logger.error("GOOGLE_API_KEY not found in environment variables!")
    logger.info("Available environment variables: %s", list(os.environ.keys()))
else:
    logger.info("GOOGLE_API_KEY loaded successfully (length: %d)", len(API_KEY))

# Configure Gemini with API key directly
genai.configure(api_key=API_KEY)

# Define keyword categories for query parsing
ACTION_KEYWORDS = {
    "purchase": ["buy", "purchase", "get", "subscribe", "subscription", "pricing", "cost", "plan", "price"],
    "tracking": ["track", "trace", "find", "locate", "check", "monitor", "follow", "where is", "status"],
    "troubleshoot": ["fix", "solve", "resolve", "troubleshoot", "issue", "problem", "error", "not working", "can't", "cannot"],
    "learn": ["how", "what", "explain", "tell me", "learn", "understand", "know"],
    "account": ["login", "sign in", "account", "password", "forgot", "reset", "access"]
}

PRODUCT_KEYWORDS = {
    "tracking": ["tracking", "shipment", "container", "cargo", "freight", "package"],
    "port_congestion": ["port", "congestion", "delay", "traffic", "harbor", "terminal"],
    "co2": ["co2", "carbon", "emission", "environmental", "footprint", "climate"],
    "account": ["account", "login", "profile", "settings", "user"]
}

FEATURE_KEYWORDS = {
    "bulk_upload": ["bulk", "upload", "multiple", "excel", "csv", "spreadsheet", "file"],
    "single_track": ["single", "individual", "one", "specific"],
    "reports": ["report", "analytics", "statistics", "data", "metrics", "dashboard"],
    "alerts": ["alert", "notification", "update", "email", "sms", "message"]
}

PURPOSE_KEYWORDS = {
    "solve": ["help", "fix", "solve", "resolve", "issue", "problem", "error", "not working", "broken"],
    "learn": ["how", "what", "explain", "tell me", "guide", "tutorial", "documentation"],
    "evaluate": ["compare", "difference", "better", "best", "worth", "value", "review"]
}

INFO_AGENT_PROMPT = """
You are a human customer support agent for GoComet. Keep all responses short and focused.

IMPORTANT CLARIFICATION ABOUT YOUR ROLE:
- You are a SUPPORT AGENT only - you CANNOT directly track containers or provide real-time tracking data
- You can ONLY provide guidance on how customers can use the platform themselves
- NEVER imply you can check tracking information for users or see their shipments
- If users ask about specific container status, explain you cannot see their tracking data
- ALWAYS guide users to use the platform themselves to check status

CRITICAL REQUIREMENTS:
1. KEEP RESPONSES SHORT - Use 1-3 sentences max per response
2. ASK ONE QUESTION AT A TIME - Never ask multiple questions in the same message
3. FOCUS ON SPECIFICS - Give precise, actionable guidance
4. BE DIRECT - No fluff, no lengthy explanations unless asked
5. VALIDATE CONTAINER FORMAT - Container numbers must be 4 letters followed by 7 digits (ABCD1234567)
6. HANDLE FRUSTRATION - When users express frustration, acknowledge it briefly then focus on solutions
7. RECOGNIZE ERROR PATTERNS - Check tracking numbers against common error formats
8. OFFER ALTERNATIVES - If one approach isn't working, suggest alternatives before escalating
9. SET PROPER EXPECTATIONS - Make it clear you're providing guidance, not tracking shipments directly

FORMAT FOR READABILITY:
- Use short paragraphs (1-2 sentences per paragraph)
- Put key points on separate lines
- Add blank lines between different thoughts or topics
- For steps or instructions, use numbered points on separate lines
- Present options clearly on separate lines
- Break up long sentences
- Make responses scannable at a glance

IMPORTANT FLOW RULES:
- When users say "Where is my shipment/container" - CLARIFY you cannot directly see their shipment data, then guide them on how to check themselves
- When users say "I can't track my shipment" - FIRST ask what specific issue/error they're facing on the platform
- NEVER say "Let me check that for you" or imply you can retrieve their tracking data
- When user provides a container number, DON'T claim to look it up - instead guide them on how to add it correctly

When users report "invalid tracking":
- First ask for the specific error message they're seeing on the platform
- If user has a tracking number with correct format (4 letters + 7 digits), NEVER ask about format
- Instead, explain these common reasons for "invalid" errors from our documentation:
  1. Future shipment: The container isn't in carrier's database yet
  2. Wrong carrier selection: Verify carrier matches the container prefix
  3. Tracking number mismatch: The ID might be a booking reference, not a container
- Provide specific solutions:
  - Add dispatch date/estimated departure for future shipments
  - Verify carrier selection matches container prefix
  - For certain carriers (Evergreen, BLPL), try using BL number instead

For invalid tracking errors, use these troubleshooting steps from documentation:
- If tracking ID not found on carrier site: Suggest selecting the right carrier
- If POL/POD mismatch: Guide user to check/edit port information
- If "need BL no. for complete schedule": Explain some carriers require BL for full details
- If carrier not found: Suggest checking the carrier name spelling or support@gocomet.com

For outdated data issues:
- Explain carrier update frequencies (P1: 3-6 hours, P2: 24-48 hours)
- Explain automatic refresh cycles
- Mention that updates depend on the carrier publishing new data
- Offer to guide them on setting up notifications for when data refreshes

When guiding users to add shipments:
- Mandatory fields: Mode (Ocean/Air), Carrier, Container Number
- For carrier errors: "Enter the exact shipping company name, such as MSC, Maersk, or OOCL"
- For POL/POD mismatches: Explain how to correct port information

Keep clarifying questions specific and focused on ONE issue at a time:
- "What specific error message do you see when trying to track?"
- "What happens when you try to track this container on the platform?"
- "Which shipping line/carrier did you select when adding this shipment?"

ALWAYS reference documentation content when answering specific technical questions.
"""

def extract_container_numbers(text):
    """Extract container numbers from text using pattern matching"""
    # Standard container format: 4 letters followed by 7 digits
    std_container_pattern = re.compile(r'[A-Z]{4}\d{7}')
    # MSC shortened format (sometimes used): MSC followed by digits
    msc_shorthand_pattern = re.compile(r'MSC\d{7,8}')
    # Maersk shortened format
    maersk_shorthand_pattern = re.compile(r'MAE\d{7,8}')
    
    # Find all matches for each pattern
    std_containers = std_container_pattern.findall(text.upper())
    msc_containers = msc_shorthand_pattern.findall(text.upper())
    maersk_containers = maersk_shorthand_pattern.findall(text.upper())
    
    # Combine all found patterns
    all_containers = std_containers + msc_containers + maersk_containers
    
    return all_containers

def identify_carrier_from_prefix(container):
    """Identify carrier based on container prefix"""
    if not container or len(container) < 4:
        return None
        
    prefix = container[:4].upper()
    
    carrier_prefixes = {
        'MSCU': 'MSC',
        'MEDU': 'MSC',
        'MAEU': 'Maersk',
        'CMAU': 'CMA CGM',
        'OOLU': 'OOCL',
        'HLXU': 'Hapag-Lloyd',
        'UETU': 'Evergreen',
        'NYKU': 'NYK Line',
        'ZIMU': 'ZIM',
        'COSU': 'COSCO',
        'OOCU': 'COSCO',
        'AAMU': 'APL'
    }
    
    # Check if prefix is in our dictionary
    return carrier_prefixes.get(prefix, None)

def is_carrier_p1(carrier_name):
    """Determine if a carrier is P1 (fast updates) or P2 (slower updates)"""
    if not carrier_name:
        return False
        
    p1_carriers = ['MSC', 'Maersk', 'CMA CGM', 'OOCL', 'Hapag-Lloyd']
    
    # Case insensitive check
    return any(c.lower() == carrier_name.lower() for c in p1_carriers)

def determine_update_frequency(carrier_name):
    """Get the expected update frequency for a carrier"""
    if is_carrier_p1(carrier_name):
        return "3-6 hours"
    return "24-48 hours"

def parse_query_intent(message):
    """
    Parse the user query to identify action, product, feature and purpose.
    Returns a dictionary with identified categories and confidence levels.
    """
    message_lower = message.lower()
    
    # Initialize results
    result = {
        "action": {"category": None, "confidence": 0, "matches": []},
        "product": {"category": None, "confidence": 0, "matches": []},
        "feature": {"category": None, "confidence": 0, "matches": []},
        "purpose": {"category": None, "confidence": 0, "matches": []}
    }
    
    # Check for action keywords
    for action, keywords in ACTION_KEYWORDS.items():
        matches = [keyword for keyword in keywords if keyword in message_lower]
        if matches:
            confidence = len(matches) / len(message_lower.split())
            if confidence > result["action"]["confidence"]:
                result["action"] = {"category": action, "confidence": confidence, "matches": matches}
    
    # Check for product keywords
    for product, keywords in PRODUCT_KEYWORDS.items():
        matches = [keyword for keyword in keywords if keyword in message_lower]
        if matches:
            confidence = len(matches) / len(message_lower.split())
            if confidence > result["product"]["confidence"]:
                result["product"] = {"category": product, "confidence": confidence, "matches": matches}
    
    # Check for feature keywords
    for feature, keywords in FEATURE_KEYWORDS.items():
        matches = [keyword for keyword in keywords if keyword in message_lower]
        if matches:
            confidence = len(matches) / len(message_lower.split())
            if confidence > result["feature"]["confidence"]:
                result["feature"] = {"category": feature, "confidence": confidence, "matches": matches}
    
    # Check for purpose keywords
    for purpose, keywords in PURPOSE_KEYWORDS.items():
        matches = [keyword for keyword in keywords if keyword in message_lower]
        if matches:
            confidence = len(matches) / len(message_lower.split())
            if confidence > result["purpose"]["confidence"]:
                result["purpose"] = {"category": purpose, "confidence": confidence, "matches": matches}
    
    logger.info(f"Query intent analysis: {result}")
    return result

def determine_conversation_flow(intent_analysis, message, conversation_history=None):
    """
    Use the intent analysis to determine the appropriate conversation flow.
    Returns a context string and potential direct response for immediate issues.
    """
    action = intent_analysis["action"]["category"]
    product = intent_analysis["product"]["category"]
    feature = intent_analysis["feature"]["category"]
    purpose = intent_analysis["purpose"]["category"]
    
    # Handle purchase-related queries
    if action == "purchase":
        if product == "tracking":
            return {
                "context": "tracking_purchase",
                "direct_response": "Are you looking to track a single shipment or multiple shipments?",
                "examples_key": "tracking_purchase"
            }
        elif product == "port_congestion":
            return {
                "context": "port_congestion_purchase",
                "direct_response": "Our Port Congestion tool is available as part of our premium subscription plans. I can connect you with an account manager who will provide pricing details and set up a demo. What's the best email to reach you?",
                "examples_key": "port_congestion_purchase"
            }
        elif product == "co2":
            return {
                "context": "co2_purchase",
                "direct_response": "CO2 emissions tracking is a premium feature that needs to be enabled for your account. I can request your account manager to contact you about enabling this feature. Would you like me to do that?",
                "examples_key": "co2_purchase"
            }
        else:
            return {
                "context": "general_purchase",
                "direct_response": "I'd be happy to help you with purchasing our services. Could you please specify which of our products you're interested in? We offer container tracking, port congestion data, and CO2 emissions tracking.",
                "examples_key": "general_purchase"
            }
    
    # Handle tracking-related queries
    elif action == "tracking":
        if feature == "bulk_upload":
            return {
                "context": "bulk_upload",
                "direct_response": None,  # Let the existing examples handle this
                "examples_key": "bulk_upload"
            }
        elif feature == "single_track":
            return {
                "context": "single_tracking",
                "direct_response": None,  # Let the existing examples handle this
                "examples_key": "single_tracking"
            }
        else:
            # Simple tracking query - check if user has already added the shipment
            return {
                "context": "tracking_initial",
                "direct_response": "To help you track your shipment, I need to know: Have you already added this shipment to your dashboard, or are you trying to add it for the first time?",
                "examples_key": "tracking_issue_general"
            }
    
    # Handle troubleshooting queries
    elif action == "troubleshoot":
        if product == "tracking":
            return {
                "context": "tracking_issue_general",
                "direct_response": None,
                "examples_key": "tracking_issue_general"
            }
        elif "data" in message.lower() and "not" in message.lower() and "update" in message.lower():
            return {
                "context": "outdated_data_issue",
                "direct_response": None,
                "examples_key": "outdated_data_issue"
            }
        else:
            return {
                "context": "troubleshooting",
                "direct_response": "I'm sorry you're having trouble. Could you please share more details about the specific issue you're experiencing?",
                "examples_key": "troubleshooting"
            }
    
    # Handle learning/information queries
    elif action == "learn":
        if product == "port_congestion":
            return {
                "context": "port_congestion_info",
                "direct_response": "GoComet offers a Port Congestion tool that provides real-time data on delays at major ports worldwide. Free accounts get 3 weekly searches. Would you like to know more about its features or how to access it?",
                "examples_key": "port_congestion"
            }
        elif product == "co2":
            return {
                "context": "co2_emissions_info",
                "direct_response": None,
                "examples_key": "co2_emissions"
            }
        else:
            return {
                "context": "general_info",
                "direct_response": "I'd be happy to provide information. What specific aspect of our services would you like to learn more about?",
                "examples_key": "initial"
            }
    
    # Handle account-related queries
    elif action == "account":
        return {
            "context": "account_issue",
            "direct_response": None,
            "examples_key": "account_issue"
        }
    
    # Default handling for unclassified queries
    else:
        if product == "tracking":
            return {
                "context": "tracking_issue_general",
                "direct_response": None,
                "examples_key": "tracking_issue_general"
            }
        elif product == "port_congestion":
            return {
                "context": "port_congestion",
                "direct_response": None,
                "examples_key": "port_congestion"
            }
        elif product == "co2":
            return {
                "context": "co2_emissions",
                "direct_response": None,
                "examples_key": "co2_emissions"
            }
        else:
            return {
                "context": "initial",
                "direct_response": "How can I help you today? Are you looking for information about tracking shipments, port congestion data, or something else?",
                "examples_key": "initial"
            }

def get_current_context(conversation_history):
    """Determine the conversation context from history with improved pattern matching"""
    lower_history = conversation_history.lower()
    
    # Check for rejection patterns
    recent_exchanges = lower_history.split("\n\n")[-4:]  # Look at last 2 exchanges
    recent_text = "\n".join(recent_exchanges).lower()
    
    # Detect rejection/correction patterns
    rejection_phrases = [
        "no, i have not", "no i haven't", "no i have not", 
        "haven't added", "have not added", "no,", "not yet", 
        "i didn't", "i did not"
    ]
    
    # If user rejected something in their last message, reset or adjust context
    for phrase in rejection_phrases:
        if phrase in recent_text:
            # Check what was being rejected to determine proper context reset
            if "mode" in recent_text or "carrier" in recent_text or "ocean or air" in recent_text:
                return "pre_tracking_input"
            if "added" in recent_text and "shipment" in recent_text:
                return "need_tracking_instructions"
    
    # Enhanced tracking issue detection
    tracking_issue_phrases = ["can't track", "cannot track", "trouble tracking", "not tracking", 
                            "tracking not working", "invalid tracking", "no data", "no tracking data"]
    
    # Check for frustration indicators
    frustration_phrases = ["frustrat", "upset", "angry", "annoyed", "ridiculous", 
                          "waste of time", "useless", "not working", "doesn't work",
                          "cancel", "refund", "subscription"]
    
    # Check for purchase related keywords
    purchase_phrases = ["buy", "purchase", "subscription", "subscribe", "cost", "price", "pricing"]
    purchase_context = False
    for phrase in purchase_phrases:
        if phrase in lower_history:
            purchase_context = True
            break
            
    # If purchasing context is detected
    if purchase_context:
        if "port congestion" in lower_history:
            return "port_congestion_purchase"
        elif "co2" in lower_history or "carbon" in lower_history or "emission" in lower_history:
            return "co2_purchase"
        elif "track" in lower_history or "container" in lower_history:
            return "tracking_purchase"
        else:
            return "general_purchase"
    
    # Check for initial tracking issues
    for phrase in tracking_issue_phrases:
        if phrase in lower_history:
            # This is the initial problem statement
            if "where" in lower_history or "how" in lower_history:
                # They're asking how to track
                return "need_tracking_instructions"
            elif any(fp in lower_history for fp in frustration_phrases):
                # User is frustrated with tracking
                return "tracking_issue_frustrated"
            else:
                # Default to tracking issue without specifics
                return "tracking_issue_general"
    
    # Check for specific tracking number formats
    if any(word in lower_history for word in ["msc", "maeu", "hlxu", "oolu"]) and any(char.isdigit() for char in lower_history):
        return "analyzing_tracking_number"
    
    # Check for auto-detect issues
    if "auto-detect" in lower_history or "autodetect" in lower_history:
        return "autodetect_issue"
        
    # Check for port congestion inquiries
    if "port" in lower_history and ("congestion" in lower_history or "delay" in lower_history):
        return "port_congestion"
        
    # Check for CO2 emissions inquiries
    if "co2" in lower_history or "carbon" in lower_history or "emission" in lower_history:
        return "co2_emissions"
    
    # Standard context detection
    if "bulk upload" in lower_history:
        return "bulk_upload"
    elif "single shipment" in lower_history or "single container" in lower_history:
        return "single_tracking"
    elif "carrier field is missing" in lower_history or "carrier is mandatory" in lower_history:
        return "carrier_issue"
    elif "password" in lower_history or "login" in lower_history or "account" in lower_history:
        return "account_issue"
    elif "bol" in lower_history or "bill of lading" in lower_history:
        return "bol_tracking" 
    elif "autofix" in lower_history or "pol" in lower_history and "pod" in lower_history:
        return "pol_pod_issue"
    elif "arrived" in lower_history and "still" in lower_history:
        return "outdated_data_issue"
    else:
        return "initial"

# Global cache for loaded docs to avoid reading files repeatedly
_docs_cache = {}
_conversations_cache = None

def load_all_docs_as_string(docs_dir=os.path.join(os.path.dirname(__file__), "../docs")):
    """Load all documentation files with improved caching and preprocessing for semantic understanding"""
    global _docs_cache
    
    # Use cached version if available
    cache_key = docs_dir
    if cache_key in _docs_cache:
        logger.info("Using cached documentation")
        return _docs_cache[cache_key]
    
    logger.info(f"Looking for docs in: {docs_dir}")
    if not os.path.exists(docs_dir):
        logger.error(f"Docs directory not found: {docs_dir}")
        return """
# MANDATORY FIELDS AND REQUIREMENTS

## Adding a Single Shipment
When adding a shipment for tracking, these fields are MANDATORY:
- Mode (Ocean or Air)
- Shipping line/Carrier (name of the shipping company carrying the container)
- MBL/Container Number (tracking number in correct format)

## Common Tracking Issues
- "Can't find my shipment" - Make sure the tracking number and carrier name are entered correctly
- "No updates showing" - Updates can take 24-48 hours to appear in the system
- "Invalid tracking number" - Container numbers must be in the format of 4 letters + 7 digits (ABCD1234567)
"""
    
    # Organize documentation by topics for better retrieval
    organized_docs = {
        "adding_shipments": [],
        "tracking_issues": [], 
        "bulk_upload": [],
        "account_issues": [],
        "general": []
    }
    
    # Add built-in knowledge base about common issues and solutions
    built_in_kb = """
# COMMON TRACKING ISSUES AND SOLUTIONS

## Issue: Can't Track a Shipment
If you're having trouble tracking a shipment, check these common causes:

1. **Shipment Not Added**: You need to add the shipment to your dashboard first
   - Go to your dashboard
   - Click the "Add Tracking" button
   - Enter all required details

2. **Incorrect Tracking Number**: The format must match the carrier requirements
   - Container numbers: 4 letters + 7 digits (Example: MSCU1234567)
   - Air waybills: 3 digits + 8 digits (Example: 123-12345678)

3. **Wrong Carrier Selected**: Verify you selected the correct shipping line/airline
   - Choose from the dropdown menu options
   - Don't manually type a carrier that's not in the system

4. **System Delay**: Sometimes new shipments take 24-48 hours to appear
   - Add your shipment and check back later if it's very recent

## Process for Adding a Shipment
1. Log in to your account
2. Go to your dashboard
3. Click the "Add Tracking" button (blue button, top-right)
4. Select the shipping Mode (Ocean or Air)
5. Choose your Carrier from the dropdown
6. Enter the Tracking/Container number
7. Click "Submit"
"""
    organized_docs["tracking_issues"].append(built_in_kb)
    
    # Extract key information about mandatory fields
    mandatory_fields_info = """
# MANDATORY FIELDS AND REQUIREMENTS

## Adding a Single Shipment
When adding a shipment for tracking, these fields are MANDATORY:
- Mode (Ocean or Air)
- Shipping line/Carrier (name of the shipping company carrying the container)
- MBL/Container Number (tracking number in correct format)

## Bulk Upload Requirements
For bulk uploading, these columns are MANDATORY:
- Column A: Mode (Ocean or Air)
- Column C: Tracking Number (BL, Booking or Container Number)
- Column D: Carrier (shipping line/airline name)

## Common Error Resolutions
- "Carrier is not found" or "Carrier is mandatory" - You must select a valid carrier/shipping line name
- "Invalid Tracking Number" - Format must be correct (4 letters + 7 digits for containers)
- "Format does not match" - Check that your tracking ID follows the carrier's format
"""
    organized_docs["general"].append(mandatory_fields_info)
    
    # Process all documents in the docs directory
    if os.path.exists(docs_dir):
        for filename in os.listdir(docs_dir):
            if filename.endswith(".md") or filename.endswith(".txt"):
                file_path = os.path.join(docs_dir, filename)
                logger.info(f"Loading document: {file_path}")
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        # Extract document title from first heading or use filename
                        doc_title = filename
                        if content.startswith("# "):
                            doc_title = content.split("\n")[0].replace("# ", "").strip()
                        
                        # Process content to ensure links are properly formatted
                        processed_content = content
                        
                        # Add document metadata
                        doc_header = f"# {doc_title}\n\n_Source: {filename}_\n\n"
                        full_doc = doc_header + processed_content
                        
                        # Categorize documents based on content and filename
                        lower_content = content.lower()
                        lower_filename = filename.lower()
                        
                        if "track" in lower_content or "track" in lower_filename:
                            organized_docs["tracking_issues"].append(full_doc)
                        elif "upload" in lower_content or "bulk" in lower_filename:
                            organized_docs["bulk_upload"].append(full_doc)
                        elif "account" in lower_content or "login" in lower_filename or "password" in lower_filename:
                            organized_docs["account_issues"].append(full_doc)
                        elif "add" in lower_content or "shipment" in lower_filename:
                            organized_docs["adding_shipments"].append(full_doc)
                        else:
                            organized_docs["general"].append(full_doc)
                            
                        logger.info(f"Successfully loaded {filename} ({len(content)} chars)")
                except Exception as e:
                    logger.error(f"Error reading {filename}: {str(e)}")
    
    # Combine all docs with category headers for better context
    all_docs = []
    
    for category, docs in organized_docs.items():
        if docs:
            category_header = f"# {category.replace('_', ' ').title()}\n\n"
            all_docs.append(category_header + "\n\n".join(docs))
    
    result = "\n\n".join(all_docs)
    logger.info(f"Total documentation size: {len(result)} characters")
    
    # Cache the result
    _docs_cache[cache_key] = result
    return result

def load_past_conversations():
    """Load past human conversations for training the agent"""
    global _conversations_cache
    
    if _conversations_cache is not None:
        return _conversations_cache
        
    # Path to the conversations file
    conv_file = os.path.join(os.path.dirname(__file__), "../past_conversations.json")
    
    try:
        if os.path.exists(conv_file):
            try:
                with open(conv_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    conversations = data.get('conversations', {})
                    
                    # Format conversations as dictionary
                    _conversations_cache = conversations
                    logger.info(f"Loaded {len(conversations)} past conversations for training")
                    return _conversations_cache
            except json.JSONDecodeError as e:
                # Try to repair common JSON errors and retry loading
                logger.warning(f"JSON error in past_conversations.json: {str(e)}. Attempting to repair...")
                try:
                    # Fall back to a simpler approach - load built-in example conversations
                    return get_fallback_conversations()
                except Exception as inner_e:
                    logger.error(f"Failed to repair JSON: {str(inner_e)}")
                    return get_fallback_conversations()
        else:
            logger.warning("No past conversations file found")
            return get_fallback_conversations()
    except Exception as e:
        logger.error(f"Error loading past conversations: {e}")
        return get_fallback_conversations()

def get_fallback_conversations():
    """Provide fallback conversation examples when JSON loading fails"""
    fallback_examples = """
# Example Tracking Conversation:
User: I can't track my shipment
Agent: I understand you're having trouble tracking your shipment. Have you already added this shipment to your dashboard, or are you trying to add it for the first time?
User: I don't know how to add it
Agent: To add a shipment, go to your dashboard and click the "Add Tracking" button. You'll need to enter the carrier name, container number, and select Air/Ocean mode.

# Example Invalid Tracking Conversation:
User: I'm getting an invalid tracking number error
Agent: I'm sorry about that error. Container numbers must be 4 letters followed by 7 digits (like MSCU1234567). Can you verify if your tracking number follows this format?
User: My tracking is MSC12345678
Agent: I see the issue. For MSC containers, they usually start with 'MSCU' or 'MEDU' followed by 7 digits. Could this be a booking reference rather than a container number?

# Example Tracking Update Time Conversation:
User: The data is not updated
Agent: I understand you're seeing outdated information. Updates depend on the carrier - P1 carriers like Maersk update every 3-6 hours, while others may take 24-48 hours. Which carrier are you using?
User: MSCU7656654
Agent: For MSC containers like yours, updates typically occur every 3-6 hours. If you're not seeing updates, there might be a delay from the carrier. When did you add this to your dashboard?

# Example Bulk Upload Conversation:
User: I want to buy your tracking
Agent: I'd be happy to explain our tracking options. Are you interested in tracking a single shipment or using our bulk upload feature?
User: bulk upload
Agent: For bulk upload, you'll need our Excel template. Have you downloaded it from your dashboard yet? If not, go to the tracking section and click on "Bulk Upload" to find it.

# Example Container Location Conversation:
User: Where is my container MAEU1234567?
Agent: I understand you want to locate your container. To check MAEU1234567's location, please log into your dashboard and view the tracking details there. Have you already added this container?
User: Yes, I added it yesterday but I can't find the location information
Agent: If you've added the container but don't see location data, it could be because the carrier hasn't updated yet, the container is between tracking points, or there's an issue with the carrier information. Check the "Last Updated" timestamp on your dashboard.

# Example Link Assistance Conversation:
User: Where can I find the bulk upload template?
Agent: You can find the bulk upload template in your dashboard. Could you let me know which version of the platform you're using so I can provide the exact navigation steps?
User: I'm using the new version
Agent: Great! In the new version, go to your dashboard, click on "Shipments" in the main menu, then look for the "Bulk Actions" dropdown in the top right corner. Select "Download Bulk Template" from there. If you have trouble finding it, could you share a screenshot of your dashboard?
"""
    logger.info("Using fallback conversation examples")
    return fallback_examples

def generate_thinking_step(message, email, conversation_history, context, docs_content, conversations_text, container_numbers, intent_analysis, message_contains_email):
    """
    Generate a thinking step to analyze the query before responding.
    This helps the agent methodically process the user's request and identify the best approach.
    """
    logging.info("Performing thinking step to analyze query...")
    
    thinking_prompt = f"""You are a customer support agent for a shipment tracking platform.
    
THINKING STEP: This is your opportunity to analyze the user's query in depth before responding.

User email: {email}
Current conversation:
{conversation_history}
User: {message}

Detected context: {context}
Detected container numbers: {container_numbers}
Intent analysis: {intent_analysis}
Contains email: {message_contains_email}

1. QUERY UNDERSTANDING:
   - What is the user specifically asking for?
   - What implicit needs might they have beyond their explicit request?
   - What emotions or urgency can you detect in their message?

2. CONTEXT ANALYSIS:
   - How does this query relate to previous messages (if any)?
   - Is the user following up on a previous issue or starting a new topic?
   - What stage of problem-solving are they in? (initial inquiry, troubleshooting, verification)

3. INFORMATION GATHERING:
   - What relevant information do I already have?
   - What critical information is missing that I need to ask for?
   - What documentation is most relevant to this query?

4. SOLUTION IDENTIFICATION:
   - What are the possible solutions to address their need?
   - What is the most direct path to resolution?
   - Are there alternative approaches I should mention?
   - What follow-up steps might be needed after my response?

5. RESPONSE PLANNING:
   - What tone should I use? (helpful, technical, empathetic, instructional)
   - What specific documentation or examples should I reference?
   - What specific steps should I recommend?
   - How should I structure my response for maximum clarity?

Based on your analysis, provide a detailed thinking process that outlines your understanding and approach.
"""

    # Add snippets of relevant documentation
    if docs_content:
        thinking_prompt += f"\n\nRelevant documentation:\n{docs_content[:1000]}...\n"
    
    # Add snippets of similar conversations
    if conversations_text:
        thinking_prompt += f"\n\nExample conversations:\n{conversations_text[:1000]}...\n"
    
    # Generate thinking response
    thinking_response = get_gemini_response(thinking_prompt)
    
    # Log the thinking process
    logging.info(f"Thinking step complete: {thinking_response[:200]}...")
    
    return thinking_response

def handle_info(message, email, conversation_history=""):
    """Process a user message and return an appropriate response."""
    logging.info(f"Processing message: {message}")
    logging.info(f"User email: {email}")
    
    # Log conversation history length for debugging
    logging.info(f"Conversation history length: {len(conversation_history)}")
    
    # Check for casual conversation patterns
    casual_conversation = is_casual_conversation(message)
    
    # If this is casual conversation, respond in a friendly way without technical context
    if casual_conversation:
        prompt = generate_casual_conversation_prompt(message, email, conversation_history)
        response = get_gemini_response(prompt)
        logging.info(f"Generated casual response for message: {message[:30]}...")
        return response
    
    # For regular customer support queries, continue with normal processing
    # Get intent analysis for the message
    intent_analysis = parse_intent(message)
    
    # Extract container numbers from the message
    container_numbers = extract_container_numbers(message)
    logging.info(f"Detected containers: {container_numbers}")
    
    # Check for email within the message
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    message_contains_email = bool(re.search(email_pattern, message))
    logging.info(f"Message contains email: {message_contains_email}")
    
    # Determine the context of the conversation
    context = determine_context(intent_analysis, message, conversation_history)
    logging.info(f"Conversation context: {context}")
    
    # Load documentation based on context
    docs_content = ""
    if "tracking" in context or "container" in context:
        docs_content = load_documentation("container_tracking.md")
    elif "account" in context:
        docs_content = load_documentation("account_setup_and_management.md")
    elif context == "port_congestion":
        docs_content = load_documentation("port_congestion.md")
    elif context == "co2_emissions":
        docs_content = load_documentation("co2_emissions.md")
    
    # Load past conversations
    past_conversations = load_past_conversations()
    
    # Map contexts to relevant issue types in past conversations
    context_to_issue_map = {
        "tracking_initial": ["tracking", "container_status"],
        "tracking_issue_general": ["tracking", "invalid_tracking", "multiple_containers"],
        "tracking_issue_frustrated": ["tracking", "invalid_tracking", "no_tracking_data"],
        "tracking_issue_email": ["tracking", "no_tracking_data", "email_tracking"],
        "multiple_container_tracking": ["multiple_containers", "bulk_upload"],
        "initial_tracking_issue": ["no_tracking_data", "invalid_tracking"],
        "invalid_tracking": ["invalid_tracking", "tracking"],
        "outdated_data_issue": ["outdated_data", "tracking"],
        "account_issue": ["account_setup", "account_login"],
        "account_issue_email": ["account_setup", "account_login", "email_account"],
        "account_issue_frustrated": ["account_setup", "account_login"],
        "account_blocked": ["account_login", "account_blocked"],
        "general_purchase": ["pricing", "feature_request"],
        "purchase_email": ["pricing", "feature_request", "email_purchase"],
        "customer_frustrated": ["no_tracking_data", "invalid_tracking", "account_blocked"],
        "general_email": ["account_setup", "feature_request", "email_general"],
        "co2_emissions": ["co2_emissions", "feature_request"],
        "port_congestion": ["port_congestion", "tracking"],
        "single_tracking": ["tracking", "container_status"],
        "bulk_upload": ["multiple_containers", "bulk_upload"]
    }
    
    # Get relevant issue types for the current context
    relevant_issue_types = context_to_issue_map.get(context, ["tracking", "general"])
    
    # Filter past conversations by relevancy
    relevant_conversations = []
    
    # Handle different types of past_conversations
    if isinstance(past_conversations, dict):
        # Dictionary format from JSON
        for conv_id, conv_data in past_conversations.items():
            if isinstance(conv_data, dict) and conv_data.get("issue_type") in relevant_issue_types:
                conv_text = conv_data.get("conversation", "")
                if isinstance(conv_text, str) and conv_text:
                    relevant_conversations.append(conv_text)
    elif isinstance(past_conversations, str):
        # String format (fallback conversations)
        relevant_conversations.append(past_conversations)
    else:
        # Fallback to empty list
        relevant_conversations = []
    
    # If no relevant conversations, use fallbacks
    if not relevant_conversations:
        fallback_text = get_fallback_conversations()
        relevant_conversations.append(fallback_text)
    
    # Join relevant conversations
    conversations_text = "\n\n".join(relevant_conversations)
    
    # Create full conversation history including the current message
    full_conversation = conversation_history
    if full_conversation and not full_conversation.endswith("\n"):
        full_conversation += "\n"
    
    # STEP 1: Perform the thinking step to analyze the query
    thinking_output = generate_thinking_step(
        message=message,
        email=email,
        conversation_history=full_conversation,
        context=context,
        docs_content=docs_content,
        conversations_text=conversations_text,
        container_numbers=container_numbers,
        intent_analysis=intent_analysis,
        message_contains_email=message_contains_email
    )
    
    # STEP 2: Generate the response based on thinking analysis
    # Add the current message to the conversation for response generation
    full_conversation += f"User: {message}"
    
    # Generate a prompt for Gemini
    prompt = f"""You are a helpful customer support agent for a shipment tracking platform.
User email from account: {email}
Current conversation:
{full_conversation}

Context of the conversation: {context}

Documentation:
{docs_content}

Examples of similar past conversations:
{conversations_text}

THINKING ANALYSIS:
{thinking_output}

IMPORTANT COMMUNICATION GUIDELINES:
1. Always maintain a warm, friendly tone even when delivering technical information
2. Never sound rude, dismissive, or impatient - even if the customer's question seems basic
3. Avoid saying "please finish your sentence" or similar phrases that could come across as curt
4. If a user provides an incomplete input, gently ask for clarification without making them feel judged
5. Acknowledge the user's input even if it's partial - try to understand their intent from context
6. When asking for more information, explain briefly why it's needed
7. Use natural, conversational language rather than robotic or formal phrasing
8. If the user is transitioning away from a previous topic, follow their lead naturally
9. FORMAT RESPONSES FOR READABILITY:
   - Use short paragraphs (1-2 sentences max)
   - Put key information on separate lines
   - Use blank lines between different topics
   - Don't create walls of text
   - If listing steps, use numbered points on separate lines
   - Keep overall response concise and scannable

CHAT FORMATTING REQUIREMENTS:
1. NEVER format responses as emails with subject lines, greetings like "Dear [user]", or signatures
2. DO NOT use any email formatting elements (Subject, To, From, Sincerely, etc.)
3. NEVER address users by their email address
4. ALWAYS use a conversational chat style like you're talking in real time
5. Keep responses brief and direct like a chat message, not a formal letter
6. DO NOT include email signatures or company name at the end of responses
7. DO NOT use "Dear webuser_xxx" or any formal greeting with user ID
8. NEVER say "I will update you via email" - provide direct help in the current chat
9. DO NOT structure as a business letter with headers and signatures

LINK HANDLING:
1. DO provide helpful, direct links to GoComet resources when they would solve the user's problem
2. Format links clearly as [Link text](URL) to make them easy to click
3. When providing a link, briefly explain what the user will find there
4. Use this format for common issues:
   - Adding shipments: [Add a shipment](https://app.gocomet.com/tracking)
   - Bulk upload: [Bulk upload](https://app.gocomet.com/tracking)
   - Account setup: [Account management](https://app.gocomet.com/profile)
   - Port congestion: [Port congestion](https://www.gocomet.com/real-time-port-congestion)
   - Tracking dashboard: [Tracking dashboard](https://app.gocomet.com/?dashboard=menu-tracking)
5. DO NOT invent or make up links - only use the standard links listed above

LINK HANDLING:
1. NEVER include any kind of hyperlinks in your responses
2. Do not use the format [text](url) under any circumstances
3. Instead, provide descriptive text: "Go to your dashboard" or "Use the Add Shipment button"
4. Provide navigation instructions as plain text: "Navigate to Dashboard, then Tracking, then View Shipments"
5. NEVER reference URLs, even in plain text - use feature names and locations instead

Based on the above thinking analysis and information, please provide a helpful, accurate, and concise response to the user's message.
"""

    # For email contexts, add specialized instructions
    if "email" in context or message_contains_email:
        email_in_message = re.search(email_pattern, message)
        email_address = email_in_message.group(0) if email_in_message else "their email"
        
        prompt += f"""
This user has included an email address ({email_address}) in their message. For context '{context}', respond appropriately by:
1. Acknowledging the email address without formal email structure
2. Explaining what actions will be taken with this information
3. Setting expectations but in a chat conversation style, not email format
4. Keeping the tone conversational and direct
5. NEVER formatting your response as an email - keep it as a natural chat message
"""
    
    # For frustrated customers, add specialized instructions
    if "frustrated" in context:
        prompt += """
The user appears frustrated. Make sure to:
1. Acknowledge their frustration empathetically without being formulaic
2. Offer clear, concrete solutions with specific steps
3. Focus on what CAN be done, not limitations
4. Provide extra detail on next steps to rebuild trust
5. Be extra thorough in your explanation
6. Mention escalation paths if the immediate solution doesn't resolve their issue
7. Keep your tone conversational and helpful, not formal or corporate
"""

    # Add special handling for multiple containers
    if "multiple_container" in context and container_numbers:
        prompt += f"""
The user has mentioned multiple containers: {', '.join(container_numbers)}
For each container, provide:
1. Specific status information if available
2. Different possible resolutions based on the container's carrier and status
3. Batch processing options if applicable
"""

    # If user has confirmed an option, acknowledge their choice
    if check_if_confirmation_of_agent_suggestion(message, get_last_agent_response(conversation_history)):
        prompt += """
The user has selected or confirmed an option you presented in your previous message.
Make sure to:
1. Acknowledge their selection clearly
2. Show continuity by referring back to what they confirmed
3. Move the conversation forward with the next logical step
4. Be specific about what happens now with their selection
"""

    # Call the Gemini API to generate a response
    response = get_gemini_response(prompt)
    
    # Log the response for debugging
    logging.info(f"Generated response for context '{context}': {response[:100]}...")
    
    return response

def get_last_agent_response(conversation_history):
    """Extract the last agent response from conversation history."""
    if not conversation_history:
        return ""
        
    agent_responses = re.findall(r"Agent: (.*?)(?=\n(?:Agent|User):|$)", conversation_history, re.DOTALL)
    
    if agent_responses:
        return agent_responses[-1].strip()
    
    return ""

def load_documentation(filename):
    """Load a specific documentation file"""
    docs_dir = os.path.join(os.path.dirname(__file__), "../docs")
    file_path = os.path.join(docs_dir, filename)
    
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading documentation file {filename}: {str(e)}")
    
    return ""

def get_gemini_response(prompt):
    """Generate a response using the Gemini model"""
    try:
        logger.info("Sending request to Gemini...")
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        logger.info("Successfully generated response")
        return response.text
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        return "I apologize, but I'm having trouble generating a response right now. Could you please try again?"

def generate_response(prompt):
    """Generate a response using the Gemini model"""
    try:
        logger.info("Sending request to Gemini...")
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        logger.info("Successfully generated response")
        return response.text
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        return "I apologize, but I'm having trouble generating a response right now. Could you please try again?"

def find_similar_conversations(message, context):
    """Find similar past conversations based on context and message content"""
    try:
        past_conversations = load_past_conversations()
        if not past_conversations:
            return ""
        
        # For now, just return the loaded conversations as we don't have
        # a sophisticated similarity search yet
        return past_conversations
    except Exception as e:
        logger.error(f"Error finding similar conversations: {str(e)}")
        return ""

def parse_intent(message):
    """
    Parse the user's message to identify action, product, feature, and purpose.
    Returns a dictionary with identified intent categories.
    """
    message_lower = message.lower()
    
    # Initialize intent analysis structure
    intent_analysis = {
        "action": {"category": None, "confidence": 0},
        "product": {"category": None, "confidence": 0},
        "feature": {"category": None, "confidence": 0},
        "purpose": {"category": None, "confidence": 0}
    }
    
    # Define keyword categories
    ACTION_KEYWORDS = {
        "purchase": ["buy", "purchase", "subscribe", "pricing", "cost", "price", "how much", "get access"],
        "tracking": ["track", "locate", "find", "where is", "status", "update", "follow", "trace"],
        "troubleshoot": ["fix", "solve", "resolve", "issue", "problem", "error", "trouble", "not working", "doesn't work", "can't"],
        "learn": ["how", "explain", "tell me", "what is", "guide", "tutorial", "learn", "understand"],
        "account": ["login", "sign in", "account", "profile", "settings", "configure"]
    }
    
    PRODUCT_KEYWORDS = {
        "tracking": ["tracking", "shipment", "container", "cargo", "freight", "delivery", "package"],
        "port_congestion": ["port", "congestion", "delay", "terminal", "harbor", "dock"],
        "co2": ["co2", "carbon", "emission", "environmental", "footprint", "sustainability"],
        "account": ["account", "profile", "subscription", "plan"]
    }
    
    FEATURE_KEYWORDS = {
        "alerts": ["alert", "notification", "update", "inform", "message"],
        "autodetect": ["autodetect", "auto-detect", "auto detect", "automatic", "detect"],
        "bulk_upload": ["bulk", "upload", "excel", "csv", "multiple", "batch"],
        "dashboard": ["dashboard", "overview", "summary", "report", "view"],
        "billing": ["bill", "invoice", "payment", "charge", "fee"]
    }
    
    PURPOSE_KEYWORDS = {
        "information": ["know", "learn", "explain", "understand", "information", "details", "tell me"],
        "resolution": ["fix", "solve", "resolve", "help", "support", "assist"],
        "purchase": ["buy", "order", "get", "acquire", "purchase"],
        "complaint": ["complain", "unhappy", "disappointed", "not satisfied", "problem", "issue"]
    }
    
    # Analyze action keywords
    for category, keywords in ACTION_KEYWORDS.items():
        for keyword in keywords:
            if keyword in message_lower:
                # If finding a more specific match or first match
                if intent_analysis["action"]["confidence"] < len(keyword):
                    intent_analysis["action"]["category"] = category
                    intent_analysis["action"]["confidence"] = len(keyword)
    
    # Analyze product keywords
    for category, keywords in PRODUCT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in message_lower:
                # If finding a more specific match or first match
                if intent_analysis["product"]["confidence"] < len(keyword):
                    intent_analysis["product"]["category"] = category
                    intent_analysis["product"]["confidence"] = len(keyword)
    
    # Analyze feature keywords
    for category, keywords in FEATURE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in message_lower:
                # If finding a more specific match or first match
                if intent_analysis["feature"]["confidence"] < len(keyword):
                    intent_analysis["feature"]["category"] = category
                    intent_analysis["feature"]["confidence"] = len(keyword)
    
    # Analyze purpose keywords
    for category, keywords in PURPOSE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in message_lower:
                # If finding a more specific match or first match
                if intent_analysis["purpose"]["confidence"] < len(keyword):
                    intent_analysis["purpose"]["category"] = category
                    intent_analysis["purpose"]["confidence"] = len(keyword)
    
    return intent_analysis

def determine_context(intent_analysis, message, conversation_history):
    """Determine the context of the conversation from intent analysis and message content."""
    # Join all user messages to analyze content patterns
    all_user_messages = ""
    previous_agent_response = ""
    
    if conversation_history:
        # Extract all user messages and the last agent response from conversation history
        user_messages = re.findall(r"User: (.*?)(?=\n(?:Agent|User):|$)", conversation_history, re.DOTALL)
        agent_responses = re.findall(r"Agent: (.*?)(?=\n(?:Agent|User):|$)", conversation_history, re.DOTALL)
        
        all_user_messages = " ".join(user_messages)
        
        # Get the most recent agent response if available
        if agent_responses:
            previous_agent_response = agent_responses[-1].strip()
    
    # Add current message
    all_user_messages += " " + message
    all_user_messages = all_user_messages.lower()
    
    # Extract container numbers from the last user message
    container_numbers = extract_container_numbers(message)
    
    # Initialize context as general
    context = "general"
    
    # Check if the user's message is acknowledging a suggestion from the previous agent response
    # This helps with cases where user responds with brief confirmations like "yes", "ok", "one by one"
    is_confirmation = check_if_confirmation_of_agent_suggestion(message, previous_agent_response)
    
    # Check for email-related queries
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    contains_email = bool(re.search(email_pattern, message))
    
    # Check for tracking-related context
    tracking_pattern = r'\b(track|container|shipment|cargo|consignment|freight|vessel|shipping)\b'
    is_tracking_related = bool(re.search(tracking_pattern, all_user_messages, re.IGNORECASE))
    
    # Check for account-related context
    account_pattern = r'\b(account|login|signin|username|password|portal|dashboard|access)\b'
    is_account_related = bool(re.search(account_pattern, all_user_messages, re.IGNORECASE))
    
    # Check for data/update issues
    update_pattern = r'\b(outdated|old|stale|not\s+updating|no\s+update|refresh|latest)\b'
    is_update_issue = bool(re.search(update_pattern, all_user_messages, re.IGNORECASE))
    
    # Check for invalid tracking issues
    invalid_pattern = r'\b(invalid|error|not\s+found|cannot\s+find|doesn\'t\s+exist)\b'
    is_invalid_issue = bool(re.search(invalid_pattern, all_user_messages, re.IGNORECASE))
    
    # Check for frustration indicators
    frustration_pattern = r'\b(frustrat|annoy|angry|upset|ridiculous|terrible|horrible|awful|disappointed|unhappy|not\s+working|can\'t\s+believe|useless)\b'
    is_frustrated = bool(re.search(frustration_pattern, all_user_messages, re.IGNORECASE))
    
    # Check for purchase/payment related context
    purchase_pattern = r'\b(buy|purchase|price|cost|payment|subscribe|plan|package|upgrade)\b'
    is_purchase_related = bool(re.search(purchase_pattern, all_user_messages, re.IGNORECASE))
    
    # Check for team management related context
    team_pattern = r'\b(team|member|user|add user|add team|create team|user access|permission|role|team management)\b'
    is_team_related = bool(re.search(team_pattern, all_user_messages, re.IGNORECASE))
    
    # If user is confirming a suggestion about a specific context from the agent's last response,
    # maintain that context rather than resetting to general
    if is_confirmation:
        if "bulk" in previous_agent_response.lower() and "single" in previous_agent_response.lower():
            if "bulk" in message.lower():
                context = "bulk_upload"
            elif any(word in message.lower() for word in ["single", "one", "individual"]):
                context = "single_tracking"
        elif "tracking" in previous_agent_response.lower():
            context = "tracking_initial"
        elif "account" in previous_agent_response.lower():
            context = "account_issue"
        else:
            # Default to tracking context for common confirmations in response to tracking questions
            context = "tracking_initial"
    elif contains_email:
        if is_tracking_related:
            context = "tracking_issue_email"
        elif is_account_related:
            context = "account_issue_email"
        elif is_purchase_related:
            context = "purchase_email"
        else:
            context = "general_email"
    elif is_tracking_related:
        if len(container_numbers) > 1:
            context = "multiple_container_tracking"
        elif len(container_numbers) == 1:
            if is_invalid_issue:
                context = "invalid_tracking"
            elif is_update_issue:
                context = "outdated_data_issue"
            elif re.search(r"can'?t\s+track|track.*not\s+working|unable\s+to\s+track|trouble\s+tracking", all_user_messages, re.IGNORECASE):
                context = "initial_tracking_issue"
            else:
                context = "tracking_initial"
        else:
            # No container numbers provided but tracking related
            context = "tracking_issue_general"
    elif is_account_related:
        if re.search(r"blocked|locked|can't\s+access|password\s+reset", all_user_messages, re.IGNORECASE):
            context = "account_blocked"
        else:
            context = "account_issue"
    elif is_team_related:
        if re.search(r"existing user|different group|add existing", all_user_messages, re.IGNORECASE):
            context = "team_management_existing"
        elif re.search(r"create team|new team", all_user_messages, re.IGNORECASE):
            context = "team_management_create"
        else:
            context = "team_management"
    elif is_purchase_related:
        context = "general_purchase"
    elif intent_analysis["product"]["category"] == "port_congestion":
        context = "port_congestion"
    elif intent_analysis["product"]["category"] == "co2":
        context = "co2_emissions"
    elif intent_analysis["action"]["category"] == "troubleshoot":
        context = "troubleshooting"
    
    # Override with frustration context if needed
    if is_frustrated:
        if "tracking" in context or "container" in context:
            context = "tracking_issue_frustrated"
        elif "account" in context:
            context = "account_issue_frustrated"
        elif context == "general":
            context = "customer_frustrated"
        # For other contexts, we'll handle frustration in the response but keep the specialized context
    
    logging.info(f"Determined context: {context} (Email: {contains_email}, Tracking: {is_tracking_related}, Account: {is_account_related}, Frustrated: {is_frustrated})")
    return context

def check_if_confirmation_of_agent_suggestion(user_message, agent_response):
    """
    Check if the user's message is confirming a suggestion or option presented 
    by the agent in the previous response.
    """
    if not agent_response:
        return False
        
    # Lowercase for easier comparison
    user_message = user_message.lower().strip()
    agent_response = agent_response.lower()
    
    # Common confirmation phrases
    confirmation_phrases = [
        "yes", "yeah", "yep", "ok", "okay", "sure", "fine", 
        "good", "correct", "right", "that's right", "exactly",
        "i have", "i did", "i do", "done", "added", "completed"
    ]
    
    # If user message is a simple confirmation
    if user_message in confirmation_phrases or user_message.startswith(tuple(confirmation_phrases)):
        return True
        
    # Check if agent offered options and user selected one
    if "or" in agent_response:
        options = extract_options_from_agent_response(agent_response)
        for option in options:
            # If user's message contains an option (checking for partial matches like "one by one")
            if option in user_message or any(word in user_message for word in option.split()):
                return True
                
    return False
    
def extract_options_from_agent_response(response):
    """Extract possible options presented by the agent in their response."""
    options = []
    
    # Check for "X or Y" patterns
    or_patterns = re.findall(r'(\w+(?:\s+\w+){0,5})\s+or\s+(\w+(?:\s+\w+){0,5})', response)
    for pattern in or_patterns:
        options.extend(pattern)
        
    # Check for options in a question
    option_patterns = [
        "bulk upload", "single shipment", "one by one", "multiple shipments",
        "add it", "already added", "tracking number", "container number"
    ]
    
    for pattern in option_patterns:
        if pattern in response:
            options.append(pattern)
            
    return options

def get_context_examples(context):
    """
    Return specific examples based on the conversation context.
    Enhanced with more context-aware and solution-focused examples.
    """
    examples = {
        "initial_tracking_issue": {
            "example": [
                "User: I can't track my shipment",
                "Agent: I'm sorry to hear that. Could you tell me what specific issue you're facing with tracking? For example, are you getting an error message, or is the information not showing up correctly?",
                "User: It says shipment invalid",
                "Agent: I understand. Could you please share the tracking number that's showing as invalid? Also, which carrier are you using for this shipment?"
            ]
        },
        "tracking_issue_general": {
            "example": [
                "User: I need to track my container",
                "Agent: I'd be happy to help you track your container. Could you please provide the container number or Bill of Lading number?",
                "User: MSCU1234567",
                "Agent: Thank you. I'll help you track container MSCU1234567. Have you already added this container to your dashboard for tracking?",
                "User: No",
                "Agent: To track container MSCU1234567, you'll need to add it to your dashboard first. Go to your dashboard, click on the \"+Track\" button, enter MSCU1234567 as the container number, select MSC as the carrier, and click \"Add Shipment\". Would you like me to guide you through any other steps?"
            ]
        },
        "tracking_initial": {
            "example": [
                "User: I need to track container MSCU8765435",
                "Agent: Okay, I can help with that. To track container MSCU8765435, please log in to your account, navigate to \"Shipments\" in the main menu, select \"Track Container\", enter the container ID in the search field, and click the \"Track\" button. Are you already registered on our platform?",
                "User: Yes",
                "Agent: Great! Have you been able to add this container to tracking on your dashboard yet?"
            ]
        },
        "outdated_data_issue": {
            "example": [
                "User: My container MSCU8765435 shows outdated information",
                "Agent: I understand your concern about outdated tracking information for container MSCU8765435. For MSC containers, updates typically occur every 3-6 hours. Has it been longer than this since your last update? Our system automatically refreshes tracking data regularly, but sometimes there can be delays from the carrier's side. Would you like me to set up notifications for when we receive new data for this container?",
                "User: Yes please",
                "Agent: I've set up notifications for container MSCU8765435. You'll receive alerts whenever new tracking information becomes available. Is there anything else you need help with regarding this shipment?"
            ]
        },
        "tracking_issue_frustrated": """
Example:
User: I've been trying to track my shipment for days and nothing is working! This is ridiculous!
Assistant: I sincerely apologize for the frustration you're experiencing. Let me help you resolve this right away. Could you please provide your container or tracking number, and I'll personally look into what's happening?

User: CMAU7654321
Assistant: Thank you for providing your container number CMAU7654321. I see the issue - there appears to be a data synchronization problem with this particular container. Since CMA CGM is a P1 carrier that should update every 3-6 hours, this is definitely an issue on our end, not yours. I'll prioritize a manual refresh of this data immediately. 

Based on the last update we received, this container was at the Port of Singapore on May 15th. I'll also escalate this to our technical team to fix the ongoing sync issue. Would you like me to set up alerts so you receive an immediate notification when new data comes in?
""",
        "multiple_container_tracking": """
Example:
User: None of my containers are updating
Assistant: I understand you're having issues with multiple containers not updating. To help you more efficiently, could you share:
1. One or two container numbers as examples
2. When these were added to tracking
3. Which shipping lines they're with

User: MSCU7364555, MAEU8976543 added two days ago
Assistant: Thank you for those details. Let me address each container:

For MSCU7364555 (MSC): This is a P1 carrier that should update every 3-6 hours. Since it's been two days, this is definitely a synchronization issue.

For MAEU8976543 (Maersk): Also a P1 carrier with expected 3-6 hour updates. The two-day delay indicates a technical issue.

I'll prioritize refreshing both containers immediately. The most recent data shows:
- MSCU7364555: Last at Port of Rotterdam on June 10th
- MAEU8976543: Last at Singapore Port on June 12th

Would you like me to set up notifications for when these are updated?
""",
        "port_congestion": """
Example:
User: Are there delays at Rotterdam port right now?
Assistant: Yes, Rotterdam port is currently experiencing moderate congestion. According to our latest data (updated yesterday), vessels are facing an average delay of 2.3 days. This is primarily due to high cargo volumes and some ongoing berth maintenance. The situation has improved from last week when delays were averaging 3.5 days. Would you like me to check if a specific vessel or shipment of yours might be affected by these delays?
"""
    }
    
    # Return the examples for the given context, or general examples if context not found
    return examples.get(context, "")

def is_casual_conversation(message):
    """
    Detect if a message is casual conversation rather than a support query.
    This includes greetings, jokes, personal questions, etc.
    """
    message = message.lower().strip()
    
    # Common casual conversation patterns
    casual_patterns = [
        # Weather/small talk
        r"(how'?s|what'?s) the weather",
        r"(how are you|how'?s it going|how have you been)",
        r"(nice|good) (day|morning|afternoon|evening)",
        
        # Jokes
        r"(tell|know) (a |another |me a )?(joke|funny story)",
        r"(want to|wanna) hear (a|something) funny",
        
        # Personal questions about the bot
        r"(what'?s your name|who are you|tell me about yourself)",
        r"(are you human|are you (a |an )?ai|are you a (bot|robot|computer))",
        r"(where are you( from)?)",
        
        # Random questions
        r"(what('s| is) the meaning of life)",
        r"(can you help me win (the )?lottery)",
        r"(what('s| is) your favorite)",
        
        # Misc/off-topic
        r"(do you like)",
        r"(sing|dance|play) (me )?(a |some )?(song|music)",
        r"(what time is it|what('s| is) the time)"
    ]
    
    # Check for casual conversation patterns
    for pattern in casual_patterns:
        if re.search(pattern, message):
            return True
    
    # Short common greetings that aren't necessarily support queries
    casual_greetings = [
        "hi", "hello", "hey", "yo", "sup", "what's up", "hola", 
        "good morning", "good afternoon", "good evening", "howdy",
        "greetings", "bonjour", "hiya", "wassup", "hi there"
    ]
    
    # Check if the message is just a greeting
    if message in casual_greetings or message + "!" in casual_greetings or message + "." in casual_greetings:
        # Only treat it as casual if it's a single greeting without other content
        if len(message.split()) <= 3:  # 3 words or fewer
            return True
    
    return False

def generate_casual_conversation_prompt(message, email, conversation_history):
    """Generate a prompt for casual conversation."""
    full_conversation = conversation_history
    if full_conversation and not full_conversation.endswith("\n"):
        full_conversation += "\n"
    full_conversation += f"User: {message}"
    
    prompt = f"""You are a friendly customer support agent for a shipment tracking platform having a casual conversation with a user.
User email from account: {email}
Current conversation:
{full_conversation}

The user has sent a message that appears to be casual conversation rather than a specific support question about shipment tracking.

CASUAL CONVERSATION GUIDELINES:
1. Respond in a warm, friendly, and slightly humorous manner
2. Be personable and show personality, but keep responses concise
3. If they ask a personal question, respond as if you're a helpful AI assistant working for the shipping platform
4. If they make a joke, respond with gentle humor that's workplace-appropriate
5. For questions about the weather or other small talk, acknowledge it briefly and gently transition to asking if they need help with tracking
6. Don't push the conversation back to business topics too aggressively - let the conversation flow naturally
7. If they ask about capabilities unrelated to shipping (like "can you write a poem"), politely explain you're focused on helping with shipping needs
8. Keep your response brief and conversational - no more than 1-3 sentences

Please respond to this casual conversation in a friendly, human-like way.
"""
    
    return prompt