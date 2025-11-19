from flask import Flask, request, jsonify
import requests
import os
import hashlib
import jwt
import datetime

# ============ Environment Variables ============

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL") 
JWT_SECRET       = os.getenv("JWT_SECRET")

JWT_ALGO         = "HS256"

if JWT_SECRET is None:
    raise RuntimeError("JWT_SECRET is required (example: supersecretkey)")

if USER_SERVICE_URL is None:
    raise RuntimeError("USER_SERVICE_URL is required (example: http://user-service:8001)")

# ============ Flask App ============

app = Flask(__name__)

# ============ Password Verification ============

def verify_password(input_password, salt, stored_hash):
    """Rebuild salted hash and compare."""
    calc_hash = hashlib.sha256((salt + input_password).encode()).hexdigest()
    return calc_hash == stored_hash

# ============ JWT Creation ============

def generate_token(user):
    payload = {
        "sub": user["id"],
        "name": user["name"],
        "email": user["email"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

# ============ Login Endpoint ============

@app.route("/auth/login", methods=["POST"])
def login():
    data = request.json

    if "email" not in data or "password" not in data:
        return jsonify({"message": "email and password are required"}), 400

    email = data["email"]
    password = data["password"]

    # 1️⃣ Call user-service to get user by email
    try:
        # This endpoint returns only public info (id, name, email)
        # But we need salt + hash → so we call the internal users.json list via a special route
        response = requests.get(f"{USER_SERVICE_URL}/email/{email}")
    except:
        return jsonify({"message": "User service unavailable"}), 503

    if response.status_code == 404:
        return jsonify({"message": "Invalid email or password"}), 401

    user = response.json()

    # 2️⃣ Verify password
    if not verify_password(password, user["salt"], user["password_hash"]):
        return jsonify({"message": "Invalid email or password"}), 401

    # 3️⃣ Generate JWT token
    token = generate_token(user)

    # 4️⃣ Return secure user info + token
    return jsonify({
        "token": token,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"]
        }
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8003)
