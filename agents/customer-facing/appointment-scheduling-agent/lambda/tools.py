import json
import boto3
from datetime import datetime, timedelta

dynamodb = boto3.resource("dynamodb")
appointments_table = dynamodb.Table("appointments")

# Mock calendar API
CALENDAR = {}

def check_availability(date, duration_minutes=30):
    # Mock availability check
    dt = datetime.fromisoformat(date)
    if dt < datetime.now():
        return {"available": False, "error": "Cannot book in the past"}
    
    # Generate available slots (9 AM - 5 PM, 30-min intervals)
    slots = []
    start = dt.replace(hour=9, minute=0)
    end = dt.replace(hour=17, minute=0)
    
    current = start
    while current < end:
        slot_time = current.strftime("%H:%M")
        # Check if slot is taken
        if slot_time not in CALENDAR.get(date.split("T")[0], []):
            slots.append(slot_time)
        current += timedelta(minutes=duration_minutes)
    
    return {"available": len(slots) > 0, "slots": slots[:10]}

def book_appointment(date, time, duration_minutes, customer_name, customer_email, appointment_type):
    appointment_id = f"APT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Check for conflicts
    date_key = date.split("T")[0]
    if date_key in CALENDAR and time in CALENDAR[date_key]:
        return {"error": "Time slot already booked"}
    
    # Book slot
    if date_key not in CALENDAR:
        CALENDAR[date_key] = []
    CALENDAR[date_key].append(time)
    
    appointments_table.put_item(Item={
        "appointment_id": appointment_id,
        "date": date,
        "time": time,
        "duration_minutes": duration_minutes,
        "customer_name": customer_name,
        "customer_email": customer_email,
        "appointment_type": appointment_type,
        "status": "confirmed",
        "created_at": datetime.now().isoformat()
    })
    
    return {"appointment_id": appointment_id, "status": "confirmed", "date": date, "time": time}

def send_reminders(appointment_id):
    appointment = appointments_table.get_item(Key={"appointment_id": appointment_id}).get("Item")
    if not appointment:
        return {"error": "Appointment not found"}
    
    # Mock reminder scheduling
    return {
        "appointment_id": appointment_id,
        "reminders_scheduled": [
            {"type": "email", "time": "24 hours before"},
            {"type": "sms", "time": "2 hours before"}
        ]
    }

def reschedule(appointment_id, new_date, new_time):
    appointment = appointments_table.get_item(Key={"appointment_id": appointment_id}).get("Item")
    if not appointment:
        return {"error": "Appointment not found"}
    
    # Remove old slot
    old_date = appointment["date"].split("T")[0]
    if old_date in CALENDAR:
        CALENDAR[old_date].remove(appointment["time"])
    
    # Book new slot
    new_date_key = new_date.split("T")[0]
    if new_date_key not in CALENDAR:
        CALENDAR[new_date_key] = []
    CALENDAR[new_date_key].append(new_time)
    
    # Update appointment
    appointments_table.update_item(
        Key={"appointment_id": appointment_id},
        UpdateExpression="SET #date = :date, #time = :time",
        ExpressionAttributeNames={"#date": "date", "#time": "time"},
        ExpressionAttributeValues={":date": new_date, ":time": new_time}
    )
    
    return {"appointment_id": appointment_id, "status": "rescheduled", "new_date": new_date, "new_time": new_time}

def handler(event, context):
    function = event["function"]
    parameters = {p["name"]: p["value"] for p in event.get("parameters", [])}
    
    functions = {
        "check_availability": lambda: check_availability(parameters["date"], int(parameters.get("duration_minutes", 30))),
        "book_appointment": lambda: book_appointment(
            parameters["date"], parameters["time"], int(parameters["duration_minutes"]),
            parameters["customer_name"], parameters["customer_email"], parameters["appointment_type"]
        ),
        "send_reminders": lambda: send_reminders(parameters["appointment_id"]),
        "reschedule": lambda: reschedule(parameters["appointment_id"], parameters["new_date"], parameters["new_time"])
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
