import os
from flask import Flask, render_template

# Look for index.html in the parent folder (which is where we saved it)
app = Flask(__name__, template_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@app.route('/')
def home():
    # This is your REAL data (currently dummy, you will replace this with your model's output)
    current_price = 794.33
    high = 802.09
    change_percent = 1.08
    confidence = 47.8

    # Data for the 24-day table
    forecast_data = [
        {'date': '2026-08-29', 'open': '₹794.33', 'high': '₹802.09', 'low': '₹790.00', 'close': '₹798.20', 'change': '+1.08%'},
        {'date': '2026-08-30', 'open': '₹798.20', 'high': '₹805.00', 'low': '₹795.10', 'close': '₹801.45', 'change': '+1.20%'},
        {'date': '2026-08-31', 'open': '₹801.45', 'high': '₹810.00', 'low': '₹799.00', 'close': '₹805.22', 'change': '+0.47%'},
        {'date': '2026-09-01', 'open': '₹805.22', 'high': '₹806.10', 'low': '₹790.00', 'close': '₹792.11', 'change': '-1.63%'},
        {'date': '2026-09-02', 'open': '₹792.11', 'high': '₹800.00', 'low': '₹790.00', 'close': '₹798.00', 'change': '+0.74%'},
        {'date': '2026-09-03', 'open': '₹798.00', 'high': '₹802.00', 'low': '₹795.00', 'close': '₹799.00', 'change': '+0.13%'}
    ]

    # Pass the data to the HTML file using variables
    return render_template('index.html', 
                           price=current_price, 
                           high=high, 
                           change=change_percent, 
                           conf=confidence, 
                           data=forecast_data)

if __name__ == '__main__':
    # Run on port 10000 to match your existing setup
    app.run(host='0.0.0.0', port=10000, debug=True)
