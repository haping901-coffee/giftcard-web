
from flask import Flask, render_template_string

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Gift Card Manager</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            padding: 40px;
        }
        h1 {
            font-size: 36px;
            margin-bottom: 10px;
        }
        .section {
            margin-top: 30px;
        }
        label {
            display: inline-block;
            width: 150px;
            margin-bottom: 10px;
        }
        input {
            padding: 8px;
            margin-bottom: 10px;
            width: 200px;
        }
        button {
            padding: 8px 12px;
            margin-left: 10px;
        }
    </style>
</head>
<body>
    <h1>Gift Card Manager</h1>

    <div class="section">
        <h2>Create a Gift Card</h2>
        <label>Amount ($):</label>
        <input type="number" placeholder="Enter amount">
        <button>Create</button>
    </div>

    <div class="section">
        <h2>Check Balance</h2>
        <label>Card Number:</label>
        <input type="text" placeholder="Enter card number">
        <button>Check</button>
    </div>

    <div class="section">
        <h2>Redeem Card</h2>
        <label>Card Number:</label>
        <input type="text" placeholder="Enter card number"><br>
        <label>Amount to Redeem ($):</label>
        <input type="number" placeholder="Enter amount">
        <button>Redeem</button>
    </div>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
