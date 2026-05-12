import network
import time
from server import HTTPServer

# --- Config ---
AP_SSID = "AdrianBox"
AP_PASSWORD = ""  # open network

# --- Message store ---
messages = []
message_id = 0
MAX_MESSAGES = 10
MAX_USERNAME = 10
MAX_MESSAGE = 250


def add_message(username, text):
    global message_id
    username = username[:MAX_USERNAME]
    text = text[:MAX_MESSAGE]
    message_id += 1
    messages.append({"id": message_id, "u": username, "m": text})
    if len(messages) > MAX_MESSAGES:
        messages.pop(0)


def setup_ap():
    ap = network.WLAN(network.WLAN.IF_AP)
    ap.active(True)
    ap.config(ssid=AP_SSID, password=AP_PASSWORD, security=0)
    for _ in range(20):
        if ap.active():
            break
        time.sleep(0.5)
    print(f"AP up: {ap.ifconfig()}")
    return ap


def main():
    ap = setup_ap()
    ip = ap.ifconfig()[0]

    http = HTTPServer(messages, add_message)
    print(f"HTTP listening on {ip}:80")
    print(f"Visit http://{ip}/ after connecting to '{AP_SSID}'")
    http.run()


main()
