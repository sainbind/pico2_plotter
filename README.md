# Pico2 Plotter

A simple Raspberry Pi Pico-based plotter built using MicroPython.

---
Refactoring of Kevin McAleer's original project, which can be found at <https://www.kevsrobots.com/projects/pico_plotter>.

I'm a seasoned Java developer but new to the python ecosystem.  
It's a learning experience both using a Raspberry Pi and Python.  
I have found Kevin's project a great starting point.

---

### Sources/turtle_main.py

Simulates the plotter using the turtle graphics library. This is useful for testing and debugging the plotting logic without needing to run it on the actual hardware.

To run, use a virtual environment without MicroPython installed:  
* cd Sources  
* ../.venv_turtle/bin/python turtle_main.py < absolute.gcode 
* ../.venv_turtle/bin/python turtle_main.py < relative.gcode 

### Project Setup

I'm using pycharm on a Mac as the IDE for this project. To set up the project, I created two virtual environments:
one with MicroPython installed for running the plotter on the Raspberry Pi Pico, 
and another without MicroPython for testing the plotting logic using the turtle and matplotlib libraries.
* create a virtual environment with MicroPython:  
  * python3 -m venv .venv
  * source .venv_/bin/activate
  * pip install pico_requirements.txt
  
* create a virtual environment without MicroPython:  
  * python3 -m venv .venv_turtle
  * source .venv_turtle/bin/activate
  * pip install -r turtle_requirements.txt
  
### Sources/pico_main.py

Change the action to either file, serial or other to run the plotter.
* serial is setup to run using the Universal Gcode Sender app.
* file loads the absolute.gcode file
* other puts the plotter in interactive mode

### Sources/mplot_main.py

Simulates the plotter using the matplotlib library. This is useful for testing and debugging the plotting logic without needing to run it on the actual hardware.

To run, use a virtual environment without MicroPython installed:  
* cd Sources  
* ../.venv_turtle/bin/python mplot_main.py < absolute.gcode 
* ../.venv_turtle/bin/python mplot_main.py < relative.gcode


#### Sources/plotter_main.py

The main program for the plotter, which runs on the Raspberry Pi Pico. 
It reads G-code commands from standard input and controls the stepper motors accordingly.

<img src='./pico_plotter.png' width=60%>

The plotter doesn't work reliably in absolute movement mode so I used the relative mode.
Even in relative mode, the lines are not perfectly straight, but it's good enough for my purposes.

#### Sources/main.py

The main program creates a rest server running on pico
You can use curl to send one or more commands separated by newlines to the plotter. For example:
* curl http://192.168.1.189:5000/run_all -d'?\nG1X10Y10\nG1Z-30'
*  curl http://192.168.1.189:5000/run_all -d'$'
*  curl http://192.168.1.189:5000/run_all -d'$j=G1Z1'

#### Sources/post_client.py

A simple client program that sends G-code commands to the plotter's REST server.
To run, use the virtual environment with MicroPython installed:
* source .venv/bin/activate
* python post_client.py