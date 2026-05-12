# AdrianRoom

Ett minimalt lokalt chattrum som körs helt på en Raspberry Pi Pico W2 via MicroPython.

Inget internet behövs. Ingen server. Bara en Pi, ett WiFi-kort och en webbläsare.

## Vad det gör

- Skapar ett öppet WiFi-nätverk med namnet `AdrianRoom`
- Serverar ett chattgränssnitt på `http://192.168.4.1/`
- Sparar de senaste 10 meddelandena i RAM-minnet
- Hämtar nya meddelanden var tredje sekund
- Hanterar flera anslutna klienter samtidigt via en icke-blockerande eventloop

## Filstruktur

```
main.py      — startar AP och HTTP-servern
server.py    — HTTP-server (GET /, GET /messages, POST /messages)
index.html   — chattgränssnitt (vanilla JS, liquid glass-design)
```

## Driftsättning på Pico

Du behöver [Thonny](https://thonny.org/) eller [mpremote](https://docs.micropython.org/en/latest/reference/mpremote.html).

### Med Thonny

1. Öppna **Files**-panelen (View → Files).
2. Högerklicka på varje fil i vänstra panelen → **Upload to /**.
3. Ladda upp: `main.py`, `server.py`, `index.html`.
4. Starta om Pico via knappen eller genom att koppla ur strömmen.

### Med mpremote

```sh
pip install mpremote

# Kopiera alla filer till Pico
mpremote cp main.py server.py index.html :

# Starta om och följ loggar
mpremote reset
mpremote connect auto repl
```

## Ansluta

1. Anslut din telefon eller dator till WiFi-nätverket `AdrianRoom` (inget lösenord).
2. Öppna `http://192.168.4.1/` i webbläsaren.
3. Ange ett namn och börja chatta.

> Ditt användarnamn sparas i `localStorage` så du slipper skriva in det igen.

## Konfiguration

Ändra toppen av `main.py` för att justera inställningarna:

| Variabel | Standard | Beskrivning |
|---|---|---|
| `AP_SSID` | `"AdrianRoom"` | WiFi-nätverkets namn |
| `AP_PASSWORD` | `""` | Tomt = öppet nätverk |
| `MAX_MESSAGES` | `10` | Antal meddelanden i RAM |
| `MAX_USERNAME` | `10` | Max längd på användarnamn |
| `MAX_MESSAGE` | `250` | Max längd på meddelande |

## Begränsningar

- **Meddelanden lagras i RAM** — försvinner vid omstart.
- **Max 10 meddelanden** — äldre meddelanden tas bort automatiskt.
- **Ingen DNS** — använd alltid `http://192.168.4.1/` direkt i webbläsaren.
