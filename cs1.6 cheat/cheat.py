# CS 1.6 Steam ESP - CONSOLE ONLY (NO PYGAME - NO "NOT RESPONDING")
# Prints enemies to console. Run in background. FULLSCREEN WORKS.
# Offsets CONFIRMED 2025 Build 8684 (current Steam)<grok-card data-id="da3b73" data-type="citation_card"></grok-card><grok-card data-id="2a4375" data-type="citation_card"></grok-card>
# Press Ctrl+C to stop.

import pymem
import pymem.process
import time
import ctypes
from ctypes import wintypes

# OFFSETS (MPGH 8684 - STILL GOOD 2025)
DW_LOCAL_PLAYER     = 0x539984
DW_ENTITY_LIST      = 0x546204
OFFSET_HEALTH       = 0x90
OFFSET_TEAM         = 0x98      # 1=CT, 2=T
OFFSET_POSITION     = 0x34C     # vecOrigin x,y,z
MAX_PLAYERS         = 32
ENTITY_SIZES        = [0x380, 0x178, 0x350]  # Try multiple

user32 = ctypes.windll.user32

def get_window_rect(hwnd):
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return rect.left, rect.top, rect.right, rect.bottom

def main():
    print("CS 1.6 ESP CONSOLE - FULLSCREEN OK")
    try:
        pm = pymem.Pymem("hl.exe")
        print("Attached hl.exe")
    except:
        print("RUN CS 1.6 STEAM FIRST.")
        return

    hwnd = None
    titles = [b"Counter-Strike", b"Counter-Strike 1.6", b"OpenGL Rendering"]
    for t in titles:
        hwnd = user32.FindWindowA(None, t)
        if hwnd:
            print(f"Found: {t.decode()}")
            break
    if not hwnd:
        print("NO CS WINDOW. JOIN SERVER.")
        return

    left, top, right, bottom = get_window_rect(hwnd)
    w = right - left
    h = bottom - top
    print(f"Window: {w}x{h} (MAXIMIZE!)")

    # Find working entity size
    local_ptr = None
    local_team = 0
    best_size = 0
    print("Finding entity size... SPAWN IN-GAME.")
    for size in ENTITY_SIZES:
        try:
            local_ptr = pm.read_int(DW_LOCAL_PLAYER)
            if local_ptr:
                local_team = pm.read_int(local_ptr + OFFSET_TEAM)
                local_hp = pm.read_int(local_ptr + OFFSET_HEALTH)
                if 1 <= local_hp <= 100 and local_team in (1,2):
                    # Test entity read
                    test_ent = pm.read_int(DW_ENTITY_LIST + (1 * size))
                    if test_ent:
                        best_size = size
                        print(f"YOU SPAWNED! HP:{local_hp} Team:{'CT' if local_team==1 else 'T'} | Size:{hex(size)}")
                        break
        except:
            pass
        time.sleep(0.5)

    if not local_ptr or not best_size:
        print("NO SPAWN DETECTED. JOIN SERVER + SPAWN.")
        return

    print("ESP RUNNING... ENEMIES:")
    print("HP | 3D X,Y,Z | SCREEN X,Y")
    print("-"*40)

    while True:
        try:
            enemies = 0
            for i in range(1, MAX_PLAYERS + 1):
                try:
                    ent_ptr = pm.read_int(DW_ENTITY_LIST + (i * best_size))
                    if not ent_ptr or ent_ptr == local_ptr:
                        continue

                    hp = pm.read_int(ent_ptr + OFFSET_HEALTH)
                    if hp < 1 or hp > 100:
                        continue

                    team = pm.read_int(ent_ptr + OFFSET_TEAM)
                    if team == local_team or team == 0:
                        continue

                    px = pm.read_float(ent_ptr + OFFSET_POSITION)
                    py = pm.read_float(ent_ptr + OFFSET_POSITION + 4)
                    pz = pm.read_float(ent_ptr + OFFSET_POSITION + 8)

                    # Screen pos (rough)
                    z = max(pz, 0.1)
                    sx = int((px * 800 / z) + w / 2)
                    sy = int((-py * 600 / z) + h / 2)

                    print(f"{hp:3d} | {px:6.0f},{py:6.0f},{pz:6.0f} | {sx:4d},{sy:4d}")
                    enemies += 1

                except:
                    continue

            if enemies == 0:
                print("No enemies...")

            time.sleep(0.2)  # Slow print

        except KeyboardInterrupt:
            print("\nStopped.")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()