"""
sprites.py — все спрайты игры
"""
import pygame
import math
import random


def make_minotaur_sprite():
    """Минотавр"""
    s = pygame.Surface((64, 64))
    s.set_colorkey((0, 0, 0))
    s.fill((0, 0, 0))
    pygame.draw.rect(s, (70, 25, 18), (22, 26, 20, 34))
    pygame.draw.rect(s, (85, 30, 22), (24, 12, 16, 16))
    pygame.draw.polygon(s, (210, 190, 150), [(24, 14), (14, 2), (28, 10)])
    pygame.draw.polygon(s, (210, 190, 150), [(40, 14), (50, 2), (36, 10)])
    return s


def make_eyes_sprite():
    """Красные глаза минотавра"""
    s = pygame.Surface((64, 64))
    s.set_colorkey((0, 0, 0))
    s.fill((0, 0, 0))
    pygame.draw.circle(s, (255, 0, 0), (29, 19), 3)
    pygame.draw.circle(s, (255, 0, 0), (35, 19), 3)
    return s


def make_gate_sprite():
    """Врата выхода"""
    s = pygame.Surface((64, 64))
    s.set_colorkey((0, 0, 0))
    s.fill((0, 0, 0))
    pygame.draw.rect(s, (120, 120, 130), (8, 12, 9, 52))
    pygame.draw.rect(s, (120, 120, 130), (47, 12, 9, 52))
    pygame.draw.arc(s, (120, 120, 130), (8, 4, 48, 26), 0, math.pi, 7)
    for i in range(30):
        x = 17 + i
        g = int(140 + 90 * abs(math.sin(i * 0.45)))
        pygame.draw.line(s, (20, g, 70), (x, 17), (x, 63), 1)
    for _ in range(10):
        x = random.randint(18, 45)
        y = random.randint(20, 60)
        s.set_at((x, y), (180, 255, 190))
    return s


def make_torch_sprite():
    """Факел"""
    s = pygame.Surface((32, 32))
    s.set_colorkey((0, 0, 0))
    s.fill((0, 0, 0))
    pygame.draw.rect(s, (90, 60, 30), (14, 16, 4, 15))
    pygame.draw.circle(s, (255, 140, 20), (16, 13), 6)
    pygame.draw.circle(s, (255, 220, 80), (16, 11), 3)
    return s


def make_skull_sprite():
    """Череп"""
    s = pygame.Surface((32, 32))
    s.set_colorkey((0, 0, 0))
    s.fill((0, 0, 0))
    pygame.draw.circle(s, (210, 210, 200), (16, 19), 8)
    pygame.draw.rect(s, (210, 210, 200), (10, 21, 12, 10))
    pygame.draw.circle(s, (15, 15, 15), (13, 18), 2)
    pygame.draw.circle(s, (15, 15, 15), (19, 18), 2)
    return s


def make_bones_sprite():
    """Кости"""
    s = pygame.Surface((32, 32))
    s.set_colorkey((0, 0, 0))
    s.fill((0, 0, 0))
    pygame.draw.line(s, (190, 190, 180), (8, 29), (24, 21), 2)
    pygame.draw.line(s, (190, 190, 180), (10, 21), (22, 29), 2)
    pygame.draw.circle(s, (190, 190, 180), (8, 29), 2)
    pygame.draw.circle(s, (190, 190, 180), (24, 21), 2)
    pygame.draw.circle(s, (190, 190, 180), (10, 21), 2)
    pygame.draw.circle(s, (190, 190, 180), (22, 29), 2)
    return s


def make_blood_sprite():
    """Лужа крови"""
    s = pygame.Surface((32, 32))
    s.set_colorkey((0, 0, 0))
    s.fill((0, 0, 0))
    pygame.draw.ellipse(s, (110, 8, 8), (6, 23, 20, 8))
    pygame.draw.circle(s, (110, 8, 8), (24, 27), 3)
    pygame.draw.circle(s, (90, 5, 5), (12, 26), 2)
    return s


def make_grass_sprite():
    """Трава"""
    s = pygame.Surface((32, 32))
    s.set_colorkey((0, 0, 0))
    s.fill((0, 0, 0))
    for _ in range(12):
        x = random.randint(6, 26)
        hgt = random.randint(4, 9)
        col = random.choice([(30, 60, 25), (25, 50, 20), (35, 70, 30)])
        pygame.draw.line(s, col, (x, 31), (x + random.randint(-2, 2), 31 - hgt), 1)
    return s


def make_puddle_sprite():
    """Лужа"""
    s = pygame.Surface((32, 32))
    s.set_colorkey((0, 0, 0))
    s.fill((0, 0, 0))
    pygame.draw.ellipse(s, (35, 45, 60), (4, 21, 24, 10))
    pygame.draw.ellipse(s, (80, 100, 130), (8, 23, 12, 3))
    return s


def make_watcher_sprite():
    """Наблюдатель — глаза в темноте"""
    s = pygame.Surface((32, 32))
    s.set_colorkey((0, 0, 0))
    s.fill((0, 0, 0))
    pygame.draw.circle(s, (255, 230, 120), (12, 14), 2)
    pygame.draw.circle(s, (255, 230, 120), (20, 14), 2)
    return s


def make_pentagram():
    """Пентаграмма на стене"""
    s = pygame.Surface((64, 64))
    s.set_colorkey((0, 0, 0))
    s.fill((0, 0, 0))
    pygame.draw.circle(s, (160, 20, 20), (32, 32), 24, 2)
    pts = []
    for i in range(5):
        a = -math.pi / 2 + i * (4 * math.pi / 5)
        pts.append((int(32 + 22 * math.cos(a)), int(32 + 22 * math.sin(a))))
    pygame.draw.polygon(s, (160, 20, 20), pts, 2)
    return s


def make_handprint():
    """Кровавый отпечаток руки"""
    s = pygame.Surface((64, 64))
    s.set_colorkey((0, 0, 0))
    s.fill((0, 0, 0))
    pygame.draw.circle(s, (120, 10, 10), (32, 38), 8)
    for ang in (-0.6, -0.3, 0.0, 0.3, 0.6):
        fx = int(32 + math.sin(ang) * 15)
        fy = int(38 - math.cos(ang) * 15)
        pygame.draw.line(s, (120, 10, 10),
                         (int(32 + math.sin(ang) * 6), int(38 - math.cos(ang) * 6)),
                         (fx, fy), 3)
        pygame.draw.circle(s, (120, 10, 10), (fx, fy), 3)
    return s


def make_scratches():
    """Царапины на стене"""
    s = pygame.Surface((64, 64))
    s.set_colorkey((0, 0, 0))
    s.fill((0, 0, 0))
    for i in range(4):
        x = 14 + i * 10
        pygame.draw.line(s, (170, 170, 160), (x, 10), (x + 6, 54), 2)
    return s


def make_ghostface():
    """Призрачное лицо"""
    s = pygame.Surface((64, 64))
    s.set_colorkey((0, 0, 0))
    s.fill((0, 0, 0))
    pygame.draw.ellipse(s, (190, 190, 180), (18, 8, 28, 40))
    pygame.draw.ellipse(s, (10, 10, 10), (24, 20, 7, 10))
    pygame.draw.ellipse(s, (10, 10, 10), (35, 20, 7, 10))
    pygame.draw.ellipse(s, (10, 10, 10), (27, 36, 10, 14))
    return s


def init_sprites():
    """Инициализация всех спрайтов"""
    return {
        'mino': make_minotaur_sprite(),
        'eyes': make_eyes_sprite(),
        'gate': make_gate_sprite(),
        'torch': make_torch_sprite(),
        'skull': make_skull_sprite(),
        'bones': make_bones_sprite(),
        'blood': make_blood_sprite(),
        'grass': make_grass_sprite(),
        'puddle': make_puddle_sprite(),
        'watcher': make_watcher_sprite(),
        'pentagram': make_pentagram(),
        'handprint': make_handprint(),
        'scratch': make_scratches(),
        'ghostface': make_ghostface(),
    }