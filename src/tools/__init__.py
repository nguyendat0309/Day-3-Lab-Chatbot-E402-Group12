# Initialize the tools module
from .restaurant_tools import (
    search_restaurants,
    get_restaurant_details,
    check_open_status,
    calculate_estimated_cost,
    human_escalation_fallback
)

# Export all tools in a list or registry if needed by the agent logic
AVAILABLE_TOOLS = {
    "search_restaurants": search_restaurants,
    "get_restaurant_details": get_restaurant_details,
    "check_open_status": check_open_status,
    "calculate_estimated_cost": calculate_estimated_cost,
    "human_escalation_fallback": human_escalation_fallback
}
