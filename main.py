import network
import time
from machine import Pin
from server import HTTPServer

# --- Config ---
AP_SSID = "AdrianRoom"
AP_PASSWORD = ""  # open network

# --- Message store ---
messages = []
message_id = 0
MAX_MESSAGES = 10
MAX_USERNAME = 10
MAX_MESSAGE = 250

# --- Onboard LED ---
led = Pin("LED", Pin.OUT)


def blink(times, on_ms=120, off_ms=120):
    led.off()
    for i in range(times):
        led.on()
        time.sleep_ms(on_ms)
        led.off()
        if i < times - 1:
            time.sleep_ms(off_ms)


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
    blink(1)  # AP is up

    ip = ap.ifconfig()[0]
    http = HTTPServer(messages, add_message)
    print(f"HTTP listening on {ip}:80")
    print(f"Visit http://{ip}/ after connecting to '{AP_SSID}'")

    blink(2)   # everything ready
    led.on()   # stay on

    try:
        http.run()
    except Exception as e:
        print("Fatal server error:", e)
        led.off()
        while True:
            blink(3, on_ms=100, off_ms=100)
            time.sleep(1)


main()
