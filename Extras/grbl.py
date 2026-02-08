# Kevin McAleer
# Pico Plotter Project
# 28 June 2025

# GRBL controller for a simple plotter machine using MicroPython

from machine import Pin, UART
import time

# Configure UART for receiving G-code
uart = UART(1, baudrate=115200, tx=17, rx=16)

# Define stepper motor pins
X_STEP = Pin(2, Pin.OUT)
X_DIR = Pin(3, Pin.OUT)

Y_STEP = Pin(4, Pin.OUT)
Y_DIR = Pin(5, Pin.OUT)

Z_STEP = Pin(6, Pin.OUT)
Z_DIR = Pin(7, Pin.OUT)

def step(pin, steps, direction):
    pin_dir, pin_step = direction
    pin_dir.value(steps >= 0)
    for _ in range(abs(steps)):
        pin_step.value(1)
        time.sleep_us(500)
        pin_step.value(0)
        time.sleep_us(500)

while True:
    if uart.any():
        line = uart.readline().decode().strip()
        print("Received:", line)
        
        # Parse very basic G1 movement
        if line.startswith('G1'):
            x = y = z = 0
            parts = line.split()
            for p in parts:
                if p.startswith('X'):
                    x = float(p[1:])
                elif p.startswith('Y'):
                    y = float(p[1:])
                elif p.startswith('Z'):
                    z = float(p[1:])
            
            # Basic fixed scaling to steps
            step(x * 10, (X_DIR, X_STEP))
            step(y * 10, (Y_DIR, Y_STEP))
            step(z * 10, (Z_DIR, Z_STEP))
