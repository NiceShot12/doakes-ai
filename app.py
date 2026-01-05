from flask import Flask, request, jsonify, render_template, session
import requests
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config['APP_NAME'] = 'Doakes AI'

# ============ CONFIGURATION ============
# EMAIL SETTINGS (Using Gmail - you'll need to set this up)
EMAIL_ENABLED = False  # Set to True after configuring
SENDER_EMAIL = "your-email@gmail.com"  # Change this
SENDER_PASSWORD = "your-app-password"  # Use Gmail App Password

# SMS SETTINGS (Using Twilio - optional, set to False if not using)
SMS_ENABLED = False  # Set to True after getting Twilio credentials
TWILIO_ACCOUNT_SID = "your_account_sid"  # Get from Twilio
TWILIO_AUTH_TOKEN = "your_auth_token"  # Get from Twilio
TWILIO_PHONE_NUMBER = "+1234567890"  # Your Twilio number

# ======================================

def geocode_location(location_input):
    """
    Convert various location formats to coordinates using Nominatim (OpenStreetMap)
    Accepts: ZIP codes, cities, states, addresses, streets, etc.
    Returns: (lat, lon, display_name) or (None, None, None)
    """
    try:
        # First check if it's a 5-digit ZIP code
        if location_input.strip().isdigit() and len(location_input.strip()) == 5:
            return get_coordinates_from_zip(location_input.strip())
        
        # Use Nominatim API for general geocoding
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': location_input,
            'format': 'json',
            'limit': 1,
            'countrycodes': 'us'  # Restrict to US since NOAA only covers US
        }
        headers = {
            'User-Agent': 'DoakesAI-SafetyApp/1.0'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                result = data[0]
                lat = float(result['lat'])
                lon = float(result['lon'])
                display_name = result['display_name']
                
                # Extract city and state for display
                city, state = extract_city_state(display_name)
                
                return lat, lon, city, state
    except Exception as e:
        app.logger.error(f"Geocoding error: {e}")
    
    return None, None, None, None

def extract_city_state(display_name):
    """Extract city and state from Nominatim display name"""
    try:
        parts = [p.strip() for p in display_name.split(',')]
        
        # Try to find state (usually second to last or last part)
        state = None
        city = None
        
        for part in reversed(parts):
            # Check if it's a US state abbreviation or name
            if len(part) == 2 and part.isupper():
                state = part
            elif 'United States' not in part and not part.isdigit():
                if not city and state:
                    city = part
                elif not state:
                    # Might be a state name
                    state = part
        
        if not city and len(parts) > 0:
            city = parts[0]
        
        if not state:
            state = "US"
            
        return city or "Unknown", state or "US"
    except:
        return "Unknown", "US"

def get_coordinates_from_zip(zipcode):
    """Convert ZIP code to coordinates using free API"""
    try:
        url = f"https://api.zippopotam.us/us/{zipcode}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            lat = data['places'][0]['latitude']
            lon = data['places'][0]['longitude']
            city = data['places'][0]['place name']
            state = data['places'][0]['state abbreviation']
            return float(lat), float(lon), city, state
    except:
        pass
    return None, None, None, None

def get_weather_alerts(lat, lon):
    """Get active weather alerts from NOAA"""
    alerts = []
    try:
        url = f"https://api.weather.gov/alerts/active?point={lat},{lon}"
        headers = {'User-Agent': 'SafetyAlertBot/1.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            features = data.get('features', [])
            
            for feature in features:
                props = feature.get('properties', {})
                alert = {
                    'event': props.get('event', 'Unknown Alert'),
                    'severity': props.get('severity', 'Unknown'),
                    'urgency': props.get('urgency', 'Unknown'),
                    'headline': props.get('headline', ''),
                    'description': props.get('description', '')[:300],
                    'instruction': props.get('instruction', '')[:200]
                }
                alerts.append(alert)
    except Exception as e:
        app.logger.error(f"Error fetching alerts: {e}")
    
    return alerts

def get_current_weather(lat, lon):
    """Get current weather conditions"""
    try:
        url = f"https://api.weather.gov/points/{lat},{lon}"
        headers = {'User-Agent': 'SafetyAlertBot/1.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            forecast_url = data['properties']['forecast']
            
            forecast_response = requests.get(forecast_url, headers=headers, timeout=10)
            if forecast_response.status_code == 200:
                forecast_data = forecast_response.json()
                current = forecast_data['properties']['periods'][0]
                return {
                    'temperature': current.get('temperature'),
                    'conditions': current.get('shortForecast'),
                    'wind': current.get('windSpeed')
                }
    except:
        pass
    return None

def get_crime_data(state_abbr, city):
    """Get crime statistics"""
    crime_info = {
        'available': False,
        'summary': 'Crime data not available for this location',
        'details': {}
    }
    
    try:
        high_crime_states = ['LA', 'NM', 'TN', 'AR', 'AK', 'MO', 'SC', 'AL']
        medium_crime_states = ['TX', 'FL', 'GA', 'NC', 'AZ', 'OK', 'NV', 'MI']
        
        if state_abbr in high_crime_states:
            crime_info['available'] = True
            crime_info['summary'] = f"⚠️ {state_abbr} has higher crime rates compared to national average. Exercise caution, especially at night."
            crime_info['risk_level'] = 'High'
        elif state_abbr in medium_crime_states:
            crime_info['available'] = True
            crime_info['summary'] = f"🟡 {state_abbr} has moderate crime rates. Use common sense safety precautions."
            crime_info['risk_level'] = 'Moderate'
        else:
            crime_info['available'] = True
            crime_info['summary'] = f"✅ {state_abbr} has relatively lower crime rates compared to national average."
            crime_info['risk_level'] = 'Low'
        
        crime_info['details'] = {
            'note': 'This is based on state-level FBI statistics. Individual neighborhoods may vary significantly.',
            'recommendation': 'Check local police department websites for more specific neighborhood crime data.'
        }
        
    except Exception as e:
        app.logger.error(f"Error fetching crime data: {e}")
    
    return crime_info

def send_email_alert(recipient_email, location, alerts, crime_data):
    """Send email alert with timeout protection"""
    if not EMAIL_ENABLED:
        return False
    
    # Check if credentials are placeholder values
    if SENDER_EMAIL == "your-email@gmail.com" or SENDER_PASSWORD == "your-app-password":
        app.logger.warning("Email not configured - skipping")
        return False
    
    try:
        subject = f"🚨 Doakes AI - SAFETY ALERT for {location}"
        
        body = f"DOAKES AI SAFETY ALERT FOR {location}\n\n"
        
        if alerts:
            body += "⚠️ ACTIVE WEATHER ALERTS:\n"
            for alert in alerts[:3]:
                body += f"• {alert['event']} - {alert['severity']}\n"
                body += f"  {alert['headline']}\n\n"
        
        if crime_data and crime_data.get('available'):
            body += f"🔒 CRIME SAFETY: {crime_data.get('risk_level', 'Unknown')} Risk\n"
            body += f"{crime_data['summary']}\n\n"
        
        body += "\nStay safe!\n- Doakes AI"
        
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        app.logger.error(f"Error sending email: {e}")
        return False

def send_sms_alert(phone_number, location, alerts):
    """Send SMS alert using Twilio with timeout protection"""
    if not SMS_ENABLED:
        return False
    
    # Check if credentials are placeholder values
    if TWILIO_ACCOUNT_SID == "your_account_sid" or TWILIO_AUTH_TOKEN == "your_auth_token":
        app.logger.warning("SMS not configured - skipping")
        return False
    
    try:
        from twilio.rest import Client
        
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        message_body = f"🚨 Doakes AI ALERT for {location}:\n"
        
        if alerts:
            for alert in alerts[:2]:  # Limit to 2 for SMS
                message_body += f"• {alert['event']} ({alert['severity']})\n"
        
        message_body += "\nCheck the app for details. Stay safe!"
        
        message = client.messages.create(
            body=message_body,
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        
        return True
    except Exception as e:
        app.logger.error(f"Error sending SMS: {e}")
        return False

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/check_safety", methods=["POST"])
def check_safety():
    """Check safety alerts for a given location (ZIP, city, address, etc.)"""
    location_input = request.json.get("location", "").strip()
    
    if not location_input:
        return jsonify({"error": "Please enter a location (ZIP code, city, address, etc.)"}), 400
    
    # Geocode the location
    lat, lon, city, state = geocode_location(location_input)
    
    if not lat or not lon:
        return jsonify({"error": "Location not found. Please try a different format (e.g., 'New York, NY' or '90210')"}), 404
    
    alerts = get_weather_alerts(lat, lon)
    weather = get_current_weather(lat, lon)
    crime_data = get_crime_data(state, city)
    
    # Save user's location for monitoring
    session['monitored_location'] = f"{city}, {state}"
    session['monitored_input'] = location_input
    
    response = {
        "location": f"{city}, {state}",
        "original_input": location_input,
        "coordinates": {"lat": lat, "lon": lon},
        "alerts": alerts,
        "weather": weather,
        "crime": crime_data,
        "alert_count": len(alerts)
    }
    
    return jsonify(response)

@app.route("/enable_notifications", methods=["POST"])
def enable_notifications():
    """Enable email/SMS notifications for user"""
    data = request.json
    email = data.get("email")
    phone = data.get("phone")
    
    if email:
        session['notification_email'] = email
    if phone:
        session['notification_phone'] = phone
    
    return jsonify({"status": "enabled", "email": bool(email), "sms": bool(phone)})

@app.route("/test_alert", methods=["POST"])
def test_alert():
    """Send test alert to verify notifications work"""
    email = session.get('notification_email')
    phone = session.get('notification_phone')
    location = session.get('monitored_location', 'Your Location')
    
    results = {
        "email_sent": False,
        "sms_sent": False
    }
    
    if email and EMAIL_ENABLED:
        test_alerts = [{"event": "Test Alert", "severity": "Minor", "headline": "This is a test notification"}]
        results["email_sent"] = send_email_alert(email, location, test_alerts, {})
    
    if phone and SMS_ENABLED:
        test_alerts = [{"event": "Test Alert", "severity": "Minor"}]
        results["sms_sent"] = send_sms_alert(phone, location, test_alerts)
    
    return jsonify(results)

@app.route("/chat", methods=["POST"])
def chat():
    """Chat interface - now accepts any location format"""
    user_message = request.json.get("message", "").strip()
    
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
    
    user_lower = user_message.lower()
    
    # Check for greetings
    if any(word in user_lower for word in ['hi', 'hello', 'hey', 'greetings']):
        reply = "Hello! 👋 I'm Doakes AI. I can:\n• Check weather alerts & disasters\n• Provide crime safety info\n• Send email/SMS alerts\n\nJust give me any location - ZIP code, city, address, or street!"
        return jsonify({"reply": reply})
    
    # Check for help/info requests
    if any(word in user_lower for word in ['help', 'what', 'how', 'info']):
        reply = "I help you stay safe! Enter any location to check for:\n✅ Weather alerts\n✅ Crime data\n✅ Current conditions\n\nExamples:\n• '90210'\n• 'Los Angeles, CA'\n• '123 Main Street, Boston'\n• 'New York City'\n\nYou can also enable notifications to get automatic alerts!"
        return jsonify({"reply": reply})
    
    # Check for notification queries
    if any(word in user_lower for word in ['notif', 'alert', 'email', 'sms', 'text']):
        reply = "I can send you alerts via email and SMS! Use the 'Enable Notifications' section to set it up."
        return jsonify({"reply": reply})
    
    # Try to geocode the message as a location
    lat, lon, city, state = geocode_location(user_message)
    
    if not lat:
        reply = "I couldn't find that location. Try:\n• ZIP code (e.g., '90210')\n• City and state (e.g., 'Boston, MA')\n• Full address (e.g., '123 Main St, Seattle')\n• Just a city name (e.g., 'Chicago')"
        return jsonify({"reply": reply})
    
    # Get safety information
    alerts = get_weather_alerts(lat, lon)
    weather = get_current_weather(lat, lon)
    crime_data = get_crime_data(state, city)
    
    reply = f"📍 **SAFETY REPORT FOR {city}, {state}**\n\n"
    
    if alerts:
        reply += f"⚠️ **ACTIVE WEATHER ALERTS:**\n"
        for alert in alerts[:2]:
            reply += f"🚨 {alert['event']} (Severity: {alert['severity']})\n"
            reply += f"{alert['headline']}\n\n"
        
        if len(alerts) > 2:
            reply += f"...and {len(alerts) - 2} more alerts.\n\n"
    else:
        reply += "✅ No active weather alerts.\n\n"
    
    if crime_data['available']:
        reply += f"🔒 **CRIME SAFETY:**\n{crime_data['summary']}\n"
        reply += f"Risk Level: {crime_data.get('risk_level', 'Unknown')}\n\n"
    
    if weather:
        reply += f"🌤️ **CURRENT CONDITIONS:**\n"
        reply += f"{weather['temperature']}°F, {weather['conditions']}, Wind: {weather['wind']}\n\n"
    
    reply += "💡 Tip: Enable notifications to get alerts automatically!"
    
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
