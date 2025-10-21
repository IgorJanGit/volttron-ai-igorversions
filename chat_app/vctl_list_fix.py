"""
This file contains a fix for the vctl_list_agents function that directly uses the vctl_status
function to ensure consistent agent reporting.
"""

def vctl_list_agents_fixed():
    """List all installed agents with their details by using vctl_status."""
    from .volttron_commands import vctl_status
    
    # IMPORTANT: We use vctl_status because it's more reliable
    print("FIXED: Using vctl_status as a more reliable replacement for vctl_list_agents")
    return vctl_status(explain=False)