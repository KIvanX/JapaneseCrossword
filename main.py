import logging
import os
import signal
import time

import pygame

from crossword import Crossword
from web_parser import get_puzzle, get_numbers, init_driver, login

AUTO_RESOLUTION = True
DISPLAY = False
num_i, nums, work = 0, [], True
crossword, driver = None, None

if AUTO_RESOLUTION:
    number = os.getpid()
    logging.root.handlers.clear()
    logging.basicConfig(level=logging.WARNING, filename='logs.log', filemode="a",
                        format=f"[{number}] %(asctime)s %(levelname)s %(message)s\n" + '\n' * 3)
    logging.warning('Start')


W, H = 0, 0
if DISPLAY:
    pygame.init()
    pygame.display.set_caption('Японский кроссворд')
    W, H = pygame.display.Info().current_w, pygame.display.Info().current_h


running = True
while running:
    try:
        if not crossword or AUTO_RESOLUTION and crossword.finished:
            if driver:
                driver.close()
            driver = init_driver()
            login(driver)

            k = 0
            while num_i >= len(nums) and k < 30:
                nums += get_numbers(driver)
                k += 1

            rows, cols, rows_colors, cols_colors, colors, deep = get_puzzle(driver, nums[num_i])
            num_i += 1

            screen, a = None, None
            if DISPLAY:
                a = int(H * 0.8 // (deep[1] + len(rows_colors)))
                w, h = a * (deep[0] + len(cols_colors)), a * (deep[1] + len(rows_colors))
                screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
            crossword = Crossword(screen, cols, rows, cols_colors, rows_colors, colors, a, deep, nums[num_i - 1], driver=driver)

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
    except Exception as e:
        try:
            driver.quit()
        except:
            pass
        driver = None
        logging.error('Main loop error: ' + str(e))
        time.sleep(3)
