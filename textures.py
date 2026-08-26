"""
textures.py — генерация текстур стен, пола, потолка и загрузка пользовательских
"""
import pygame
import random
import os
import numpy as np


def make_brick_texture():
    """Кирпичная стена"""
    t = pygame.Surface((64, 64))
    t.fill((70, 70, 75))
    bw, bh = 16, 8
    for row in range(0, 64, bh):
        offset = 8 if (row // bh) % 2 else 0
        for col in range(-1, 5):
            x = col * bw + offset
            shade = random.randint(95, 130)
            pygame.draw.rect(t, (shade, shade, shade + 5), (x + 1, row + 1, bw - 2, bh - 2))
    for _ in range(150):
        x, y = random.randint(0, 63), random.randint(0, 63)
        d = random.randint(-25, 25)
        t.set_at((x, y), (110 + d, 110 + d, 112 + d))
    return t


def make_mossy_texture():
    """Замшелый кирпич"""
    t = make_brick_texture()
    for _ in range(60):
        x, y = random.randint(0, 63), random.randint(20, 63)
        g = random.randint(60, 110)
        t.set_at((x, y), (30, g, 30))
    for _ in range(20):
        x, y = random.randint(0, 62), random.randint(30, 62)
        pygame.draw.rect(t, (35, 90, 35), (x, y, 2, 2))
    return t


def make_stone_texture():
    """Каменные блоки"""
    t = pygame.Surface((64, 64))
    t.fill((60, 60, 68))
    bw, bh = 32, 16
    for row in range(0, 64, bh):
        offset = 16 if (row // bh) % 2 else 0
        for col in range(-1, 3):
            x = col * bw + offset
            shade = random.randint(80, 110)
            pygame.draw.rect(t, (shade, shade, shade + 8), (x + 2, row + 2, bw - 4, bh - 4))
    for _ in range(100):
        x, y = random.randint(0, 63), random.randint(0, 63)
        d = random.randint(-20, 20)
        t.set_at((x, y), (95 + d, 95 + d, 100 + d))
    return t


def make_blood_texture():
    """Кирпич с кровью"""
    t = make_brick_texture()
    for _ in range(7):
        x = random.randint(4, 60)
        y0 = random.randint(0, 20)
        length = random.randint(15, 44)
        for yy in range(y0, min(63, y0 + length)):
            w = 2 if yy < y0 + 4 else 1
            pygame.draw.rect(t, (110, 8, 8), (x, yy, w, 1))
    pygame.draw.ellipse(t, (120, 10, 10), (20, 6, 18, 10))
    return t


def make_floor_tex():
    """[НОВАЯ ФИЧА] Каменный пол с трещинами"""
    t = pygame.Surface((64, 64))
    t.fill((45, 40, 35))
    for _ in range(300):
        x, y = random.randint(0, 63), random.randint(0, 63)
        d = random.randint(-20, 20)
        t.set_at((x, y), (45 + d, 40 + d, 35 + d))
    for _ in range(5):
        x1, y1 = random.randint(0, 63), random.randint(0, 63)
        x2, y2 = x1 + random.randint(-20, 20), y1 + random.randint(-20, 20)
        pygame.draw.line(t, (25, 20, 15), (x1, y1), (x2, y2), 1)
    return t


def make_ceil_tex():
    """[НОВАЯ ФИЧА] Тёмный потолок"""
    t = pygame.Surface((64, 64))
    t.fill((25, 25, 30))
    for _ in range(200):
        x, y = random.randint(0, 63), random.randint(0, 63)
        d = random.randint(-10, 10)
        t.set_at((x, y), (25 + d, 25 + d, 30 + d))
    return t


def make_sky():
    """Небо с луной, кратерами и облаками"""
    w, h = 1024, 128
    s = pygame.Surface((w, h))
    # Градиент
    for y in range(h):
        t = y / h
        pygame.draw.line(s, (int(4 + 8 * t), int(4 + 8 * t), int(12 + 18 * t)), (0, y), (w, y))
    # Звёзды
    for _ in range(220):
        x = random.randint(0, w - 1)
        y = random.randint(0, int(h * 0.8))
        c = random.randint(120, 255)
        s.set_at((x, y), (c, c, min(255, c + 20)))
    # Луна с кратерами
    moon_x = random.randint(200, 800)
    pygame.draw.circle(s, (220, 220, 200), (moon_x, 34), 16)
    pygame.draw.circle(s, (180, 180, 165), (moon_x - 5, 30), 4)
    pygame.draw.circle(s, (180, 180, 165), (moon_x + 6, 40), 3)
    for rr in range(18, 30, 3):
        pygame.draw.circle(s, (50, 50, 45), (moon_x, 34), rr, 1)
    # Облака
    for _ in range(14):
        cx = random.randint(0, w)
        cy = random.randint(10, 70)
        for _ in range(6):
            ox = random.randint(-40, 40)
            oy = random.randint(-8, 8)
            rw = random.randint(20, 60)
            rh = random.randint(6, 14)
            col = random.choice([(18, 18, 28), (24, 24, 34), (14, 14, 22)])
            pygame.draw.ellipse(s, col, (cx + ox - rw // 2, cy + oy - rh // 2, rw, rh))
    return s


def load_custom_images(folder):
    """Загрузка пользовательских текстур из папки"""
    imgs = []
    if os.path.isdir(folder):
        for name in sorted(os.listdir(folder)):
            if name.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                try:
                    s = pygame.image.load(os.path.join(folder, name)).convert_alpha()
                    imgs.append(pygame.transform.scale(s, (64, 64)))
                    print('Загружено:', name)
                except Exception as e:
                    print('Не удалось загрузить', name, ':', e)
    return imgs


def init_textures(tex_dir, pic_dir):
    """
    Инициализация всех текстур.
    Возвращает: (TEXTURES, TEX_ARRAYS, FLOOR_ARR, CEIL_ARR, SKY, sky_tmp, CUSTOM_PICS)
    """
    textures = [
        make_brick_texture(),
        make_mossy_texture(),
        make_stone_texture(),
        make_blood_texture()
    ]

    custom_tex = load_custom_images(tex_dir)
    custom_pics = load_custom_images(pic_dir)
    textures += custom_tex

    # [ОПТИМИЗАЦИЯ] Конвертируем в массивы numpy
    textures = [t.convert() for t in textures]
    tex_arrays = [pygame.surfarray.array3d(t) for t in textures]

    floor_tex = make_floor_tex().convert()
    ceil_tex = make_ceil_tex().convert()
    floor_arr = pygame.surfarray.array3d(floor_tex)
    ceil_arr = pygame.surfarray.array3d(ceil_tex)

    sky = make_sky()
    sky_tmp = pygame.Surface((1024 // 5, 128))

    return textures, tex_arrays, floor_arr, ceil_arr, sky, sky_tmp, custom_pics