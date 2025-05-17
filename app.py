import os
import uuid
import requests
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET", "supersecretkey")

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
LOCATION_ID = os.getenv("LOCATION_ID")
BASE_URL = "https://connect.squareup.com"

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")

@app.route("/create", methods=["POST"])
def create():
    amount = request.form.get("amount")
    if not amount:
        flash("Amount is required", "error")
        return redirect(url_for("index"))

    try:
        amount_cents = int(float(amount) * 100)
    except:
        flash("Invalid amount format", "error")
        return redirect(url_for("index"))

    create_url = f"{BASE_URL}/v2/gift-cards"
    create_body = {
        "idempotency_key": str(uuid.uuid4()),
        "location_id": LOCATION_ID
    }
    res = requests.post(create_url, headers=HEADERS, json=create_body)
    if res.status_code != 200:
        flash("Gift card creation failed", "error")
        return redirect(url_for("index"))

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
        flash("Gift card loading failed", "error")
        return redirect(url_for("index"))

    flash(f"✅ Created and loaded gift card: {gan} with ${amount}", "success")
    return redirect(url_for("index"))

@app.route("/redeem", methods=["POST"])
def redeem():
    gan = request.form.get("redeem_gan")
    amount = request.form.get("redeem_amount")
    if not gan or not amount:
        flash("Both card number and amount are required", "error")
        return redirect(url_for("index"))

    try:
        amount_cents = int(float(amount) * 100)
    except:
        flash("Invalid amount", "error")
        return redirect(url_for("index"))

    find_url = f"{BASE_URL}/v2/gift-cards/from-gan"
    res = requests.post(find_url, headers=HEADERS, json={"gan": gan})
    if res.status_code != 200:
        flash("Card not found", "error")
        return redirect(url_for("index"))

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
        flash("Redemption failed", "error")
        return redirect(url_for("index"))

    flash(f"✅ Redeemed ${amount} from card {gan}", "success")
    return redirect(url_for("index"))

@app.route("/check", methods=["POST"])
def check():
    gan = request.form.get("check_gan")
    if not gan:
        flash("Card number is required", "error")
        return redirect(url_for("index"))

    search_url = f"{BASE_URL}/v2/gift-cards/from-gan"
    res = requests.post(search_url, headers=HEADERS, json={"gan": gan})
    if res.status_code != 200:
        flash("Card not found", "error")
        return redirect(url_for("index"))

    gift_card = res.json()["gift_card"]
    balance = gift_card.get("balance_money", {}).get("amount", 0) / 100
    flash(f"💳 Balance for {gan}: ${balance:.2f}", "success")
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
