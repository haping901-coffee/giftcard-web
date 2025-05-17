from flask import Flask, render_template, request
import requests, uuid

app = Flask(__name__)

# Replace these with your real production values
ACCESS_TOKEN = "REPLACE_WITH_YOUR_PRODUCTION_ACCESS_TOKEN"
LOCATION_ID = "REPLACE_WITH_YOUR_PRODUCTION_LOCATION_ID"
BASE_URL = "https://connect.squareup.com"

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

@app.route("/", methods=["GET", "POST"])
def home():
    message = ""
    if request.method == "POST":
        amount = request.form.get("amount")
        try:
            cents = int(float(amount) * 100)
            order_id = create_order(cents)
            if order_id:
                result = record_payment(order_id, cents)
                if result:
                    message = f"✅ Successfully logged ${amount} to Square"
                else:
                    message = "❌ Error logging payment to Square"
            else:
                message = "❌ Error creating order"
        except:
            message = "❌ Invalid amount entered"
    return render_template("index.html", message=message)

def create_order(amount_cents):
    url = f"{BASE_URL}/v2/orders"
    body = {
        "order": {
            "location_id": LOCATION_ID,
            "line_items": [{
                "name": "External Gift Card Redemption",
                "quantity": "1",
                "base_price_money": {
                    "amount": amount_cents,
                    "currency": "USD"
                }
            }]
        },
        "idempotency_key": str(uuid.uuid4())
    }
    res = requests.post(url, headers=HEADERS, json=body).json()
    return res.get("order", {}).get("id")

def record_payment(order_id, amount_cents):
    url = f"{BASE_URL}/v2/payments"
    body = {
        "source_id": "EXTERNAL",
        "idempotency_key": str(uuid.uuid4()),
        "amount_money": {
            "amount": amount_cents,
            "currency": "USD"
        },
        "order_id": order_id,
        "location_id": LOCATION_ID,
        "external_details": {
            "type": "OTHER_GIFT_CARD",
            "source": "External Gift Card"
        }
    }
    res = requests.post(url, headers=HEADERS, json=body).json()
    return "payment" in res

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)