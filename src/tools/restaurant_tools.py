import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

# Load data once when the module is imported
# Adjust path assuming this runs from the root of the project
DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'restaurants_hanoi.json')

def load_data() -> List[Dict[str, Any]]:
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading data from {DATA_FILE}: {e}")
        return []

RESTAURANTS = load_data()

def search_restaurants(
    cuisine: str = None,
    district: str = None,
    max_price: int = None,
    min_rating: float = None,
    dish_type: str = None,
    ambiance: str = None,
    amenity: str = None
) -> str:
    """
    Search for a list of restaurants based on filter criteria. Very useful when the user asks to "find an X restaurant in area Y".

    Args:
        cuisine (str, optional): Type of cuisine (e.g., "vietnamese", "french", "japanese", "korean", "italian", "seafood", "vegetarian").
        district (str, optional): District in Hanoi (e.g., "Cầu Giấy", "Tây Hồ", "Đống Đa", "Hoàn Kiếm", "Ba Đình", "Hai Bà Trưng", "Thanh Xuân", "Nam Từ Liêm", "Hà Đông").
        max_price (int, optional): Maximum average price per person in VND.
        min_rating (float, optional): Minimum rating score (e.g., 4.0, 4.5).
        dish_type (str, optional): Specific dish type (e.g., "phở", "bún_chả", "sushi", "bbq", "buffet", "fine_dining", "casual_dining", "cơm").
        ambiance (str, optional): Atmosphere of the restaurant (e.g., "romantic", "casual", "elegant", "cozy_indoor", "street_food_style").
        amenity (str, optional): A required facility (e.g., "wifi", "parking", "live_music", "outdoor_seating", "air_conditioning").

    Returns:
        str: A JSON string containing a list of matched restaurants (includes name, id, cuisine, dish_type, district, price_avg, rating, ambiance). Returns an error message if none found.
    """
    results = RESTAURANTS
    if cuisine:
        results = [r for r in results if r.get('cuisine', '').lower() == cuisine.lower()]
    if district:
        results = [r for r in results if r.get('district', '').lower() == district.lower()]
    if max_price is not None:
        results = [r for r in results if r.get('price_avg', float('inf')) <= max_price]
    if min_rating is not None:
        results = [r for r in results if r.get('rating', 0.0) >= min_rating]
    if dish_type:
        results = [r for r in results if r.get('dish_type', '').lower() == dish_type.lower()]
    if ambiance:
        results = [r for r in results if r.get('ambiance', '').lower() == ambiance.lower()]
    if amenity:
        results = [r for r in results if amenity.lower() in [a.lower() for a in r.get('amenities', [])]]

    if not results:
        return json.dumps({"error": "Could not find any restaurants matching these criteria."}, ensure_ascii=False)

    # Drop detailed info to save LLM context window tokens
    simplified_results = [
        {
            "id": r["id"],
            "name": r["name"],
            "cuisine": r["cuisine"],
            "dish_type": r.get("dish_type", ""),
            "district": r["district"],
            "price_avg": r["price_avg"],
            "rating": r["rating"],
            "ambiance": r.get("ambiance", "")
        } for r in results
    ]
    return json.dumps(simplified_results, ensure_ascii=False)

def get_restaurant_details(restaurant_name: str) -> str:
    """
    Look up detailed information of a specific restaurant based on its name. Use this when you know the restaurant name and need more data about it.
    
    Args:
        restaurant_name (str): The exact or partial name of the restaurant.
        
    Returns:
        str: A JSON string containing full detailed info of the restaurant (address, opening hours, capacity, amenities, etc.).
    """
    for r in RESTAURANTS:
        if restaurant_name.lower() in r['name'].lower():
            return json.dumps(r, ensure_ascii=False)
    return json.dumps({"error": f"Could not find detailed data for a restaurant named '{restaurant_name}'."}, ensure_ascii=False)

def check_open_status(restaurant_name: str, time_str: str) -> str:
    """
    Check if a restaurant is currently open at a specific time.
    
    Args:
        restaurant_name (str): The name of the restaurant to check.
        time_str (str): The time to check in "HH:MM" format (e.g., "09:30", "21:00").
        
    Returns:
        str: A message stating whether the restaurant is OPEN or CLOSED at that time, or an error if the time_str format is invalid.
    """
    restaurant = None
    for r in RESTAURANTS:
        if restaurant_name.lower() in r['name'].lower():
            restaurant = r
            break
            
    if not restaurant:
        return json.dumps({"error": f"Could not find a restaurant named '{restaurant_name}' to check opening hours."}, ensure_ascii=False)
        
    opening_hours = restaurant.get("opening_hours", {})
    open_time_str = opening_hours.get("open")
    close_time_str = opening_hours.get("close")
    
    if not open_time_str or not close_time_str:
        return json.dumps({"status": "unknown", "message": "This restaurant does not have specific opening hours data."}, ensure_ascii=False)
        
    try:
        check_time = datetime.strptime(time_str, "%H:%M").time()
        open_time = datetime.strptime(open_time_str, "%H:%M").time()
        close_time = datetime.strptime(close_time_str, "%H:%M").time()
        
        # Assumption: No restaurant in this dataset has overnight hours (e.g., 22:00 PM to 06:00 AM)
        if open_time <= check_time <= close_time:
             return json.dumps({"status": "open", "message": f"Restaurant '{restaurant['name']}' is OPEN at {time_str} (Operating Hours: {open_time_str} - {close_time_str})."}, ensure_ascii=False)
        else:
             return json.dumps({"status": "closed", "message": f"Restaurant '{restaurant['name']}' is CLOSED at {time_str} (Operating Hours: {open_time_str} - {close_time_str})."}, ensure_ascii=False)
    except ValueError:
        return json.dumps({"error": "Invalid time format. Please use 'HH:MM' format."}, ensure_ascii=False)

def calculate_estimated_cost(restaurant_name: str, num_people: int) -> str:
    """
    Calculate the estimated total cost for a specific number of people eating at a certain restaurant.
    
    Args:
        restaurant_name (str): The name of the restaurant.
        num_people (int): The number of people having the meal.
        
    Returns:
        str: A string containing the total estimated cost in VND.
    """
    if num_people <= 0:
        return json.dumps({"error": "Number of people must be strictly greater than 0."}, ensure_ascii=False)
        
    for r in RESTAURANTS:
        if restaurant_name.lower() in r['name'].lower():
            avg_price = r.get("price_avg", 0)
            total = avg_price * num_people
            return json.dumps({"restaurant": r['name'], "num_people": num_people, "estimated_total_cost_vnd": total}, ensure_ascii=False)
            
    return json.dumps({"error": f"Could not find restaurant '{restaurant_name}' to calculate cost."}, ensure_ascii=False)

def human_escalation_fallback(reason: str) -> str:
    """
    Call this tool ONLY when the Agent encounters repeated errors, cannot understand the request, 
    or when no matching data can be found after trying multiple searches (e.g. Edge Cases).
    
    Args:
        reason (str): The reason for escalating to a human agent (e.g., "Cannot find any Mexican food in Cau Giay").
        
    Returns:
        str: A confirmation code that the request has been forwarded to human support.
    """
    return json.dumps({
        "status": "escalated_to_human", 
        "reason": reason, 
        "message": "The request has been forwarded to customer support. Please output the Final Answer to let the user know they will be contacted shortly."
    }, ensure_ascii=False)
