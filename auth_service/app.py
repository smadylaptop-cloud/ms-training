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

# Service credentials (all services share the same)
SERVICE_APP_ID     = os.getenv("SERVICE_APP_ID")
SERVICE_APP_SECRET = os.getenv("SERVICE_APP_SECRET")

if JWT_SECRET is None:
    raise RuntimeError("JWT_SECRET is required (example: supersecretkey)")
if USER_SERVICE_URL is None:
    raise RuntimeError("USER_SERVICE_URL is required (example: http://user-service:8001)")
if SERVICE_APP_ID is None or SERVICE_APP_SECRET is None:
    raise RuntimeError("SERVICE_APP_ID and SERVICE_APP_SECRET are required for service login")

# ============ Flask App ============
app = Flask(__name__)

# ============ Password Verification ============
def verify_password(input_password, salt, stored_hash):
    """Rebuild salted hash and compare."""
    calc_hash = hashlib.sha256((salt + input_password).encode()).hexdigest()
    return calc_hash == stored_hash

# ============ JWT Creation ============
def generate_token(user_or_service, is_service=False):
    payload = {
        "sub": str(user_or_service["id"]) if not is_service else user_or_service["app_id"],
        "name": user_or_service.get("name") or user_or_service["app_id"],
        "email": user_or_service.get("email") if not is_service else None,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        "is_service": is_service
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token

# ============ User Login ============
@app.route("/auth/login", methods=["POST"])
def login():
    data = request.json
    if "email" not in data or "password" not in data:
        return jsonify({"message": "email and password are required"}), 400

    email = data["email"]
    password = data["password"]

    try:
        response = requests.get(f"{USER_SERVICE_URL}/email/{email}")
    except:
        return jsonify({"message": "User service unavailable"}), 503

    if response.status_code == 404:
        return jsonify({"message": "Invalid email or password"}), 401

    user = response.json()
    if not verify_password(password, user["salt"], user["password_hash"]):
        return jsonify({"message": "Invalid email or password"}), 401

    token = generate_token(user)
    return jsonify({
        "token": token,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"]
        }
    }), 200

# ============ Service Login ============
@app.route("/auth/service-login", methods=["POST"])
def service_login():
    data = request.json
    if "app_id" not in data or "app_secret" not in data:
        return jsonify({"message": "app_id and app_secret are required"}), 400

    app_id = data["app_id"]
    app_secret = data["app_secret"]

    # Validate against env vars
    if app_id != SERVICE_APP_ID or app_secret != SERVICE_APP_SECRET:
        return jsonify({"message": "Invalid app_id or app_secret"}), 401

    token = generate_token({"app_id": app_id}, is_service=True)
    return jsonify({"token": token, "app_id": app_id}), 200

# ======================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8003)
