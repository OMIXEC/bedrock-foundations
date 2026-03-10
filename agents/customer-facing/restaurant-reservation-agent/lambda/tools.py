import json
import os
import boto3
from datetime import datetime, timedelta

dynamodb = boto3.resource("dynamodb")
reservations_table = dynamodb.Table("restaurant-reservations")

# Mock restaurant API
RESTAURANTS = {
    "rest-001": {"name": "Italian Bistro", "capacity": 50, "hours": "11:00-22:00"},
    "rest-002": {"name": "Sushi Palace", "capacity": 30, "hours": "12:00-23:00"},
    "rest-003": {"name": "Steakhouse Prime", "capacity": 40, "hours": "17:00-23:00"}
}

def check_availability(restaurant_id, date, time, party_size):
    # Validation
    if party_size > 12:
        return {"available": False, "error": "Party size exceeds maximum (12)"}
    
    dt = datetime.fromisoformat(f"{date}T{time}")
    if dt < datetime.now():
        return {"available": False, "error": "Cannot book in the past"}
    
    # Check business hours
    restaurant = RESTAURANTS.get(restaurant_id)
    if not restaurant:
        return {"available": False, "error": "Restaurant not found"}
    
    hour = int(time.split(":")[0])
    if hour < 11 or hour > 22:
        return {"available": False, "error": "Outside business hours"}
    
    # Check capacity (mock)
    return {"available": True, "restaurant": restaurant["name"], "slots": ["18:00", "18:30", "19:00"]}

def create_reservation(restaurant_id, date, time, party_size, customer_name, customer_email):
    reservation_id = f"RES-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    reservations_table.put_item(Item={
        "reservation_id": reservation_id,
        "restaurant_id": restaurant_id,
        "date": date,
        "time": time,
        "party_size": party_size,
        "customer_name": customer_name,
        "customer_email": customer_email,
        "status": "confirmed",
        "created_at": datetime.now().isoformat()
    })
    return {"reservation_id": reservation_id, "status": "confirmed", "restaurant": RESTAURANTS[restaurant_id]["name"]}

def modify_booking(reservation_id, new_date=None, new_time=None, new_party_size=None):
    update_expr = "SET "
    expr_values = {}
    
    if new_date:
        update_expr += "#date = :date, "
        expr_values[":date"] = new_date
    if new_time:
        update_expr += "#time = :time, "
        expr_values[":time"] = new_time
    if new_party_size:
        update_expr += "party_size = :size, "
        expr_values[":size"] = new_party_size
    
    update_expr = update_expr.rstrip(", ")
    
    reservations_table.update_item(
        Key={"reservation_id": reservation_id},
        UpdateExpression=update_expr,
        ExpressionAttributeNames={"#date": "date", "#time": "time"},
        ExpressionAttributeValues=expr_values
    )
    return {"reservation_id": reservation_id, "status": "modified"}

def send_confirmation(reservation_id, customer_email):
    # Mock email send
    return {"status": "sent", "email": customer_email, "reservation_id": reservation_id}

def handler(event, context):
    function = event["function"]
    parameters = {p["name"]: p["value"] for p in event.get("parameters", [])}
    
    functions = {
        "check_availability": lambda: check_availability(
            parameters["restaurant_id"], parameters["date"], parameters["time"], int(parameters["party_size"])
        ),
        "create_reservation": lambda: create_reservation(
            parameters["restaurant_id"], parameters["date"], parameters["time"], 
            int(parameters["party_size"]), parameters["customer_name"], parameters["customer_email"]
        ),
        "modify_booking": lambda: modify_booking(
            parameters["reservation_id"], parameters.get("new_date"), 
            parameters.get("new_time"), parameters.get("new_party_size")
        ),
        "send_confirmation": lambda: send_confirmation(parameters["reservation_id"], parameters["customer_email"])
    }
    
    result = functions[function]()
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event["actionGroup"],
            "function": function,
            "functionResponse": {"responseBody": {"TEXT": {"body": json.dumps(result)}}}
        }
    }
