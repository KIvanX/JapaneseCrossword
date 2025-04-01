
import subprocess
import sys
import threading
import time
import pygame
from crossword import Crossword
from web_parser import get_puzzle, get_numbers
import psutil


def recover():
    global work
    while True:
        work = False
        time.sleep(120)
        if not work:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                        proc.terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            subprocess.Popen([sys.executable] + sys.argv)
            sys.exit()


AUTO_RESOLUTION = True
num_i, nums, work = 0, [], True
crossword = None

pygame.init()
pygame.display.set_caption('Японский кроссворд')

if AUTO_RESOLUTION:
    threading.Thread(target=recover, daemon=True).start()

W, H = pygame.display.Info().current_w, pygame.display.Info().current_h
running = True
while running:
    events = pygame.event.get()
    work = True

    if not crossword or AUTO_RESOLUTION and crossword.finished:
        if num_i >= len(nums):
            nums += get_numbers()
        while True:
            try:
                rows, cols, rows_colors, cols_colors, colors, deep = get_puzzle(nums[num_i])
                num_i += 1
                break
            except:
                print(f'Load error: {nums[num_i]}')
                time.sleep(3)
                num_i += 1

        a = int(H * 0.8 // (deep[1] + len(rows_colors)))
        w, h = a * (deep[0] + len(cols_colors)), a * (deep[1] + len(rows_colors))
        screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
        crossword = Crossword(screen, cols, rows, cols_colors, rows_colors, colors, a, deep, nums[num_i - 1], auto=AUTO_RESOLUTION)

    crossword.draw()
    crossword.update(events)

    if AUTO_RESOLUTION:
        crossword.find_answer()

    for event in events:
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.VIDEORESIZE and crossword:
            W, H = pygame.display.Info().current_w, pygame.display.Info().current_h
            h, w = crossword.deep[1] + len(crossword.rows_color), crossword.deep[0] + len(crossword.cols_color)
            crossword.pix = min(H // h, W // w)

        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and not AUTO_RESOLUTION:
            crossword.finished = False
            crossword.find_answer()
