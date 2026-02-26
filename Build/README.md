# Ryzen Master Commander – Installation

Linux GUI application (PyQt6) to monitor and control Ryzen laptops: temperature, fan (NBFC), TDP (ryzenadj), real-time graphs, and custom profiles.

**Target:** Ubuntu 24.04.4 (Noble). May work on other Ubuntu/Debian-based systems.

**Requirements:** Internet connection (the installer will fetch all dependencies).

---

## Contents of this folder

| File | Description |
|------|-------------|
| **install-standalone.sh** | One-shot installer: system deps, extract bundle, Python venv, polkit, desktop shortcut, ryzenadj, nbfc. |
| **RyzenMasterCommander-bundle.tar.gz** | Application sources (no installer inside). |
| **README.md** | This file. |

The installer script must sit in the **same folder** as the `.tar.gz` file.

---

## Dependencies

The script installs everything; you do not need to install anything manually.

### System (apt)

- **python3** – Python 3 interpreter  
- **python3-venv** – Virtual environments  
- **python3.X-venv** – Venv for default Python (e.g. python3.12-venv on Ubuntu 24.04)  
- **python3-pip** – Pip for Python packages  
- **libxcb-cursor0** – Qt6 xcb plugin (GUI)  
- **lm-sensors** – Power/temperature readout (`sensors` command)  
- **curl** – Used only if needed to download nbfc .deb  

### Optional (installed by the script when available)

- **ryzenadj** – TDP/power limits (installed via Snap: `ryzenadj --beta --devmode`)  
- **nbfc** – Fan control (apt if in repos, otherwise .deb from [nbfc-linux](https://github.com/nbfc-linux/nbfc-linux/releases))  

### Python (pip, inside venv)

- **PyQt6** – GUI  
- **pyqtgraph** – Graphs  
- **numpy** – Numeric data  
- **Pillow** – Images  
- **pystray** – System tray icon  

---

## Installation (single command)

1. Download or clone this repo and go into the **Build** folder (or download only the Build folder with the three files).
2. In a terminal, inside that folder:

```bash
chmod +x install-standalone.sh
./install-standalone.sh
```

You will be prompted for your sudo password to install system packages, polkit, and optionally Snap/nbfc.

The script will:

1. Install system dependencies (Python, venv, pip, libxcb-cursor0).
2. Extract `RyzenMasterCommander-bundle.tar.gz` to `~/.local/ryzen-master-commander`.
3. Create the run script and Python virtual environment and install Python dependencies.
4. Install the polkit policy (fewer password prompts for TDP/fan).
5. Create a desktop shortcut.
6. Install **ryzenadj** via Snap (if Snap is available).
7. Install **nbfc** via apt or by downloading the .deb from nbfc-linux releases.

Then run **Ryzen Master Commander** from the desktop icon or:

```bash
~/.local/ryzen-master-commander/run-ryzen-master-commander.sh
```

### System-wide install (/opt)

```bash
./install-standalone.sh --system
```

Uses sudo to install under `/opt/ryzen-master-commander`.

---

## After installation

- **TDP (ryzenadj):** Installed by the script via Snap when available. If not, run:  
  `sudo snap install ryzenadj --beta --devmode`
- **Fan (nbfc):** Installed by the script (apt or .deb). Configure a profile for your laptop (e.g. “Lenovo ThinkPad T14 Gen2” for Lenovo V15 G3).

---

## License

This project is licensed under the Apache-2.0 license. Ryzen Master Commander uses [nbfc-linux](https://github.com/nbfc-linux/nbfc-linux) and [ryzenadj](https://github.com/FlyGoat/RyzenAdj).
