import logging
import os
import random
import signal
import subprocess
import sys
import threading
import time
import pygame
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from crossword import Crossword
from web_parser import get_puzzle, get_numbers, login


def handle_exit_signal(_, __):
    if driver:
        driver.quit()
    exit(0)


signal.signal(signal.SIGINT, handle_exit_signal)
signal.signal(signal.SIGTERM, handle_exit_signal)


AUTO_RESOLUTION = True
DISPLAY = False
num_i, nums, work = 0, [], True
crossword, driver = None, None

options = Options()
if AUTO_RESOLUTION:
    # options.add_argument("--start-maximized")
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")

    number = os.getpid()
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    with open('logs.log', "a") as f:
        f.write('@' * 50 + f' The process {number} is running... ' + '@' * 50 + '\n\n')

    logging.basicConfig(level=logging.WARNING, filename='logs.log', filemode="w",
                        format=f"[{number}] %(asctime)s %(levelname)s %(message)s\n" + '\n' * 3)

driver = webdriver.Chrome(options)
login(driver)

W, H = 0, 0
if DISPLAY:
    pygame.init()
    pygame.display.set_caption('Японский кроссворд')
    W, H = pygame.display.Info().current_w, pygame.display.Info().current_h

running = True
while running:
    if not crossword or AUTO_RESOLUTION and crossword.finished:
        if num_i >= len(nums):
            nums += get_numbers(driver)
        while True:
            try:
                rows, cols, rows_colors, cols_colors, colors, deep = get_puzzle(driver, nums[num_i])
                num_i += 1
                break
            except:
                print(f'Load error: {nums[num_i]}')
                time.sleep(3)
                num_i += 1
                if num_i >= len(nums):
                    nums += get_numbers(driver)

        screen, a = None, None
        if DISPLAY:
            a = int(H * 0.8 // (deep[1] + len(rows_colors)))
            w, h = a * (deep[0] + len(cols_colors)), a * (deep[1] + len(rows_colors))
            screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
        crossword = Crossword(screen, cols, rows, cols_colors, rows_colors, colors, a, deep, nums[num_i - 1],
                              auto=AUTO_RESOLUTION, driver=driver)

    if AUTO_RESOLUTION:
        crossword.find_answer()

    if DISPLAY:
        events = pygame.event.get()
        crossword.draw()
        crossword.update(events)

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
