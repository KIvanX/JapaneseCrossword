import random

import pygame
import numpy as np
from numba import njit
from web_parser import paste_puzzle


class Crossword:
    def __init__(self, screen: pygame.display, cols, rows, cols_colors, rows_colors, colors, pix, deep, num,
                 auto=False, driver=None):
        self.screen = screen
        self.a = np.array([[0] * len(cols) for _ in range(len(rows))], dtype=np.byte)
        self.a_exclude = np.array([[[1] * len(colors) for __ in range(len(cols))] for _ in range(len(rows))], dtype=np.byte)
        self.a_cols_old = np.array([[1] * len(rows) for _ in range(len(cols))], dtype=np.byte)
        self.a_rows_old = np.array([[1] * len(cols) for _ in range(len(rows))], dtype=np.byte)
        self.deep = deep
        self.pix = pix
        self.cols, self.rows = [np.array(e, dtype=np.byte) for e in cols], [np.array(e, dtype=np.byte) for e in rows]
        self.cols_color, self.rows_color = cols_colors, rows_colors
        self.colors = colors
        self.dump, self.dump_exclude, self.dump_v = None, None, None
        self.finished = False
        self.num = num
        self.no_way = {}
        self.drawing, self.pen, self.clear = False, 1, False
        self.n, self.m = len(self.a), len(self.a[0])
        self.auto = auto
        self.driver = driver

        for i in range(self.n):
            for j in range(self.m):
                self.a_exclude[i][j] = [i0 + 1 in self.rows_color[i] and i0 + 1 in self.cols_color[j] for i0 in range(len(colors))]

    def update(self, events):
        x, y = pygame.mouse.get_pos()
        i, j = y // self.pix - self.deep[1], x // self.pix - self.deep[0]
        if self.drawing:
            if 0 <= i < self.n and 0 <= j < self.m:
                self.a[i][j] = self.pen if not self.clear else -1

        for event in events:
            if event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP]:
                self.drawing = event.type == pygame.MOUSEBUTTONDOWN
                self.clear = event.button == 3

                if event.button == 1 and not self.drawing:
                    if i < 0 <= j and -i <= len(self.cols_color[j]):
                        self.pen = self.cols_color[j][i]
                    elif j < 0 <= i and -j <= len(self.rows_color[i]):
                        self.pen = self.rows_color[i][j]
                    elif i < 0 and j < 0:
                        self.pen = 0

            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                self.find_answer()

    def draw(self):
        a = self.pix
        dx = a / 3
        w, h = self.deep[0] * a + self.m * a, self.deep[1] * a + self.n * a
        font = pygame.font.SysFont('Liberation Sans', self.pix * 3 // 4)

        # Закрашиваем фон
        self.screen.fill((200, 200, 200))

        # Рисуем фон подсказок
        pygame.draw.rect(self.screen, (180, 180, 180), (0, 0, self.deep[0] * self.pix, h))
        pygame.draw.rect(self.screen, (180, 180, 180), (0, 0, w, self.deep[1] * self.pix))

        # Подсвечиваем строку и столбец под курсором
        x, y = pygame.mouse.get_pos()
        i, j = x // a - self.deep[0], y // a - self.deep[1]
        if 0 <= i < self.n and 0 <= j < self.m:
            pygame.draw.rect(self.screen, (200, 200, 200), (self.deep[0] * a + i * a, 0, a, a * self.deep[1]))
            pygame.draw.rect(self.screen, (200, 200, 200), (0, self.deep[1] * a + j * a, a * self.deep[0], a))

        # Рисуем подсказки
        for i in range(self.n):
            for j, k in enumerate(self.rows[i][::-1]):
                color = self.colors[self.rows_color[i][len(self.rows[i]) - j - 1]] if len(self.colors) > 2 else (180, 180, 180)
                text = font.render(str(k), True, (0, 0, 0) if sum(color) // 3 > 150 else (255, 255, 255))
                pygame.draw.rect(self.screen, color, (self.deep[0] * a - a - j * a + 1, self.deep[1] * a + i * a + 1, a - 1, a - 1))
                self.screen.blit(text, (self.deep[0] * a - a - j * a + (dx if k < 10 else dx // 3), self.deep[1] * a + 2 + i * a))
        for i in range(self.m):
            for j, k in enumerate(self.cols[i][::-1]):
                color = self.colors[self.cols_color[i][len(self.cols[i]) - j - 1]] if len(self.colors) > 2 else (180, 180, 180)
                text = font.render(str(k), True, (0, 0, 0) if sum(color) // 3 > 150 else (255, 255, 255))
                pygame.draw.rect(self.screen, color, (self.deep[0] * a + i * a + 1, self.deep[1] * a - a - j * a + 1, a - 1, a - 1))
                self.screen.blit(text, (self.deep[0] * a + i * a + (dx if k < 10 else dx // 3), self.deep[1] * a - a + 2 - j * a))

        # Рисуем кроссворд
        for i in range(self.n):
            for j in range(self.m):
                st_x, st_y = self.deep[0] * a + j * a + 1, self.deep[1] * a + i * a + 1
                if self.a[i][j] > 0:
                    pygame.draw.rect(self.screen, self.colors[self.a[i][j]], (st_x, st_y, a - 1, a - 1))
                elif self.a[i][j] == -1:
                    pygame.draw.line(self.screen, (20, 20, 20), (st_x, st_y), (st_x + a - 1, st_y + a - 1), 2)
                    pygame.draw.line(self.screen, (20, 20, 20), (st_x + a - 1, st_y), (st_x, st_y + a - 1), 2)

        # Рисуем сетку
        for i in range(self.n + self.deep[1]):
            wd = 2 if i - self.deep[1] > 0 and (i - self.deep[1]) % 5 == 0 else 1
            pygame.draw.line(self.screen, (80, 80, 80), (0, i * a), (w, i * a), wd)
        for i in range(self.m + self.deep[0]):
            wd = 2 if i - self.deep[0] > 0 and (i - self.deep[0]) % 5 == 0 else 1
            pygame.draw.line(self.screen, (80, 80, 80), (i * a, 0), (i * a, h), wd)
        color = self.colors[self.pen] if self.pen > 0 else (200, 200, 200)
        pygame.draw.rect(self.screen, color, (0, 0, self.deep[0] * a, self.deep[1] * a))

        # Рисуем рамку
        pygame.draw.line(self.screen, (80, 80, 80), (self.deep[0] * a, 0), (self.deep[0] * a, h), 3)
        pygame.draw.line(self.screen, (80, 80, 80), (0, self.deep[1] * a), (w, self.deep[1] * a), 3)
        pygame.draw.line(self.screen, (80, 80, 80), (w, 0), (w, h), 3)
        pygame.draw.line(self.screen, (80, 80, 80), (0, h), (w, h), 3)

        pygame.display.update()

    def find_answer(self):
        if self.finished:
            return 0

        updated = False
        for i in range(self.n):
            if self.rows[i].any() and np.any(self.a[i, :] != self.a_rows_old[i]):
                updated = True
                self.a_rows_old[i] = self.a[i, :]
                self.a[i, :], self.a_exclude[i, :] = line_paste(self.a[i, :], self.rows[i], self.rows_color[i], self.a_exclude[i, :])

        for j in range(self.m):
            if self.cols[j].any() and np.any(self.a[:, j] != self.a_cols_old[j]):
                updated = True
                self.a_cols_old[j] = self.a[:, j]
                self.a[:, j], self.a_exclude[:, j] = line_paste(self.a[:, j], self.cols[j], self.cols_color[j], self.a_exclude[:, j])

        if not np.any(self.a == 0):
            col_valid = [not is_valid_line(self.a[i, :], self.rows[i], self.rows_color[i], self.a_exclude[i, :])[0] for i in range(self.n)
                         if self.rows[i].any()]
            row_valid = [not is_valid_line(self.a[:, j], self.cols[j], self.cols_color[j], self.a_exclude[:, j])[0] for j in range(self.m)
                         if self.cols[j].any()]
            if (np.any(col_valid) or np.any(row_valid)) and self.dump:
                self.a = np.array([e.copy() for e in self.dump])
                self.a_exclude = np.array([[e.copy() for e in line] for line in self.dump_exclude])
                # self.a_exclude[self.dump_v[0]][self.dump_v[1]][self.dump_v[2]] = 0
                return 0

            self.draw()
            self.finished = True
            if self.auto:
                paste_puzzle(self.driver, self.num, self.a)
        elif not updated:
            if not self.dump:
                self.dump = [e.copy() for e in self.a]
                self.dump_exclude = [[e.copy() for e in line] for line in self.a_exclude]

            x, y = random.choice([(x, y) for x in range(self.n) for y in range(self.m) if self.a[x][y] == 0])
            self.a[x][y] = next((i + 1 for i in range(len(self.colors)) if self.a_exclude[x][y][i]))
            # self.dump_v = (x, y, self.a[y][x] - 1)


@njit
def line_paste(line, hints, hints_colors, line_exclude):
    for i in range(line.size):
        if line[i] != 0:
            continue

        for i_c in [i0 + 1 for i0 in range(line_exclude[i].size) if line_exclude[i][i0]]:
            line[i] = i_c
            status, way = is_valid_line(line, hints, hints_colors, line_exclude)
            if not status:
                line_exclude[i][i_c - 1] = 0
            line[i] = 0

        if np.all(line_exclude[i] == 0):
            line[i] = -1
        elif sum(line_exclude[i] != 0) == 1:
            line[i] = -1
            status, way = is_valid_line(line, hints, hints_colors, line_exclude)
            line[i] = [j + 1 for j in range(line_exclude[i].size) if line_exclude[i][j] != 0][0] if not status else 0

    return line, line_exclude


@njit
def is_valid_line(line, hints, hints_c, line_ex_c):
    pos = [0] * hints.size
    if hints.size:
        order(pos, hints, hints_c, 0, 0)
    else:
        return not np.any(line > 0), pos

    while True:
        flag = False
        for i in range(line.size):
            if line[i] > 0 and not [j for j in range(hints.size) if pos[j] <= i < pos[j] + hints[j] and line[i] == hints_c[j]]:
                left = [j for j in range(hints.size) if pos[j] < i and line[i] == hints_c[j]]
                if not left:
                    return False, pos
                order(pos, hints, hints_c, left[-1], i - pos[left[-1]] - hints[left[-1]] + 1)
                flag = True

        for i in range(hints.size):
            if (pos[i] + hints[i] <= line.size and
                    (np.any(line[pos[i]: pos[i] + hints[i]] == -1) or not np.all(line_ex_c[pos[i]: pos[i] + hints[i], hints_c[i] - 1]))):
                delta = [j for j in range(hints[i]) if line[pos[i] + j] == -1 or not line_ex_c[pos[i] + j][hints_c[i] - 1]][-1]
                order(pos, hints, hints_c, i, delta + 1)
                flag = True

        if pos[-1] + hints[-1] > line.size or not flag:
            return pos[-1] + hints[-1] <= line.size, pos


@njit
def order(pos, lens, colors, i, k):
    delta = i + 1 < len(pos) and (1 if colors[i] == colors[i + 1] else 0)
    if i + 1 < len(pos) and pos[i] + k + lens[i] + delta > pos[i + 1]:
        order(pos, lens, colors, i + 1, pos[i] + k + lens[i] + delta - pos[i + 1])
    pos[i] += k
