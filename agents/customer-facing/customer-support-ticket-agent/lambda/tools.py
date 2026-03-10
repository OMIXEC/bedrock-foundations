import json
import os
import boto3
from pinecone import Pinecone
from datetime import datetime

pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
pinecone_index = pc.Index("product-docs")
bedrock = boto3.client("bedrock-runtime")
bedrock_agent = boto3.client("bedrock-agent-runtime")
dynamodb = boto3.resource("dynamodb")
tickets_table = dynamodb.Table("support-tickets")

def search_solutions(query):
    # Search Pinecone KB
    response = bedrock.invoke_model(
        modelId="amazon.titan-embed-text-v2:0",
        body=json.dumps({"inputText": query})
    )
    embedding = json.loads(response["body"].read())["embedding"]
    results = pinecone_index.query(vector=embedding, top_k=3, include_metadata=True)
    
    # Search Bedrock KB
    kb_response = bedrock_agent.retrieve(
        knowledgeBaseId=os.environ["BEDROCK_KB_ID"],
        retrievalQuery={"text": query}
    )
    
    solutions = [m["metadata"] for m in results["matches"]]
    solutions.extend([r["content"]["text"] for r in kb_response["retrievalResults"]])
    return {"solutions": solutions}

def create_ticket(customer_id, issue, priority="medium"):
    ticket_id = f"TKT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    tickets_table.put_item(Item={
        "ticket_id": ticket_id,
        "customer_id": customer_id,
        "issue": issue,
        "priority": priority,
        "status": "open",
        "created_at": datetime.now().isoformat()
    })
    return {"ticket_id": ticket_id, "status": "created"}

def escalate_to_human(ticket_id, reason):
    tickets_table.update_item(
        Key={"ticket_id": ticket_id},
        UpdateExpression="SET #status = :status, escalation_reason = :reason",
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={":status": "escalated", ":reason": reason}
    )
    return {"ticket_id": ticket_id, "status": "escalated"}

def check_warranty(product_id, purchase_date):
    # Mock warranty check
    from datetime import datetime, timedelta
    purchase = datetime.fromisoformat(purchase_date)
    warranty_end = purchase + timedelta(days=365)
    is_valid = datetime.now() < warranty_end
    return {"product_id": product_id, "warranty_valid": is_valid, "expires": warranty_end.isoformat()}

def handler(event, context):
    function = event["function"]
    parameters = {p["name"]: p["value"] for p in event.get("parameters", [])}
    
    functions = {
        "search_solutions": lambda: search_solutions(parameters["query"]),
        "create_ticket": lambda: create_ticket(parameters["customer_id"], parameters["issue"], parameters.get("priority", "medium")),
        "escalate_to_human": lambda: escalate_to_human(parameters["ticket_id"], parameters["reason"]),
        "check_warranty": lambda: check_warranty(parameters["product_id"], parameters["purchase_date"])
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
