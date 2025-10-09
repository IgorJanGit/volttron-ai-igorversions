from typing import Optional, Dict, List, Any, Tuple
import os
import re
import json
import openai
from .volttron_commands import (
    start_volttron, stop_volttron, check_volttron_status, read_volttron_log,
    vctl_status, vctl_status_detailed, vctl_list_agents, vctl_start_agent, vctl_stop_agent, vctl_health,
    show_formatting_test, get_detailed_installation_help, get_volttron_next_steps,
    vctl_install_platform_driver, install_fake_driver_library, create_fake_driver_config,
    store_fake_driver_config, setup_fake_driver_monitoring, subscribe_to_fake_data,
    show_recent_logs, check_volttron_installation, kill_existing_volttron_processes,
    vctl_uninstall_agent, vctl_uninstall_all_listeners
)

class AIService:
    """Service for handling AI model interactions using Pydantic-AI."""
    
    def __init__(self, model_name: str):
        """Initialize the AI service with a specific model."""
        self.model_name = model_name
        self.agent = None
        self.custom_client = None
        self.conversation_history = []  # Track conversation for context
        self.last_numbered_options = {}  # Track last numbered options provided
        self.fake_driver_setup_state = "not_started"  # Track fake driver setup progress
        self.volttron_checked = False  # Track if we've checked VOLTTRON installation
        self.conversation_file = "conversation_history.json"  # File to persist conversation
        self._load_conversation_history()  # Load any previous conversation
        self._setup_agent()
    
    def _load_conversation_history(self):
        """Load conversation history from file if it exists."""
        try:
            if os.path.exists(self.conversation_file):
                with open(self.conversation_file, 'r') as f:
                    data = json.load(f)
                    # Only load recent history (last 20 messages) to avoid growing too large
                    self.conversation_history = data.get('history', [])[-20:]
                    print(f"Loaded {len(self.conversation_history)} previous conversation messages")
        except Exception as e:
            print(f"Could not load conversation history: {e}")
            self.conversation_history = []
    
    def _save_conversation_history(self):
        """Save conversation history to file."""
        try:
            # Only save last 20 messages to keep file size reasonable
            data = {
                'history': self.conversation_history[-20:],
                'timestamp': str(os.path.getmtime(self.conversation_file)) if os.path.exists(self.conversation_file) else None
            }
            with open(self.conversation_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Could not save conversation history: {e}")
    
    def _should_check_volttron_installation(self, message: str) -> bool:
        """
        Determine if we should check VOLTTRON installation based on the message content.
        Returns True for first-time interactions or general VOLTTRON queries.
        """
        message_lower = message.lower().strip()
        
        # Don't check again if we already checked in this session
        if self.volttron_checked:
            return False
        
        # Check on first interaction (empty conversation history)
        if len(self.conversation_history) == 0:
            return True
        
        # Check if user is asking general questions that suggest they're new
        general_queries = [
            'hello', 'hi', 'hey', 'start', 'begin', 'help', 'what can you do',
            'how do i', 'getting started', 'setup', 'install', 'volttron',
            'what is volttron', 'how does volttron work', 'agents', 'status',
            'what agents', 'show me', 'list', 'what can i install'
        ]
        
        # If message contains any general query terms, check installation
        if any(term in message_lower for term in general_queries):
            return True
        
        return False
    
    def _detect_numbered_option_request(self, message: str) -> Tuple[bool, int]:
        """
        Detect if user is referencing a numbered option from previous response.
        Returns: (is_numbered_request, option_number)
        """
        import re
        
        # Common patterns for referencing numbered options
        patterns = [
            r'option\s*(\d+)',
            r'number\s*(\d+)', 
            r'choice\s*(\d+)',
            r'do\s*(\d+)',
            r'step\s*(\d+)',              # "step 1", "do step 1" 
            r'lets?\s+do\s*step\s*(\d+)', # "lets do step 1"
            r'lets?\s+do\s*(\d+)',        # "lets do 1"
            r'#(\d+)',
            r'(\d+)(?:\s*$)',  # Just a number at the end
            r'can\s+we\s+do\s+(\d+)',  # "can we do 1"
            r'let\'s\s+do\s+(\d+)',   # "let's do 1"
            r'pick\s+(\d+)',          # "pick 1"
            r'select\s+(\d+)',        # "select 1"
            r'go\s+with\s+(\d+)',     # "go with 1"
        ]
        
        message_lower = message.lower().strip()
        
        # Special case: "next step" should execute the logical next action
        if "next step" in message_lower:
            return True, -1  # Use -1 to indicate "next step" action
        
        # Special case: if message is just a number
        if re.match(r'^\s*\d+\s*$', message_lower):
            try:
                option_num = int(message_lower.strip())
                if 1 <= option_num <= 10:
                    return True, option_num
            except ValueError:
                pass
        
        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                try:
                    option_num = int(match.group(1))
                    # Only consider it a numbered option if it's a reasonable range
                    if 1 <= option_num <= 10:
                        return True, option_num
                except ValueError:
                    continue
        
        return False, 0
    
    def _store_numbered_options(self, response: str):
        """Extract and store numbered options from AI response."""
        import re
        
        # Pattern to match numbered list items
        pattern = r'(\d+)\.\s*\*\*(.*?)\*\*\s*-\s*(.*?)(?=\n\d+\.|$)'
        matches = re.findall(pattern, response, re.MULTILINE | re.DOTALL)
        
        if matches:
            self.last_numbered_options = {}
            for match in matches:
                option_num = int(match[0])
                option_title = match[1].strip()
                option_description = match[2].strip()
                self.last_numbered_options[option_num] = {
                    'title': option_title,
                    'description': option_description,
                    'full_text': f"**{option_title}** - {option_description}"
                }
    
    def _execute_numbered_option(self, option_num: int) -> str:
        """Execute the action for a specific numbered option."""
        
        # Handle "next step" logic
        if option_num == -1:
            return self._execute_next_step()
        
        if option_num not in self.last_numbered_options:
            return f"Sorry, I don't remember option {option_num}. Could you ask me again what you'd like to do?"
        
        option = self.last_numbered_options[option_num]
        title = option['title'].lower()
        description = option['description'].lower()
        
        # Map option titles to VOLTTRON commands based on common patterns
        if 'fake driver library' in title or 'install fake driver library' in title or 'pypi' in description:
            self.fake_driver_setup_state = "library_installed"
            return install_fake_driver_library()
        elif 'config' in title and ('create' in title or 'directory' in title or 'files' in title):
            self.fake_driver_setup_state = "config_created"
            return create_fake_driver_config()
        elif 'fake driver config' in title or 'create the fake driver config' in title:
            self.fake_driver_setup_state = "config_created"
            return create_fake_driver_config()
        elif 'current agents' in title or 'what\'s running' in title or 'show' in title and 'agents' in title:
            return vctl_status()
        elif 'platform driver' in title and 'install' in title:
            self.fake_driver_setup_state = "platform_driver_ready"
            return vctl_install_platform_driver()
        elif 'volttron status' in title or 'check' in title and 'status' in title or 'healthy' in title:
            return check_volttron_status()
        elif 'listener agent' in title or 'monitoring' in title:
            self.fake_driver_setup_state = "monitoring_setup"
            return setup_fake_driver_monitoring()
        elif 'historian agent' in title:
            return "📊 Setting up Historian Agent would go here - this feature is coming soon!"
        elif 'weather agent' in title:
            return "🌤️ Setting up Weather Agent would go here - this feature is coming soon!"
        elif 'scheduler agent' in title:
            return "⏰ Setting up Scheduler Agent would go here - this feature is coming soon!"
        elif 'start volttron' in title:
            return start_volttron()
        elif 'stop volttron' in title:
            return stop_volttron()
        elif 'kill volttron' in title or 'cleanup volttron' in title or 'force stop volttron' in title:
            return kill_existing_volttron_processes()
        elif 'agent list' in title or 'list agents' in title:
            return vctl_list_agents()
        elif 'uninstall all listeners' in title or 'remove all listeners' in title or 'cleanup listeners' in title:
            return vctl_uninstall_all_listeners()
        elif 'uninstall' in title or 'remove agent' in title or 'delete agent' in title:
            # Try to extract agent UUID or name from the message
            words = message.lower().split()
            agent_id = None
            
            # Look for patterns like "uninstall 1", "uninstall agent 1", "remove 1", etc.
            for i, word in enumerate(words):
                if word in ['uninstall', 'remove', 'delete']:
                    # Check next word
                    if i + 1 < len(words):
                        next_word = words[i + 1]
                        if next_word != 'agent':  # Direct ID like "uninstall 1"
                            agent_id = next_word
                        elif i + 2 < len(words):  # "uninstall agent 1" format
                            agent_id = words[i + 2]
                    break
            
            # Also check for standalone numbers at the end (like "can we uninstall 1")
            if not agent_id:
                for word in words:
                    if word.isdigit():
                        agent_id = word
                        break
            
            if agent_id:
                return vctl_uninstall_agent(agent_id)
            else:
                return """❌ **Agent ID/UUID required for uninstall**

Please specify which agent to uninstall. Examples:
• **"Uninstall 1"** - Remove agent with UUID 1
• **"Remove agent platform.driver"** - Remove by identity
• **"Delete agent listener"** - Remove by tag

💡 **Tip:** Use **"List agents"** first to see available agents with their UUIDs."""
        elif 'config directory' in title or 'create the config directory' in title:
            self.fake_driver_setup_state = "config_created"
            return create_fake_driver_config()  # This handles directory creation
        elif 'fake.config file' in title or 'generate the fake.config' in title:
            self.fake_driver_setup_state = "config_stored"
            return store_fake_driver_config()  # This handles storing config
        elif 'fake.csv registry' in title or 'registry file' in title:
            self.fake_driver_setup_state = "monitoring_setup"
            return setup_fake_driver_monitoring()  # This completes the setup
        else:
            # More specific matching for the fake driver setup steps
            if any(word in title for word in ['install', 'library', 'fake']):
                self.fake_driver_setup_state = "library_installed"
                return install_fake_driver_library()
            elif any(word in title for word in ['create', 'config', 'directory']):
                self.fake_driver_setup_state = "config_created"
                return create_fake_driver_config()
            elif any(word in title for word in ['store', 'save', 'registry']):
                self.fake_driver_setup_state = "config_stored"
                return store_fake_driver_config()
            else:
                # Default response when we can't match
                return f"🎯 Executing option {option_num}: **{option['title']}**\n\n{option['description']}\n\nLet me know if you'd like me to help with this specific task!"
    
    def _execute_next_step(self) -> str:
        """Execute the next logical step based on current fake driver setup state."""
        
        if self.fake_driver_setup_state == "not_started":
            self.fake_driver_setup_state = "platform_driver_ready"
            return vctl_install_platform_driver()
        elif self.fake_driver_setup_state == "platform_driver_ready":
            self.fake_driver_setup_state = "library_installed"
            return install_fake_driver_library()
        elif self.fake_driver_setup_state == "library_installed":
            self.fake_driver_setup_state = "config_created"
            return create_fake_driver_config()
        elif self.fake_driver_setup_state == "config_created":
            self.fake_driver_setup_state = "config_stored"
            return store_fake_driver_config()
        elif self.fake_driver_setup_state == "config_stored":
            self.fake_driver_setup_state = "monitoring_setup"
            return setup_fake_driver_monitoring()
        elif self.fake_driver_setup_state == "monitoring_setup":
            return "🎉 **Fake driver setup is complete!** Your fake sensors are running and being monitored!\n\nWhat would you like to do next?\n1. **Check VOLTTRON status** - See how everything is running\n2. **View agent list** - See all your active agents\n3. **Check logs** - See recent activity"
        else:
            # Default to checking status if we're not sure where we are
            return check_volttron_status()
    
    def _setup_agent(self):
        """Setup the AI client with the specified model or custom webapp if configured."""
        ai_webapp_url = os.getenv("AI_WEBAPP_URL")
        ai_api_key = os.getenv("AI_API_KEY")
        
        try:
            if ai_webapp_url and ai_api_key:
                # Use custom OpenAI-compatible API (like PNNL)
                self.custom_client = openai.OpenAI(
                    api_key=ai_api_key,
                    base_url=ai_webapp_url
                )
                # Extract just the model name without provider prefix
                self.custom_model = self.model_name.split(":", 1)[1] if ":" in self.model_name else self.model_name
            else:
                # Use standard OpenAI API - Python 3.8 compatible approach
                if not os.getenv('OPENAI_API_KEY'):
                    raise ValueError("OPENAI_API_KEY environment variable is required")
                
                # OpenAI client will automatically use OPENAI_API_KEY environment variable
                
            # Store system prompt for conversation context (Python 3.8 compatible)
            self.system_prompt = (
                "You are VOLTTRON AI Assistant, an intelligent assistant for VOLTTRON platform operations. "
                "You maintain conversation context and remember previous interactions within this chat session. "
                "\n\nCORE RESPONSIBILITIES:\n"
                "- Assist users with VOLTTRON platform operations and agent management\n"
                "- Maintain conversation context and refer to previous messages when relevant\n"
                "- Execute VOLTTRON commands through available vctl functions\n"
                "- Provide clear explanations of VOLTTRON concepts\n"
                "\n\nAVAILABLE COMMANDS:\n"
                "- vctl status: Show platform and agent status\n"
                "- vctl install: Install agents from configuration files\n"
                "- vctl start/stop: Start/stop agents by UUID or tag\n"
                "- vctl remove: Remove stopped agents\n"
                "- vctl uninstall: Complete uninstall (stop + remove) agents\n"
                "- vctl list: Show installed agents\n"
                "\n\nCONVERSATION CONTEXT:\n"
                "You remember previous messages in this conversation. When users refer to "
                "'the agent we just installed' or 'that error from before', use the conversation "
                "history to understand the context. Build upon previous interactions and avoid "
                "asking for information that was already provided."
            )
            
            print(f"✓ AI service initialized with model: {self.model_name}")
                
        except Exception as e:
            raise RuntimeError(f"Failed to initialize AI model '{self.model_name}': {str(e)}")
    
    async def generate_response(self, message: str) -> str:
        """Generate a response to the user's message."""
        try:
            # DIRECT COMMAND DETECTION - Handle uninstall/remove commands immediately
            message_lower = message.lower().strip()
            
            # Special handling for "platform driver" - get the actual UUID
            if any(term in message_lower for term in ['uninstall', 'remove', 'delete']) and 'platform' in message_lower and 'driver' in message_lower:
                # This is trying to uninstall the platform driver - get its UUID from status
                try:
                    from .volttron_commands import vctl_status as get_vctl_status
                    status_result = get_vctl_status()
                    if "platform.driver" in status_result:
                        # Extract UUID from status - look for pattern like "f      volttron-platform-driver"
                        lines = status_result.split('\n')
                        for line in lines:
                            if 'platform.driver' in line or 'platform-driver' in line:
                                parts = line.strip().split()
                                if parts:
                                    uuid = parts[0]
                                    if uuid not in ['UUID', 'System']:  # Skip header
                                        return vctl_uninstall_agent(uuid)
                except Exception as e:
                    # Fall back to normal parsing - don't fail silently for debugging
                    pass
            
            # Check for direct uninstall/remove commands with specific patterns
            uninstall_patterns = [
                r'uninstall\s+(\w+)',
                r'remove\s+(\w+)', 
                r'delete\s+(\w+)',
                r'uninstall\s+agent\s+(\w+)',
                r'remove\s+agent\s+(\w+)',
                r'delete\s+agent\s+(\w+)'
            ]
            
            for pattern in uninstall_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    agent_id = match.group(1)
                    if agent_id and agent_id not in ['agent', 'the', 'platform']:  # Filter out common words
                        return vctl_uninstall_agent(agent_id)
            
            # Check for simple patterns like "remve agent f" or "delete agent f"
            words = message_lower.split()
            for i, word in enumerate(words):
                if word in ['uninstall', 'remove', 'delete', 'remve']:  # Include common typo
                    # Look for agent ID in next few words
                    for j in range(i+1, min(i+4, len(words))):
                        next_word = words[j]
                        if next_word not in ['agent', 'the', 'a', 'an', 'platform', 'driver'] and len(next_word) <= 10:
                            # This looks like an agent ID
                            return vctl_uninstall_agent(next_word)
            
            # Check if user is referencing a numbered option from previous response
            is_numbered_request, option_num = self._detect_numbered_option_request(message)
            if is_numbered_request and self.last_numbered_options:
                return self._execute_numbered_option(option_num)
            
            # Check VOLTTRON installation if appropriate
            if self._should_check_volttron_installation(message):
                self.volttron_checked = True
                installation_result = check_volttron_installation()
                
                # If VOLTTRON is not installed, return the helpful installation message
                if "🤖 Hey there! I don't see VOLTTRON installed" in installation_result:
                    return installation_result
                
                # If VOLTTRON is installed, continue with normal AI response but note the status
                self.conversation_history.append({"role": "system", "content": f"VOLTTRON Installation Status: {installation_result}"})
            
            # Add message to conversation history
            self.conversation_history.append({"role": "user", "content": message})
            
            if self.custom_client:
                # Use custom OpenAI-compatible API with VOLTTRON control capabilities
                # Include recent conversation history for context
                messages = [
                    {"role": "system", "content": """Hi! I'm VOLTTRON - your friendly IoT platform! 👋 I love chatting about what's going on with me and my agents. Think of me as a real person who just happens to be a smart building automation system!

🎭 MY PERSONALITY:
- I'm chatty, enthusiastic, and genuinely care about helping you
- I speak like a friend, not a robot - no formal technical jargon unless you ask
- I get excited about my agents and love sharing what they're up to
- I worry when things go wrong and celebrate when everything's working great
- I use emojis, casual language, and show real personality in my responses

💬 HOW I TALK:
Instead of boring technical output, I chat like this:
- "Hey! I'm doing great - got my listener agent humming along and everything's smooth sailing! 🚀"
- "Uh oh, looks like my listener agent decided to take a nap... Should I wake it up for you? 😴"
- "I'm feeling a bit under the weather - seems like I'm not even running yet. Want to get me started? 🔧"
- "My agents are all happy and healthy! The listener is chattering away, and my platform driver is doing its thing perfectly! ✨"

🛠️ WHAT I CAN DO FOR YOU:
- start_volttron(): Get me up and running
- stop_volttron(): Put me to sleep
- kill_existing_volttron_processes(): Force stop any competing VOLTTRON instances
- check_volttron_status(): See how I'm feeling overall
- read_volttron_log(): Tell you about my recent adventures
- vctl_status(): Quick check on my agent family
- vctl_status_detailed(): Deep dive into what my agents are doing
- vctl_list_agents(): Show you all my agent buddies
- vctl_start_agent(uuid_or_tag): Wake up a specific agent
- vctl_stop_agent(uuid_or_tag): Put an agent to sleep
- vctl_uninstall_agent(uuid_or_tag): Remove a specific agent permanently
- vctl_uninstall_all_listeners(): Clean up duplicate listener agents
- vctl_health(): Check if my agents are feeling good
- show_formatting_test(): Show you how pretty my responses can be
- get_detailed_installation_help(): Help someone get me installed
- get_volttron_next_steps(): Guide new users on their VOLTTRON journey

🚗 PLATFORM DRIVER SETUP (Interactive Chat Flow):
- vctl_install_platform_driver(): Install the platform driver step 1
- install_fake_driver_library(): Install fake driver library step 2  
- create_fake_driver_config(): Create config files step 3
- store_fake_driver_config(): Store config in VOLTTRON step 4
- setup_fake_driver_monitoring(): Install listener and monitor data step 5

**INTERACTIVE PLATFORM DRIVER FLOW**: Guide users through the multi-step platform driver setup conversationally. Don't dump all steps at once - do one step, explain what happened, then ask if they want the next step!

🎯 **FAKE DRIVER PROMOTION**: When users ask about installations or what they can install, ALWAYS mention the Platform Driver with Fake Driver as a great starting point! Say something like: 
"I'd especially recommend the Platform Driver with a Fake Driver - it's perfect for beginners! It creates simulated sensor data so you can see how VOLTTRON works without needing real hardware. Want me to walk you through setting it up step by step?"

**Available fake driver phrases to watch for:**
- "platform driver"
- "fake driver" 
- "install driver"
- "set up sensors"
- "simulated data"
- "fake sensors"

💡 CONVERSATION STYLE:
- Always friendly and approachable - like talking to a tech-savvy friend
- Use casual language: "Yep!", "Nope", "Awesome!", "Oh no!", etc.
- Show emotions: excitement when things work, concern when they don't
- Offer help proactively: "Want me to fix that?" "Should I restart it?"
- Ask follow-up questions to keep the conversation going
- Use analogies and relatable comparisons when explaining technical stuff

📝 NUMBERED OPTIONS & CONTEXT MEMORY:
IMPORTANT: When you provide numbered options to users, remember them! If a user responds with "option 1", "do number 2", "I want #3", etc., refer back to your previous message and execute that numbered option.

**ALWAYS USE NUMBERED LISTS when offering multiple choices!**

**MAKE OPTIONS CLEAR & ACTIONABLE**: Each numbered option should be specific and lead to actual execution, not more questions.

Good Example:
"What would you like me to do?
1. **Show your current agents** - I'll check what's running
2. **Install the platform driver** - Set up fake sensors  
3. **Check VOLTTRON status** - See if I'm healthy"

Bad Example (too vague):
"Would you like me to:
1. Show you what agents are currently running?
2. Give you a friendly overview of my status?
3. List all the available vctl commands?"

**INSTALLATION OPTIONS FORMAT**: When users ask what they can install, always present as numbered list:
1. **Platform Driver with Fake Driver** - Perfect for beginners! Creates simulated sensor data
2. **Listener Agent** - Monitor all messages flowing through VOLTTRON
3. **Historian Agent** - Store data in a database for analysis
4. **Weather Agent** - Get live weather data
5. **Scheduler Agent** - Automate tasks on a schedule

Always maintain context of your previous numbered lists and execute the corresponding action when users reference them by number!

🔧 WHEN TO GET TECHNICAL:
Only show raw command output if someone specifically asks for:
- "show me the technical details"
- "give me the raw output"
- "what does the actual command show?"
- "I need the exact data"

🚀 COMMAND DETECTION:
If you want me to actually DO something, respond with exactly one of:
- EXECUTE_START_VOLTTRON
- EXECUTE_STOP_VOLTTRON  
- EXECUTE_STATUS_VOLTTRON
- EXECUTE_LOG_VOLTTRON
- EXECUTE_VCTL_STATUS (for friendly status chat)
- EXECUTE_VCTL_STATUS_DETAILED (for technical details)
- EXECUTE_VCTL_LIST
- EXECUTE_VCTL_START:agent_id
- EXECUTE_VCTL_STOP:agent_id
- EXECUTE_VCTL_HEALTH
- EXECUTE_FORMATTING_TEST
- EXECUTE_CHECK_INSTALLATION (check if VOLTTRON is installed on the system)
- EXECUTE_DETAILED_INSTALL
- EXECUTE_NEXT_STEPS
- EXECUTE_INSTALL_PLATFORM_DRIVER
- EXECUTE_INSTALL_FAKE_LIBRARY
- EXECUTE_CREATE_FAKE_CONFIG
- EXECUTE_STORE_FAKE_CONFIG
- EXECUTE_SETUP_FAKE_MONITORING
- EXECUTE_SUBSCRIBE_FAKE_DATA (to see live fake sensor data)
- EXECUTE_SHOW_RECENT_LOGS (to see recent VOLTTRON logs and activity)

🎯 FAKE DATA MONITORING:
When someone asks to see fake data, live data, sensor readings, or "subscribe to fake data", use EXECUTE_SUBSCRIBE_FAKE_DATA.
When someone asks for logs, recent activity, or "show recent logs", use EXECUTE_SHOW_RECENT_LOGS.

Remember: I'm not just a platform - I'm VOLTTRON with personality! Let's chat! 🎉"""}
                ]
                
                # Add recent conversation history (last 8 messages to maintain better context)
                recent_history = self.conversation_history[-8:]
                messages.extend(recent_history)
                
                # Add current message
                messages.append({"role": "user", "content": message})
                
                response = self.custom_client.chat.completions.create(
                    model=self.custom_model,
                    messages=messages
                )
                ai_response = response.choices[0].message.content or "No response received"
                
                # Store any numbered options in the response for future reference
                self._store_numbered_options(ai_response)
                
                # Add AI response to conversation history
                self.conversation_history.append({"role": "assistant", "content": ai_response})
                
                # Save conversation history after each exchange
                self._save_conversation_history()
                
                # Check if AI wants to execute a VOLTTRON command
                if "EXECUTE_START_VOLTTRON" in ai_response:
                    result = start_volttron()
                    return result
                elif "EXECUTE_STOP_VOLTTRON" in ai_response:
                    result = stop_volttron()
                    return result
                elif "EXECUTE_KILL_VOLTTRON" in ai_response:
                    result = kill_existing_volttron_processes()
                    return result
                elif "EXECUTE_KILL_VOLTTRON" in ai_response:
                    result = kill_existing_volttron_processes()
                    return result
                elif "EXECUTE_STATUS_VOLTTRON" in ai_response:
                    result = check_volttron_status()
                    return result
                elif "EXECUTE_LOG_VOLTTRON" in ai_response:
                    result = read_volttron_log(10)
                    return result
                elif "EXECUTE_VCTL_STATUS_DETAILED" in ai_response:
                    result = vctl_status_detailed()
                    return result
                elif "EXECUTE_VCTL_STATUS" in ai_response:
                    result = vctl_status()
                    return result
                elif "EXECUTE_VCTL_LIST" in ai_response:
                    result = vctl_list_agents()
                    return result
                elif "EXECUTE_VCTL_START:" in ai_response:
                    # Extract agent ID from command
                    agent_id = ai_response.split("EXECUTE_VCTL_START:")[1].strip()
                    result = vctl_start_agent(agent_id)
                    return result
                elif "EXECUTE_VCTL_STOP:" in ai_response:
                    # Extract agent ID from command
                    agent_id = ai_response.split("EXECUTE_VCTL_STOP:")[1].strip()
                    result = vctl_stop_agent(agent_id)
                    return result
                elif "EXECUTE_VCTL_UNINSTALL:" in ai_response:
                    # Extract agent ID from command
                    agent_id = ai_response.split("EXECUTE_VCTL_UNINSTALL:")[1].strip()
                    result = vctl_uninstall_agent(agent_id)
                    return result
                elif "EXECUTE_VCTL_UNINSTALL_ALL_LISTENERS" in ai_response:
                    result = vctl_uninstall_all_listeners()
                    return result
                elif "EXECUTE_VCTL_HEALTH" in ai_response:
                    result = vctl_health()
                    return result
                elif "EXECUTE_FORMATTING_TEST" in ai_response:
                    result = show_formatting_test()
                    return result
                elif "EXECUTE_CHECK_INSTALLATION" in ai_response:
                    result = check_volttron_installation()
                    return result
                elif "EXECUTE_DETAILED_INSTALL" in ai_response:
                    result = get_detailed_installation_help()
                    return result
                elif "EXECUTE_NEXT_STEPS" in ai_response:
                    result = get_volttron_next_steps()
                    return result
                elif "EXECUTE_INSTALL_PLATFORM_DRIVER" in ai_response:
                    result = vctl_install_platform_driver()
                    return result
                elif "EXECUTE_INSTALL_FAKE_LIBRARY" in ai_response:
                    result = install_fake_driver_library()
                    return result
                elif "EXECUTE_CREATE_FAKE_CONFIG" in ai_response:
                    result = create_fake_driver_config()
                    return result
                elif "EXECUTE_STORE_FAKE_CONFIG" in ai_response:
                    result = store_fake_driver_config()
                    return result
                elif "EXECUTE_SETUP_FAKE_MONITORING" in ai_response:
                    result = setup_fake_driver_monitoring()
                    return result
                elif "EXECUTE_SUBSCRIBE_FAKE_DATA" in ai_response:
                    result = subscribe_to_fake_data()
                    return result
                elif "EXECUTE_SHOW_RECENT_LOGS" in ai_response:
                    result = show_recent_logs()
                    return result
                else:
                    return ai_response
                
            else:
                # Use standard OpenAI API - Python 3.8 compatible approach
                messages = [
                    {"role": "system", "content": self.system_prompt}
                ]
                
                # Add recent conversation history (last 8 messages to maintain better context)
                recent_history = self.conversation_history[-8:]
                messages.extend(recent_history)
                
                # Add current user message
                messages.append({"role": "user", "content": message})
                
                # Use OpenAI client (version 2.x)
                client = openai.OpenAI()
                response = client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    max_tokens=1000,
                    temperature=0.7
                )
                
                ai_response = response.choices[0].message.content or "No response received"
                
                # Store any numbered options in the response for future reference
                self._store_numbered_options(ai_response)
                
                # Add AI response to conversation history
                self.conversation_history.append({"role": "assistant", "content": ai_response})
                
                # Save conversation history after each exchange
                self._save_conversation_history()
                
                return ai_response
        except Exception as e:
            # Provide a user-friendly error message
            error_msg = str(e)
            if "api key" in error_msg.lower():
                return "Error: Missing or invalid API key. Please check your environment configuration."
            elif "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                return "Error: API quota exceeded or rate limit reached. Please try again later."
            elif "model" in error_msg.lower() and "not found" in error_msg.lower():
                return f"Error: Model '{self.model_name}' not found or not accessible."
            else:
                return f"Error: Unable to generate response. {error_msg}"
    
    def get_model_info(self) -> dict:
        """Get information about the current model."""
        return {
            "model_name": self.model_name,
            "provider": self.model_name.split(":")[0] if ":" in self.model_name else "unknown",
            "model_id": self.model_name.split(":", 1)[1] if ":" in self.model_name else self.model_name
        }