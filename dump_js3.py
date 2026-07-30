#!/usr/bin/env python3
import io
PATH = r"C:\Users\diamo\Deskktoptop\Desktop\Codes\EndWord\index.html"
with io.open(PATH, "rb") as f:
    data = f.read().replace(b"\r\n", b"\n").decode("utf-8")
for i, line in enumerate(data.split("\n"), 1):
    if "Screen shake" in line or "setShakeLevel" in line or "clearShake" in line:
        print(f"L{i}: {line}")