import pygame
from numba import njit
import numpy as np


class Crossword:
    def __init__(self, screen: pygame.display, cols, rows, deep):
        self.screen = screen
        self.a = np.array([[False] * len(cols) for _ in range(len(rows))], dtype=np.byte)
        self.deep = deep
        self.cols, self.rows = [np.array(e, dtype=np.byte) for e in cols], [np.array(e, dtype=np.byte) for e in rows]
        self.drawing, self.pen = False, False
        self.w, self.h = self.screen.get_size()
        self.n, self.m = len(self.a), len(self.a[0])
        self.font = pygame.font.SysFont('Liberation Sans', 15)

    def update(self, events):
        if self.drawing:
            x, y = pygame.mouse.get_pos()
            i, j = y // 20 - self.deep[1], x // 20 - self.deep[0]
            if 0 <= i < self.n and 0 <= j < self.m:
                self.a[i][j] = self.pen

        for event in events:
            if event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP]:
                self.drawing = event.type == pygame.MOUSEBUTTONDOWN
                x, y = pygame.mouse.get_pos()
                if 0 <= y // 20 - self.deep[0] < self.n and 0 <= x // 20 - self.deep[1] < self.m:
                    self.pen = not self.a[y // 20 - self.deep[0]][x // 20 - self.deep[1]] if event.button == 1 else -1

            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                self.find_answer()

    def draw(self):
        # Закрашиваем фон
        self.screen.fill((200, 200, 200))

        # Рисуем фон подсказок
        pygame.draw.rect(self.screen, (180, 180, 180), (0, 0, self.deep[0] * 20, self.h))
        pygame.draw.rect(self.screen, (180, 180, 180), (0, 0, self.w, self.deep[1] * 20))

        # Подсвечиваем строку и столбец под курсором
        x, y = pygame.mouse.get_pos()
        i, j = x // 20 - self.deep[0], y // 20 - self.deep[1]
        if 0 <= i < self.n and 0 <= j < self.m:
            pygame.draw.rect(self.screen, (200, 200, 200), (self.deep[0] * 20 + i * 20, 0, 20, 20 * self.deep[1]))
            pygame.draw.rect(self.screen, (200, 200, 200), (0, self.deep[1] * 20 + j * 20, 20 * self.deep[0], 20))

        # Рисуем сетку
        for i in range(self.n + self.deep[1]):
            wd = 2 if i - self.deep[1] > 0 and (i - self.deep[1]) % 5 == 0 else 1
            pygame.draw.line(self.screen, (80, 80, 80), (0, i * 20), (self.w, i * 20), wd)
        for i in range(self.m + self.deep[0]):
            wd = 2 if i - self.deep[0] > 0 and (i - self.deep[0]) % 5 == 0 else 1
            pygame.draw.line(self.screen, (80, 80, 80), (i * 20, 0), (i * 20, self.h), wd)
        pygame.draw.rect(self.screen, (180, 180, 180), (0, 0, self.deep[0] * 20, self.deep[1] * 20))

        # Рисуем подсказки
        for i in range(self.n):
            for j, k in enumerate(self.rows[i][::-1]):
                text = self.font.render(str(k), True, (0, 0, 0))
                self.screen.blit(text, (self.deep[0] * 20 - 20 - j * 20 + (6 if k < 10 else 2),
                                        self.deep[1] * 20 + 2 + i * 20))
        for i in range(self.m):
            for j, k in enumerate(self.cols[i][::-1]):
                text = self.font.render(str(k), True, (0, 0, 0))
                self.screen.blit(text, (self.deep[0] * 20 + i * 20 + (6 if k < 10 else 2),
                                        self.deep[1] * 20 - 18 - j * 20))

        # Рисуем кроссворд
        for i in range(self.n):
            for j in range(self.m):
                st_x, st_y = self.deep[0] * 20 + j * 20 + 1, self.deep[1] * 20 + i * 20 + 1
                if self.a[i][j] == 1:
                    pygame.draw.rect(self.screen, (20, 20, 20), (st_x, st_y, 19, 19))
                elif self.a[i][j] == -1:
                    pygame.draw.line(self.screen, (20, 20, 20), (st_x, st_y), (st_x + 19, st_y + 19), 3)
                    pygame.draw.line(self.screen, (20, 20, 20), (st_x + 19, st_y), (st_x, st_y + 19), 3)

        # Рисуем рамку
        pygame.draw.line(self.screen, (80, 80, 80), (self.deep[0] * 20, 0), (self.deep[0] * 20, self.h), 3)
        pygame.draw.line(self.screen, (80, 80, 80), (0, self.deep[1] * 20), (self.w, self.deep[1] * 20), 3)

        pygame.display.update()

    def find_answer(self):
        for i in range(self.n):
            line = _checker(self.a[i, :], self.rows[i])
            for j in range(self.m):
                self.a[i][j] = line[j]

        for j in range(self.m):
            line = _checker(self.a[:, j], self.cols[j])
            for i in range(self.n):
                self.a[i][j] = line[i]


@njit
def _checker(line, hints):
    for i in range(line.size):
        if line[i] == 0:
            line[i] = 1
            if not _is_valid(line, hints):
                line[i] = -1
                continue

            line[i] = -1
            if not _is_valid(line, hints):
                line[i] = 1
                continue

            line[i] = 0

    return line


@njit
def _is_valid(line, hints):
    if np.sum(hints) + hints.size - 1 > line.size:
        return False

    k = 0
    for i in range(hints.size):
        h = hints[i]
        while k < line.size and (np.any(line[k:k + h] == -1) or (k + h < line.size and line[k + h] == 1) or
                                 not _is_valid(line[k + h + 1:], hints[i + 1:])):
            if line[k] == 1 or k + h >= line.size:
                return False
            k += 1
        k += h

    if np.any(line[k:] == 1):
        return False
    return True

    # def load_image(self, path: str, size: tuple):
    #     # Загружаем изображение и преобразуем его к нужному размеру
    #     image = pygame.image.load(path)
    #     scale_image = pygame.transform.scale(image, size)
    #
    #     # Преобразуем изображение в массив булевых значений
    #     self.a = [[0] * size[1] for _ in range(size[0])]
    #     for i in range(size[0]):
    #         for j in range(size[1]):
    #             self.a[i][j] = sum(scale_image.get_at((i, j))) / 3 < 128
    #
    #     self.calc_hints()
    #
    # def calc_hints(self):
    #     # Устанавливаем размеры кроссворда и инициализируем массивы подсказок
    #     self.n, self.m = len(self.a), len(self.a[0])
    #     self.cols = [[] for _ in range(self.n)]
    #     self.rows = [[] for _ in range(self.m)]
    #
    #     # Считаем подсказки
    #     for i in range(self.n):
    #         ki, kj = 0, 0
    #         for j in range(self.m):
    #             if not self.a[i][j] and ki:
    #                 self.cols[i] = [ki] + self.cols[i]
    #                 ki = 0
    #             elif self.a[i][j]:
    #                 ki += 1
    #
    #             if not self.a[j][i] and kj:
    #                 self.rows[i] = [kj] + self.rows[i]
    #                 kj = 0
    #             elif self.a[j][i]:
    #                 kj += 1
    #
    #         if ki:
    #             self.cols[i] = [ki] + self.cols[i]
    #         if kj:
    #             self.rows[i] = [kj] + self.rows[i]

    # def _division(self, line, hints):
    #     starts = [j for j in range(len(line)) if line[j] == -1] + [len(line)]
    #     sizes = [starts[j] - (starts[j - 1] + 1 if j - 1 >= 0 else 0) for j in range(len(starts))]
    #
    #     lands1, k = [[] for _ in range(len(sizes))], 0
    #     for j in range(len(hints)):
    #         while k < len(lands1) - 1 and sum([hints[i0] for i0 in lands1[k]]) + len(lands1[k]) + hints[j] > sizes[k]:
    #             k += 1
    #         lands1[k].append(j)
    #
    #     lands2, k = [[] for _ in range(len(sizes))], len(sizes) - 1
    #     for j in range(len(hints) - 1, -1, -1):
    #         while k > 0 and sum([hints[i0] for i0 in lands2[k]]) + len(lands2[k]) + hints[j] > sizes[k]:
    #             k -= 1
    #         lands2[k] = [j] + lands2[k]
    #
    #     for j in range(len(lands1)):
    #         if lands1[j] == lands2[j]:
    #             st = starts[j - 1] + 1 if j - 1 >= 0 else 0
    #             line = self._fill(line, st, st + sizes[j], [hints[i0] for i0 in lands1[j]])
    #     return line
    #
    # @staticmethod
    # def _fill(line, st_j, en_j, nums):
    #     for j in range(len(nums)):
    #         st = [nums[j1] for j1 in range(j)]
    #         en = [nums[j1] for j1 in range(j + 1, len(nums))]
    #         free = en_j - st_j - sum(st) - sum(en) - len(st) - len(en)
    #         if free < nums[j] * 2:
    #             for j1 in range(free - (free - nums[j]) * 2):
    #                 line[st_j + sum(st) + len(st) + (free - nums[j]) + j1] = 1
    #     return line
