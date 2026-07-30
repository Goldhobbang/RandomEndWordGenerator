#!/usr/bin/env python3
"""Dump lines around the JS shake block."""
import io

PATH = r"C:\Users\diamo\Deskktoptop\Desktop\Codes\EndWord\index.html"
with io.open(PATH, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

# Find "Screen shake"
for i, ln in enumerate(lines):
    if "Screen shake" in ln:
        for j in range(max(0, i-2), min(len(lines), i+25)):
            print(f"L{j+1:4d} |{lines[j].rstrip()}|")
        break