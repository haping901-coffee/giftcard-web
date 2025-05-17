import uuid
import json
import os
from flask import Flask, request, render_template_string

app = Flask(__name__)
DATA_FILE = "giftcards.json"

def load_db():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_db(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Gift Card Manager</title>
    <style>
        body { font-family: Arial; margin: 2rem; }
        input { padding: 0.5rem; margin: 0.5rem 0; }
        button { padding: 0.5rem 1rem; }
    </style>
</head>
<body>
    <h1>Gift Card Manager</h1>

    <h2>Create a Gift Card</h2>
    <form action="/create" method="POST">
        Amount ($): <input name="amount" type="number" required>
        <button type="submit">Create</button>
    </form>

    <h2>Check Balance</h2>
    <form action="/check" method="POST">
        Card Number: <input name="gan" required>
        <button type="submit">Check</button>
    </form>

    <h2>Redeem Card</h2>
    <form action="/redeem" method="POST">
        Card Number: <input name="gan" required><br>
        Amount to Redeem ($): <input name="amount" type="number" required>
        <button type="submit">Redeem</button>
    </form>

    {% if message %}
        <p><strong>{{ message }}</strong></p>
    {% endif %}
</body>
</html>
'''

@app.route("/", methods=["GET"])
def index():
    return render_template_string(TEMPLATE)

@app.route("/create", methods=["POST"])
def create():
    amount = int(request.form["amount"]) * 100
    gan = str(uuid.uuid4().int)[:16]
    data = load_db()
    data[gan] = {"balance": amount, "active": True}
    save_db(data)
    return render_template_string(TEMPLATE, message=f"✅ Created gift card {gan} with ${amount / 100:.2f}")

@app.route("/check", methods=["POST"])
def check():
    gan = request.form["gan"]
    data = load_db()
    card = data.get(gan)
    if card and card["active"]:
        return render_template_string(TEMPLATE, message=f"💳 Balance for {gan}: ${card['balance'] / 100:.2f}")
    return render_template_string(TEMPLATE, message="❌ Card not found or inactive.")

@app.route("/redeem", methods=["POST"])
def redeem():
    gan = request.form["gan"]
    amount = int(request.form["amount"]) * 100
    data = load_db()
    card = data.get(gan)
    if not card or not card["active"]:
        return render_template_string(TEMPLATE, message="❌ Card not found or inactive.")
    if card["balance"] < amount:
        return render_template_string(TEMPLATE, message="❌ Insufficient balance.")
    card["balance"] -= amount
    save_db(data)
    return render_template_string(TEMPLATE, message=f"✅ Redeemed ${amount / 100:.2f} from {gan}. New balance: ${card['balance'] / 100:.2f}")

if __name__ == "__main__":
    app.run(debug=True)