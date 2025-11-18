from flask import Flask, jsonify, request
import requests
import os
import json

ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL")

if ORDER_SERVICE_URL is None:
    raise RuntimeError("Environment variable ORDER_SERVICE_URL is required but not set.")

app = Flask(__name__)

with open("data/users.json", "r") as f:
    users = json.load(f)

@app.route("/users/orders/<int:user_id>", methods=["GET"])
def get_user_orders(user_id):
    # 1. Find user locally
    user = next((u for u in users if u["id"] == user_id), None)
    if not user:
        return jsonify({"message": "User not found"}), 404

    # 2. Call Order Service
    try:
        response = requests.get(f"{ORDER_SERVICE_URL}/user/{user_id}")
    except Exception as e:
        return jsonify({"message": "Order service unavailable"}), 503

    # If the order service returns 404 → user has no orders
    if response.status_code == 404:
        orders = []
    else:
        orders = response.json()

    # 3. Combine user + orders
    result = {
        "user": user,
        "orders": orders
    }

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
    with open("data/users.json", "w") as f:
        json.dump(users, f, indent=4)
    return jsonify(new_user), 201

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001)
