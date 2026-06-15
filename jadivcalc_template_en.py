#!/usr/bin/env python3
"""JadivCalc Template – parametric math-example generator (PyQt6).

Generates N-digit numbers divisible by a chosen divisor (optionally with a
condition on the divisibility of the digit sum), in ascending or descending
order.

Output uses typographic signs (÷, ×); the text template is stored exactly as
you type it (e.g. with '/' and '*').

Settings live in a separate window (button in the top-right corner).

Saves:
  - registry of used examples       -> template-math_used.json
  - template definition + parameters -> template-math.json
"""

import json
import os
import sys
from datetime import datetime

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog,
    QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPlainTextEdit, QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

APP_NAME = "JadivCalc Template"
APP_VERSION = "1.1"
DIV_SIGN = "÷"
MUL_SIGN = "×"

DEFAULT_USED_FILE = "template-math_used.json"
DEFAULT_TEMPLATE_FILE = "template-math.json"
DEFAULT_TEMPLATE = "abcd/3=3*x       a+b+c+d=3*y"


# --- core (GUI-independent logic) -------------------------------------------

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
    """N-digit numbers divisible by `divisor`, optionally with a digit sum
    divisible by `sum_divisor`. Returns a list in the requested order."""
    low = 1 if num_digits == 1 else 10 ** (num_digits - 1)
    high = 10 ** num_digits - 1
    start = low + ((-low) % divisor)          # first >= low divisible by divisor
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
        "eq_div": f"{n}{DIV_SIGN}{divisor}={q}" + ("" if r == 0 else f" r.{r}"),
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
        elif "abcd" in r:            # backward compatibility with older files
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


# --- settings window --------------------------------------------------------

class SettingsDialog(QDialog):
    def __init__(self, parent, settings):
        super().__init__(parent)
        self.setWindowTitle(f"Settings – {APP_NAME}")
        self.setMinimumWidth(540)
        self._build(settings)

    def _build(self, s):
        lay = QVBoxLayout(self)

        # Files
        files = QGroupBox("Files")
        fg = QGridLayout(files)
        fg.addWidget(QLabel("Registry (JSON):"), 0, 0)
        self.used_path = QLineEdit(s["used_path"])
        fg.addWidget(self.used_path, 0, 1)
        bu = QPushButton("…")
        bu.setFixedWidth(32)
        bu.clicked.connect(lambda: self._pick(self.used_path))
        fg.addWidget(bu, 0, 2)

        fg.addWidget(QLabel("Template (JSON):"), 1, 0)
        self.tpl_path = QLineEdit(s["tpl_path"])
        fg.addWidget(self.tpl_path, 1, 1)
        bt = QPushButton("…")
        bt.setFixedWidth(32)
        bt.clicked.connect(lambda: self._pick(self.tpl_path))
        fg.addWidget(bt, 1, 2)

        fg.addWidget(QLabel("Template (text):"), 2, 0)
        self.template = QLineEdit(s["template"])
        fg.addWidget(self.template, 2, 1, 1, 2)
        fg.setColumnStretch(1, 1)
        lay.addWidget(files)

        # Generation parameters
        params = QGroupBox("Generation parameters")
        pg = QGridLayout(params)
        pg.addWidget(QLabel("Number of digits:"), 0, 0)
        self.num_digits = QSpinBox()
        self.num_digits.setRange(1, 6)
        self.num_digits.setValue(s["num_digits"])
        pg.addWidget(self.num_digits, 0, 1)

        pg.addWidget(QLabel("Divisor:"), 1, 0)
        self.divisor = QSpinBox()
        self.divisor.setRange(1, 9999)
        self.divisor.setValue(s["divisor"])
        pg.addWidget(self.divisor, 1, 1)

        self.use_sum = QCheckBox("Digit sum must be divisible by:")
        self.use_sum.setChecked(s["use_sum"])
        pg.addWidget(self.use_sum, 2, 0)
        self.sum_divisor = QSpinBox()
        self.sum_divisor.setRange(1, 99)
        self.sum_divisor.setValue(s["sum_divisor"])
        pg.addWidget(self.sum_divisor, 2, 1)
        self.use_sum.toggled.connect(self.sum_divisor.setEnabled)
        self.sum_divisor.setEnabled(s["use_sum"])

        pg.addWidget(QLabel("Order:"), 3, 0)
        self.order = QComboBox()
        self.order.addItems(["ascending", "descending"])
        self.order.setCurrentIndex(0 if s["order"] == "asc" else 1)
        pg.addWidget(self.order, 3, 1)
        pg.setColumnStretch(1, 1)
        lay.addWidget(params)

        # Saving
        opts = QGroupBox("Saving")
        og = QVBoxLayout(opts)
        self.skip_used = QCheckBox("Skip examples already in the registry")
        self.skip_used.setChecked(s["skip_used"])
        og.addWidget(self.skip_used)
        self.save_used = QCheckBox("Save generated examples to the registry")
        self.save_used.setChecked(s["save_used"])
        og.addWidget(self.save_used)
        self.save_tpl = QCheckBox("Save template to file")
        self.save_tpl.setChecked(s["save_tpl"])
        og.addWidget(self.save_tpl)
        lay.addWidget(opts)

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        bb.rejected.connect(self.accept)
        bb.accepted.connect(self.accept)
        lay.addWidget(bb)

    def _pick(self, line_edit):
        p, _ = QFileDialog.getSaveFileName(
            self, "Select file", line_edit.text() or "data.json",
            "JSON (*.json);;All files (*.*)")
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


# --- main window ------------------------------------------------------------

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        self.resize(720, 620)
        self.setMinimumSize(560, 480)
        self.records = []
        self.settings = SettingsDialog(self, default_settings())
        self.settings.finished.connect(self._refresh_subtitle)
        self._build()
        self._refresh_subtitle()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(10)

        # header + settings button in the corner
        top = QHBoxLayout()
        title = QLabel(APP_NAME)
        hf = QFont()
        hf.setPointSize(15)
        hf.setBold(True)
        title.setFont(hf)
        top.addWidget(title)
        top.addStretch(1)
        gear = QPushButton("⚙ Settings")
        gear.clicked.connect(self.open_settings)
        top.addWidget(gear)
        root.addLayout(top)

        self.subtitle = QLabel()
        self.subtitle.setStyleSheet("color: gray;")
        root.addWidget(self.subtitle)

        # count + generate + export
        row = QHBoxLayout()
        row.addWidget(QLabel("Number of examples:"))
        self.count = QSpinBox()
        self.count.setRange(1, 1_000_000)
        self.count.setValue(10)
        row.addWidget(self.count)
        row.addStretch(1)
        gen = QPushButton("Generate")
        gen.setMinimumHeight(34)
        gen.setStyleSheet("font-weight: bold;")
        gen.clicked.connect(self.generate)
        row.addWidget(gen)
        self.btn_txt = QPushButton("Save as TXT")
        self.btn_txt.setMinimumHeight(34)
        self.btn_txt.setEnabled(False)
        self.btn_txt.clicked.connect(self.save_txt)
        row.addWidget(self.btn_txt)
        root.addLayout(row)

        # output
        out_box = QGroupBox("Result")
        out_lay = QVBoxLayout(out_box)
        self.out = QPlainTextEdit()
        self.out.setReadOnly(True)
        self.out.setFont(QFont("Monospace", 10))
        out_lay.addWidget(self.out)
        root.addWidget(out_box, 1)

        self.status = QLabel("Ready.")
        root.addWidget(self.status)

    def open_settings(self):
        self.settings.show()
        self.settings.raise_()
        self.settings.activateWindow()

    def _refresh_subtitle(self):
        s = self.settings.get_values()
        cond = f", digit sum {DIV_SIGN}{s['sum_divisor']}" if s["use_sum"] else ""
        order = "ascending" if s["order"] == "asc" else "descending"
        self.subtitle.setText(
            f"{s['num_digits']}-digit numbers divisible by {s['divisor']}{cond} · {order}")

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
            QMessageBox.warning(self, "Warning",
                                "No new examples available for the given parameters.")
            return
        if count > len(pool):
            QMessageBox.warning(
                self, "Warning",
                f"Only {len(pool)} examples available. {len(pool)} will be generated.")
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
                QMessageBox.critical(self, "Error saving registry", str(e))
                return
            notes.append(f"registry +{len(new)}")

        if s["save_tpl"] and s["tpl_path"]:
            params = {k: s[k] for k in
                      ("num_digits", "divisor", "use_sum", "sum_divisor", "order")}
            try:
                save_template(s["tpl_path"], s["template"], params, len(records))
            except OSError as e:
                QMessageBox.critical(self, "Error saving template", str(e))
                return
            notes.append("template saved")

        self._show(records)
        self.records = records
        self.btn_txt.setEnabled(True)
        suffix = ("  (" + ", ".join(notes) + ")") if notes else ""
        self.status.setText(f"Generated {len(records)} examples.{suffix}")

    def _format_lines(self, records):
        w = max((len(str(r["n"])) for r in records), default=5)
        head = f"{'#':>4}  {'number':<{w}}  {'division':<16}  digit sum"
        lines = [head, "─" * max(len(head), 40)]
        for i, r in enumerate(records, 1):
            lines.append(
                f"{i:>4}  {r['n']:<{w}}  {r['eq_div']:<16}  {r['eq_sum']}")
        return lines

    def _show(self, records):
        self.out.setPlainText("\n".join(self._format_lines(records)))

    def save_txt(self):
        if not self.records:
            return
        p, _ = QFileDialog.getSaveFileName(
            self, "Save as TXT", "examples.txt",
            "Text (*.txt);;All files (*.*)")
        if not p:
            return
        s = self.settings.get_values()
        cond = f", digit sum {DIV_SIGN}{s['sum_divisor']}" if s["use_sum"] else ""
        order = "ascending" if s["order"] == "asc" else "descending"
        header = [
            f"{APP_NAME} {APP_VERSION}",
            f"Template: {s['template']}",
            f"Parameters: {s['num_digits']}-digit divisible by {s['divisor']}{cond} · {order}",
            f"Count: {len(self.records)}   "
            f"({datetime.now().isoformat(timespec='seconds')})",
            "",
        ]
        body = self._format_lines(self.records)
        try:
            with open(p, "w", encoding="utf-8") as f:
                f.write("\n".join(header + body) + "\n")
        except OSError as e:
            QMessageBox.critical(self, "Error saving", str(e))
            return
        self.status.setText(f"Saved to {os.path.basename(p)}")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    w = App()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
