from flask import Flask, jsonify, request
import json
import os
import threading
from confluent_kafka import Consumer, KafkaError
from auth_middleware import require_jwt
import requests
import redis


USER_SERVICE_URL = os.getenv("USER_SERVICE_URL")
SERVICE_APP_ID = os.getenv("SERVICE_APP_ID")
SERVICE_APP_SECRET = os.getenv("SERVICE_APP_SECRET")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL")

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)

if REDIS_HOST is None:
    raise RuntimeError("Environment variable REDIS_HOST is required but not set.")

if REDIS_PORT is None:
    raise RuntimeError("Environment variable REDIS_PORT is required but not set.")

if SERVICE_APP_ID is None or SERVICE_APP_SECRET is None:
    raise RuntimeError("Environment variables SERVICE_APP_ID and SERVICE_APP_SECRET are required but not set.")

if USER_SERVICE_URL is None:
    raise RuntimeError("Environment variable USER_SERVICE_URL is required but not set.")

app = Flask(__name__)

ORDERS_FILE = "data/orders.json"

# ---------------- Load existing orders ---------------- #
if os.path.exists(ORDERS_FILE):
    with open(ORDERS_FILE, "r") as f:
        orders = json.load(f)
else:
    orders = []

# ---------------- Helper Functions ---------------- #
def add_order_to_storage(user_id, item, request_type="api"):
    """Add an order to the in-memory list and save to file.

    - request_type="api": JWT from incoming request headers
    - request_type="kafka": get service JWT from Auth Service
    """
    headers = {}

    if request_type == "api":
        # Get JWT from incoming request headers
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            headers["Authorization"] = auth_header
        else:
            return {"error": "Missing Authorization header"}, 401

    elif request_type == "kafka":
        # Request a service JWT from Auth Service
        try:
            cache_key = f"user_orders:SYSTEM_TOKEN"
            cached = redis_client.get(cache_key)
            if cached:
                token = cached
            else:
                resp = requests.post(f"{AUTH_SERVICE_URL}/service-login", json={
                    "app_id": SERVICE_APP_ID,
                    "app_secret": SERVICE_APP_SECRET
                })
                if resp.status_code != 200:
                    return {"error": "Failed to get service token"}, 500
                token = resp.json()["token"]
                redis_client.setex(cache_key,  300, token)
            
            headers["Authorization"] = f"Bearer {token}"
        except Exception as e:
            return {"error": "Auth service unavailable", "details": str(e)}, 503

    # ----- Validate user via User Service -----
    try:
        user_response = requests.get(f"{USER_SERVICE_URL}/{user_id}", headers=headers)
    except Exception as e:
        return {"error": "User service unavailable", "details": str(e)}, 503

    if user_response.status_code == 404:
        return {"error": "User not found"}, 404

    if user_response.status_code != 200:
        return {"error": "Failed to validate user"}, 500

    # ----- Create the order -----
    new_order = {
        "id": len(orders) + 1,
        "user_id": user_id,
        "item": item
    }

    orders.append(new_order)
    with open(ORDERS_FILE, "w") as f:
        json.dump(orders, f, indent=4)

    return new_order, 201

# ---------------- Flask Routes ---------------- #
@app.route("/orders", methods=["GET"])
def get_orders():
    return jsonify(orders), 200

@app.route("/orders/<int:order_id>", methods=["GET"])
def get_order(order_id):
    order = next((o for o in orders if o["id"] == order_id), None)
    if not order:
        return jsonify({"message": "Order not found"}), 404
    return jsonify(order), 200

@app.route("/orders/user/<int:user_id>", methods=["GET"])
def get_orders_by_user_id(user_id):
    user_orders = [o for o in orders if o["user_id"] == user_id]
    return jsonify(user_orders), 200

@app.route("/orders", methods=["POST"])
@require_jwt
def create_order_api():
    """Flask route to create a new order."""
    data = request.json
    user_id = data.get("user_id")
    item = data.get("item")
    if not user_id or not item:
        return jsonify({"message": "user_id and item are required"}), 400

    new_order = add_order_to_storage(user_id, item)
    return jsonify(new_order), 201

# ---------------- Kafka Consumer ---------------- #
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP")

if KAFKA_BOOTSTRAP is None:
    raise RuntimeError("Environment variable KAFKA_BOOTSTRAP is required but not set.")

KAFKA_TOPIC = "NEW_USER_CREATED"

consumer_conf = {
    "bootstrap.servers": KAFKA_BOOTSTRAP,
    "group.id": "order-service-group",
    "auto.offset.reset": "latest" #latest, earliest
}

consumer = Consumer(consumer_conf)

def consume_new_users():
    """Kafka consumer for NEW_USER_CREATED messages."""
    consumer.subscribe([KAFKA_TOPIC])
    while True:
        msg = consumer.poll(timeout=1.0)
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() != KafkaError._PARTITION_EOF:
                print("Kafka error:", msg.error())
            continue
        try:
            new_user = json.loads(msg.value().decode("utf-8"))
            print("Received NEW_USER_CREATED:", new_user)
            # Use shared function to create gift order
            gift_order = add_order_to_storage(new_user["id"], "🎁 Welcome Gift", request_type="kafka")
            print(f"Created gift order: {gift_order}")
        except Exception as e:
            print("Error processing Kafka message:", e)

# Run consumer in a background thread
threading.Thread(target=consume_new_users, daemon=True).start()

# ---------------- Main ---------------- #
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8002)
