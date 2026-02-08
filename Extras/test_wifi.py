# text_wifi.py
# Tests Wifi connectivity and displays web interface
# Kevin McAleer
# Pico Plotter Project
# 20 June 2025

import asyncio
from machine import WDT, Pin
from wifi_config import WIFI_SSID, WIFI_PASSWORD
from web import connect_to_wifi, is_connected_to_wifi, get_ip_address
from time import sleep

connect_to_wifi(WIFI_SSID, WIFI_PASSWORD)

if not is_connected_to_wifi():
    print(".", ends_with="")
    sleep(0.25)

print(f"connected to Wifi! - IP is {get_ip_address()}")

# Read web page
f = open("../Tests/index.html", "r")
html = f.read()
f.close()

status = "IDLE"

onboard = Pin("LED", Pin.OUT, value=0)

async def serve_client(reader, writer):
    global status
    print("Client Connected")
    request_line = await reader.readline()
    print("Request:", request_line)
    while await reader.readline() != b"\r\n":
        pass
    
    request = str(request_line)
    jog_up = request.find("/jog_up")
    jog_down = request.find("/jog_down")
    
    if jog_up == 6: print("jog up")
    if jog_down == 6: print("jog down")
    
    response = html % (status)
    print(response)
    writer.write('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
    writer.write(response)
    
    await writer.drain()
    await writer.wait_closed()
    print('Client Disconnected')

async def main():
    print ("setting up webserver")
    asyncio.create_task(asyncio.start_server(serve_client, "0.0.0.0", 80))
    wdt = WDT(timeout=8000)
    while True:
        # check wifi is connected:
        if not is_connected_to_wifi():
            print("wifi disconnected")
            reset()
        onboard.on()
        print("heartbeat")
        wdt.feed()
        await asyncio.sleep(0.25)
        onboard.off()
        await asyncio.sleep(5)
          
print("done")
sleep(0.1)

try:
    asyncio.run(main())
finally:
    asyncio.new_event_loop()
