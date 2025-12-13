<!-- # **Ash’s Modbus RTU Tester**  
### *For when you need to speak fluent Modbus RTU and want to look cool AF while doing it.*

---
<img width="831" height="798" alt="image" src="https://github.com/user-attachments/assets/370774bb-e466-443e-abaa-e5812d00064c" />

---
## What Is This?

**Ash’s Modbus RTU Tester** is a (thankfully) dark-themed, feature-packed, ""highly-engineered"" desktop tool that lets you:

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

### **Serial Port Scanning (Auto + Manual Refresh)**
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
#### Welcome to the world of clean Modbus debugging.

## Usage
**1. Select COM Port**  
Use the dropdown or hit Refresh.  
If nothing appears, check your cables, your drivers, and your life choices.  
  
**2. Choose Serial Settings**  
Baud rate, parity, data bits, stop bits — all the classics.  
Defaults match most industrial devices.  
  
**3. Pick Register Type**  
Choose from:  
Holding Registers  
Input Registers  
Coils  
Discrete Inputs  
  
**UI adapts automatically (e.g., scaling disabled for bit types).**  
  
**4. Set Start Address & Count**  
Tell the tester how many values you want.  
(Up to 125 registers — because Modbus has rules and we follow them.)  
  
**5. Click “Fetch Data”**  
Watch the table fill and the log scroll.  
Feel powerful.  

**6. Write Values**  
Pick an address  
Enter a value  
Click Write Value  
**Be responsible**....... Like seriously....  
  
### Double-check before writing to coils connected to anything that's in prod, near people or can cause any mischief...   

Seriously

I see you

## Tips, Tricks & Real-World Wisdom
- If a read fails, 90% of the time it's the baud rate.

- If a write fails, 90% of the time it's the slave ID.

- If nothing works, 90% of the time your RS-485 A/B wires are backwards.

- If things work intermittently, your ground reference is probably laughing at you.

- If everything works perfectly, celebrate — you are now a Modbus professional.
(Or extremely lucky....... or a witch)


# Roadmap
### (a.k.a. Features That Might Exist If Future-Me Is Feeling Energetic..... or you bug me enough)

- Batch reads/writes

- Live graphing of register values

- Saving/loading device profiles

- CRC visualiser

- Hex inspector

- Automatic detection of slave address

- **“Chaos Mode™” — writes random values to everything
(for when you want to leave your impression on site)**
  

 -->



# Ash’s Modbus RTU Tester
### A pragmatic tool for people who have already been hurt by Modbus.

---

<img width="831" height="798" alt="image" src="https://github.com/user-attachments/assets/370774bb-e466-443e-abaa-e5812d00064c" />

---

## What This Is (And Why It Exists)

It was built because:
- Register maps are works of fiction
- Vendors lie with confidence
- Serial terminals hate you personally
- And “just try another baud rate” is not a debugging strategy

This tool is:
- 100% local
- No cloud
- No accounts
- No telemetry
- No “free tier”
- No asking you nicely to sign in with Google

It runs on your machine and minds its own business.  
Like software used to.

This tool assumes you are tired, skeptical, and just want the truth.

---

## What It Does

It lets you:

- Find serial ports without guessing
- Connect to Modbus RTU devices over RS-485
- Read:
  - Holding Registers
  - Input Registers
  - Coils
  - Discrete Inputs
- Write:
  - Holding Registers
  - Coils
- Apply scaling so values resemble physics again
- Watch registers update live without re-clicking buttons
- Inspect raw RTU frames when something smells wrong
- Decode Modbus exceptions into something approximating English
- Scan a bus and figure out which slave IDs actually exist

No cloud.  
No accounts.  
No “smart” automation making assumptions on your behalf.

---

## Yes, There’s an EXE (Relax)

There is a **pre-built Windows EXE** included in this repository.

Before anyone starts clearing their throat:

- Yes, it’s there
- Yes, you can use it
- No, it does not make you a bad engineer
- Yes, some people will judge you anyway

The EXE exists for:
- Being on site
- Being tired
- Being done with Python environments
- Wanting the tool to just open and work immediately

Using the EXE is:
- Considered “cheating” by people who haven’t shipped anything this year
- Deeply offensive to the “I always build from source” crowd
- Extremely convenient in the real world

**OGs build from source.**  
They also mention it.  
Repeatedly.

Everyone else double-clicks the EXE, gets the job done, and keeps it to themselves.

Both approaches work.  
One just comes with a louder opinion.

---

## Features (All Earned the Hard Way)

### Serial Port Scanning
Plug in your USB–RS485 adapter.  
Hit Refresh.  
Ports appear.

If they don’t:
- The driver is wrong
- The adapter is fake
- Or Windows has decided to be Windows

---

### Actual Modbus Coverage
Reads:
- FC3 Holding Registers
- FC4 Input Registers
- FC1 Coils
- FC2 Discrete Inputs

Writes:
- FC16 Holding Registers
- FC5 Single Coil

Unsupported operations are blocked, because Modbus already has enough undefined behavior without encouragement.

---

### Scaling and Signed Values
Because raw registers are rarely the truth.

- Apply decimal scaling
- Interpret registers as signed or unsigned
- Stop pretending 65535 is a temperature

No magic.  
No guessing.  
You decide how lies become numbers.

---

### Data Table That Tells You What’s Going On
Every read shows:
- Address
- Raw value
- Scaled value

Nothing hidden.  
Nothing “helpfully” rounded away.

---

### Live Polling
For when “click Read again” stops being a lifestyle you enjoy.

- Enable polling
- Set interval
- Watch values drift, increment, or misbehave in real time

Useful for:
- Sensors
- Counters
- Verifying whether anything is actually changing
- Confirming that no, the device really is stuck

---

### Raw RTU Frame Inspector
Because sometimes the only way to know who’s lying is to look at the bytes.

You get:
- Exact TX frames
- Exact RX frames

Good for:
- CRC sanity checks
- Gateway weirdness
- Confirming that the slave replied with something technically valid and still useless

---

### Modbus Exception Decoder
Instead of:
“Exception code 0x02”

You get:
- Illegal Function: Not supported, never was, c'mon bro
- Illegal Data Address: That register does not exist, stop asking
- Illegal Data Value: Technically valid, practically nonsense
- Device Failure: Something inside me is burning.

Still Modbus.  
Just less cryptic.

---

### Operation Log
A running log that records:
- What was requested
- What function code was used
- What came back
- Whether it failed
- How it failed
- And sometimes why

Readable by humans who have already accepted the nature of this protocol.

---

### Device Scanner
For buses where:
- Slave IDs were never written down
- Half the devices were added “temporarily”
- Nobody is sure what still responds
- The bus was obviously wired during a nasty divorce

Scan an ID range and see who answers.

It’s not discovery.  
It’s survival.

---

### Dark Theme
- High contrast
- Low glare
- Designed for late nights and bad documentation

It will not fix Modbus.  
But it won’t make it worse.

---

## Requirements

- Python 3.8+
- PyQt5
- pyserial
- minimalmodbus
- A USB–RS485 adapter

Modbus is not Ethernet.  
It will not negotiate.  
It does not forgive.

---

## Installation

- Clone or download the repository
- Install dependencies
- Plug in your adapter
- Run the application

Or:
- Double-click the EXE
- Ignore the faint screaming from GitHub purists
- Finish the job

No installers.  
No wizards.  
No surprise background services.

---

## Usage (You Already Know How This Goes)

- Select COM port
- Set serial parameters
- Choose register type
- Enter address and count
- Read once or enable polling
- Write carefully

Do NOT write to:
- Live machinery
- Safety systems
- Anything that spins
- Anything expensive
- Anything connected to humans

### If you ignore this and something explodes, that’s between you and God.
### Modbus will not stop you.

---

## Notes From Experience

- If reads fail, check baud rate
- If writes fail, check slave ID
- If nothing works, swap A/B
- If it works intermittently, grounding is probably bad
- If it works perfectly, shut up and don’t touch anything

---

## Roadmap
### Also Known As “After I Recover Emotionally”

- Batch reads and writes
- Live plotting
- Device profiles
- CRC visualisation
- Packet filtering
- Better device fingerprinting
- Auto-filling tester settings from scanner results

- **Chaos Mode™**
  Writes random values everywhere! For when you want to leave a permanent emotional imprint on a site

---
