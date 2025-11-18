from flask import Flask, jsonify, request
import json

with open("data/orders.json", "r") as f:
    orders = json.load(f)

app = Flask(__name__)


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
    order = [o for o in orders if o["user_id"] == user_id]
    return jsonify(order), 200

@app.route("/orders", methods=["POST"])
def create_order():
    data = request.json
    new_order = {
        "id": len(orders) + 1,
        "user_id": data.get("user_id"),
        "item": data.get("item")
    }
    
    orders.append(new_order)
    with open("data/orders.json", "w") as f:
        json.dump(orders, f, indent=4)
    
    return jsonify(new_order), 201

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8002)
