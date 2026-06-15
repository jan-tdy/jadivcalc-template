# JadivCalc Template

A small, friendly desktop GUI (PyQt6) that **generates math practice
examples** — N-digit numbers divisible by a chosen divisor, optionally
filtered by the divisibility of their digit sum. Results can be exported to
plain text, and every generated example is tracked in a registry so you never
hand out the same exercise twice.

Available in two languages:

| File | Language | UI |
|------|----------|----|
| `jadivcalc_template_en.py` | English | English |
| `jadivcalc_template(2).py` | Slovak  | Slovenčina |

> 📥 **Downloads / releases:** https://github.com/jan-tdy/jadivcalc-template/releases

---

## Features

- **Parametric generation** — pick the number of digits (1–6), the divisor,
  and the sort order (ascending / descending).
- **Digit-sum condition** — optionally require the digit sum to be divisible
  by a second number (great for practising divisibility rules).
- **Typographic output** — uses proper `÷` and `×` signs in the results.
- **No repeats** — generated examples are saved to a JSON registry and can be
  skipped on the next run.
- **Template + parameters saved** — your text template and settings are stored
  to a JSON file so they persist between sessions.
- **Export to TXT** — save a clean, formatted worksheet for printing.
- **Self-update** — on startup the app checks GitHub for a newer release and
  offers to update itself with a single click (see below).

---

## Requirements

- **Python 3.8+**
- **PyQt6**

```bash
pip install PyQt6
```

---

## Running

Pick the language you want and run it directly:

```bash
# English
python3 jadivcalc_template_en.py

# Slovak
python3 "jadivcalc_template(2).py"
```

---

## Desktop launcher (Linux)

To get a clickable entry (with icon) in your application menu instead of
running from a terminal:

```bash
./install-launcher.sh
```

This installs two launchers — **JadivCalc Template** (English) and
**JadivCalc Template (SK)** (Slovak) — plus the icon into your per-user XDG
directories (`~/.local/share/applications` and
`~/.local/share/icons`). No root access is required, and the launchers point
back at the scripts in this folder, so keep the repository where it is.

To remove them again:

```bash
./install-launcher.sh --uninstall
```

---

## Usage

1. Click **⚙ Settings** (top-right corner) to configure:
   - **Files** — where the registry and template JSON files are stored, and
     the free-text template string.
   - **Generation parameters** — number of digits, divisor, optional digit-sum
     divisor, and sort order.
   - **Saving** — whether to skip already-used examples, save new ones to the
     registry, and save the template.
2. Set the **number of examples** you want.
3. Click **Generate**. The results appear in the table below.
4. Click **Save as TXT** to export a printable worksheet.

### Output files

| File | Purpose |
|------|---------|
| `template-math_used.json` | Registry of every example that has been generated (used to avoid repeats). |
| `template-math.json` | The current text template plus the generation parameters and a timestamp. |

Both paths are configurable in **Settings**.

---

## Self-update

When the app starts it quietly asks GitHub for the latest published
[tag](https://github.com/jan-tdy/jadivcalc-template/tags) and compares it with
the version it is running.

- If a **newer version** exists, a popup appears offering to download and
  install it. Choosing **Yes** replaces the running script in place and keeps a
  backup with a `.bak` extension; you then restart the app to use the new
  version.
- If you are **already up to date**, nothing happens.
- If you are **offline** (or GitHub can't be reached), the check is skipped
  silently and the app starts normally.

The update only ever overwrites the script file it is launched from, and a
`.bak` copy of the previous version is kept right next to it so you can roll
back manually if needed.

---

## Project layout

```
jadivcalc-template/
├── jadivcalc_template_en.py   # English version
├── jadivcalc_template(2).py   # Slovak version
├── install-launcher.sh        # installs Linux desktop launchers
├── assets/
│   ├── jadivcalc.svg          # application icon
│   ├── jadivcalc.desktop      # English launcher
│   └── jadivcalc-sk.desktop   # Slovak launcher
└── README.md
```

The core logic (number generation, digit-sum filtering, registry handling) is
GUI-independent and lives in plain functions near the top of each file, with
the PyQt6 windows built on top.

---

## Contributing

Issues and pull requests are welcome. New versions are published as GitHub
releases/tags so the in-app updater can pick them up automatically — remember
to bump `APP_VERSION` in both files to match the new tag.
