"""
game_state.py — все глобальные переменные и константы игры
"""
import pygame
import time
import random
import math
import os
import json

# ================= КОНСТАНТЫ =================
W, H = 400, 250              # внутреннее разрешение рендера
TORCH_R = 6.0                # радиус света факела
MM = 112                     # размер миникарты
MM_CS = 4                    # размер клетки на миникарте
MAX_STAMINA = 100.0          # [НОВАЯ ФИЧА] максимальная выносливость

# Сканд-коды клавиш
SCAN_W, SCAN_A, SCAN_S, SCAN_D = 26, 4, 22, 7
SCAN_R, SCAN_ESC = 21, 41
SCAN_LEFT, SCAN_RIGHT = 80, 79
SCAN_SHIFT = 225

# ================= СОСТОЯНИЕ ИГРЫ =================
level = 1
state = 'name'
player_name = ""
scores = {}

# Лабиринт
maze = None
mw = mh = 0
wtex = None
goal = (0, 0)

# Игрок
px = py = angle = 0.0
bob_phase = 0.0
moving = False
stamina = MAX_STAMINA
current_plane_len = 0.66

# Минотавр
mx = my = 0.0
m_speed = 2.0
m_path = []
m_retarget = 0.0
m_last_cell = (0, 0)

# Объекты мира
torches = []
decors = []
watchers = []
pics = []
mm_base = None

# Эффекты
shake_until = 0.0
next_whisper = 0.0
next_creep = 0.0
creepy_msg = ""
creepy_until = 0.0
gate_dark_until = 0.0
next_gate_dark = 0.0
level_start = 0.0
level_end = 0.0

# Тайминги звуков
last_step = last_roar = last_heart = last_thud = 0.0

# Отображение
SW, SH = 1280, 720
BW, BH = 400, 250
OX, OY = 0, 0
surface = None
screen = None
clock = None
font = None
font_big = None
vignette = None

# Ассеты (заполняются в других модулях)
TEXTURES = []
TEX_ARRAYS = []
FLOOR_ARR = None
CEIL_ARR = None
SKY = None
sky_tmp = None

# Спрайты
MINO_SPRITE = None
EYES_SPRITE = None
GATE_SPRITE = None
TORCH_SPRITE = None
SKULL_SPRITE = None
BONES_SPRITE = None
BLOOD_SPRITE = None
GRASS_SPRITE = None
PUDDLE_SPRITE = None
WATCHER_SPRITE = None
PENTAGRAM_SPRITE = None
HANDPRINT_SPRITE = None
SCRATCH_SPRITE = None
GHOSTFACE_SPRITE = None

# Звуки
step_sound = None
roar_sound = None
heart_sound = None
thud_sound = None
whisper_sound = None
rumble_sound = None

# Пути
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEX_DIR = os.path.join(BASE_DIR, 'assets', 'textures')
PIC_DIR = os.path.join(BASE_DIR, 'assets', 'pics')
SCORES_FILE = os.path.join(BASE_DIR, 'leaderboard.json')


def init_display():
    """Инициализация окна и поверхностей"""
    global SW, SH, BW, BH, OX, OY, surface, screen, clock, font, font_big, vignette

    try:
        disp_info = pygame.display.Info()
        SW, SH = disp_info.current_w, disp_info.current_h
        if SW < 320 or SH < 240:
            raise ValueError
        screen = pygame.display.set_mode((SW, SH), pygame.FULLSCREEN)
    except Exception:
        SW, SH = 1280, 720
        screen = pygame.display.set_mode((SW, SH))

    pygame.display.set_caption("Лабиринт Минотавра: Ужас Бесконечности")
    pygame.mouse.set_visible(False)

    scale_f = min(SW / W, SH / H)
    BW, BH = SW, SH
    OX, OY = 0, 0
    surface = pygame.Surface((W, H))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont('dejavusans', 22)
    font_big = pygame.font.SysFont('dejavusans', 40)

    # Виньетка
    vignette = pygame.Surface((W, H), pygame.SRCALPHA)
    R = max(W, H) // 2
    for r in range(R, 0, -4):
        a = int(130 * (r / R) ** 2)
        pygame.draw.circle(vignette, (0, 0, 0, a), (W // 2, H // 2), r)