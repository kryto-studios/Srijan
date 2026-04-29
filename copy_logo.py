import shutil
import os

src = r"C:\Users\gamer\.gemini\antigravity\brain\a3b0213a-12ec-454c-8862-f5db91c4d08c\.tempmediaStorage\media_a3b0213a-12ec-454c-8862-f5db91c4d08c_1777233824575.png"
dst = r"assets\logo.png"

try:
    os.makedirs("assets", exist_ok=True)
    shutil.copy(src, dst)
    print("Logo copied successfully!")
except Exception as e:
    print(f"Error: {e}")
