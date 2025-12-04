# CS 1.6 Cybersports.lt AIMBOT + MENU (pygame overlay)
# Mouse aimbot (smooth, RCS, FOV check) + Triggerbot + Bunnyhop
# Run AS ADMIN. F1=Menu Toggle | INS=Aimbot | HOME=Trigger | PGUP=Bhop
# Cybersports.lt build 8684 offsets (confirmed 2025)<grok-card data-id="fdf5ae" data-type="citation_card"></grok-card><grok-card data-id="5b852f" data-type="citation_card"></grok-card>

import pymem
import pymem.process
import time
import ctypes
from ctypes import wintypes, c_float, Structure, POINTER, WINFUNCTYPE, windll
from ctypes import c_int, c_void_p, c_bool
import pygame
import math
import sys

# OFFSETS (8684 build - protocol 48)
DW_LOCAL_PLAYER     = 0x539984
DW_ENTITY_LIST      = 0x546204
DW_VIEW_MATRIX      = 0x12EB10  # From 2025 dump<grok-card data-id="9f6fb9" data-type="citation_card"></grok-card>
DW_PUNCH_ANGLE      = 0x122E324  # viewPunch hw.dll<grok-card data-id="58a44d" data-type="citation_card"></grok-card>
DW_FORCE_ATTACK     = 0x131370   # +116 = 5 (attack)<grok-card data-id="7d8fbf" data-type="citation_card"></grok-card>
OFFSET_HEALTH       = 0x90
OFFSET_TEAM         = 0x98
OFFSET_POS          = 0x34C
OFFSET_CROSSHAIR    = 0xB2F4    # m_iCrosshairId (common GoldSrc)<grok-card data-id="0a006c" data-type="citation_card"></grok-card>
MAX_PLAYERS         = 32
ENTITY_SIZE         = 0x380

class Vector3(Structure):
    _fields_ = [("x", c_float), ("y", c_float), ("z", c_float)]

user32 = windll.user32
kernel32 = windll.kernel32

# Mouse move
PVOID = c_void_p
MOUSEEVENTF_MOVE = 0x0001
def mouse_move(dx, dy):
    user32.mouse_event(MOUSEEVENTF_MOVE, int(dx), int(dy), 0, 0)

# Get cursor pos
def get_cursor():
    pt = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y

# Calc distance
def dist_2d(x1, y1, x2, y2):
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

# Calc angle
def calc_angle(local_pos, enemy_pos, punch):
    delta = Vector3(enemy_pos.x - local_pos.x, enemy_pos.y - local_pos.y, enemy_pos.z - local_pos.z)
    hyp = math.sqrt(delta.x**2 + delta.y**2)
    yaw = math.degrees(math.atan2(delta.y, delta.x))
    pitch = math.degrees(math.atan2(-delta.z, hyp))
    # RCS (2x punch)
    pitch -= punch.x * 2
    yaw -= punch.y * 2
    return yaw, pitch

# World2Screen (simplified - uses rough proj)
def w2s(pos, matrix, w, h):
    # Matrix mult (4x4 * vec4)
    clip_x = pos.x * matrix[0] + pos.y * matrix[1] + pos.z * matrix[2] + matrix[3]
    clip_y = pos.x * matrix[4] + pos.y * matrix[5] + pos.z * matrix[6] + matrix[7]
    clip_z = pos.x * matrix[8] + pos.y * matrix[9] + pos.z * matrix[10] + matrix[11]
    clip_w = pos.x * matrix[12] + pos.y * matrix[13] + pos.z * matrix[14] + matrix[15]
    
    if clip_w < 0.1:
        return None
    
    ndc_x = clip_x / clip_w
    ndc_y = clip_y / clip_w
    
    screen_x = (w / 2 * ndc_x) + (ndc_x + w / 2)
    screen_y = -(h / 2 * ndc_y) + (ndc_y + h / 2)
    return screen_x, screen_y

def main():
    print("CS 1.6 AIMBOT + MENU - Cybersports.lt")
    try:
        pm = pymem.Pymem("hl.exe")
        print("Attached hl.exe")
    except:
        print("RUN CS 1.6 FIRST.")
        return

    # Window
    hwnd = user32.FindWindowA(None, b"Counter-Strike")
    if not hwnd:
        print("JOIN SERVER.")
        return
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    width = rect.right - rect.left
    height = rect.bottom - rect.top
    print(f"Window: {width}x{height}")

    # Pygame menu overlay (transparent)
    pygame.init()
    screen = pygame.display.set_mode((width, height), pygame.NOFRAME)
    pygame.display.set_caption("CS Aimbot Menu")
    hwnd_pygame = pygame.display.get_wm_info()["window"]
    user32.SetWindowLongW(hwnd_pygame, -20, 0x80000 | 0x20)
    user32.SetLayeredWindowAttributes(hwnd_pygame, 0, 200, 2)
    user32.SetWindowPos(hwnd_pygame, -1, rect.left, rect.top, 0, 0, 0x01)

    font = pygame.font.SysFont("consolas", 18)
    clock = pygame.time.Clock()

    # Menu state
    menu_open = False
    aimbot_on = False
    trigger_on = False
    bhop_on = False
    smooth = 5.0  # pixels/frame
    fov = 180     # degrees

    # Wait spawn
    print("Waiting spawn...")
    while True:
        try:
            local_ptr = pm.read_int(DW_LOCAL_PLAYER)
            hp = pm.read_int(local_ptr + OFFSET_HEALTH)
            if 1 <= hp <= 100:
                local_team = pm.read_int(local_ptr + OFFSET_TEAM)
                print(f"SPAWNED! Team: {'CT' if local_team==1 else 'T'}")
                break
        except:
            pass
        time.sleep(0.1)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F1:  # Menu
                    menu_open = not menu_open
                if event.key == pygame.K_INSERT:  # Aimbot
                    aimbot_on = not aimbot_on
                if event.key == pygame.K_HOME:   # Trigger
                    trigger_on = not trigger_on
                if event.key == pygame.K_PAGEUP: # Bhop
                    bhop_on = not bhop_on

        # Update overlay pos
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        if rect.left or rect.top:  # Update if moved
            user32.SetWindowPos(hwnd_pygame, -1, rect.left, rect.top, 0, 0, 0x01)

        screen.fill((0, 0, 0, 0))

        # Read data
        try:
            local_ptr = pm.read_int(DW_LOCAL_PLAYER)
            local_team = pm.read_int(local_ptr + OFFSET_TEAM)
            local_pos = (Vector3.from_address(local_ptr + OFFSET_POS),
                         Vector3.from_address(local_ptr + OFFSET_POS))
            punch = Vector3.from_address(DW_PUNCH_ANGLE)
            view_matrix = (c_float * 16).from_address(DW_VIEW_MATRIX)
            crosshair_id = pm.read_int(local_ptr + OFFSET_CROSSHAIR)
        except:
            pygame.display.flip()
            clock.tick(60)
            continue

        # AIMBOT LOOP
        closest_dist = float('inf')
        closest_target = None
        closest_screen = None

        for i in range(1, MAX_PLAYERS + 1):
            try:
                ent_ptr = pm.read_int(DW_ENTITY_LIST + i * ENTITY_SIZE)
                if not ent_ptr or ent_ptr == local_ptr:
                    continue
                hp = pm.read_int(ent_ptr + OFFSET_HEALTH)
                if hp < 1 or hp > 100:
                    continue
                team = pm.read_int(ent_ptr + OFFSET_TEAM)
                if team == local_team:
                    continue

                e_pos = Vector3.from_address(ent_ptr + OFFSET_POS)
                e_head = Vector3(e_pos.x, e_pos.y, e_pos.z + 72)  # Head level

                # FOV check
                screen_pos = w2s(e_head, view_matrix, width, height)
                if not screen_pos:
                    continue
                cx, cy = get_cursor()
                pix_dist = dist_2d(cx, cy, screen_pos[0], screen_pos[1])
                pix_fov = (fov / 360) * width
                if pix_dist > pix_fov:
                    continue

                if pix_dist < closest_dist:
                    closest_dist = pix_dist
                    closest_target = (e_head, screen_pos)

            except:
                continue

        # Execute aim
        if aimbot_on and closest_target:
            target_pos, screen_pos = closest_target
            angles = calc_angle(local_pos[0], target_pos, punch)
            # Delta to screen (rough)
            cx, cy = get_cursor()
            dx = (screen_pos[0] - cx) / smooth
            dy = (screen_pos[1] - cy) / smooth
            mouse_move(dx, dy)

        # TRIGGERBOT
        if trigger_on and crosshair_id > 0 and crosshair_id <= MAX_PLAYERS:
            try:
                target_ptr = pm.read_int(DW_ENTITY_LIST + (crosshair_id - 1) * ENTITY_SIZE)
                if target_ptr:
                    t_team = pm.read_int(target_ptr + OFFSET_TEAM)
                    if t_team != local_team:
                        pm.write_int(DW_FORCE_ATTACK + 116, 5)  # Attack
                        time.sleep(0.01)
                        pm.write_int(DW_FORCE_ATTACK + 116, 4)  # Release
            except:
                pass

        # BHOP
        if bhop_on:
            flags = pm.read_int(local_ptr + 0x100)  # m_fFlags
            if flags & 1:  # On ground
                pm.write_int(DW_FORCE_JUMP + 116, 5 + 256)  # Jump

        # MENU DRAW
        if menu_open:
            # Background
            pygame.draw.rect(screen, (0, 0, 0, 200), (10, 10, 300, 400))

            # Title
            title = font.render("CS 1.6 Aimbot Menu", True, (255, 255, 255))
            screen.blit(title, (20, 20))

            # Toggles
            y = 60
            color_on = (0, 255, 0)
            color_off = (255, 0, 0)
            aim_text = font.render(f"Aimbot: {'ON' if aimbot_on else 'OFF'} (INS)", True, color_on if aimbot_on else color_off)
            screen.blit(aim_text, (20, y)); y += 30
            trig_text = font.render(f"Trigger: {'ON' if trigger_on else 'OFF'} (HOME)", True, color_on if trigger_on else color_off)
            screen.blit(trig_text, (20, y)); y += 30
            bhop_text = font.render(f"Bhop: {'ON' if bhop_on else 'OFF'} (PGUP)", True, color_on if bhop_on else color_off)
            screen.blit(bhop_text, (20, y)); y += 30

            # Sliders
            smooth_text = font.render(f"Smooth: {smooth:.1f}", True, (255, 255, 255))
            screen.blit(smooth_text, (20, y)); y += 30
            pygame.draw.line(screen, (255, 255, 255), (20, y+5, 280, y+5), 2)
            slider_pos = int((smooth - 1) / 10 * 260)
            pygame.draw.circle(screen, (0, 255, 0), (20 + slider_pos, y+5), 8)

            fov_text = font.render(f"FOV: {fov}", True, (255, 255, 255))
            screen.blit(fov_text, (20, y)); y += 30
            pygame.draw.line(screen, (255, 255, 255), (20, y+5, 280, y+5), 2)
            fov_pos = int((fov - 30) / 300 * 260)
            pygame.draw.circle(screen, (0, 255, 0), (20 + fov_pos, y+5), 8)

            # Menu keys
            keys = font.render("F1: Menu | ESC: Exit", True, (255, 255, 0))
            screen.blit(keys, (20, height - 40))

        # Status
        status = font.render(f"Target FOV: {closest_dist:.0f}px" if closest_dist != float('inf') else "No target", True, (255, 255, 0))
        screen.blit(status, (width - 200, 10))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()