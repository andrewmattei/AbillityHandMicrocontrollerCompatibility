# Python Serial Communication 📡

This folder contains small example scripts and a controller class for communicating with an Ability Hand microcontroller (Teensy) over a serial port.

## Files & purpose 🔧

- `ability_hand_controller.py` — **threaded controller** that runs a background serial worker thread to send joint-position packets without blocking your main program.
- `threading_example.py` — a simple demo that **uses `AbilityHandController`** to exercise the hand (extends/retracts fingers); edit the hard-coded port value inside the script to match your device.
- `ability_hand_without_threading.py` — a standalone demo that **sends packets synchronously** on the main thread (useful for debugging or simple scripts).
- `requirements.txt` — pinned Python dependencies used by the examples (install them into a virtual environment before running the scripts).

---

## Quick setup & dependency installation ✅

1. Change to this folder:

```bash
cd "Python Serial Communication"
```

2. Create and activate a virtual environment (recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt
```

4. Verify installation (optional):

```bash
python -c "import serial, numpy; print('pyserial', getattr(serial, '__version__', 'unknown'), 'numpy', numpy.__version__)"
```

> Tip: Add `.venv/` to your repo `.gitignore` to avoid committing virtual environment files.

---

## Running the examples ▶️

- `threading_example.py`:
  - Edit the `port=` argument inside the script to the serial device that corresponds to your Teensy (or change the file to accept a CLI argument). Then run:

```bash
python threading_example.py
```

- `ability_hand_without_threading.py`:
  - Edit the `main()` call at the bottom of the file to point to your serial device, or call the `main()` function from another script. Example:

```bash
python ability_hand_without_threading.py
```

Both scripts write 6 float32 values as the packet format expected by the firmware (indexes 0–4: 0–100, index 5: -100–0). Make sure you set the correct baud rate and port name.

---