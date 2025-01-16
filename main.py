import pygame
from crossword import Crossword
from parser import get_puzzle

rows, cols, deep = get_puzzle(49391)
w, h = (len(cols) + deep[0]) * 20, (len(rows) + deep[1]) * 20
pygame.init()
screen = pygame.display.set_mode((w, h))
pygame.display.set_caption('Японский кроссворд')

crossword = Crossword(screen, cols=cols, rows=rows, deep=deep)

running, drawing, pen = True, False, False
while running:
    events = pygame.event.get()

    crossword.draw()
    crossword.update(events)
    crossword.find_answer()

    for event in events:
        if event.type == pygame.QUIT:
            running = False
