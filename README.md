# **Ash’s Modbus RTU Tester**  
*For when you need to speak fluent Modbus RTU, but would rather click buttons and look cool while doing it.*

---

## What Is This?

**Ash’s Modbus RTU Tester** is a dark-themed, feature-packed, highly-engineered desktop tool that lets you:

- Scan serial ports for RS-485 tools
- Connect to any Modbus RTU device via RS-485  
- Read Holding Registers, Input Registers, Coils, and Discrete Inputs  
- Write to coils or holding registers (responsibly… preferably not while the machine is in production...come on boys....)  
- View raw and scaled values, including signed/unsigned handling  
- Log every operation in plain English so even non-Modbus people can follow along  
- Do all this *without* ever touching a command line

Whether you’re debugging an ESP32, reading sensors, configuring industrial controllers, or desperately trying to understand why the register map says one thing and the device does another — this tool has you covered.

---

## Features

### 🔌 **Serial Port Scanning (Auto + Manual Refresh)**
Plug in your USB–RS485 adapter.  
Click **Refresh**.  
Boom — ports appear.  
Magic.  
(The good kind, not the black-magic-Modbus kind.)

### **All Major Modbus Data Types**
Read:
- **Holding Registers (FC3)**
- **Input Registers (FC4)**
- **Coils (FC1)**
- **Discrete Inputs (FC2)**

Write:
- **Holding Register (FC16)**  
- **Single Coil (FC5)**

If a register type can't be written (e.g., Input Registers), the GUI will politely tell you to stop trying to break the universe.

### **Scaling, Signed/Unsigned, Decimals**
Automatically scale register values:
- Want `1234` to become `12.34`? → Set decimals to `2`.
- Want to treat a 16-bit register as a signed int? → Tick **Signed**.
- Want to cause Modbus chaos? → Don’t use scaling and pretend it’s the device’s fault.

### **Live Data Table**
Every read populates a three-column table:
- **Address**
- **Raw Value**
- **Scaled Value**

Columns auto-resize, text is centre-aligned, and values are displayed cleanly.

### **Operation Log**
A timestamped log explains:
- What function code was used  
- What registers were touched  
- What values were read/written  
- Successes  
- Errors  
- Your life decisions  

All in easy human language, not the cryptic nonsense Modbus usually gives you.

### **Dark Navy Theme**
High-contrast, professional, and easy on the eyes during late-night debugging sessions.  
Looks good enough that people might think you know what you’re doing.

---

## Requirements

- **Python 3.8+**
- **PyQt5**
- **pyserial**
- **minimalmodbus**
- An RS-485 adapter  
  *(Please don’t try talking Modbus through HDMI. Someone has done this before.)*

## Install required packages:


pip install PyQt5 pyserial minimalmodbus

### Installation  
Clone or download this repository

Install the dependencies above

Plug in your USB–RS485 adapter

### Run the tester:

python modtest.py
Welcome to the world of clean Modbus debugging.

## Usage
1. Select COM Port
Use the dropdown or hit Refresh.
If nothing appears, check your cables, your drivers, and your life choices.

2. Choose Serial Settings
Baud rate, parity, data bits, stop bits — all the classics.
Defaults match most industrial devices.

3. Pick Register Type
Choose from:

Holding Registers

Input Registers

Coils

Discrete Inputs

UI adapts automatically (e.g., scaling disabled for bit types).

4. Set Start Address & Count
Tell the tester how many values you want.
(Up to 125 registers — because Modbus has rules and we follow them.)

5. Click “Fetch Data”
Watch the table fill and the log scroll.
Feel powerful.

6. Write Values
Pick an address

Enter a value

Click Write Value

Be responsible

### Double-check before writing to coils connected to anything thats in prod, near people or can cause any mischief...   

Seriously

I see you

## Tips, Tricks & Real-World Wisdom
If a read fails, 90% of the time it's the baud rate.

If a write fails, 90% of the time it's the slave ID.

If nothing works, 90% of the time your RS-485 A/B wires are backwards.

If things work intermittently, your ground reference is probably laughing at you.

If everything works perfectly, celebrate — you are now a Modbus professional.
(Or extremely lucky....... or a witch)


# Roadmap
### (a.k.a. Features That Might Exist If Future-Me Is Feeling Energetic..... or you bug me enough)

Batch reads/writes

Live graphing of register values

Saving/loading device profiles

CRC visualiser

Hex inspector

Automatic detection of slave address

“Chaos Mode™” — writes random values to everything
(for when you want to leave your impression on site)


