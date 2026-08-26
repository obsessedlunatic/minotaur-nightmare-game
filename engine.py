"""
engine.py — рендеринг: рейкастинг, текстурированный пол, спрайты, миникарта
"""
import pygame
import math
import numpy as np


def light_at(gs, x, y, now):
    """Расчёт освещения в точке"""
    b = 0.10
    for tx, ty, ph in gs.torches:
        dx = x - tx
        dy = y - ty
        d2 = dx * dx + dy * dy
        if d2 < gs.TORCH_R * gs.TORCH_R:
            d = math.sqrt(d2)
            b += (1 - d / gs.TORCH_R) * (0.9 + 0.1 * math.sin(now * 12 + ph))
    return min(1.0, b)


def render_sky(gs, surface, angle, horizon):
    """Рендеринг неба (скайбокс)"""
    win = 1024 // 5
    off = int(((angle % (2 * math.pi)) / (2 * math.pi)) * 1024) % 1024
    if off + win <= 1024:
        gs.sky_tmp.blit(gs.SKY, (0, 0), (off, 0, win, 128))
    else:
        first = 1024 - off
        gs.sky_tmp.blit(gs.SKY, (0, 0), (off, 0, first, 128))
        gs.sky_tmp.blit(gs.SKY, (first, 0), (0, 0, win - first, 128))
    sky_scaled = pygame.transform.scale(gs.sky_tmp, (gs.W, max(1, horizon)))
    surface.blit(sky_scaled, (0, 0))


def render_walls_and_floor(gs, surface, angle, horizon, now):
    """
    [ОПТИМИЗАЦИЯ] Рендеринг стен и текстурированного пола через numpy
    Возвращает zbuf для спрайтов
    """
    W, H = gs.W, gs.H
    px, py = gs.px, gs.py
    maze = gs.maze
    wtex = gs.wtex
    TEX_ARRAYS = gs.TEX_ARRAYS
    FLOOR_ARR = gs.FLOOR_ARR
    CEIL_ARR = gs.CEIL_ARR
    plane_len = gs.current_plane_len

    # Блокируем surface для прямой записи через numpy
    surf_array = pygame.surfarray.pixels3d(surface)

    dirX = math.cos(angle)
    dirY = math.sin(angle)
    planeX = -dirY * plane_len
    planeY = dirX * plane_len

    # ===== ТЕКСТУРИРОВАННЫЙ ПОЛ И ПОТОЛОК =====
    rayDirX0 = dirX - planeX
    rayDirY0 = dirY - planeY
    rayDirX1 = dirX + planeX
    rayDirY1 = dirY + planeY
    posZ = 0.5 * H
    x_coords = np.arange(W)

    # Пол (ниже горизонта)
    for y in range(horizon + 1, H):
        p = y - horizon
        if p == 0:
            continue
        rowDistance = posZ / p
        floorStepX = rowDistance * (rayDirX1 - rayDirX0) / W
        floorStepY = rowDistance * (rayDirY1 - rayDirY0) / W
        floorX = px + rowDistance * rayDirX0
        floorY = py + rowDistance * rayDirY0
        fx = floorX + floorStepX * x_coords
        fy = floorY + floorStepY * x_coords
        tx = (64 * (fx - fx.astype(int))).astype(int) & 63
        ty = (64 * (fy - fy.astype(int))).astype(int) & 63
        pixels = FLOOR_ARR[tx, ty]
        fog = np.clip(1.0 / (1.0 + rowDistance * 0.15), 0.1, 1.0)
        surf_array[:, y] = (pixels * fog).astype(np.uint8)

    # Потолок (выше горизонта) — рисуем только если нет неба
    # В данной версии потолок заменяет небо, поэтому пропускаем

    # ===== СТЕНЫ (РЕЙКАСТИНГ) =====
    zbuf = [0.0] * W
    for x in range(W):
        cam = 2 * x / W - 1
        rdx = dirX + planeX * cam
        rdy = dirY + planeY * cam
        map_x, map_y = int(px), int(py)
        ddx = abs(1 / rdx) if rdx != 0 else 1e30
        ddy = abs(1 / rdy) if rdy != 0 else 1e30
        if rdx < 0:
            sx, sdx = -1, (px - map_x) * ddx
        else:
            sx, sdx = 1, (map_x + 1 - px) * ddx
        if rdy < 0:
            sy, sdy = -1, (py - map_y) * ddy
        else:
            sy, sdy = 1, (map_y + 1 - py) * ddy

        side = 0
        dist = 64.0
        for _ in range(64):
            if sdx < sdy:
                sdx += ddx
                map_x += sx
                side = 0
            else:
                sdy += ddy
                map_y += sy
                side = 1
            if map_y < 0 or map_y >= gs.mh or map_x < 0 or map_x >= gs.mw:
                break
            if maze[map_y][map_x] == 1:
                dist = (sdx - ddx) if side == 0 else (sdy - ddy)
                break

        zbuf[x] = dist
        line_h = max(1, int(H / max(0.01, dist)))
        top = max(0, horizon - line_h // 2)
        bottom = min(H - 1, horizon + line_h // 2)
        draw_h = bottom - top

        if draw_h > 0:
            tex_arr = TEX_ARRAYS[wtex[map_y][map_x]]
            indices = np.linspace(0, 63, draw_h, dtype=int)
            if side == 0:
                wallX = py + dist * rdy
            else:
                wallX = px + dist * rdx
            wallX -= int(wallX)
            texX = int(wallX * 64)
            if (side == 0 and rdx > 0) or (side == 1 and rdy < 0):
                texX = 63 - texX
            col_pixels = tex_arr[texX, indices]
            b = light_at(gs, px + dist * rdx, py + dist * rdy, now)
            shade = b * (0.85 if side == 1 else 1.0)
            surf_array[x, top:bottom] = np.clip(col_pixels * shade, 0, 255).astype(np.uint8)

    # Разблокируем surface
    del surf_array
    return zbuf


def render_sprites(gs, surface, angle, horizon, zbuf, now):
    """Рендеринг спрайтов с учётом Z-буфера"""
    W, H = gs.W, gs.H
    px, py = gs.px, gs.py
    dirX = math.cos(angle)
    dirY = math.sin(angle)
    plane_len = gs.current_plane_len
    planeX = -dirY * plane_len
    planeY = dirX * plane_len

    sprites = [(gs.goal[0], gs.goal[1], gs.GATE_SPRITE, 'portal', 0.95)]
    sprites.append((gs.mx, gs.my, gs.MINO_SPRITE, 'lit', 1.0))
    sprites.append((gs.mx, gs.my, gs.EYES_SPRITE, 'glow', 1.0))
    for txx, tyy, tph in gs.torches:
        sprites.append((txx, tyy, gs.TORCH_SPRITE, 'torch', 0.6))
    for pxx, pyy, psurf, pkind in gs.pics:
        sprites.append((pxx, pyy, psurf, pkind, 0.5))
    for wxx, wyy in gs.watchers:
        sprites.append((wxx, wyy, gs.WATCHER_SPRITE, 'watcher', 0.45))
    for dxx, dyy, dsurf, dsc, dkind in gs.decors:
        sprites.append((dxx, dyy, dsurf, dkind, dsc))

    sprites.sort(key=lambda s: -((s[0] - px) ** 2 + (s[1] - py) ** 2))
    inv = 1.0 / (planeX * dirY - dirX * planeY)

    for sx0, sy0, spr, kind, scale in sprites:
        if spr is None:
            continue  # <--- ДОБАВЬ ЭТИ 2 СТРОЧКИ
        rx, ry = sx0 - px, sy0 - py
        tx = inv * (dirY * rx - dirX * ry)
        ty = inv * (-planeY * rx + planeX * ry)
        if ty <= 0.1:
            continue
        scrX = int((W / 2) * (1 + tx / ty))
        half_wall = int((H / ty) / 2)
        size = max(2, int((H / ty) * scale))
        if size > H * 4:
            continue

        # Освещение спрайта
        if kind in ('glow', 'torch'):
            b = 1.0
        elif kind == 'portal':
            b = 0.2 if now < gs.gate_dark_until else 1.0
        elif kind == 'pic_glow':
            b = 0.45 + 0.15 * math.sin(now * 2.5 + sx0 * 5.1)
        elif kind == 'pic_lit':
            b = light_at(gs, sx0, sy0, now) * 0.95 + 0.05
        elif kind == 'watcher':
            dwatch = math.hypot(sx0 - px, sy0 - py)
            b = 1.0 if dwatch > 6 else 0.0
            if b and math.sin(now * 0.9 + sx0 * 7) > 0.98:
                b = 0.0
        elif kind == 'puddle':
            b = 0.30 + 0.10 * math.sin(now * 2 + sx0 * 3.1)
        elif kind == 'lit':
            b = light_at(gs, sx0, sy0, now)
        else:
            b = light_at(gs, sx0, sy0, now) * 0.9 + 0.05
        if b <= 0.03:
            continue

        if kind in ('torch', 'pic_glow', 'pic_lit'):
            v_top = horizon + int(half_wall * 0.4) - size
        else:
            v_top = horizon + half_wall - size

        ds = pygame.transform.scale(spr, (size, size))
        tinted = ds.copy()
        g = int(255 * b)
        tinted.fill((g, g, g), special_flags=pygame.BLEND_RGB_MULT)

        x0 = max(0, scrX - size // 2)
        x1 = min(W, scrX + size // 2)
        for stripe in range(x0, x1):
            if zbuf[stripe] > ty:
                tex_x = stripe - (scrX - size // 2)
                surface.blit(tinted, (stripe, v_top), (tex_x, 0, 1, size))


def render_minimap(gs, screen, angle):
    """Умная миникарта с индикаторами"""
    MM = gs.MM
    MM_CS = gs.MM_CS
    mmw = pygame.Surface((MM, MM))
    mmw.fill((5, 5, 8))

    full_w = gs.mw * MM_CS
    full_h = gs.mh * MM_CS
    if full_w <= MM:
        sx = (full_w - MM) // 2
    else:
        sx = int(gs.px * MM_CS) - MM // 2
        sx = max(0, min(full_w - MM, sx))
    if full_h <= MM:
        sy = (full_h - MM) // 2
    else:
        sy = int(gs.py * MM_CS) - MM // 2
        sy = max(0, min(full_h - MM, sy))

    ox = max(0, sx)
    oy = max(0, sy)
    ex = min(full_w, sx + MM)
    ey = min(full_h, sy + MM)
    if ex > ox and ey > oy:
        mmw.blit(gs.mm_base, (ox - sx, oy - sy), (ox, oy, ex - ox, ey - oy))

    def mm_dot(wx, wy, col, r=2, arrow=True):
        x = int(wx - sx)
        y = int(wy - sy)
        if 0 <= x < MM and 0 <= y < MM:
            pygame.draw.circle(mmw, col, (x, y), r)
            return
        if not arrow:
            return
        cxm = MM // 2
        cym = MM // 2
        ddx = x - cxm
        ddy = y - cym
        t = 1000000.0
        if ddx != 0:
            t = min(t, ((MM - 6) - cxm) / ddx if ddx > 0 else (6 - cxm) / ddx)
        if ddy != 0:
            t = min(t, ((MM - 6) - cym) / ddy if ddy > 0 else (6 - cym) / ddy)
        pygame.draw.circle(mmw, col, (int(cxm + ddx * t), int(cym + ddy * t)), r)

    for txx, tyy, tph in gs.torches:
        mm_dot(txx * MM_CS, tyy * MM_CS, (255, 150, 50), 1, arrow=False)

    mm_dot(gs.goal[0] * MM_CS, gs.goal[1] * MM_CS, (0, 255, 120))
    mm_dot(gs.mx * MM_CS, gs.my * MM_CS, (255, 0, 0))

    pcx = int(gs.px * MM_CS - sx)
    pcy = int(gs.py * MM_CS - sy)
    pygame.draw.circle(mmw, (255, 255, 0), (pcx, pcy), 2)
    pygame.draw.line(mmw, (255, 255, 0), (pcx, pcy),
                     (int(pcx + math.cos(angle) * 6), int(pcy + math.sin(angle) * 6)))

    mmw.set_alpha(200)
    screen.blit(mmw, (gs.SW - MM - 8, 8))
    pygame.draw.rect(screen, (60, 60, 70), (gs.SW - MM - 8, 8, MM, MM), 2)