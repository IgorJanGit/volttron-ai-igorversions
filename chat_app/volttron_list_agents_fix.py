"""
Fix for the vctl_list_agents function to ensure it properly shows installed agents
by using vctl_status instead.
"""

def vctl_list_agents():
    """List all installed agents with their details."""
    # Import here to avoid circular imports
    from .volttron_commands import vctl_status
    
    # IMPORTANT: This function has reliability issues.
    # We're going to just delegate to the vctl_status function which is more reliable
    # This ensures agents are consistently reported whether using status or list_agents
    print("Using vctl_status as a more reliable replacement for vctl_list_agents")
    return vctl_status(explain=False)