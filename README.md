# Z3spr1 Client

A lightweight, open-source Minecraft launcher built with Python and Tkinter. Z3spr1 Client lets you launch Minecraft (Vanilla or Fabric) with a clean dark-themed GUI, without requiring a premium Mojang account.

---

## Repository Files

| File | Description |
|------|-------------|
| `launcher.py.txt` | Main launcher application written in Python (Tkinter GUI). The `.txt` extension is intentional — see [Running the Launcher](#running-the-launcher). |
| `Iniciar Launcher.bat` | Windows batch file that starts the launcher by running `python launcher.py.txt`. Double-click this to launch the app. |
| `icono.ico.ico` | Application icon used by the launcher window. |
| `z3spr1 Launcher.lnk` | Windows shortcut that can be used as an alternative way to open the launcher. |

---

## Requirements

- **Windows** (the batch file is Windows-only)
- **Python 3.8 or newer** — [Download Python](https://www.python.org/downloads/)
  - Make sure Python is added to your system `PATH` during installation.
- **minecraft_launcher_lib** Python package

Install the required Python package by running this command in a terminal or Command Prompt:

```
pip install minecraft_launcher_lib
```

---

## Running the Launcher

> **Note about the filename:** The launcher script is saved as `launcher.py.txt`. Despite the `.txt` extension, it is valid Python code and Python can run it directly. This is how the batch file calls it.

**Recommended method — use the batch file:**

1. Double-click `Iniciar Launcher.bat`.

This opens a Command Prompt window and starts the GUI launcher automatically.

**Alternative — run directly from a terminal:**

```
python launcher.py.txt
```

---

## Features

- **Version selection** — Fetches the latest Minecraft release list from Mojang on startup. Falls back to a preset list (`1.21.1`, `1.20.1`, `1.16.5`, `1.8.9`) if no internet connection is available.
- **Game core options:**
  - *Vanilla (Original / Limpio)* — Standard Minecraft with no modifications.
  - *Fabric (Soporte para Mods)* — Installs Fabric mod loader automatically for the selected version.
- **Skin system options:**
  - *Oficial (Mojang Base)* — Uses the default Mojang skin service.
  - *Ely.by (Cargar Skins No-Prem)* — Redirects skin and authentication endpoints to [Ely.by](https://ely.by), allowing custom skins without a premium account.
- **Minecraft data folder** — All game files are stored in a `datos_minecraft` subfolder next to the launcher, keeping your installation self-contained.
- **Memory allocation** — The launcher starts the JVM with 1 GB minimum and 2 GB maximum heap by default.

---

## Disclaimer

This launcher runs Minecraft in **offline mode** and does not authenticate with Mojang servers. It is intended for educational and personal use only.

- You are solely responsible for complying with [Minecraft's End User License Agreement](https://www.minecraft.net/en-us/eula) and [Mojang's Terms of Service](https://account.mojang.com/terms).
- The use of third-party skin services such as Ely.by is at your own discretion.
- The project is open-source and provided as-is, with no warranty of any kind.
