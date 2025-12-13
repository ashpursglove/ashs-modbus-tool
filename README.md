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

**I've also included the pepe .ICO file and the base images i used to make it as well as
the pyinstaller command if you want to mess round with everything and re-build it**
  
### And who says I'm not a nice guy!

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
Even though it tastes the same

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

---

## Unless you really **REALLY** know what youre doing, do NOT write to:
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
### If I get round to it or if you bother me enough

- Batch reads and writes
- Live plotting
- Device profiles
- CRC visualisation
- Packet filtering
- Better device fingerprinting
- Auto-filling tester settings from scanner results

- **Chaos Mode™**
  Writes random values everywhere! For when you want to leave a permanent emotional imprint on a site

# License

MIT License.  
Use it, modify it, ship it, break it — just don’t blame me when you bring down the whole site!

---
