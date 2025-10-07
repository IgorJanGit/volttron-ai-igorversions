from pydantic_ai import Agent
from typing import Optional
import os
import openai
from .volttron_commands import (
    start_volttron, stop_volttron, check_volttron_status, read_volttron_log,
    vctl_status, vctl_status_detailed, vctl_list_agents, vctl_start_agent, vctl_stop_agent, vctl_health,
    show_formatting_test, get_detailed_installation_help, get_volttron_next_steps,
    vctl_install_platform_driver, install_fake_driver_library, create_fake_driver_config,
    store_fake_driver_config, setup_fake_driver_monitoring, subscribe_to_fake_data,
    show_recent_logs
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
        self._setup_agent()
    
    def _detect_numbered_option_request(self, message: str) -> tuple[bool, int]:
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
        elif 'agent list' in title or 'list agents' in title:
            return vctl_list_agents()
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
        """Setup the Pydantic-AI agent with the specified model or custom webapp if configured."""
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
                # Use default provider logic (OpenAI, Anthropic, etc.) with pydantic-ai
                self.agent = Agent(
                    self.model_name,
                    system_prompt=(
                        "You are a helpful AI assistant in a chat application. "
                        "Provide clear, concise, and helpful responses to user questions. "
                        "Be friendly and conversational while maintaining accuracy."
                    )
                )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize AI model '{self.model_name}': {str(e)}")
    
    async def generate_response(self, message: str) -> str:
        """Generate a response to the user's message."""
        try:
            # Check if user is referencing a numbered option from previous response
            is_numbered_request, option_num = self._detect_numbered_option_request(message)
            if is_numbered_request and self.last_numbered_options:
                return self._execute_numbered_option(option_num)
            
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
- check_volttron_status(): See how I'm feeling overall
- read_volttron_log(): Tell you about my recent adventures
- vctl_status(): Quick check on my agent family
- vctl_status_detailed(): Deep dive into what my agents are doing
- vctl_list_agents(): Show you all my agent buddies
- vctl_start_agent(uuid_or_tag): Wake up a specific agent
- vctl_stop_agent(uuid_or_tag): Put an agent to sleep
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
                
                # Add recent conversation history (last 4 messages to maintain context)
                recent_history = self.conversation_history[-4:]
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
                
                # Check if AI wants to execute a VOLTTRON command
                if "EXECUTE_START_VOLTTRON" in ai_response:
                    result = start_volttron()
                    return result
                elif "EXECUTE_STOP_VOLTTRON" in ai_response:
                    result = stop_volttron()
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
                elif "EXECUTE_VCTL_HEALTH" in ai_response:
                    result = vctl_health()
                    return result
                elif "EXECUTE_FORMATTING_TEST" in ai_response:
                    result = show_formatting_test()
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
                
            elif self.agent:
                # Use pydantic-ai agent for standard providers
                result = await self.agent.run(message)
                return result.output
            else:
                return "Error: No AI service initialized"
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