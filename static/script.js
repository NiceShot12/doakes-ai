const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");
const locationInput = document.getElementById("location-input");
const resultsContainer = document.getElementById("results-container");
const checkBtn = document.getElementById("check-btn");
const alarmSound = document.getElementById("alarm-sound");

// Browser notification permission
async function enableBrowserNotifications() {
    if (!("Notification" in window)) {
        alert("This browser doesn't support notifications");
        return;
    }

    const permission = await Notification.requestPermission();
    const statusEl = document.getElementById("browser-notif-status");
    
    if (permission === "granted") {
        statusEl.textContent = "✅ Enabled";
        statusEl.style.color = "green";
        
        // Test notification
        new Notification("Doakes AI", {
            body: "Browser notifications are now enabled!",
            icon: "🛡️"
        });
    } else {
        statusEl.textContent = "❌ Denied";
        statusEl.style.color = "red";
    }
}

// Save notification settings
async function saveNotificationSettings() {
    const email = document.getElementById("email-input").value.trim();
    const phone = document.getElementById("phone-input").value.trim();

    if (!email && !phone) {
        alert("Please enter at least an email or phone number");
        return;
    }

    try {
        const response = await fetch("/enable_notifications", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, phone })
        });

        if (response.ok) {
            alert("✅ Notification settings saved! You'll receive alerts when dangers are detected.");
        } else {
            alert("Failed to save settings. Please try again.");
        }
    } catch (error) {
        console.error("Error:", error);
        alert("Network error. Please try again.");
    }
}

// Test alerts
async function testAlerts() {
    try {
        const response = await fetch("/test_alert", {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        });

        const data = await response.json();
        
        let message = "Test results:\n";
        message += data.email_sent ? "✅ Email sent\n" : "❌ Email not configured\n";
        message += data.sms_sent ? "✅ SMS sent\n" : "❌ SMS not configured\n";
        
        alert(message);
        
        // Also test browser notification
        if (Notification.permission === "granted") {
            new Notification("🚨 Doakes AI Test Alert", {
                body: "This is a test safety alert!",
                icon: "🛡️"
            });
        }
        
        // Play alarm sound
        playAlarmSound();
        
    } catch (error) {
        console.error("Error:", error);
        alert("Failed to send test alerts");
    }
}

// Play alarm sound
function playAlarmSound() {
    alarmSound.play().catch(err => {
        console.log("Could not play alarm sound:", err);
    });
}

// Show browser notification for danger
function showDangerNotification(location, alerts) {
    if (Notification.permission === "granted") {
        const title = `🚨 DOAKES AI - DANGER ALERT - ${location}`;
        let body = "";
        
        if (alerts && alerts.length > 0) {
            body = alerts[0].event + " - " + alerts[0].severity;
        }
        
        new Notification(title, {
            body: body,
            icon: "🚨",
            requireInteraction: true // Keeps notification until user dismisses
        });
        
        // Play alarm
        playAlarmSound();
    }
}

// Check safety for any location format
async function checkSafety() {
    const location = locationInput.value.trim();
    
    if (!location) {
        showError("Please enter a location (ZIP code, city, address, etc.)");
        return;
    }

    checkBtn.disabled = true;
    checkBtn.textContent = "Checking...";
    resultsContainer.innerHTML = '<div class="loading">🔍 Checking safety information...</div>';

    try {
        const response = await fetch("/check_safety", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ location: location })
        });

        const data = await response.json();

        if (response.ok) {
            displayResults(data);
            
            // Check if there are severe alerts
            const severeAlerts = data.alerts.filter(a => 
                a.severity === "Extreme" || a.severity === "Severe"
            );
            
            if (severeAlerts.length > 0) {
                showDangerNotification(data.location, severeAlerts);
            }
        } else {
            showError(data.error || "Failed to fetch safety information");
        }
    } catch (error) {
        console.error("Error:", error);
        showError("Network error. Please try again.");
    } finally {
        checkBtn.disabled = false;
        checkBtn.textContent = "Check Safety";
    }
}

// Display safety results
function displayResults(data) {
    let html = `
        <div class="results-header">
            <h2>📍 ${data.location}</h2>
            <p class="zip-label">Searched: ${data.original_input}</p>
        </div>
    `;

    // Weather Alerts
    html += '<div class="section weather-section">';
    html += '<h3>⛈️ Weather Alerts</h3>';
    
    if (data.alerts && data.alerts.length > 0) {
        data.alerts.forEach(alert => {
            const severityClass = alert.severity.toLowerCase();
            html += `
                <div class="alert-card ${severityClass}">
                    <div class="alert-header">
                        <strong>🚨 ${alert.event}</strong>
                        <span class="severity-badge ${severityClass}">${alert.severity}</span>
                    </div>
                    <p class="alert-headline">${alert.headline}</p>
                    ${alert.instruction ? `<p class="alert-instruction">💡 ${alert.instruction}</p>` : ''}
                </div>
            `;
        });
    } else {
        html += '<p class="no-alerts">✅ No active weather alerts</p>';
    }
    html += '</div>';

    // Crime Data
    if (data.crime && data.crime.available) {
        html += '<div class="section crime-section">';
        html += '<h3>🔒 Crime Safety</h3>';
        
        const riskLevel = data.crime.risk_level || 'Unknown';
        const riskClass = riskLevel.toLowerCase();
        
        html += `
            <div class="crime-card">
                <div class="risk-badge ${riskClass}">${riskLevel} Risk</div>
                <p>${data.crime.summary}</p>
                ${data.crime.details?.note ? `<p class="crime-note"><small>${data.crime.details.note}</small></p>` : ''}
                ${data.crime.details?.recommendation ? `<p class="recommendation">💡 ${data.crime.details.recommendation}</p>` : ''}
            </div>
        `;
        html += '</div>';
    }

    // Current Weather
    if (data.weather) {
        html += '<div class="section weather-current">';
        html += '<h3>🌤️ Current Conditions</h3>';
        html += `
            <div class="weather-card">
                <div class="temp">${data.weather.temperature}°F</div>
                <p>${data.weather.conditions}</p>
                <p class="wind">💨 ${data.weather.wind}</p>
            </div>
        `;
        html += '</div>';
    }

    resultsContainer.innerHTML = html;
}

// Show error message
function showError(message) {
    resultsContainer.innerHTML = `<div class="error-message">⚠️ ${message}</div>`;
}

// Chat functionality
async function sendMessage() {
    const message = userInput.value.trim();

    if (!message) return;

    userInput.disabled = true;
    appendMessage("You", message, "user");
    userInput.value = "";

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message })
        });

        const data = await response.json();

        if (response.ok) {
            if (data.error) {
                appendMessage("Bot", data.error, "bot error");
            } else {
                appendMessage("Bot", data.reply, "bot");
            }
        } else {
            appendMessage("Bot", "Sorry, something went wrong.", "bot error");
        }
    } catch (error) {
        console.error("Error:", error);
        appendMessage("Bot", "Network error. Please try again.", "bot error");
    } finally {
        userInput.disabled = false;
        userInput.focus();
    }
}

// Append message to chat
function appendMessage(sender, message, type) {
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${type}`;

    const senderSpan = document.createElement("strong");
    senderSpan.textContent = sender + ": ";

    const messageSpan = document.createElement("span");
    messageSpan.innerHTML = message.replace(/\n/g, '<br>');

    msgDiv.appendChild(senderSpan);
    msgDiv.appendChild(messageSpan);

    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Enter key handlers
userInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendMessage();
});

locationInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") checkSafety();
});

// Auto-check for alerts every 10 minutes if user has enabled notifications
setInterval(() => {
    const monitoredLocation = sessionStorage.getItem('monitored_location');
    if (monitoredLocation && (Notification.permission === "granted")) {
        // Silently check for new alerts
        checkSafety();
    }
}, 600000); // 10 minutes
