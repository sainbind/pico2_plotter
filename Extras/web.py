# Web controlled plotter
# Wifi code based on Pimoroni Phew!
# https://www.github.com/pimoroni/phew
# Kevin McAleer
# Pico Plotter Project
# 20 June 2025

import network
import time
import pico_logging

def connect_to_wifi(ssid, password, timeout_seconds=30):
    
    statuses = {
    network.STAT_IDLE: "idle",
    network.STAT_CONNECTING: "connecting",
    network.STAT_WRONG_PASSWORD: "wrong password",
    network.STAT_NO_AP_FOUND: "access point not found",
    network.STAT_CONNECT_FAIL: "connection failed",
    network.STAT_GOT_IP: "got ip address"
    }

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)    
    wlan.connect(ssid, password)
    start = time.ticks_ms()
    status = wlan.status()

    logging.debug(f"  - {statuses[status]}")
    while not wlan.isconnected() and (time.ticks_ms() - start) < (timeout_seconds * 1000):
        new_status = wlan.status()
        if status != new_status:
          logging.debug(f"  - {statuses[status]}")
          status = new_status
        time.sleep(0.25)

    if wlan.status() == network.STAT_GOT_IP:
        return wlan.ifconfig()[0]
    return None
    
def is_connected_to_wifi():
  import network, time
  wlan = network.WLAN(network.STA_IF)
  return wlan.isconnected()

def get_ip_address():
  import network
  try:
    return network.WLAN(network.STA_IF).ifconfig()[0]
  except:
    return None