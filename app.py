
import os
from flask import Flask, request, jsonify
import uuid
import requests

app = Flask(__name__)

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
LOCATION_ID = os.getenv("LOCATION_ID")
BASE_URL = "https://connect.squareup.com"

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

@app.route("/")
def index():
    return "Gift Card Manager is running."

@app.route("/create", methods=["POST"])
def create_card():
    try:
        amount_dollars = float(request.json.get("amount"))
        amount_cents = int(amount_dollars * 100)
    except:
        return jsonify({"error": "Invalid amount"}), 400

    create_url = f"{BASE_URL}/v2/gift-cards"
    create_body = {
        "idempotency_key": str(uuid.uuid4()),
        "location_id": LOCATION_ID
    }
    res = requests.post(create_url, headers=HEADERS, json=create_body)
    if res.status_code != 200:
        return jsonify({"error": "Failed to create gift card", "details": res.json()}), 400

    gift_card = res.json()["gift_card"]
    gift_card_id = gift_card["id"]
    gan = gift_card["gan"]

    load_url = f"{BASE_URL}/v2/gift-cards/activities"
    load_body = {
        "idempotency_key": str(uuid.uuid4()),
        "gift_card_id": gift_card_id,
        "location_id": LOCATION_ID,
        "type": "ACTIVATE",
        "activate_activity_details": {
            "amount_money": {
                "amount": amount_cents,
                "currency": "USD"
            }
        }
    }
    load_res = requests.post(load_url, headers=HEADERS, json=load_body)
    if load_res.status_code != 200:
        return jsonify({"error": "Failed to load gift card", "details": load_res.json()}), 400

    return jsonify({"success": True, "gan": gan, "amount": amount_dollars})

@app.route("/balance", methods=["POST"])
def check_balance():
    gan = request.json.get("gan")
    if not gan:
        return jsonify({"error": "Missing card number"}), 400

    search_url = f"{BASE_URL}/v2/gift-cards/from-gan"
    res = requests.post(search_url, headers=HEADERS, json={"gan": gan})
    if res.status_code != 200:
        return jsonify({"error": "Failed to find card", "details": res.json()}), 400

    gift_card_id = res.json()["gift_card"]["id"]
    card_url = f"{BASE_URL}/v2/gift-cards/{gift_card_id}"
    balance_res = requests.get(card_url, headers=HEADERS)
    if balance_res.status_code != 200:
        return jsonify({"error": "Failed to retrieve balance", "details": balance_res.json()}), 400

    balance = balance_res.json()["gift_card"]["balance_money"]["amount"] / 100
    return jsonify({"balance": balance})

@app.route("/redeem", methods=["POST"])
def redeem_card():
    gan = request.json.get("gan")
    amount_dollars = float(request.json.get("amount", 0))
    amount_cents = int(amount_dollars * 100)

    search_url = f"{BASE_URL}/v2/gift-cards/from-gan"
    res = requests.post(search_url, headers=HEADERS, json={"gan": gan})
    if res.status_code != 200:
        return jsonify({"error": "Card not found", "details": res.json()}), 400

    gift_card_id = res.json()["gift_card"]["id"]
    redeem_url = f"{BASE_URL}/v2/gift-cards/activities"
    redeem_body = {
        "idempotency_key": str(uuid.uuid4()),
        "gift_card_id": gift_card_id,
        "location_id": LOCATION_ID,
        "type": "REDEEM",
        "redeem_activity_details": {
            "amount_money": {
                "amount": amount_cents,
                "currency": "USD"
            }
        }
    }
    redeem_res = requests.post(redeem_url, headers=HEADERS, json=redeem_body)
    if redeem_res.status_code != 200:
        return jsonify({"error": "Redemption failed", "details": redeem_res.json()}), 400

    return jsonify({"success": True, "redeemed": amount_dollars})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
