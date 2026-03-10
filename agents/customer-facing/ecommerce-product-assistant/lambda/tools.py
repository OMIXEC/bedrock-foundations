import json
import os
import boto3
from pinecone import Pinecone

pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
index = pc.Index("ecommerce-products")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("ecommerce-sessions")
bedrock = boto3.client("bedrock-runtime")

def search_products(query, max_price=None):
    response = bedrock.invoke_model(
        modelId="amazon.titan-embed-text-v2:0",
        body=json.dumps({"inputText": query})
    )
    embedding = json.loads(response["body"].read())["embedding"]
    results = index.query(vector=embedding, top_k=5, include_metadata=True)
    products = [m["metadata"] for m in results["matches"]]
    if max_price:
        products = [p for p in products if p["price"] <= max_price]
    return {"products": products}

def add_to_cart(session_id, product_id, quantity=1):
    response = table.get_item(Key={"session_id": session_id})
    cart = response.get("Item", {}).get("cart", [])
    cart.append({"product_id": product_id, "quantity": quantity})
    table.put_item(Item={"session_id": session_id, "cart": cart})
    return {"status": "added", "cart_size": len(cart)}

def check_inventory(product_id):
    return {"product_id": product_id, "in_stock": True, "quantity": 50}

def get_recommendations(session_id, product_id):
    product = index.fetch([product_id])["vectors"][product_id]
    results = index.query(vector=product["values"], top_k=4, include_metadata=True)
    return {"recommendations": [m["metadata"] for m in results["matches"][1:]]}

def handler(event, context):
    action = event["actionGroup"]
    function = event["function"]
    parameters = {p["name"]: p["value"] for p in event.get("parameters", [])}
    
    functions = {
        "search_products": lambda: search_products(parameters.get("query"), parameters.get("max_price")),
        "add_to_cart": lambda: add_to_cart(parameters["session_id"], parameters["product_id"], parameters.get("quantity", 1)),
        "check_inventory": lambda: check_inventory(parameters["product_id"]),
        "get_recommendations": lambda: get_recommendations(parameters["session_id"], parameters["product_id"])
    }
    
    result = functions[function]()
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": action,
            "function": function,
            "functionResponse": {"responseBody": {"TEXT": {"body": json.dumps(result)}}}
        }
    }
