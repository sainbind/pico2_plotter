# Kevin McAleer
# Pico Plotter Project
# 28 June 2025

# example script to show how uri routing and parameters work
#
# create a file called secrets.py alongside this one and add the
# following two lines to it:
#
#	WIFI_SSID = "<ssid>"
#	WIFI_PASSWORD = "<password>"
#
# with your wifi details instead of <ssid> and <password>.

from phew import server, connect_to_wifi
from phew.template import render_template

from wifi_config import WIFI_SSID, WIFI_PASSWORD

connect_to_wifi(WIFI_SSID, WIFI_PASSWORD)

message = "booted up"

# basic response with status code and content type
@server.route("/", methods=["GET", "POST"])
def basic(request):
#   return "Gosh, a request", 200, "text/html"
  return await render_template("index.html", status="IDLE")

@server.route("/messages", methods=["GET"])
def messages(request):
    return messages, 200, "text/html"


@server.route("/api/<command>", methods=["GET", "POST"])
def api(request,command):
    global status
    status = f"{command}"
    return await render_template("index.html", status=status)


# catchall example
@server.catchall()
def catchall(request):
  return "Not found", 404

# start the webserver
server.run()