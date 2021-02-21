#!/usr/bin/env python3

import pygame
import random

WIDTH, HEIGHT = 120, 80
SCALE = 8

display = pygame.display.set_mode((SCALE*WIDTH, SCALE*HEIGHT))
clock = pygame.time.Clock()

snake_body = [(10, 10), (9, 10), (8, 10)]
snake_direction = (1, 0)
snake_max_length = 3
food = (random.randrange(WIDTH), random.randrange(HEIGHT))

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                snake_direction = (0, -1)
            elif event.key == pygame.K_DOWN:
                snake_direction = (0, +1)
            elif event.key == pygame.K_LEFT:
                snake_direction = (-1, 0)
            elif event.key == pygame.K_RIGHT:
                snake_direction = (+1, 0)

    display.fill("white")

    pygame.draw.rect(display, "red", (SCALE * food[0], SCALE * food[1], SCALE, SCALE))

    for pos in snake_body:
        x, y = pos
        pygame.draw.rect(display, "green", (SCALE*x, SCALE*y, SCALE, SCALE))

        if food == pos:
            snake_max_length += 1
            food = (random.randrange(WIDTH), random.randrange(HEIGHT))

        if not (0 <= x < WIDTH and 0 <= y < HEIGHT):
            print("Snake collided with wall")
            running = False

        if snake_body.count(pos) > 1:
            print("Snake bit itself")
            running = False

    # move snake
    old_head = snake_body[0]
    new_head = (old_head[0] + snake_direction[0],
                old_head[1] + snake_direction[1])
    snake_body.insert(0, new_head)
    while len(snake_body) > snake_max_length:
        snake_body.pop()

    # update window
    pygame.display.flip()
    clock.tick(15)

pygame.quit()
