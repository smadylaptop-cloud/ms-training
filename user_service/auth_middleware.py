import os
import jwt
from flask import request, jsonify

JWT_SECRET = os.getenv("JWT_SECRET")

if JWT_SECRET is None:
    raise RuntimeError("JWT_SECRET environment variable is required but not set.")

JWT_ALGO = "HS256"

def require_jwt(func):
    """Decorator that checks for Authorization: Bearer <token>."""
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        token = auth_header.split(" ")[1]

        try:
            decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
            request.user = decoded  # store user info for route access
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidAudienceError as e:
            return jsonify({"error": f"Invalid audience: {str(e)}"}), 401
        except jwt.InvalidIssuerError as e:
            return jsonify({"error": f"Invalid issuer: {str(e)}"}), 401
        except jwt.DecodeError as e:
            return jsonify({"error": f"Decode error (signature mismatch or malformed): {str(e)}"}), 401
        except jwt.InvalidTokenError as e:
            return jsonify({"error": f"Other invalid token error: {str(e)}"}), 401

        return func(*args, **kwargs)

    wrapper.__name__ = func.__name__
    return wrapper
