# Ash’s Modbus RTU Tester
### For when you need to interrogate Modbus devices and refuse to do it like a caveman.

---

<img width="831" height="798" alt="image" src="https://github.com/user-attachments/assets/370774bb-e466-443e-abaa-e5812d00064c" />

---

## What Is This?

**Ash’s Modbus RTU Tester** is a dark-themed, aggressively practical desktop application for talking to Modbus RTU devices without losing your sanity, your eyesight, or your temper.

It exists because:
- Register maps lie
- Serial terminals are hostile environments
- Clicking “read” 300 times should not be a personality trait
- And life is too short to decode Modbus exceptions by vibes alone

This is a **local-only**, **no-cloud**, **no-login**, **no-subscription**, **no-bullshit** tool.  
Your data stays on your machine.  
Your devices stay confused, but less so.

---

## What It Does (In Plain English)

You can use this tool to:

- Scan your system for serial ports like a civilized human
- Connect to Modbus RTU devices over RS-485
- Read:
  - Holding Registers
  - Input Registers
  - Coils
  - Discrete Inputs
- Write:
  - Holding Registers
  - Coils
- Apply scaling, signed/unsigned handling, and decimal sanity
- Watch values update live without hammering buttons
- See raw Modbus RTU frames because sometimes you need receipts
- Decode Modbus exception responses into actual words
- Scan an entire RS-485 bus and find out what’s *actually alive*

All without touching a terminal.  
All without memorizing function codes like it’s 1997.

---

## Features (a.k.a. Why This Exists)

### Serial Port Scanning
Plug in your USB–RS485 adapter.  
Click **Refresh**.  
Ports appear.

If nothing shows up:
- Check drivers
- Check cables
- Check whether the adapter is actually plugged in
- Check your life choices, briefly

---

### Supports All The Important Modbus Stuff
Read functions:
- FC3 Holding Registers
- FC4 Input Registers
- FC1 Coils
- FC2 Discrete Inputs

Write functions:
- FC16 Write Holding Registers
- FC5 Write Single Coil

If you try to write to something that cannot be written, the UI will gently stop you instead of letting you set fire to reality.

---

### Scaling, Signedness & Decimals
Because raw register values are lies wrapped in integers.

- Convert 1234 into 12.34 by setting decimals
- Treat registers as signed when the device designer had feelings
- Or ignore scaling entirely and blame the device manufacturer

All options are explicit. Nothing is hidden. Nothing is guessed.

---

### Live Data Table
Every read populates a clean table showing:
- Address
- Raw Value
- Scaled Value

Columns auto-size.  
Text is readable.  
No Excel rituals required.

---

### Live Polling Mode
For when clicking “Read” repeatedly starts to feel like a cry for help.

- Enable polling
- Set an interval
- Watch values update continuously

Perfect for:
- Sensors that drift
- Counters that increment
- Diagnosing flaky wiring
- Pretending you’re running a SCADA system while actually reading register 0

---

### Raw RTU Frame Inspector
When vibes are not enough.

Every transaction logs:
- Raw TX bytes
- Raw RX bytes

You can:
- Verify CRCs
- Inspect payloads
- Prove the gateway is lying
- Or confirm that yes, the device really did send that nonsense

Nothing hidden. Nothing abstracted away.

---

### Modbus Exception Decoder
When the device responds with a firm, confident “No.”

Instead of dumping a cryptic error code, the log explains it in human language:

- Illegal Function: “I don’t support that”
- Illegal Data Address: “That register does not exist”
- Illegal Data Value: “That value is cursed”
- Device Failure: “Something inside me is screaming”

You get clarity.  
The device gets judged.

---

### Operation Log
A brutally honest, timestamped log that records:
- Function codes used
- Addresses accessed
- Values read or written
- Errors
- Exceptions
- Raw frames
- Your slow descent into Modbus expertise

Readable by humans.  
Not written by demons.

---

### Device Scanner Tab
For inherited installs where:
- Nobody documented slave IDs
- Half the bus is dead
- The rest was wired by someone who vanished in 2013

Scan a range of slave IDs and instantly see which devices actually respond.

It answers the most important Modbus question:
“Who the hell is even here?”

---

### Dark Navy Theme
- High contrast
- Easy on the eyes
- Late-night-debugging approved

Looks professional enough that people might stop hovering behind you asking questions.

---

## Requirements

- Python 3.8+
- PyQt5
- pyserial
- minimalmodbus
- A USB–RS485 adapter

Do not attempt Modbus over HDMI.  
Do not attempt Modbus over vibes.

---

## Installation

- Clone or download the repository
- Install dependencies
- Plug in your RS-485 adapter
- Run the application

That’s it.  
No installers arguing with you.  
No license agreements written by lawyers.

---

## Usage (The Short Version)

- Select a COM port
- Set serial parameters
- Choose register type
- Enter start address and count
- Read once or enable live polling
- Write values carefully and with intent

Double-check before writing to anything connected to:
- Motors
- Valves
- Humans
- Expensive machinery
- Anything that could ruin your week

I am serious.

---

## Tips From The Field

- If reads fail, it’s probably the baud rate
- If writes fail, it’s probably the slave ID
- If nothing works, swap A/B lines
- If it works sometimes, your ground reference is mocking you
- If everything works perfectly, do not celebrate too loudly

Something will notice.

---

## Roadmap
### a.k.a. Features That May Exist If I Am Fueled By Coffee And Spite

- Batch reads and writes
- Live graphing
- Device profiles
- CRC visualisation
- Packet filters
- Auto slave detection
- Better device fingerprinting
- Double-click devices from Scanner to auto-configure the Tester

- **Chaos Mode™**
  Writes random values to everything  
  For when you want to leave a permanent emotional imprint on a site

(Chaos Mode is a joke.  
Probably.)

---

If this tool saves you time, confusion, or at least one angry sigh, it has done its job.



