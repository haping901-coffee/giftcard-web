
import os
import uuid
from flask import Flask, request, redirect, url_for, flash, render_template_string
import requests

app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET", "supersecretkey")

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
LOCATION_ID = os.getenv("LOCATION_ID")
BASE_URL = "https://connect.squareup.com"

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Gift Card Sales Recorder</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f9f9f9; }
        h1 { color: #333; }
        form { background: #fff; padding: 20px; margin-bottom: 20px; border-radius: 8px; }
        label, input, button { display: block; margin: 10px 0; }
        input, button { padding: 8px; }
        .success { color: green; }
        .error { color: red; }
    </style>
</head>
<body>
    <h1>Gift Card Sale</h1>
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        {% for category, message in messages %}
          <p class="{{ category }}">{{ message }}</p>
        {% endfor %}
      {% endif %}
    {% endwith %}
    <form method="POST" action="/redeem">
        <label>Gift Card Number (GAN):</label>
        <input type="text" name="gan" required>
        <label>Amount to Redeem ($):</label>
        <input type="number" name="amount" step="0.01" required>
        <button type="submit">Redeem and Record Sale</button>
    </form>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/redeem", methods=["POST"])
def redeem():
    gan = request.form.get("gan")
    amount_dollars = request.form.get("amount")
    if not gan or not amount_dollars:
        flash("Card number and amount are required", "error")
        return redirect(url_for("index"))

    try:
        amount_cents = int(float(amount_dollars) * 100)
    except ValueError:
        flash("Invalid amount format", "error")
        return redirect(url_for("index"))

    # Step 1: Lookup the gift card by GAN
    find_url = f"{BASE_URL}/v2/gift-cards/from-gan"
    find_res = requests.post(find_url, headers=HEADERS, json={"gan": gan})
    if find_res.status_code != 200:
        flash("Gift card not found", "error")
        return redirect(url_for("index"))

    gift_card_id = find_res.json()["gift_card"]["id"]

    # Step 2: Redeem the gift card
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

    # Step 3: Create an order
    order_url = f"{BASE_URL}/v2/orders"
    order_body = {
        "order": {
            "location_id": LOCATION_ID,
            "line_items": [
                {
                    "name": "External Gift Card Sale",
                    "quantity": "1",
                    "base_price_money": {
                        "amount": amount_cents,
                        "currency": "USD"
                    }
                }
            ]
        },
        "idempotency_key": str(uuid.uuid4())
    }
    order_res = requests.post(order_url, headers=HEADERS, json=order_body)
    if order_res.status_code != 200:
        flash("Failed to create order", "error")
        return redirect(url_for("index"))

    order_id = order_res.json()["order"]["id"]

    # Step 4: Record external payment to Square
    payment_url = f"{BASE_URL}/v2/payments"
    payment_body = {
        "idempotency_key": str(uuid.uuid4()),
        "amount_money": {
            "amount": amount_cents,
            "currency": "USD"
        },
        "source_type": "EXTERNAL",
        "external_details": {
            "type": "OTHER_GIFT_CARD",
            "source": "SwipeIt Redemption"
        },
        "location_id": LOCATION_ID,
        "order_id": order_id
    }
    payment_res = requests.post(payment_url, headers=HEADERS, json=payment_body)
    if payment_res.status_code != 200:
        flash("Failed to log payment in Square", "error")
        return redirect(url_for("index"))

    flash(f"✅ Redeemed ${amount_dollars} and recorded sale to Square!", "success")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
