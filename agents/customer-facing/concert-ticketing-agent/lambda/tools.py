import json
import os
import boto3
from datetime import datetime, timedelta
import hashlib
import secrets

dynamodb = boto3.resource("dynamodb")
sessions_table = dynamodb.Table("ticketing-sessions")
orders_table = dynamodb.Table("ticket-orders")
cloudwatch = boto3.client("logs")

LOG_GROUP = "/aws/bedrock/ticketing-agent"

def log_audit(session_id, operation, resource_id, status, user_email=None):
    cloudwatch.put_log_events(
        logGroupName=LOG_GROUP,
        logStreamName=datetime.now().strftime("%Y/%m/%d"),
        logEvents=[{
            "timestamp": int(datetime.now().timestamp() * 1000),
            "message": f"{datetime.now().isoformat()} | {session_id} | {operation} | {resource_id} | {status} | {user_email or 'N/A'}"
        }]
    )

def verify_identity(session_id, email, order_id=None, card_last4=None):
    # Check verification attempts
    session = sessions_table.get_item(Key={"session_id": session_id}).get("Item", {})
    attempts = session.get("verification_attempts", 0)
    
    if attempts >= 3:
        log_audit(session_id, "VERIFY_IDENTITY", order_id or "N/A", "BLOCKED_MAX_ATTEMPTS", email)
        return {"verified": False, "error": "Maximum verification attempts exceeded"}
    
    # Verify credentials
    order = orders_table.get_item(Key={"order_id": order_id}).get("Item")
    if not order or order["email"] != email:
        sessions_table.update_item(
            Key={"session_id": session_id},
            UpdateExpression="SET verification_attempts = verification_attempts + :inc",
            ExpressionAttributeValues={":inc": 1}
        )
        log_audit(session_id, "VERIFY_IDENTITY", order_id, "FAILED", email)
        return {"verified": False, "error": "Invalid credentials"}
    
    # Create session token
    session_token = secrets.token_urlsafe(32)
    sessions_table.put_item(Item={
        "session_id": session_id,
        "session_token": session_token,
        "verified_user": True,
        "user_email": email,
        "order_id": order_id,
        "verification_attempts": 0,
        "last_activity": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(minutes=15)).isoformat()
    })
    
    log_audit(session_id, "VERIFY_IDENTITY", order_id, "SUCCESS", email)
    return {"verified": True, "session_token": session_token}

def retrieve_tickets(session_token):
    # Validate session
    response = sessions_table.scan(FilterExpression="session_token = :token", ExpressionAttributeValues={":token": session_token})
    if not response["Items"]:
        return {"error": "Invalid or expired session"}
    
    session = response["Items"][0]
    if datetime.fromisoformat(session["expires_at"]) < datetime.now():
        return {"error": "Session expired"}
    
    # Get tickets
    order = orders_table.get_item(Key={"order_id": session["order_id"]})["Item"]
    log_audit(session["session_id"], "RETRIEVE_TICKETS", session["order_id"], "SUCCESS", session["user_email"])
    return {"tickets": order["tickets"], "total": len(order["tickets"])}

def cancel_tickets(session_token, ticket_ids):
    response = sessions_table.scan(FilterExpression="session_token = :token", ExpressionAttributeValues={":token": session_token})
    if not response["Items"]:
        return {"error": "Invalid session"}
    
    session = response["Items"][0]
    order = orders_table.get_item(Key={"order_id": session["order_id"]})["Item"]
    
    # Check cancellation policy (>7 days = full refund)
    event_date = datetime.fromisoformat(order["event_date"])
    days_until = (event_date - datetime.now()).days
    refund_pct = 1.0 if days_until > 7 else 0.5 if days_until > 2 else 0.0
    
    refund_amount = sum(t["price"] for t in order["tickets"] if t["ticket_id"] in ticket_ids) * refund_pct
    
    # Update order
    orders_table.update_item(
        Key={"order_id": session["order_id"]},
        UpdateExpression="SET #status = :status",
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={":status": "cancelled"}
    )
    
    log_audit(session["session_id"], "CANCEL_TICKETS", session["order_id"], "SUCCESS", session["user_email"])
    return {"status": "cancelled", "refund_amount": refund_amount, "refund_days": "5-7"}

def reschedule_tickets(session_token, ticket_ids, new_event_id):
    response = sessions_table.scan(FilterExpression="session_token = :token", ExpressionAttributeValues={":token": session_token})
    if not response["Items"]:
        return {"error": "Invalid session"}
    
    session = response["Items"][0]
    # Mock price difference calculation
    price_diff = 25.00
    
    log_audit(session["session_id"], "RESCHEDULE_TICKETS", new_event_id, "SUCCESS", session["user_email"])
    return {"status": "rescheduled", "price_difference": price_diff, "new_event_id": new_event_id}

def transfer_tickets(session_token, ticket_ids, recipient_email):
    response = sessions_table.scan(FilterExpression="session_token = :token", ExpressionAttributeValues={":token": session_token})
    if not response["Items"]:
        return {"error": "Invalid session"}
    
    session = response["Items"][0]
    log_audit(session["session_id"], "TRANSFER_TICKETS", f"to:{recipient_email}", "SUCCESS", session["user_email"])
    return {"status": "transfer_initiated", "verification_sent": True, "recipient": recipient_email}

def check_event_status(event_id):
    # Mock event status
    return {"event_id": event_id, "status": "scheduled", "venue": "Madison Square Garden", "date": "2026-03-15"}

def handler(event, context):
    function = event["function"]
    parameters = {p["name"]: p["value"] for p in event.get("parameters", [])}
    
    functions = {
        "verify_identity": lambda: verify_identity(parameters["session_id"], parameters["email"], parameters.get("order_id"), parameters.get("card_last4")),
        "retrieve_tickets": lambda: retrieve_tickets(parameters["session_token"]),
        "cancel_tickets": lambda: cancel_tickets(parameters["session_token"], parameters["ticket_ids"]),
        "reschedule_tickets": lambda: reschedule_tickets(parameters["session_token"], parameters["ticket_ids"], parameters["new_event_id"]),
        "transfer_tickets": lambda: transfer_tickets(parameters["session_token"], parameters["ticket_ids"], parameters["recipient_email"]),
        "check_event_status": lambda: check_event_status(parameters["event_id"])
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
