# py_clocks

`py_clocks` is a native desktop clock utility built with **DearPyGui**.

It provides three always-on productivity windows:

1. **World Clocks**
   - View multiple timezone clocks.
   - Add new clocks dynamically.
   - Search and select timezones from the IANA timezone list.

2. **Stopwatch**
   - Start / Pause / Lap / Reset controls.
   - Live precision display with lap history.

3. **Wellness Alerts**
   - Built-in reminders:
     - Close eyes every 30 minutes
     - Take a 2-minute walk every 60 minutes
   - Add custom alerts with your own interval.
   - Visual alert window border glow/pulse when reminders trigger.

## Tech Stack

- Python 3.10+
- [DearPyGui](https://github.com/hoffstadt/DearPyGui)
- pytz

## Installation

```bash
pip install -e .
```

## Run the App

```bash
python src/py_clocks/app.py
```

## Build an Executable (PyInstaller)

```bash
pyinstaller --onefile src/py_clocks/app.py
```

Generated executable:

- `dist/app.exe` (or platform-specific output name)

## Notes

- The app currently uses a fixed viewport/layout tuned for desktop usage.
- Timezone values use standard IANA timezone names such as `America/New_York` or `Europe/Berlin`.

## Documentation

- [Source manual](https://chaitu-ycr.github.io/py-clocks/source-manual)
