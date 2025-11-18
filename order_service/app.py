from flask import Flask, jsonify, request
import json
import os
import threading
from confluent_kafka import Consumer, KafkaError

app = Flask(__name__)

ORDERS_FILE = "data/orders.json"

# ---------------- Load existing orders ---------------- #
if os.path.exists(ORDERS_FILE):
    with open(ORDERS_FILE, "r") as f:
        orders = json.load(f)
else:
    orders = []

# ---------------- Helper Functions ---------------- #
def add_order_to_storage(user_id, item):
    """Add an order to the in-memory list and save to file."""
    new_order = {
        "id": len(orders) + 1,
        "user_id": user_id,
        "item": item
    }
    orders.append(new_order)
    with open(ORDERS_FILE, "w") as f:
        json.dump(orders, f, indent=4)
    return new_order

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
            gift_order = add_order_to_storage(new_user["id"], "🎁 Welcome Gift")
            print(f"Created gift order: {gift_order}")
        except Exception as e:
            print("Error processing Kafka message:", e)

# Run consumer in a background thread
threading.Thread(target=consume_new_users, daemon=True).start()

# ---------------- Main ---------------- #
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8002)
