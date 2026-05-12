# pi-room

A minimal local chat room running entirely on a Raspberry Pi Pico W2 via MicroPython.

No internet required. No server. Just a Pi, a WiFi radio, and a browser.

## What it does

- Creates an open WiFi network called `pi-room`
- Serves a chat UI at `http://chat.dev/` (via a local DNS responder)
- Accepts and stores the last 5 messages in RAM
- Polls for new messages every 3 seconds

## File layout

```
main.py      — boot script: sets up AP, starts DNS + HTTP
dns.py       — minimal UDP DNS server (answers all A queries with Pi's IP)
server.py    — minimal HTTP server (GET /, GET /messages, POST /messages)
index.html   — chat UI (vanilla JS, dark theme, no dependencies)
```

## Deploying to the Pico

You need [mpremote](https://docs.micropython.org/en/latest/reference/mpremote.html) or [Thonny](https://thonny.org/).

### With mpremote

```sh
pip install mpremote

# Copy all files to the Pico root
mpremote cp main.py dns.py server.py index.html :

# Reset and watch logs
mpremote reset
mpremote connect auto repl
```

### With Thonny

1. Open each file and use **File → Save as… → Raspberry Pi Pico**.
2. Save `main.py` last (it runs on boot).
3. Press the reset button or power-cycle the Pico.

## Connecting

1. On your phone or laptop, join the `pi-room` WiFi network (no password).
2. Navigate to `http://chat.dev/` in your browser.
   - If DNS doesn't resolve, go to `http://192.168.4.1/` directly.
3. Enter a name and start chatting.

> Your username is saved in `localStorage` so you don't have to retype it.

## Caveats

- **No DHCP**: clients must either accept an auto-assigned address from the AP's
  built-in DHCP (the Pico W's network stack provides basic DHCP in AP mode) or
  set a static IP in the `192.168.4.x` range manually.
- **Single-threaded HTTP**: one request is served at a time. Fine for a small group.
- **Messages are in RAM**: they are lost on reboot.
- **DNS resolves everything to the Pi**: any domain typed in a browser will
  point here, which is intentional for captive-portal convenience.

## Configuration

Edit the top of `main.py` to change:

| Variable | Default | Description |
|---|---|---|
| `AP_SSID` | `"pi-room"` | WiFi network name |
| `AP_PASSWORD` | `""` | Empty = open network |
| `PI_IP` | `"192.168.4.1"` | Pi's IP on the AP |
| `CHAT_DOMAIN` | `"chat.dev"` | Domain to advertise |
| `MAX_MESSAGES` | `5` | Messages kept in RAM |
| `MAX_USERNAME` | `10` | Max username length |
| `MAX_MESSAGE` | `250` | Max message length |
