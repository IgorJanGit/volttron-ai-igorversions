def vctl_status(explain=False):
    """Get detailed VOLTTRON agent status using vctl status command."""
    try:
        vctl_cmd = find_vctl_command()
        volttron_home = get_volttron_home()
        
        if not vctl_cmd:
            return "❌ VOLTTRON commands not found. Please install VOLTTRON first."
        
        # Set environment variables
        env = os.environ.copy()
        env["VOLTTRON_HOME"] = volttron_home
        
        # First check if VOLTTRON is running via direct process check (most reliable)
        is_running = False
        try:
            result = subprocess.run(
                "ps aux | grep bin/volttron | grep -v grep",
                shell=True,
                capture_output=True, text=True, timeout=5
            )
            is_running = result.returncode == 0 and result.stdout.strip()
        except Exception:
            pass
            
        if not is_running:
            warning_msg = ""
            if explain:
                return f"""{warning_msg}❌ **Oops! VOLTTRON isn't running right now.**

The platform needs to be started before I can check on your agents.

🚀 **Ready to fire it up?** Just say:
   • "Start VOLTTRON"
   • "Launch the platform"  
   • "Get VOLTTRON running"

I'll get it started for you! ⚡
"""
            else:
                return f"{warning_msg}Uh oh, I'm not running right now! Want to start me up?"
        
        # Try to get detailed agent status with timeout
        try:
            # Try with shell=True to ensure proper environment variable handling
            cmd_str = f"export VOLTTRON_HOME={volttron_home} && {vctl_cmd} status"
            result = subprocess.run(
                cmd_str,
                shell=True,
                capture_output=True, 
                text=True,
                timeout=15  # Add timeout to prevent hanging
            )
            
            # Format any system warnings
            warning_msg = format_volttron_warnings(result.stderr)
            
            if result.returncode == 0:
                status_output = result.stdout.strip()
                
                # Check if no agents are installed
                if not status_output or "No installed Agents found" in status_output:
                    if explain:
                        return f"""{warning_msg}🟡 **VOLTTRON is running, but it looks pretty quiet in here!**

No agents are currently installed or running. This is normal for a fresh VOLTTRON installation.

💡 **Want to get started?**
   • Install some agents
   • Check out the platform driver for connecting to devices
   • Ask me "How do I install agents?" for help

Your VOLTTRON platform is ready - it just needs some agents to manage! 🤖
"""
                    else:
                        return f"{warning_msg}I'm up and running, but I don't have any agents installed yet. Pretty quiet around here!"
                
                # Make the status output more readable and conversational
                readable_status = make_status_readable(status_output)
                conversational_summary = make_status_conversational(status_output)
                
                # Return brief status by default, detailed explanation if requested
                if explain:
                    explanation = """
📊 **Here's what's happening with your VOLTTRON agents:**

Let me break down what you're seeing:
• **UUID** = Each agent gets a unique ID number  
• **AGENT** = The agent's name and version (like volttron-listener-2.0.0rc3)
• **IDENTITY** = How the agent introduces itself on the message bus
• **TAG** = Optional nickname you can give agents
• **PRIORITY** = Startup order (lower numbers start first)  
• **STATUS** = What the agent is doing right now
• **HEALTH** = How the agent is feeling (good/bad/unknown)

**Current Status:**
"""
                    return f"{warning_msg}{explanation}\n{readable_status}\n\n💬 Need help with any of these agents? Just ask!"
                else:
                    # For brief status, show both the formatted table AND conversational summary
                    return f"{warning_msg}🤖 **Here's what I've got running:**\n\n{readable_status}\n\n💬 {conversational_summary}"
                    
            else:
                error_msg = result.stderr or result.stdout or "Unknown error"
                
                if "not connected" in error_msg.lower() or "connection" in error_msg.lower():
                    if explain:
                        return f"""{warning_msg}❌ **Oops! VOLTTRON isn't running right now.**

The platform needs to be started before I can check on your agents.

🚀 **Ready to fire it up?** Just say:
   • "Start VOLTTRON"
   • "Launch the platform"  
   • "Get VOLTTRON running"

I'll get it started for you! ⚡
"""
                    else:
                        return f"{warning_msg}Uh oh, I'm not running right now! Want to start me up?"
                else:
                    # Try using process check as fallback to confirm VOLTTRON is running
                    if is_running:
                        return f"{warning_msg}VOLTTRON is running, but the status command had issues: {error_msg}. You might need to check it directly."
                    else:
                        return f"{warning_msg}I'm having trouble checking my status: {error_msg}"
        
        except subprocess.TimeoutExpired:
            # If vctl status times out but process check shows VOLTTRON is running
            if is_running:
                return f"VOLTTRON appears to be running, but the status command is taking too long to respond. This could mean the system is under heavy load or experiencing issues."
            else:
                return "VOLTTRON doesn't seem to be running currently. The status command timed out."
                
    except Exception as e:
        # Try using process check as final fallback
        try:
            if is_volttron_running_quick():
                return f"VOLTTRON appears to be running, but I encountered an error while checking detailed status: {str(e)}"
            else:
                return f"VOLTTRON doesn't seem to be running. Error details: {str(e)}"
        except Exception:
            return f"Something went wrong while I was checking on myself: {str(e)}"