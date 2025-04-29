import re
import logging
from collections import Counter
from difflib import SequenceMatcher

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConversationMonitor:
    """
    Monitors conversations to detect loops and ensure progress toward resolution.
    """
    
    def __init__(self):
        self.conversation_states = {}  # Stores conversation state by user_id
        self.resolution_progress = {}  # Tracks progress toward resolution
        
    def initialize_conversation(self, user_id):
        """Initialize a new conversation for a user"""
        self.conversation_states[user_id] = {
            "messages": [],
            "agent_asks": [],
            "user_provides": [],
            "topics": set(),
            "loops_detected": 0,
            "progress_score": 0,
            "stage": "initial",
            "resolution_path": []
        }
        self.resolution_progress[user_id] = {
            "identified_issue": False,
            "collected_details": False,
            "proposed_solution": False,
            "confirmed_resolution": False,
            "loops": []
        }
        
    def add_message(self, user_id, role, message, context=None):
        """Add a message to the conversation history and analyze for loops"""
        if user_id not in self.conversation_states:
            self.initialize_conversation(user_id)
            
        state = self.conversation_states[user_id]
        state["messages"].append({"role": role, "message": message})
        
        # Track the progression stages
        if role == "agent":
            self._analyze_agent_message(user_id, message, context)
        else:
            self._analyze_user_message(user_id, message)
            
        # Detect loops and calculate progress
        if len(state["messages"]) >= 4:  # Need at least 2 exchanges
            self._detect_loops(user_id)
            self._calculate_progress(user_id)
            
        return self._get_conversation_status(user_id)
    
    def _analyze_agent_message(self, user_id, message, context):
        """Analyze agent messages to track questions and progress"""
        state = self.conversation_states[user_id]
        progress = self.resolution_progress[user_id]
        
        # Extract questions the agent is asking
        questions = self._extract_questions(message)
        if questions:
            state["agent_asks"].extend(questions)
        
        # Update resolution stage based on message content and context
        if context:
            if context in ["tracking_issue_general", "invalid_tracking", "tracking_initial"]:
                state["topics"].add("tracking")
            elif context in ["account_issue", "account_blocked"]:
                state["topics"].add("account")
            elif "frustrated" in context:
                state["topics"].add("customer_frustration")
        
        # Identify stage transitions
        if re.search(r"(what|which|specific|tell me).*(issue|problem|error|happening)", message, re.I):
            progress["identified_issue"] = True
            state["stage"] = "issue_identification"
            state["resolution_path"].append("issue_identification")
            state["progress_score"] += 1
            
        elif re.search(r"(provide|tell me|share|what is).*(container|tracking number|carrier|shipping line)", message, re.I):
            progress["collected_details"] = True
            state["stage"] = "information_gathering" 
            if "information_gathering" not in state["resolution_path"]:
                state["resolution_path"].append("information_gathering")
                state["progress_score"] += 1
            
        elif re.search(r"(you can|suggest|recommend|try|here's what|solution|resolve)", message, re.I):
            progress["proposed_solution"] = True
            state["stage"] = "solution_proposal"
            if "solution_proposal" not in state["resolution_path"]:
                state["resolution_path"].append("solution_proposal")
                state["progress_score"] += 2
                
        elif re.search(r"(anything else|help you with|all set|resolved|completed|finished)", message, re.I):
            progress["confirmed_resolution"] = True
            state["stage"] = "resolution_confirmation"
            if "resolution_confirmation" not in state["resolution_path"]:
                state["resolution_path"].append("resolution_confirmation")
                state["progress_score"] += 3
    
    def _analyze_user_message(self, user_id, message):
        """Analyze user messages to track responses and detect potential issues"""
        state = self.conversation_states[user_id]
        
        # Check if user provided what agent asked for
        last_agent_asks = state["agent_asks"][-3:] if state["agent_asks"] else []
        
        # Look for specific patterns in user responses
        for ask in last_agent_asks:
            if any(self._similar_content(ask, message, 0.3) for ask in last_agent_asks):
                state["user_provides"].append({"asked": ask, "provided": message})
                
        # Check for user frustration indicators
        frustration_indicators = [
            r"(still not|doesn't work|not working|same issue|again|repeated|loop)",
            r"(frustrated|annoyed|tired|upset|angry)",
            r"(already told|already said|already mentioned)",
            r"(going in circles|same question|asked before)"
        ]
        
        for indicator in frustration_indicators:
            if re.search(indicator, message, re.I):
                state["loops_detected"] += 1
                self.resolution_progress[user_id]["loops"].append({
                    "message_index": len(state["messages"]) - 1,
                    "message": message,
                    "frustration_indicator": indicator
                })
                break
    
    def _extract_questions(self, message):
        """Extract questions from a message"""
        # Simple question extraction
        question_patterns = [
            r"(what|which|where|when|how|why|can you|could you|please tell)[^.!?]+\?",
            r"[^.!?]+\?"
        ]
        
        questions = []
        for pattern in question_patterns:
            matches = re.findall(pattern, message, re.I)
            questions.extend(matches)
            
        return questions
    
    def _detect_loops(self, user_id):
        """Detect conversation loops where the same topics are repeated"""
        state = self.conversation_states[user_id]
        recent_messages = state["messages"][-6:]  # Look at last 3 exchanges
        
        # Check for similar agent questions
        agent_messages = [m["message"] for m in recent_messages if m["role"] == "agent"]
        if len(agent_messages) >= 2:
            for i in range(len(agent_messages)-1):
                for j in range(i+1, len(agent_messages)):
                    if self._similar_content(agent_messages[i], agent_messages[j], 0.6):
                        state["loops_detected"] += 1
                        self.resolution_progress[user_id]["loops"].append({
                            "type": "agent_repetition",
                            "message_index": len(state["messages"]) - 1,
                            "similar_messages": [agent_messages[i], agent_messages[j]]
                        })
        
        # Check for repeated request for same information
        recent_asks = state["agent_asks"][-4:]
        if len(recent_asks) >= 2:
            ask_counter = Counter(recent_asks)
            repeated_asks = [ask for ask, count in ask_counter.items() if count > 1]
            if repeated_asks:
                state["loops_detected"] += 1
                self.resolution_progress[user_id]["loops"].append({
                    "type": "repeated_requests",
                    "message_index": len(state["messages"]) - 1,
                    "repeated_asks": repeated_asks
                })
    
    def _similar_content(self, text1, text2, threshold=0.6):
        """Check if two texts are similar using SequenceMatcher"""
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio() > threshold
    
    def _calculate_progress(self, user_id):
        """Calculate the conversation's progress toward resolution"""
        state = self.conversation_states[user_id]
        progress = self.resolution_progress[user_id]
        
        # Calculate progress penalty for loops
        loop_penalty = min(5, state["loops_detected"]) * 0.5
        
        # Calculate progress score based on resolution stages
        stage_scores = {
            "initial": 0,
            "issue_identification": 1,
            "information_gathering": 2,
            "solution_proposal": 3,
            "resolution_confirmation": 4
        }
        
        current_stage_score = stage_scores.get(state["stage"], 0)
        
        # Apply bonuses for completed stages
        stage_bonus = sum([
            1 if progress["identified_issue"] else 0,
            1 if progress["collected_details"] else 0,
            2 if progress["proposed_solution"] else 0,
            3 if progress["confirmed_resolution"] else 0
        ])
        
        # Final progress score (0-10 scale)
        raw_score = (current_stage_score + stage_bonus - loop_penalty)
        state["progress_score"] = max(0, min(10, raw_score))
        
    def _get_conversation_status(self, user_id):
        """Get the current status of the conversation"""
        state = self.conversation_states[user_id]
        progress = self.resolution_progress[user_id]
        
        # Determine if we need intervention
        needs_intervention = (
            state["loops_detected"] >= 2 or
            state["progress_score"] < 2 and len(state["messages"]) > 6
        )
        
        # Calculate progress percentage
        progress_pct = state["progress_score"] * 10  # 0-100%
        
        # Generate guidance for the agent based on the conversation state
        guidance = self._generate_guidance(user_id)
        
        return {
            "conversation_id": user_id,
            "message_count": len(state["messages"]),
            "current_stage": state["stage"],
            "progress_score": state["progress_score"],
            "progress_percentage": progress_pct,
            "loops_detected": state["loops_detected"],
            "needs_intervention": needs_intervention,
            "resolution_path": state["resolution_path"],
            "guidance": guidance
        }
    
    def _generate_guidance(self, user_id):
        """Generate guidance for the agent based on conversation analysis"""
        state = self.conversation_states[user_id]
        progress = self.resolution_progress[user_id]
        
        if state["loops_detected"] >= 2:
            # Conversation is looping
            return {
                "issue": "conversation_loop_detected",
                "suggestion": "Change approach and acknowledge to the user that we might be going in circles. "
                             "Summarize what we know so far and propose a concrete next step or solution.",
                "prompt_addition": "You notice this conversation seems to be going in circles. "
                                  "Acknowledge this to the user, summarize what you've understood so far, "
                                  "and take a different approach to move toward resolution."
            }
        
        if state["stage"] == "initial" and len(state["messages"]) > 4:
            # Conversation hasn't progressed past initial stage
            return {
                "issue": "stuck_in_initial_stage",
                "suggestion": "Ask a direct question to identify the specific issue the user is having.",
                "prompt_addition": "The conversation hasn't moved beyond the initial stage. "
                                  "Ask a specific, direct question to identify the core issue."
            }
            
        if state["stage"] == "issue_identification" and len(state["messages"]) > 6:
            # Stuck in issue identification
            return {
                "issue": "stuck_in_issue_identification",
                "suggestion": "Propose the most likely issue based on information so far and ask for confirmation.",
                "prompt_addition": "The conversation is stuck at identifying the issue. "
                                  "Make your best guess about what the problem is based on information provided, "
                                  "and ask the user to confirm or correct your understanding."
            }
            
        if state["stage"] == "information_gathering" and len(state["messages"]) > 8:
            # Too much information gathering
            return {
                "issue": "excessive_information_gathering",
                "suggestion": "Move forward with the information you have. Propose a solution.",
                "prompt_addition": "You've spent sufficient time gathering information. "
                                  "Now propose a solution based on what you know, even if some details are missing."
            }
            
        if not progress["proposed_solution"] and len(state["messages"]) > 10:
            # No solution proposed after many messages
            return {
                "issue": "no_solution_proposed",
                "suggestion": "Propose a concrete solution now, even with limited information.",
                "prompt_addition": "The conversation has gone on for several exchanges without proposing a solution. "
                                  "Offer a specific solution now based on available information."
            }
            
        # Default guidance for normal progression
        return {
            "issue": None,
            "suggestion": "Continue with the current approach.",
            "prompt_addition": None
        }
        
    def get_intervention_prompt(self, user_id):
        """Get a prompt addition to help the agent break out of loops"""
        status = self._get_conversation_status(user_id)
        
        if status["needs_intervention"]:
            intervention_prompt = f"""
IMPORTANT: This conversation needs intervention. {status['guidance']['issue']}

The conversation is currently in stage '{status['current_stage']}' with a progress score of {status['progress_score']}/10.
There have been {status['loops_detected']} conversation loops detected.

INTERVENTION GUIDANCE:
{status['guidance']['prompt_addition']}

Your next response should break this pattern and move the conversation forward.
"""
            return intervention_prompt
        
        return "" 