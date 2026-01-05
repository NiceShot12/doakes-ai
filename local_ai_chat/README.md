# Local AI Chatbot

## Setup
1. Create a virtual environment:
   ```bash
   python -m venv venv

🔔 Notification Setup Instructions
Your Safety Alert Bot now supports 3 types of alerts:

🔔 Browser Notifications (FREE - works immediately)
📧 Email Alerts (FREE - needs Gmail setup)
📱 SMS Alerts (Twilio - free trial available)


✅ What Works NOW (No Setup Needed):
Browser Notifications + Sound Alerts

Click "Enable" for browser notifications
Automatic checks every 10 minutes
Plays alarm sound when severe danger detected
Already working!


📧 Email Alerts Setup (Optional - FREE)
Step 1: Get Gmail App Password

Go to your Google Account: https://myaccount.google.com
Click Security → 2-Step Verification (turn it ON if not already)
Scroll down to App passwords
Create new app password for "Mail"
Copy the 16-character password

Step 2: Update app.py
Open app.py and change these lines:
pythonEMAIL_ENABLED = True  # Change from False to True
SENDER_EMAIL = "your-email@gmail.com"  # Your Gmail address
SENDER_PASSWORD = "xxxx xxxx xxxx xxxx"  # Your 16-char app password
Step 3: Restart Flask
bashpython app.py
Done! Email alerts now work! ✅

📱 SMS Alerts Setup (Optional)
Step 1: Get Twilio Free Trial

Go to https://www.twilio.com/try-twilio
Sign up (FREE - no credit card for trial)
Get $15 in free credits
Verify your phone number

Step 2: Get Credentials
From Twilio Dashboard, copy:

Account SID
Auth Token
Phone Number

Step 3: Install Twilio
bashpip install twilio
Step 4: Update app.py
pythonSMS_ENABLED = True  # Change from False
TWILIO_ACCOUNT_SID = "your_account_sid"
TWILIO_AUTH_TOKEN = "your_auth_token"
TWILIO_PHONE_NUMBER = "+1234567890"  # Your Twilio number
Step 5: Restart Flask
bashpython app.py
Done! SMS alerts now work! ✅

🚨 How Alerts Work:

User enters their ZIP code
Bot checks for dangers (weather alerts, crime)
If SEVERE/EXTREME alert detected:

🔔 Browser notification pops up
🔊 Alarm sound plays
📧 Email sent (if configured)
📱 SMS sent (if configured)


Auto-checks every 10 minutes while page is open


💡 Tips:

Browser notifications work best - they're free and instant
Email is great for keeping a record of alerts
SMS is best for when you're away from computer
Test your setup using the "Test Alerts" button


⚠️ Limitations:

Browser notifications only work when the page is open
For TRUE background monitoring, you'd need a native mobile app
SMS costs money after Twilio's free trial ($15 credit)
Email requires Gmail with 2-factor authentication enabled


🎯 Quick Start (Easiest):

Just enable browser notifications (click the button)
Enter a ZIP code
Keep the page open
You'll get alerts automatically!

That's it! No email or SMS setup needed for basic functionality. 🚀

All dependencies - 
Flask==3.0.0
gunicorn==21.2.0
requests==2.31.0
twilio==8.10.0
email-validator==2.1.0
python-dotenv==1.0.0
Flask-Limiter==3.5.0
Flask-WTF==1.2.1
Flask-Talisman==1.1.0
