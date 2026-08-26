"""
main.py — главный игровой цикл
Запуск: python main.py
"""
import pygame
import math
import random
import time

import game_state as gs
from audio import init_audio
from textures import init_textures
from sprites import init_sprites
from content import CREEPY_TEXTS, load_scores, save_scores, get_rank
from maze import generate_maze, braid_maze, find_path, bfs_dist, mutate_maze, build_minimap_base
from engine import light_at, render_sky, render_walls_and_floor, render_sprites, render_minimap


def can_stand(x, y):
    """Проверка коллизии игрока со стенами"""
    r = 0.2
    for ox in (-r, r):
        for oy in (-r, r):
            if gs.maze[int(y + oy)][int(x + ox)] == 1:
                return False
    return True


def update_minotaur(dt, now):
    """Обновление позиции минотавра"""
    if now - gs.level_start < 2.0:
        return
    if now - gs.m_retarget > 0.6:
        gs.m_retarget = now
        path = find_path(gs.maze, (int(gs.mx), int(gs.my)), (int(gs.px), int(gs.py)))
        gs.m_path = [(cx + 0.5, cy + 0.5) for cx, cy in path[1:]] if path else []
    if gs.m_path:
        tx, ty = gs.m_path[0]
        dx, dy = tx - gs.mx, ty - gs.my
        d = math.hypot(dx, dy)
        if d < 0.1:
            gs.m_path.pop(0)
        else:
            gs.mx += dx / d * gs.m_speed * dt
            gs.my += dy / d * gs.m_speed * dt

    cell = (int(gs.mx), int(gs.my))
    if cell != gs.m_last_cell:
        mutate_maze(gs, gs.m_last_cell[0], gs.m_last_cell[1], now)
        gs.m_last_cell = cell


def new_game(lvl):
    """Инициализация нового уровня"""
    gs.mw = 21 + (lvl - 1) * 4
    if gs.mw % 2 == 0:
        gs.mw += 1
    gs.mh = gs.mw

    gs.maze = generate_maze(gs.mw, gs.mh)
    braid_maze(gs.maze, gs.mw, gs.mh)

    gs.wtex = [[random.randrange(len(gs.TEXTURES)) for _ in range(gs.mw)] for _ in range(gs.mh)]

    free_cells = [(x, y) for y in range(1, gs.mh - 1) for x in range(1, gs.mw - 1) if gs.maze[y][x] == 0]
    p_cell = random.choice(free_cells)
    dist_map = bfs_dist(gs.maze, gs.mw, gs.mh, p_cell)
    far_gate = [c for c in free_cells if dist_map.get(c, 0) >= (gs.mw + gs.mh) // 3]
    far_mino = [c for c in free_cells if dist_map.get(c, 0) >= (gs.mw + gs.mh) // 2]
    if not far_gate:
        far_gate = free_cells
    if not far_mino:
        far_mino = far_gate
    g_cell = random.choice(far_gate)
    m_cell = random.choice(far_mino)

    gs.px, gs.py = p_cell[0] + 0.5, p_cell[1] + 0.5
    gs.goal = (g_cell[0] + 0.5, g_cell[1] + 0.5)
    gs.mx, gs.my = m_cell[0] + 0.5, m_cell[1] + 0.5
    gs.angle = random.uniform(0, 2 * math.pi)
    gs.m_speed = 1.6 + lvl * 0.25
    gs.stamina = gs.MAX_STAMINA  # Восстанавливаем стамину

    wall_cells = [(x, y) for y in range(1, gs.mh - 1) for x in range(1, gs.mw - 1) if gs.maze[y][x] == 1]

    # Факелы
    gs.torches = []
    tc = wall_cells[:]
    random.shuffle(tc)
    need_torch = min(40, max(10, (gs.mw * gs.mh) // 45))
    for (x, y) in tc:
        if len(gs.torches) >= need_torch:
            break
        for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if gs.maze[y + ddy][x + ddx] == 0:
                gs.torches.append((x + 0.5 + ddx * 0.55, y + 0.5 + ddy * 0.55, random.uniform(0, 6.28)))
                break

    # Картинки на стенах (пентаграммы, отпечатки, царапины, призраки)
    gs.pics = []
    pc = wall_cells[:]
    random.shuffle(pc)
    pic_kinds = [
        (gs.PENTAGRAM_SPRITE, 'pic_glow'),
        (gs.GHOSTFACE_SPRITE, 'pic_glow'),
        (gs.HANDPRINT_SPRITE, 'pic_lit'),
        (gs.SCRATCH_SPRITE, 'pic_lit')
    ]
    for cp in gs.CUSTOM_PICS:
        pic_kinds.append((cp, random.choice(('pic_lit', 'pic_glow'))))
    need_pic = random.randint(0, 9)
    for (x, y) in pc:
        if len(gs.pics) >= need_pic:
            break
        for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if gs.maze[y + ddy][x + ddx] == 0:
                surf, kind = random.choice(pic_kinds)
                gs.pics.append((x + 0.5 + ddx * 0.55, y + 0.5 + ddy * 0.55, surf, kind))
                break

    # Декоры на полу (черепа, кости, кровь, трава, лужи)
    gs.decors = []
    creepy_kinds = [
        (gs.SKULL_SPRITE, 0.30),
        (gs.BONES_SPRITE, 0.25),
        (gs.BLOOD_SPRITE, 0.22)
    ]
    floor_kinds = [
        (gs.GRASS_SPRITE, 0.35),
        (gs.GRASS_SPRITE, 0.28),
        (gs.PUDDLE_SPRITE, 0.55)
    ]
    fc = free_cells[:]
    random.shuffle(fc)
    need_creepy = min(60, max(8, (gs.mw * gs.mh) // 60))
    need_floor = min(80, max(10, (gs.mw * gs.mh) // 50))
    count_c = count_f = 0
    for (x, y) in fc:
        if count_c >= need_creepy and count_f >= need_floor:
            break
        if (x, y) == p_cell:
            continue
        if count_f < need_floor and random.random() < 0.6:
            surf, sc = random.choice(floor_kinds)
            ox, oy = random.uniform(-0.2, 0.2), random.uniform(-0.2, 0.2)
            kind = 'puddle' if surf is gs.PUDDLE_SPRITE else 'floor'
            gs.decors.append((x + 0.5 + ox, y + 0.5 + oy, surf, sc, kind))
            count_f += 1
        elif count_c < need_creepy:
            surf, sc = random.choice(creepy_kinds)
            ox = oy = 0.0
            for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if gs.maze[y + ddy][x + ddx] == 1:
                    ox, oy = ddx * 0.3, ddy * 0.3
                    break
            gs.decors.append((x + 0.5 + ox, y + 0.5 + oy, surf, sc, 'floor'))
            count_c += 1

    # Наблюдатели
    gs.watchers = []
    far_cells = [c for c in free_cells if dist_map.get(c, 0) > 6]
    random.shuffle(far_cells)
    for c in far_cells[:4]:
        gs.watchers.append((c[0] + 0.5, c[1] + 0.5))

    gs.m_path = []
    gs.m_retarget = 0.0
    gs.m_last_cell = (int(gs.mx), int(gs.my))
    gs.shake_until = 0.0
    build_minimap_base(gs)
    gs.level_start = time.time()
    now = time.time()
    gs.next_whisper = now + random.uniform(6, 15)
    gs.next_creep = now + random.uniform(12, 25)
    gs.next_gate_dark = now + random.uniform(20, 40)


def draw_text(msg, col, y, big=False):
    """Вывод текста по центру экрана"""
    f = gs.font_big if big else gs.font
    s = f.render(msg, True, col)
    gs.screen.blit(s, (gs.SW // 2 - s.get_width() // 2, y))


def main():
    """Главная функция игры"""
    pygame.init()
    gs.init_display()

    # Инициализация ассетов
    sounds = init_audio()
    gs.step_sound = sounds['step']
    gs.roar_sound = sounds['roar']
    gs.heart_sound = sounds['heart']
    gs.thud_sound = sounds['thud']
    gs.whisper_sound = sounds['whisper']
    gs.rumble_sound = sounds['rumble']

    (gs.TEXTURES, gs.TEX_ARRAYS, gs.FLOOR_ARR, gs.CEIL_ARR,
     gs.SKY, gs.sky_tmp, gs.CUSTOM_PICS) = init_textures(gs.TEX_DIR, gs.PIC_DIR)

    sprites = init_sprites()
    gs.MINO_SPRITE = sprites['mino']
    gs.EYES_SPRITE = sprites['eyes']
    gs.GATE_SPRITE = sprites['gate']
    gs.TORCH_SPRITE = sprites['torch']
    gs.SKULL_SPRITE = sprites['skull']
    gs.BONES_SPRITE = sprites['bones']
    gs.BLOOD_SPRITE = sprites['blood']
    gs.GRASS_SPRITE = sprites['grass']
    gs.PUDDLE_SPRITE = sprites['puddle']
    gs.WATCHER_SPRITE = sprites['watcher']
    gs.PENTAGRAM_SPRITE = sprites['pentagram']
    gs.HANDPRINT_SPRITE = sprites['handprint']
    gs.SCRATCH_SPRITE = sprites['scratch']
    gs.GHOSTFACE_SPRITE = sprites['ghostface']

    gs.scores = load_scores(gs.SCORES_FILE)

    held = set()
    new_game(gs.level)

    running = True
    while running:
        dt = gs.clock.tick(60) / 1000
        now = time.time()

        # ================= СОБЫТИЯ =================
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            if e.type == pygame.KEYDOWN:
                held.add(e.scancode)
                if e.scancode == gs.SCAN_ESC:
                    running = False

                if gs.state == 'name':
                    if e.key == pygame.K_BACKSPACE:
                        gs.player_name = gs.player_name[:-1]
                    elif e.key == pygame.K_RETURN:
                        if gs.player_name.strip():
                            gs.player_name = gs.player_name.strip()[:12]
                            gs.scores.setdefault(gs.player_name, {'best': 0, 'wins': 0, 'deaths': 0})
                            gs.state = 'menu'
                    elif len(gs.player_name) < 12 and len(e.unicode) == 1 and e.unicode.isprintable():
                        gs.player_name += e.unicode
                    continue

                if gs.state == 'menu':
                    gs.state = 'play'
                    gs.level_start = now
                    try:
                        pygame.event.set_grab(True)
                    except Exception:
                        pass
                    pygame.mouse.set_visible(False)
                    continue
                if e.scancode == gs.SCAN_R:
                    if gs.state == 'win':
                        gs.level += 1
                    new_game(gs.level)
                    gs.state = 'play'
            if e.type == pygame.KEYUP:
                held.discard(e.scancode)
            if e.type == pygame.MOUSEBUTTONDOWN and gs.state == 'menu':
                gs.state = 'play'
                gs.level_start = now
                pygame.mouse.set_visible(False)
            if e.type == pygame.MOUSEMOTION and gs.state == 'play':
                gs.angle += e.rel[0] * 0.0022

        # ================= ЛОГИКА ИГРЫ =================
        if gs.state == 'play':
            rot = 2.2 * dt
            if gs.SCAN_LEFT in held:
                gs.angle -= rot
            if gs.SCAN_RIGHT in held:
                gs.angle += rot

            # [НОВАЯ ФИЧА] Выносливость и динамический FOV
            sprint = gs.SCAN_SHIFT in held and gs.stamina > 5
            move = (4.4 if sprint else 3.0) * dt

            dx = math.cos(gs.angle)
            dy = math.sin(gs.angle)
            vx = vy = 0.0
            if gs.SCAN_W in held:
                vx += dx * move; vy += dy * move
            if gs.SCAN_S in held:
                vx -= dx * move; vy -= dy * move
            if gs.SCAN_A in held:
                vx += dy * move; vy -= dx * move
            if gs.SCAN_D in held:
                vx -= dy * move; vy += dx * move

            gs.moving = bool(vx or vy)
            if gs.moving:
                if can_stand(gs.px + vx, gs.py):
                    gs.px += vx
                if can_stand(gs.px, gs.py + vy):
                    gs.py += vy
                gs.bob_phase += dt * (11 if sprint else 8)
                if now - gs.last_step > (0.28 if sprint else 0.4):
                    gs.step_sound.play()
                    gs.last_step = now

                # Трата/восстановление выносливости
                if sprint:
                    gs.stamina -= 35 * dt
                else:
                    gs.stamina += 20 * dt
            else:
                gs.stamina += 20 * dt
            gs.stamina = max(0, min(gs.MAX_STAMINA, gs.stamina))

            # [НОВАЯ ФИЧА] Плавное изменение FOV при спринте
            target_plane = 0.85 if sprint else 0.66
            gs.current_plane_len += (target_plane - gs.current_plane_len) * dt * 5

            update_minotaur(dt, now)

            # Звуки приближения минотавра
            d_min = math.hypot(gs.px - gs.mx, gs.py - gs.my)
            if d_min < 10:
                if now - gs.last_heart > 0.35 + (d_min / 10) * 0.7:
                    gs.heart_sound.play()
                    gs.last_heart = now
            if d_min < 9:
                if now - gs.last_thud > 0.55:
                    gs.thud_sound.play()
                    gs.last_thud = now
            if d_min < 6 and now - gs.last_roar > 3:
                gs.roar_sound.play()
                gs.last_roar = now
            if d_min < 0.6:
                gs.state = 'dead'
                gs.roar_sound.play()
                rec = gs.scores.setdefault(gs.player_name, {'best': 0, 'wins': 0, 'deaths': 0})
                rec['deaths'] += 1
                rec['best'] = max(rec['best'], gs.level)
                save_scores(gs.scores, gs.SCORES_FILE)
            if math.hypot(gs.px - gs.goal[0], gs.py - gs.goal[1]) < 0.7:
                gs.state = 'win'
                gs.level_end = now  # Фиксируем время в момент победы!
                rec = gs.scores.setdefault(gs.player_name, {'best': 0, 'wins': 0, 'deaths': 0})
                rec['wins'] += 1
                rec['best'] = max(rec['best'], gs.level + 1)
                save_scores(gs.scores, gs.SCORES_FILE)

            # Случайные события
            if now > gs.next_whisper:
                ch = gs.whisper_sound.play()
                ch.set_volume(0.5)
                gs.next_whisper = now + random.uniform(10, 25)
            if now > gs.next_creep:
                gs.creepy_msg = random.choice(CREEPY_TEXTS)
                gs.creepy_until = now + 3
                ch = gs.roar_sound.play()
                ch.set_volume(0.25)
                gs.next_creep = now + random.uniform(18, 35)
            if now > gs.next_gate_dark:
                gs.gate_dark_until = now + 2
                gs.next_gate_dark = now + random.uniform(25, 45)

        # ================= РЕНДЕР =================
        gs.screen.fill((0, 0, 0))

        if gs.state == 'name':
            draw_text("КАК ТЕБЯ ЗОВУТ, ОХОТНИК?", (200, 200, 200), gs.SH // 2 - 90)
            draw_text(gs.player_name + ("_" if int(now * 2) % 2 == 0 else ""), (255, 255, 100), gs.SH // 2 - 30, big=True)
            draw_text("Enter - войти в лабиринт, ESC - выход", (150, 150, 150), gs.SH // 2 + 40)
            pygame.display.flip()
            continue

        if gs.state == 'menu':
            draw_text("ЛАБИРИНТ МИНОТАВРА", (200, 30, 30), 30, big=True)
            draw_text(f"Охотник: {gs.player_name}", (255, 255, 100), 90)
            board = sorted(gs.scores.items(), key=lambda kv: (-kv[1]['best'], -kv[1]['wins']))[:5]
            y = 130
            draw_text("РЕЙТИНГ ОХОТНИКОВ:", (0, 255, 255), y)
            y += 30
            if not board:
                draw_text("пока пусто - стань первым!", (150, 150, 150), y)
                y += 28
            for i, (n, r) in enumerate(board):
                draw_text(f"{i + 1}. {n} - уровень {r['best']} (побед: {r['wins']})", (200, 200, 200), y)
                y += 28
            draw_text("Найди ворота. Не попадись минотавру.", (200, 200, 200), gs.SH - 120)
            draw_text("WASD - движение, мышь - обзор, Shift - бег", (150, 150, 150), gs.SH - 90)
            draw_text("R - заново, ESC - выход", (150, 150, 150), gs.SH - 60)
            draw_text("Кликни или нажми любую клавишу", (255, 255, 100), gs.SH - 30)
            pygame.display.flip()
            continue

        # Эффекты камеры
        bob = int(math.sin(gs.bob_phase) * 3) if gs.moving else 0
        if now < gs.shake_until:
            bob += random.randint(-2, 2)
        horizon = gs.H // 2 + bob

        # Небо
        render_sky(gs, gs.surface, gs.angle, horizon)

        # Стены и пол
        zbuf = render_walls_and_floor(gs, gs.surface, gs.angle, horizon, now)

        # Спрайты
        render_sprites(gs, gs.surface, gs.angle, horizon, zbuf, now)

        # Виньетка
        gs.surface.blit(gs.vignette, (0, 0))

        # Масштабирование и вывод
        big = pygame.transform.scale(gs.surface, (gs.BW, gs.BH))
        gs.screen.blit(big, (gs.OX, gs.OY))

        # Миникарта
        render_minimap(gs, gs.screen, gs.angle)

        # ================= HUD =================
        if gs.state == 'play':
            draw_text(f"Время: {now - gs.level_start:.1f}  Уровень: {gs.level}  Shift-бег", (0, 255, 255), 6)
            d = math.hypot(gs.px - gs.mx, gs.py - gs.my)
            if d < 6:
                draw_text("ОН РЯДОМ! БЕГИ!", (255, 0, 0), 45, big=True)
            elif d < 10:
                draw_text("Минотавр близко...", (255, 80, 80), 45)
            if now < gs.creepy_until and int(now * 8) % 2 == 0:
                draw_text(gs.creepy_msg, (140, 0, 0), 90, big=True)

            # [НОВАЯ ФИЧА] Шкала выносливости
            bar_w, bar_h, bar_x, bar_y = 150, 12, 10, gs.SH - 30
            pygame.draw.rect(gs.screen, (30, 30, 30), (bar_x - 2, bar_y - 2, bar_w + 4, bar_h + 4))
            pygame.draw.rect(gs.screen, (50, 50, 50), (bar_x, bar_y, bar_w, bar_h))
            st_col = (0, 255, 0) if gs.stamina > 30 else (255, 100, 0)
            pygame.draw.rect(gs.screen, st_col, (bar_x, bar_y, int(bar_w * gs.stamina / gs.MAX_STAMINA), bar_h))

        elif gs.state == 'dead':
            # [НОВАЯ ФИЧА] JUMPSCARE при смерти
            js_size = int(max(gs.SW, gs.SH) * 1.2)
            js = pygame.transform.scale(gs.MINO_SPRITE, (js_size, js_size))
            js.fill((255, 30, 30), special_flags=pygame.BLEND_RGB_MULT)
            shake_x = random.randint(-20, 20)
            shake_y = random.randint(-20, 20)
            gs.screen.blit(js, (gs.SW // 2 - js_size // 2 + shake_x, gs.SH // 2 - js_size // 2 + shake_y))

            overlay = pygame.Surface((gs.SW, gs.SH), pygame.SRCALPHA)
            overlay.fill((150, 0, 0, 180))
            gs.screen.blit(overlay, (0, 0))

            draw_text("МИНОТАВР РАСТЕРЗАЛ ВАС!", (255, 255, 255), gs.SH // 2 - 80, big=True)
            rec = gs.scores.get(gs.player_name, {'best': gs.level})
            draw_text(f"Твой рекорд: уровень {rec['best']} - место #{get_rank(gs.player_name, gs.scores)}", (255, 255, 100), gs.SH // 2 - 20)
            draw_text("R - заново, ESC - выход", (255, 255, 255), gs.SH // 2 + 30)

        elif gs.state == 'win':
            final_time = gs.level_end - gs.level_start  # Время остановлено!
            draw_text(f"ТЫ ПРОШЁЛ СКВОЗЬ ВОРОТА! Время: {final_time:.1f}", (0, 255, 0), gs.SH // 2 - 80, big=True)
            rec = gs.scores.get(gs.player_name, {'best': gs.level + 1})
            draw_text(f"Рекорд: уровень {rec['best']} - место #{get_rank(gs.player_name, gs.scores)}", (255, 255, 100), gs.SH // 2 - 20)
            draw_text("R - следующий уровень", (255, 255, 255), gs.SH // 2 + 30)

        pygame.display.flip()

    pygame.quit()


if __name__ == '__main__':
    main()