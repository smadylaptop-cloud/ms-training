from flask import Flask, jsonify, request
import requests
import os
import json
from confluent_kafka import Producer
import redis
import hashlib
import secrets
from auth_middleware import require_jwt

# ================== Environment Variables ==================

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

# ================== Redis ==================

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)

# ================== Kafka Producer ==================

producer_conf = {
    "bootstrap.servers": KAFKA_BOOTSTRAP
}
producer = Producer(producer_conf)

def send_kafka_message(topic, message_dict):
    try:
        producer.produce(topic, json.dumps(message_dict).encode("utf-8"))
        producer.flush()
    except Exception as e:
        print("Kafka produce error:", e)

# ================== Password Hashing ==================

def hash_password(password):
    """Create salt + SHA256 salted password hash."""
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return salt, hashed

# ================== Flask App ==================

app = Flask(__name__)

# Load users from file
if os.path.exists("data/users.json"):
    with open("data/users.json", "r") as f:
        users = json.load(f)
else:
    users = []

# ================== Routes ==================

@app.route("/users/orders/<int:user_id>", methods=["GET"])
def get_user_orders(user_id):

    cache_key = f"user_orders:{user_id}"

    cached = redis_client.get(cache_key)
    if cached:
        cached_obj = json.loads(cached)
        cached_obj["from_cache"] = True
        return jsonify(cached_obj), 200

    # find user
    user = next((u for u in users if u["id"] == user_id), None)
    if not user:
        return jsonify({"message": "User not found"}), 404

    # call order-service
    try:
        response = requests.get(f"{ORDER_SERVICE_URL}/user/{user_id}")
    except Exception:
        return jsonify({"message": "Order service unavailable"}), 503

    orders = [] if response.status_code == 404 else response.json()

    result = {
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"]
        },
        "orders": orders,
        "from_cache": False
    }

    redis_client.setex(cache_key, 5, json.dumps(result))

    return jsonify(result), 200


@app.route("/users", methods=["GET"])
@require_jwt 
def get_users():
    safe_users = [
        {"id": u["id"], "name": u["name"], "email": u["email"]}
        for u in users
    ]
    return jsonify(safe_users), 200


@app.route("/users/<int:user_id>", methods=["GET"])
@require_jwt    
def get_user(user_id):
    user = next((u for u in users if u["id"] == user_id), None)
    if not user:
        return jsonify({"message": "User not found"}), 404

    safe_user = {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"]
    }

    return jsonify(safe_user), 200


@app.route("/users", methods=["POST"])
@require_jwt
def create_user():
    data = request.json

    if "name" not in data or "email" not in data or "password" not in data:
        return jsonify({"message": "name, email, and password are required"}), 400

    # hash the password
    salt, password_hash = hash_password(data["password"])

    new_user = {
        "id": len(users) + 1,
        "name": data["name"],
        "email": data["email"],
        "salt": salt,
        "password_hash": password_hash
    }

    users.append(new_user)

    # save to file
    with open("data/users.json", "w") as f:
        json.dump(users, f, indent=4)

    # send kafka event (safe public info only)
    send_kafka_message("NEW_USER_CREATED", {
        "id": new_user["id"],
        "name": new_user["name"],
        "email": new_user["email"]
    })

    # return safe user without password hash
    safe_response = {
        "id": new_user["id"],
        "name": new_user["name"],
        "email": new_user["email"]
    }

    return jsonify(safe_response), 201


@app.route("/users/email/<string:email>", methods=["GET"])
def get_user_by_email(email):
    # Case-insensitive match
    user = next((u for u in users if u["email"].lower() == email.lower()), None)

    if not user:
        return jsonify({"message": "User not found"}), 404

    safe_user = {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "salt": user["salt"],
        "password_hash": user["password_hash"]
    }

    return jsonify(safe_user), 200



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001)
