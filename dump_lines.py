#!/usr/bin/env python3
"""Dump exact bytes of lines 30-105 to find true indentation."""
import io

PATH = r"C:\Users\diamo\Deskktoptop\Desktop\Codes\EndWord\index.html"
with io.open(PATH, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

for i, ln in enumerate(lines[29:105], start=30):
    stripped_len = len(ln) - len(ln.lstrip(" "))
    print(f"L{i:3d} ind={stripped_len:2d} |{ln.rstrip()}|")