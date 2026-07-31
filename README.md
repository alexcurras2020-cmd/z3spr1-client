# Z3spr1 Client

A lightweight, open-source Minecraft launcher built with Python and Tkinter. Z3spr1 Client lets you launch Minecraft (Vanilla or Fabric) with a clean dark-themed GUI, without requiring a premium Mojang account.

---

## Repository Files

| File | Description |
|------|-------------|
| `launcher.py` | Main launcher application written in Python (Tkinter GUI). |
| `Iniciar Launcher.bat` | Windows batch file that starts the launcher. Double-click this to launch the app. |
| `requirements.txt` | Python dependencies. |
| `icono.ico.ico` | Application icon, used for the launcher window. |
| `z3spr1 Launcher.lnk` | Windows shortcut. **Note:** it stores an absolute path from the machine it was created on, so it only works if the project sits in that exact folder. Use the `.bat` instead, or create your own shortcut to it. |

Two paths are created next to the launcher at runtime and are excluded from git:

- `datos_minecraft/` — self-contained Minecraft installation (several GB).
- `config.json` — your last used nickname, version, core, RAM and skin choice.

---

## Requirements

- **Windows** (the batch file is Windows-only; the Python script itself is portable apart from the RAM auto-detection)
- **Python 3.8 or newer** — [Download Python](https://www.python.org/downloads/)
  - Make sure Python is added to your system `PATH` during installation.
- **Java** — required by Minecraft itself. Modern versions need Java 17+.

Install the Python dependency:

```
pip install -r requirements.txt
```

---

## Running the Launcher

**Recommended — use the batch file:**

1. Double-click `Iniciar Launcher.bat`.

It switches to the project folder, finds `python` (or `py -3`), and starts the GUI. The window stays open only if something fails, so you can read the error.

**Alternative — run directly from a terminal:**

```
python launcher.py
```

---

## Features

- **Version selection** — Fetches the Minecraft release list from Mojang **in the background**, so the window opens instantly. Falls back to a preset list (`1.21.1`, `1.20.1`, `1.16.5`, `1.8.9`) if there is no internet connection.
- **Game core options:**
  - *Vanilla (Original / Limpio)* — Standard Minecraft with no modifications.
  - *Fabric (Soporte para Mods)* — Installs the Fabric mod loader for the selected version. If a Fabric profile is already installed it is reused, and the newest loader is picked. Unsupported versions are reported up front instead of failing mid-install.
- **Skin system options:**
  - *Oficial (Mojang Base)* — Uses the default Mojang skin service.
  - *Ely.by (Cargar Skins No-Prem)* — Redirects skin and authentication endpoints to [Ely.by](https://ely.by), allowing custom skins without a premium account.
- **Responsive UI** — Downloading and running the game happen on a worker thread. The window never freezes, and a progress bar shows the current file and percentage.
- **Memory allocation** — Selectable from 2 GB to 16 GB. The default is derived from your installed RAM. The JVM is started with G1GC tuning flags that reduce in-game stutter.
- **Stable offline identity** — Each nickname gets a deterministic offline UUID (the same one a vanilla offline server derives), so inventories and permissions persist across sessions.
- **Remembered preferences** — Your last nickname, version, core, RAM and skin choice are restored on the next start.
- **Self-contained data** — All game files live in `datos_minecraft` next to the launcher, resolved from the script's own location so shortcuts work from anywhere.

---

## Disclaimer

This launcher runs Minecraft in **offline mode** and does not authenticate with Mojang servers. It is intended for educational and personal use only.

- You are solely responsible for complying with [Minecraft's End User License Agreement](https://www.minecraft.net/en-us/eula) and [Mojang's Terms of Service](https://account.mojang.com/terms).
- The use of third-party skin services such as Ely.by is at your own discretion.
- The project is open-source and provided as-is, with no warranty of any kind.
