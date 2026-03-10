import json
import boto3

bedrock = boto3.client("bedrock-agent-runtime")
dynamodb = boto3.resource("dynamodb")
sessions_table = dynamodb.Table("hotel-booking-sessions")

# Sub-agent IDs (created separately)
SEARCH_AGENT_ID = "search-agent-id"
PRICING_AGENT_ID = "pricing-agent-id"
BOOKING_AGENT_ID = "booking-agent-id"

def search_hotels(location, checkin, checkout, guests):
    response = bedrock.invoke_agent(
        agentId=SEARCH_AGENT_ID,
        agentAliasId="TSTALIASID",
        sessionId=f"search-{location}",
        inputText=f"Find hotels in {location} for {guests} guests from {checkin} to {checkout}"
    )
    
    result = ""
    for event in response["completion"]:
        if "chunk" in event:
            result += event["chunk"]["bytes"].decode()
    
    return {"hotels": result}

def calculate_total_cost(hotel_id, checkin, checkout, room_type, guests):
    response = bedrock.invoke_agent(
        agentId=PRICING_AGENT_ID,
        agentAliasId="TSTALIASID",
        sessionId=f"pricing-{hotel_id}",
        inputText=f"Calculate cost for {hotel_id}, {room_type}, {checkin} to {checkout}, {guests} guests"
    )
    
    result = ""
    for event in response["completion"]:
        if "chunk" in event:
            result += event["chunk"]["bytes"].decode()
    
    return {"pricing": result}

def apply_discounts(total_amount, customer_tier="standard"):
    discounts = {"standard": 0, "silver": 0.05, "gold": 0.10, "platinum": 0.15}
    discount = discounts.get(customer_tier, 0)
    final_amount = total_amount * (1 - discount)
    return {"original": total_amount, "discount": discount * 100, "final": final_amount}

def process_booking(session_id, hotel_id, room_type, checkin, checkout):
    # Get session data
    session = sessions_table.get_item(Key={"session_id": session_id}).get("Item", {})
    
    response = bedrock.invoke_agent(
        agentId=BOOKING_AGENT_ID,
        agentAliasId="TSTALIASID",
        sessionId=session_id,
        inputText=f"Book {hotel_id}, {room_type}, {checkin} to {checkout}"
    )
    
    result = ""
    for event in response["completion"]:
        if "chunk" in event:
            result += event["chunk"]["bytes"].decode()
    
    return {"booking": result, "confirmation": f"BKG-{session_id[:8]}"}

def handler(event, context):
    function = event["function"]
    parameters = {p["name"]: p["value"] for p in event.get("parameters", [])}
    
    functions = {
        "search_hotels": lambda: search_hotels(
            parameters["location"], parameters["checkin"], parameters["checkout"], int(parameters["guests"])
        ),
        "calculate_total_cost": lambda: calculate_total_cost(
            parameters["hotel_id"], parameters["checkin"], parameters["checkout"], 
            parameters["room_type"], int(parameters["guests"])
        ),
        "apply_discounts": lambda: apply_discounts(float(parameters["total_amount"]), parameters.get("customer_tier", "standard")),
        "process_booking": lambda: process_booking(
            parameters["session_id"], parameters["hotel_id"], parameters["room_type"], 
            parameters["checkin"], parameters["checkout"]
        )
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
