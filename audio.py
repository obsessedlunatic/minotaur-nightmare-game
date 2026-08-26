"""
audio.py — все звуки генерируются математически, без внешних файлов
"""
import pygame
import math
import random
import array
import wave
import io


def wav_sound(gen, duration, rate=22050):
    """Генерирует WAV-файл в памяти из математической функции"""
    n = int(rate * duration)
    data = array.array('h')
    for i in range(n):
        v = gen(i / rate)
        v = max(-32767, min(32767, int(v)))
        data.append(v)
        data.append(v)  # стерео: дублируем канал
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(data.tobytes())
    buf.seek(0)
    return pygame.mixer.Sound(buf)


# ================= ГЕНЕРАТОРЫ ЗВУКОВ =================
def step_gen(t):
    """Шаги — короткий шумовой щелчок"""
    return random.uniform(-6000, 6000) * math.exp(-t * 30)


def roar_gen(t):
    """Рёв минотавра — низкий гул с шумом"""
    env = math.exp(-t * 2) * (1 + 0.5 * math.sin(2 * math.pi * 3 * t))
    noise = random.uniform(-1, 1)
    low = math.sin(2 * math.pi * 40 * t) + 0.5 * math.sin(2 * math.pi * 80 * t)
    return (noise * 0.7 + low) * 8000 * env


def heart_gen(t):
    """Сердцебиение — два удара"""
    b1 = math.sin(2 * math.pi * 60 * t) * math.exp(-t * 12) * 8000
    b2 = 0.0
    if t > 0.2:
        b2 = math.sin(2 * math.pi * 50 * (t - 0.2)) * math.exp(-(t - 0.2) * 15) * 4000
    return b1 + b2


def thud_gen(t):
    """Тяжёлый шаг минотавра"""
    return math.sin(2 * math.pi * 45 * t) * math.exp(-t * 10) * 9000


def whisper_gen(t):
    """Шёпот из тьмы"""
    env = (0.5 + 0.5 * math.sin(2 * math.pi * 6 * t)) * math.exp(-t * 2)
    return random.uniform(-1, 1) * 3000 * env


def rumble_gen(t):
    """Грохот мутации стен"""
    env = math.exp(-t * 3)
    noise = random.uniform(-1, 1)
    return noise * 5000 * env + math.sin(2 * math.pi * 30 * t) * 3000 * env


def init_audio():
    """Инициализация микшера и создание всех звуков"""
    pygame.mixer.init(22050, -16, 2)
    return {
        'step': wav_sound(step_gen, 0.12),
        'roar': wav_sound(roar_gen, 1.5),
        'heart': wav_sound(heart_gen, 0.8),
        'thud': wav_sound(thud_gen, 0.25),
        'whisper': wav_sound(whisper_gen, 1.2),
        'rumble': wav_sound(rumble_gen, 0.6),
    }