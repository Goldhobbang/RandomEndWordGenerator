#!/usr/bin/env python3
import io
PATH = r"C:\Users\diamo\Deskktoptop\Desktop\Codes\EndWord\index.html"
with io.open(PATH, "rb") as f:
    data = f.read().replace(b"\r\n", b"\n").decode("utf-8")
# Find containerEl occurrences
for i, line in enumerate(data.split("\n"), 1):
    if "containerEl" in line:
        print(f"L{i}: {line}")