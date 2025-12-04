# CS 1.6 ESP CONSOLE - DEBUG MODE + NON-STEAM OFFSETS + SCAN
# Your window 159x27 = MINIMIZED MENU. MAXIMIZE + SPAWN!
# Tries ALL offsets. Prints RAW MEMORY. Exits after.

import pymem
import pymem.process
import time
import ctypes
from ctypes import wintypes

# ALL KNOWN OFFSETS
OFFSETS = {
    'steam_8684': {'local': 0x539984, 'entity': 0x546204},
    'nonsteam': {'local': 0x0379C4B0, 'entity': 0x0379D4B8},
    'steam_alt': {'local': 0x11F6F4, 'entity': 0x11F7A4}  # Common alt
}

user32 = ctypes.windll.user32

def get_window_rect(hwnd):
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return rect.left, rect.top, rect.right, rect.bottom

def main():
    print("CS 1.6 DEBUG ESP - SCAN ALL OFFSETS")
    try:
        pm = pymem.Pymem("hl.exe")
        print("Attached hl.exe")
        base = pm.process_base
        print(f"Module base: 0x{base:X}")
    except:
        print("NO hl.exe RUNNING.")
        return

    hwnd = None
    titles = [b"Counter-Strike", b"Counter-Strike 1.6", b"OpenGL Rendering"]
    for t in titles:
        hwnd = user32.FindWindowA(None, t)
        if hwnd:
            print(f"Found: {t.decode()}")
            break
    if not hwnd:
        print("NO CS WINDOW.")
        return

    l, t, r, b = get_window_rect(hwnd)
    w, h = r-l, b-t
    print(f"Window: {w}x{h}")
    if w < 300:
        print("MINIMIZED! MAXIMIZE + JOIN SERVER + SPAWN!")
        return

    # SCAN ALL OFFSETS
    print("\n--- SCANNING OFFSETS ---")
    working = None
    for name, offs in OFFSETS.items():
        try:
            local_ptr = pm.read_int(base + offs['local'])
            print(f"{name} local: 0x{local_ptr:X}")
            if local_ptr > 0x10000:
                hp = pm.read_int(local_ptr + 0x90)
                team = pm.read_int(local_ptr + 0x98)
                print(f"  HP:{hp} Team:{team}")
                if 1 <= hp <= 100 and team in (1,2,3):
                    working = (name, offs, local_ptr)
                    break
        except:
            print(f"{name} FAIL")

    if not working:
        print("\n--- RAW LOCAL SCAN ---")
        # Bruteforce common
        for off in [0x539984, 0x0379C4B0, 0x11F6F4, 0x546204-0xC280, 0x379C4B0]:
            try:
                ptr = pm.read_int(base + off)
                hp = pm.read_int(ptr + 0x90) if ptr else 0
                print(f"Off 0x{off:X}: ptr=0x{ptr:X} HP=0x{hp:X}({hp})")
            except:
                pass
        print("NO LOCAL FOUND. WRONG BUILD/OFFSETS.")
        return

    name, offs, local_ptr = working
    local_team = pm.read_int(local_ptr + 0x98)
    print(f"\n*** WORKING: {name} | YOU: 0x{local_ptr:X} Team:{local_team} ***")

    # QUICK ENEMY SCAN
    print("\n--- ENEMIES (first 5) ---")
    enemies = 0
    ent_base = base + offs['entity']
    for i in range(1, 6):
        try:
            ent_ptr = pm.read_int(ent_base + i * 0x380)
            if ent_ptr:
                hp = pm.read_int(ent_ptr + 0x90)
                team = pm.read_int(ent_ptr + 0x98)
                if hp > 1 and hp <= 100 and team != local_team:
                    print(f"Enemy {i}: 0x{ent_ptr:X} HP:{hp} Team:{team}")
                    enemies += 1
        except:
            pass

    print(f"\nFOUND {enemies} enemies. MAXIMIZE + SPAWN = FIXED.")
    print("Use these offsets in main script.")

if __name__ == "__main__":
    main()
    print("\nEXIT.")