#!/usr/bin/env python3
"""JadivCalc Template – parametrický generátor matematických príkladov (PyQt6).

Generuje N-ciferné čísla deliteľné zvoleným deliteľom (voliteľne s podmienkou
na deliteľnosť ciferného súčtu) vo vzostupnom alebo zostupnom poradí.

Výstup používa typografické znamienka (÷, ×); textová šablóna sa ukladá tak,
ako ju zadáš (napr. s '/' a '*').

Nastavenia sú v samostatnom okne (tlačidlo v pravom hornom rohu).

Ukladá:
  - register použitých príkladov  -> template-math_used.json
  - definíciu šablóny + parametre  -> template-math.json
"""

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime
from urllib.parse import quote

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog,
    QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPlainTextEdit, QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

APP_NAME = "JadivCalc Template"
APP_VERSION = "0.2.0"
DIV_SIGN = "÷"
MUL_SIGN = "×"

DEFAULT_USED_FILE = "template-math_used.json"
DEFAULT_TEMPLATE_FILE = "template-math.json"
DEFAULT_TEMPLATE = "abcd/3=3*x       a+b+c+d=3*y"

# --- automatická aktualizácia -----------------------------------------------

GITHUB_OWNER = "jan-tdy"
GITHUB_REPO = "jadivcalc-template"
GITHUB_API_TAGS = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/tags"
RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}"


def version_tuple(v):
    """Rozparsuje verziu/tag ('v0.1.1', '1.2') na porovnateľnú n-ticu."""
    parts = []
    for chunk in str(v).strip().lstrip("vV").split("."):
        digits = "".join(ch for ch in chunk if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def fetch_latest_tag(timeout=6):
    """Vráti najnovší tag na GitHube (napr. 'v0.1.2'), alebo None."""
    req = urllib.request.Request(
        GITHUB_API_TAGS,
        headers={"Accept": "application/vnd.github+json", "User-Agent": APP_NAME},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        tags = json.load(resp)
    if not isinstance(tags, list) or not tags:
        return None
    best = max(tags, key=lambda t: version_tuple(t.get("name", "")))
    return best.get("name")


def download_script(tag, timeout=20):
    """Stiahne zdrojový kód tohto skriptu publikovaný pod `tag`."""
    filename = os.path.basename(os.path.abspath(__file__))
    url = f"{RAW_BASE}/{quote(tag)}/{quote(filename)}"
    req = urllib.request.Request(url, headers={"User-Agent": APP_NAME})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def install_update(tag):
    """Stiahne `tag` a prepíše spustený skript (so zálohou .bak)."""
    new_code = download_script(tag)
    if not new_code or b"JadivCalc" not in new_code:
        raise OSError("Stiahnutý súbor sa zdá byť poškodený.")
    target = os.path.abspath(__file__)
    tmp = target + ".new"
    backup = target + ".bak"
    with open(tmp, "wb") as f:
        f.write(new_code)
    if os.path.exists(target):
        os.replace(target, backup)
    os.replace(tmp, target)


def restart_app():
    """Znovu spustí bežiaci skript s rovnakým interpretrom a argumentmi."""
    os.execv(sys.executable,
             [sys.executable, os.path.abspath(__file__), *sys.argv[1:]])


def check_for_update(parent=None, silent=True):
    """Skontroluje na GitHube novší tag a cez okno ponúkne aktualizáciu.

    Pri `silent` = True (automatická kontrola pri štarte) sa chyby aj prípad
    „máš najnovšiu verziu“ nezobrazia, takže sa aplikácia spustí aj offline.
    Pri False (manuálne „Skontrolovať aktualizácie“) sa zobrazí každý výsledok.
    """
    try:
        tag = fetch_latest_tag()
    except (urllib.error.URLError, OSError, ValueError, json.JSONDecodeError) as e:
        if not silent:
            QMessageBox.warning(
                parent, "Kontrola aktualizácií zlyhala",
                f"Nepodarilo sa spojiť s GitHubom kvôli kontrole aktualizácií:\n{e}")
        return

    if not tag:
        if not silent:
            QMessageBox.warning(parent, "Kontrola aktualizácií",
                                "Na GitHube sa nenašli žiadne vydania.")
        return

    if version_tuple(tag) <= version_tuple(APP_VERSION):
        if not silent:
            QMessageBox.information(
                parent, "Aktuálna verzia",
                f"Používaš najnovšiu verziu (v{APP_VERSION}).")
        return

    ask = QMessageBox(parent)
    ask.setIcon(QMessageBox.Icon.Information)
    ask.setWindowTitle("Dostupná aktualizácia")
    ask.setText(f"K dispozícii je nová verzia {tag} "
                f"(používaš v{APP_VERSION}).")
    ask.setInformativeText("Stiahnuť a nainštalovať teraz?")
    ask.setStandardButtons(
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    ask.setDefaultButton(QMessageBox.StandardButton.Yes)
    if ask.exec() != QMessageBox.StandardButton.Yes:
        return

    try:
        install_update(tag)
    except (urllib.error.URLError, OSError) as e:
        QMessageBox.critical(parent, "Aktualizácia zlyhala",
                             f"Aktualizáciu sa nepodarilo nainštalovať:\n{e}")
        return

    done = QMessageBox(parent)
    done.setIcon(QMessageBox.Icon.Information)
    done.setWindowTitle("Aktualizácia dokončená")
    done.setText(f"Aktualizované na {tag}.")
    done.setInformativeText("Reštartovať teraz, aby sa nová verzia prejavila?")
    done.setStandardButtons(
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    done.setDefaultButton(QMessageBox.StandardButton.Yes)
    if done.exec() == QMessageBox.StandardButton.Yes:
        restart_app()


# --- jadro (logika, nezávislá od GUI) ---------------------------------------

def default_settings():
    return {
        "used_path": os.path.abspath(DEFAULT_USED_FILE),
        "tpl_path": os.path.abspath(DEFAULT_TEMPLATE_FILE),
        "template": DEFAULT_TEMPLATE,
        "num_digits": 4,
        "divisor": 3,
        "use_sum": True,
        "sum_divisor": 3,
        "order": "asc",
        "skip_used": True,
        "save_used": True,
        "save_tpl": True,
    }


def digit_sum(n):
    s = 0
    while n:
        s += n % 10
        n //= 10
    return s


def build_pool(num_digits, divisor, use_sum, sum_divisor, order):
    """N-ciferné čísla deliteľné `divisor`, voliteľne s ciferným súčtom
    deliteľným `sum_divisor`. Vracia zoznam v zadanom poradí."""
    low = 1 if num_digits == 1 else 10 ** (num_digits - 1)
    high = 10 ** num_digits - 1
    start = low + ((-low) % divisor)          # prvé >= low deliteľné `divisor`
    nums = range(start, high + 1, divisor)
    if use_sum and sum_divisor > 0:
        pool = [n for n in nums if digit_sum(n) % sum_divisor == 0]
    else:
        pool = list(nums)
    if order == "desc":
        pool.reverse()
    return pool


def make_record(n, divisor, use_sum, sum_divisor):
    digits = [int(ch) for ch in str(n)]
    ds = sum(digits)
    q, r = divmod(n, divisor)
    rec = {
        "n": n,
        "digits": digits,
        "divisor": divisor,
        "quotient": q,
        "remainder": r,
        "digit_sum": ds,
        "eq_div": f"{n}{DIV_SIGN}{divisor}={q}" + ("" if r == 0 else f" zv.{r}"),
    }
    plus = "+".join(str(d) for d in digits)
    if use_sum and sum_divisor > 0:
        rec["sum_divisor"] = sum_divisor
        rec["sum_quotient"] = ds // sum_divisor
        rec["eq_sum"] = f"{plus}={sum_divisor}{MUL_SIGN}{ds // sum_divisor}"
    else:
        rec["eq_sum"] = f"{plus}={ds}"
    return rec


def load_registry(path):
    if not path or not os.path.isfile(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("examples"), list):
        return data["examples"]
    return []


def used_set(registry):
    out = set()
    for r in registry:
        if "n" in r:
            out.add(r["n"])
        elif "abcd" in r:            # spätná kompatibilita so staršími súbormi
            out.add(r["abcd"])
    return out


def save_registry(path, registry):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)


def save_template(path, template_str, params, last_count):
    data = {
        "template": template_str,
        "params": params,
        "last_generated_count": last_count,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# --- okno nastavení ---------------------------------------------------------

class SettingsDialog(QDialog):
    def __init__(self, parent, settings):
        super().__init__(parent)
        self.setWindowTitle(f"Nastavenia – {APP_NAME}")
        self.setMinimumWidth(540)
        self._build(settings)

    def _build(self, s):
        lay = QVBoxLayout(self)

        # Súbory
        files = QGroupBox("Súbory")
        fg = QGridLayout(files)
        fg.addWidget(QLabel("Register (JSON):"), 0, 0)
        self.used_path = QLineEdit(s["used_path"])
        fg.addWidget(self.used_path, 0, 1)
        bu = QPushButton("…")
        bu.setFixedWidth(32)
        bu.clicked.connect(lambda: self._pick(self.used_path))
        fg.addWidget(bu, 0, 2)

        fg.addWidget(QLabel("Šablóna (JSON):"), 1, 0)
        self.tpl_path = QLineEdit(s["tpl_path"])
        fg.addWidget(self.tpl_path, 1, 1)
        bt = QPushButton("…")
        bt.setFixedWidth(32)
        bt.clicked.connect(lambda: self._pick(self.tpl_path))
        fg.addWidget(bt, 1, 2)

        fg.addWidget(QLabel("Šablóna (text):"), 2, 0)
        self.template = QLineEdit(s["template"])
        fg.addWidget(self.template, 2, 1, 1, 2)
        fg.setColumnStretch(1, 1)
        lay.addWidget(files)

        # Parametre generovania
        params = QGroupBox("Parametre generovania")
        pg = QGridLayout(params)
        pg.addWidget(QLabel("Počet číslic:"), 0, 0)
        self.num_digits = QSpinBox()
        self.num_digits.setRange(1, 6)
        self.num_digits.setValue(s["num_digits"])
        pg.addWidget(self.num_digits, 0, 1)

        pg.addWidget(QLabel("Deliteľ:"), 1, 0)
        self.divisor = QSpinBox()
        self.divisor.setRange(1, 9999)
        self.divisor.setValue(s["divisor"])
        pg.addWidget(self.divisor, 1, 1)

        self.use_sum = QCheckBox("Ciferný súčet musí byť deliteľný:")
        self.use_sum.setChecked(s["use_sum"])
        pg.addWidget(self.use_sum, 2, 0)
        self.sum_divisor = QSpinBox()
        self.sum_divisor.setRange(1, 99)
        self.sum_divisor.setValue(s["sum_divisor"])
        pg.addWidget(self.sum_divisor, 2, 1)
        self.use_sum.toggled.connect(self.sum_divisor.setEnabled)
        self.sum_divisor.setEnabled(s["use_sum"])

        pg.addWidget(QLabel("Poradie:"), 3, 0)
        self.order = QComboBox()
        self.order.addItems(["vzostupne", "zostupne"])
        self.order.setCurrentIndex(0 if s["order"] == "asc" else 1)
        pg.addWidget(self.order, 3, 1)
        pg.setColumnStretch(1, 1)
        lay.addWidget(params)

        # Ukladanie
        opts = QGroupBox("Ukladanie")
        og = QVBoxLayout(opts)
        self.skip_used = QCheckBox("Vynechať príklady, ktoré sú už v registri")
        self.skip_used.setChecked(s["skip_used"])
        og.addWidget(self.skip_used)
        self.save_used = QCheckBox("Uložiť vygenerované do registra")
        self.save_used.setChecked(s["save_used"])
        og.addWidget(self.save_used)
        self.save_tpl = QCheckBox("Uložiť šablónu do súboru")
        self.save_tpl.setChecked(s["save_tpl"])
        og.addWidget(self.save_tpl)
        lay.addWidget(opts)

        # Aktualizácie
        updates = QGroupBox("Aktualizácie")
        ug = QHBoxLayout(updates)
        ug.addWidget(QLabel(f"Aktuálna verzia: v{APP_VERSION}"))
        ug.addStretch(1)
        btn_upd = QPushButton("Skontrolovať aktualizácie")
        btn_upd.clicked.connect(lambda: check_for_update(self, silent=False))
        ug.addWidget(btn_upd)
        lay.addWidget(updates)

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        bb.rejected.connect(self.accept)
        bb.accepted.connect(self.accept)
        lay.addWidget(bb)

    def _pick(self, line_edit):
        p, _ = QFileDialog.getSaveFileName(
            self, "Vybrať súbor", line_edit.text() or "data.json",
            "JSON (*.json);;Všetky súbory (*.*)")
        if p:
            line_edit.setText(p)

    def get_values(self):
        return {
            "used_path": self.used_path.text().strip(),
            "tpl_path": self.tpl_path.text().strip(),
            "template": self.template.text(),
            "num_digits": self.num_digits.value(),
            "divisor": self.divisor.value(),
            "use_sum": self.use_sum.isChecked(),
            "sum_divisor": self.sum_divisor.value(),
            "order": "asc" if self.order.currentIndex() == 0 else "desc",
            "skip_used": self.skip_used.isChecked(),
            "save_used": self.save_used.isChecked(),
            "save_tpl": self.save_tpl.isChecked(),
        }


# --- hlavné okno ------------------------------------------------------------

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        self.resize(720, 620)
        self.setMinimumSize(560, 480)
        self.settings = SettingsDialog(self, default_settings())
        self.settings.finished.connect(self._refresh_subtitle)
        self._build()
        self._refresh_subtitle()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(10)

        # hlavička + tlačidlo nastavení v rohu
        top = QHBoxLayout()
        title = QLabel(APP_NAME)
        hf = QFont()
        hf.setPointSize(15)
        hf.setBold(True)
        title.setFont(hf)
        top.addWidget(title)
        top.addStretch(1)
        gear = QPushButton("⚙ Nastavenia")
        gear.clicked.connect(self.open_settings)
        top.addWidget(gear)
        root.addLayout(top)

        self.subtitle = QLabel()
        self.subtitle.setStyleSheet("color: gray;")
        root.addWidget(self.subtitle)

        # počet + generovať
        row = QHBoxLayout()
        row.addWidget(QLabel("Počet príkladov:"))
        self.count = QSpinBox()
        self.count.setRange(1, 1_000_000)
        self.count.setValue(10)
        row.addWidget(self.count)
        row.addStretch(1)
        gen = QPushButton("Generovať")
        gen.setMinimumHeight(34)
        gen.setStyleSheet("font-weight: bold;")
        gen.clicked.connect(self.generate)
        row.addWidget(gen)
        self.btn_txt = QPushButton("Uložiť ako TXT")
        self.btn_txt.setMinimumHeight(34)
        self.btn_txt.setEnabled(False)
        self.btn_txt.clicked.connect(self.save_txt)
        row.addWidget(self.btn_txt)
        root.addLayout(row)

        # výstup
        out_box = QGroupBox("Výsledok")
        out_lay = QVBoxLayout(out_box)
        self.out = QPlainTextEdit()
        self.out.setReadOnly(True)
        self.out.setFont(QFont("Monospace", 10))
        out_lay.addWidget(self.out)
        root.addWidget(out_box, 1)

        self.status = QLabel("Pripravené.")
        root.addWidget(self.status)

    def open_settings(self):
        self.settings.show()
        self.settings.raise_()
        self.settings.activateWindow()

    def _refresh_subtitle(self):
        s = self.settings.get_values()
        cond = f", ciferný súčet {DIV_SIGN}{s['sum_divisor']}" if s["use_sum"] else ""
        order = "vzostupne" if s["order"] == "asc" else "zostupne"
        self.subtitle.setText(
            f"{s['num_digits']}-cifer. čísla deliteľné {s['divisor']}{cond} · {order}")

    def generate(self):
        s = self.settings.get_values()
        count = self.count.value()

        registry = load_registry(s["used_path"])
        used = used_set(registry)

        pool = build_pool(s["num_digits"], s["divisor"], s["use_sum"],
                          s["sum_divisor"], s["order"])
        if s["skip_used"]:
            pool = [n for n in pool if n not in used]

        if not pool:
            QMessageBox.warning(self, "Upozornenie",
                                "Pre dané parametre nie sú dostupné žiadne nové príklady.")
            return
        if count > len(pool):
            QMessageBox.warning(
                self, "Upozornenie",
                f"Dostupných je len {len(pool)} príkladov. Vygeneruje sa {len(pool)}.")
            count = len(pool)

        chosen = pool[:count]
        records = [make_record(n, s["divisor"], s["use_sum"], s["sum_divisor"])
                   for n in chosen]

        notes = []
        if s["save_used"] and s["used_path"]:
            new = [r for r in records if r["n"] not in used]
            try:
                save_registry(s["used_path"], registry + new)
            except OSError as e:
                QMessageBox.critical(self, "Chyba pri ukladaní registra", str(e))
                return
            notes.append(f"register +{len(new)}")

        if s["save_tpl"] and s["tpl_path"]:
            params = {k: s[k] for k in
                      ("num_digits", "divisor", "use_sum", "sum_divisor", "order")}
            try:
                save_template(s["tpl_path"], s["template"], params, len(records))
            except OSError as e:
                QMessageBox.critical(self, "Chyba pri ukladaní šablóny", str(e))
                return
            notes.append("šablóna uložená")

        self._show(records)
        self.records = records
        self.btn_txt.setEnabled(True)
        suffix = ("  (" + ", ".join(notes) + ")") if notes else ""
        self.status.setText(f"Vygenerovaných {len(records)} príkladov.{suffix}")

    def _format_lines(self, records):
        w = max((len(str(r["n"])) for r in records), default=5)
        head = f"{'#':>4}  {'číslo':<{w}}  {'delenie':<16}  ciferný súčet"
        lines = [head, "─" * max(len(head), 40)]
        for i, r in enumerate(records, 1):
            lines.append(
                f"{i:>4}  {r['n']:<{w}}  {r['eq_div']:<16}  {r['eq_sum']}")
        return lines

    def _show(self, records):
        self.out.setPlainText("\n".join(self._format_lines(records)))

    def save_txt(self):
        if not getattr(self, "records", None):
            return
        p, _ = QFileDialog.getSaveFileName(
            self, "Uložiť ako TXT", "priklady.txt",
            "Text (*.txt);;Všetky súbory (*.*)")
        if not p:
            return
        s = self.settings.get_values()
        cond = f", ciferný súčet {DIV_SIGN}{s['sum_divisor']}" if s["use_sum"] else ""
        order = "vzostupne" if s["order"] == "asc" else "zostupne"
        header = [
            f"{APP_NAME} {APP_VERSION}",
            f"Šablóna: {s['template']}",
            f"Parametre: {s['num_digits']}-cifer. deliteľné {s['divisor']}{cond} · {order}",
            f"Počet: {len(self.records)}   "
            f"({datetime.now().isoformat(timespec='seconds')})",
            "",
        ]
        body = self._format_lines(self.records)
        try:
            with open(p, "w", encoding="utf-8") as f:
                f.write("\n".join(header + body) + "\n")
        except OSError as e:
            QMessageBox.critical(self, "Chyba pri ukladaní", str(e))
            return
        self.status.setText(f"Uložené do {os.path.basename(p)}")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    w = App()
    w.show()
    # Kontrolu aktualizácií spusti až po vykreslení okna; pri chybách / aktuálnej
    # verzii ostane ticho, aby spustenie offline nič nerušilo.
    QTimer.singleShot(0, lambda: check_for_update(w, silent=True))
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
