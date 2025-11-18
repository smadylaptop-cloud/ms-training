from flask import Flask, jsonify, request
import requests
import os
import json
from confluent_kafka import Producer
import redis

ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL")
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP")
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")

if REDIS_HOST is None:
    raise RuntimeError("Environment variable REDIS_HOST is required but not set.")

if REDIS_PORT is None:
    raise RuntimeError("Environment variable REDIS_PORT is required but not set.")


if KAFKA_BOOTSTRAP is None:
    raise RuntimeError("Environment variable KAFKA_BOOTSTRAP is required but not set.")


if ORDER_SERVICE_URL is None:
    raise RuntimeError("Environment variable ORDER_SERVICE_URL is required but not set.")


redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)


# ---------------- Kafka Producer ---------------- #

producer_conf = {
    "bootstrap.servers": KAFKA_BOOTSTRAP
}

producer = Producer(producer_conf)

def send_kafka_message(topic, message_dict):
    """Serialize JSON and send to Kafka"""
    try:
        producer.produce(topic, json.dumps(message_dict).encode("utf-8"))
        producer.flush()
    except Exception as e:
        print("Kafka produce error:", e)

# ------------------------------------------------ #

app = Flask(__name__)

with open("data/users.json", "r") as f:
    users = json.load(f)

@app.route("/users/orders/<int:user_id>", methods=["GET"])
def get_user_orders(user_id):
    
    cache_key = f"user_orders:{user_id}"
    
    cached = redis_client.get(cache_key)
    if cached:
        cached_obj = json.loads(cached)
        cached_obj["from_cache"] = True
        return jsonify(cached_obj), 200
    
    user = next((u for u in users if u["id"] == user_id), None)
    if not user:
        return jsonify({"message": "User not found"}), 404

    try:
        response = requests.get(f"{ORDER_SERVICE_URL}/user/{user_id}")
    except Exception:
        return jsonify({"message": "Order service unavailable"}), 503

    orders = [] if response.status_code == 404 else response.json()
    
    result = {"user": user, "orders": orders,"from_cache": False}
    
    redis_client.setex(cache_key, 5, json.dumps(result))

    return jsonify(result), 200


@app.route("/users", methods=["GET"])
def get_users():
    return jsonify(users), 200


@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = next((u for u in users if u["id"] == user_id), None)
    if not user:
        return jsonify({"message": "User not found"}), 404
    return jsonify(user), 200


@app.route("/users", methods=["POST"])
def create_user():
    data = request.json
    new_user = {
        "id": len(users) + 1,
        "name": data.get("name")
    }
    users.append(new_user)

    # Save to JSON file
    with open("data/users.json", "w") as f:
        json.dump(users, f, indent=4)

    # ---- NEW: Send Kafka event ---- #
    send_kafka_message("NEW_USER_CREATED", new_user)

    return jsonify(new_user), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001)
