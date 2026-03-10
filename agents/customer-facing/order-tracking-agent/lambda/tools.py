import json
import boto3
from datetime import datetime

dynamodb = boto3.resource("dynamodb")
sessions_table = dynamodb.Table("order-tracking-sessions")

# Mock shipping API
ORDERS = {
    "ORD-12345": {"status": "in_transit", "carrier": "UPS", "tracking": "1Z999AA10123456784", "eta": "2026-03-10"},
    "ORD-12346": {"status": "delivered", "carrier": "FedEx", "tracking": "123456789012", "delivered_at": "2026-03-05"},
    "ORD-12347": {"status": "processing", "carrier": None, "tracking": None, "eta": "2026-03-12"}
}

def lookup_order(order_id, session_id):
    order = ORDERS.get(order_id)
    if not order:
        return {"error": "Order not found"}
    
    # Store in session
    session = sessions_table.get_item(Key={"session_id": session_id}).get("Item", {})
    tracked_orders = session.get("tracked_orders", [])
    if order_id not in tracked_orders:
        tracked_orders.append(order_id)
    
    sessions_table.put_item(Item={
        "session_id": session_id,
        "tracked_orders": tracked_orders,
        "last_activity": datetime.now().isoformat()
    })
    
    return {"order_id": order_id, **order}

def track_shipment(tracking_number):
    # Mock tracking API call
    return {
        "tracking_number": tracking_number,
        "status": "in_transit",
        "location": "Memphis, TN",
        "last_update": "2026-03-08 14:30",
        "events": [
            {"time": "2026-03-08 14:30", "location": "Memphis, TN", "status": "In transit"},
            {"time": "2026-03-08 08:15", "location": "Louisville, KY", "status": "Departed facility"},
            {"time": "2026-03-07 22:00", "location": "Louisville, KY", "status": "Arrived at facility"}
        ]
    }

def initiate_return(order_id, reason):
    rma_number = f"RMA-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    return {
        "order_id": order_id,
        "rma_number": rma_number,
        "status": "approved",
        "return_label": f"https://returns.example.com/{rma_number}",
        "instructions": "Print label and drop off at any carrier location"
    }

def update_address(order_id, new_address):
    order = ORDERS.get(order_id)
    if not order:
        return {"error": "Order not found"}
    
    if order["status"] == "delivered":
        return {"error": "Cannot update address for delivered order"}
    
    if order["status"] == "in_transit":
        return {"error": "Order already shipped. Contact carrier for address change"}
    
    return {"order_id": order_id, "status": "address_updated", "new_address": new_address}

def handler(event, context):
    function = event["function"]
    parameters = {p["name"]: p["value"] for p in event.get("parameters", [])}
    
    functions = {
        "lookup_order": lambda: lookup_order(parameters["order_id"], parameters["session_id"]),
        "track_shipment": lambda: track_shipment(parameters["tracking_number"]),
        "initiate_return": lambda: initiate_return(parameters["order_id"], parameters["reason"]),
        "update_address": lambda: update_address(parameters["order_id"], parameters["new_address"])
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
