from src.tools.restaurant_tools import (
    search_restaurants,
    get_restaurant_details,
    check_open_status,
    calculate_estimated_cost,
    human_escalation_fallback
)

def run_tests():
    print("--- Test 1: Search Restaurants (French in Tay Ho) ---")
    res1 = search_restaurants(cuisine="french", district="Tây Hồ")
    print(res1)
    
    print("\n--- Test 2: Search Restaurants (Price <= 50000, Rating >= 4.5) ---")
    res2 = search_restaurants(max_price=50000, min_rating=4.5)
    print(res2)
    
    print("\n--- Test 3: Get Detailed Info ---")
    res3 = get_restaurant_details("Phở Đặc Biệt")
    print(res3)
    
    print("\n--- Test 4: Check Open Status ---")
    res4 = check_open_status("Phở Đặc Biệt", "08:00")
    print("At 08:00: ", res4)
    res4_closed = check_open_status("Phở Đặc Biệt", "23:00")
    print("At 23:00: ", res4_closed)
    
    print("\n--- Test 5: Calculate Cost ---")
    res5 = calculate_estimated_cost("Hoa Sữa Restaurant", 4)
    print("Cost for 4 people: ", res5)
    
    print("\n--- Test 6: Fallback Tool ---")
    res6 = human_escalation_fallback("Cannot find any Mexican restaurant")
    print(res6)

if __name__ == "__main__":
    run_tests()
