#!/usr/bin/env python3
import io
PATH = r"C:\Users\diamo\Deskktoptop\Desktop\Codes\EndWord\index.html"
with io.open(PATH, "rb") as f:
    data = f.read()
# Find Screen shake and dump surrounding 200 bytes as repr
idx = data.find(b"Screen shake")
print("FOUND AT", idx)
print(repr(data[idx-30:idx+200]))