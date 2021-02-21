#!/usr/bin/env python3
"""
Event-driven Snake game

"""

import pygame
from dataclasses import dataclass
from typing import List, Tuple
import random

# ----------------------------------------------------------------------
# MESSAGES (EVENTS)
# ----------------------------------------------------------------------

@dataclass
class Message:
    pass

@dataclass
class SnakeChangeDirectionMessage(Message):
    direction: Tuple[int, int]

@dataclass
class SpawnFoodMessage(Message):
    pass

@dataclass
class RemoveEntityMessage(Message):
    entity: "Entity"

@dataclass
class EntityCollisionMessage(Message):
    entity: "Entity"
    other: "Entity"

@dataclass
class GameOverMessage(Message):
    reason: str

# ----------------------------------------------------------------------
# ENTITIES
# ----------------------------------------------------------------------

@dataclass
class Entity:
    def render(self, surface: pygame.Surface):
        pass

    def update(self, messages: List[Message]) -> List[Message]:
        return []

    def get_extent(self) -> List[Tuple[int, int]]:
        return []

    def collides_with(self, other: "Entity") -> bool:
        if other is self:
            return False  # no self collision by default
        else:
            return bool(set(self.get_extent()) & set(other.get_extent()))

@dataclass
class Food(Entity):
    position: Tuple[int, int]

    def render(self, surface: pygame.Surface):
        surface.set_at(self.position, "red")

    def get_extent(self) -> List[Tuple[int, int]]:
        return [self.position]

@dataclass
class Wall(Entity):
    positions: List[Tuple[int, int]]

    def render(self, surface: pygame.Surface):
        for position in self.positions:
            x, y = position
            if (x + y) % 2 == 0:
                surface.set_at(position, (100, 100, 100))
            else:
                surface.set_at(position, (120, 120, 120))

    def get_extent(self) -> List[Tuple[int, int]]:
        return self.positions

@dataclass
class Snake(Entity):
    body: List[Tuple[int, int]]  # [head, ..., tail]
    direction: Tuple[int, int]  # (1, 0) or such
    max_length: int

    def render(self, surface: pygame.Surface):
        for i, position in enumerate(self.body):
            if i == 0:
                surface.set_at(position, (0, 200, 0))  # make head slightly darker
            else:
                surface.set_at(position, (0, 255, 0))

    def update(self, messages: List[Message]) -> List[Message]:
        new_messages = []

        # handle events
        for message in messages:
            if isinstance(message, SnakeChangeDirectionMessage):
                # make sure we don't allow changing to opposite direction, which would self-collide our hero
                if any(x+y != 0 for x, y in zip(message.direction, self.direction)):
                    self.direction = message.direction
            elif isinstance(message, EntityCollisionMessage) and message.entity is self:
                if message.other is self:
                    new_messages.append(GameOverMessage("Snake bit its tail"))
                elif isinstance(message.other, Wall):
                    new_messages.append(GameOverMessage("Snake hit wall"))
                elif isinstance(message.other, Food):
                    self.max_length += 1
                    new_messages.append(RemoveEntityMessage(message.other))
                    new_messages.append(SpawnFoodMessage())

        # move snake
        old_head = self.body[0]
        new_head = (old_head[0] + self.direction[0],
                    old_head[1] + self.direction[1])
        self.body.insert(0, new_head)

        while len(self.body) > self.max_length:
            self.body.pop()

        return new_messages

    def get_extent(self) -> List[Tuple[int, int]]:
        return self.body

    def collides_with(self, other: "Entity") -> bool:
        if other is self:
            return len(set(self.body)) != len(self.body)  # detect snake self-collision
        else:
            return super(Snake, self).collides_with(other)  # defer to default implementation

# ----------------------------------------------------------------------
# MAIN LOGIC
# ----------------------------------------------------------------------

class World:
    def __init__(self, surface: pygame.Surface):
        self.width: int = surface.get_width()
        self.height: int = surface.get_height()
        self.surface = surface
        self.entities: List[Entity] = []
        self.message_queue: List[Message] = []
        self.running = True
        self.paused = False

    def render(self):
        for entity in self.entities:
            entity.render(self.surface)

    def update(self):
        pygame_events = pygame.event.get()

        # handle outside events
        for event in pygame_events:
            if event.type == pygame.QUIT:
                self.running = False
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.message_queue.append(SnakeChangeDirectionMessage((0, -1)))
                elif event.key == pygame.K_DOWN:
                    self.message_queue.append(SnakeChangeDirectionMessage((0, 1)))
                elif event.key == pygame.K_RIGHT:
                    self.message_queue.append(SnakeChangeDirectionMessage((1, 0)))
                elif event.key == pygame.K_LEFT:
                    self.message_queue.append(SnakeChangeDirectionMessage((-1, 0)))
                elif event.key == pygame.K_p:
                    self.paused = not self.paused  # toggle pause

        if self.paused:
            self.message_queue.clear()
            return

        # handle collisions
        for i in range(len(self.entities)):
            for j in range(i, len(self.entities)):
                if self.entities[i].collides_with(self.entities[j]):
                    self.message_queue.append(EntityCollisionMessage(self.entities[i], self.entities[j]))
                    self.message_queue.append(EntityCollisionMessage(self.entities[j], self.entities[i]))

        # update entities
        new_messages: List[Message] = []

        for entity in self.entities:
            tmp = entity.update(self.message_queue)
            new_messages.extend(tmp)

        # handle global messages, clear queue
        self.message_queue.extend(new_messages)

        for message in self.message_queue:
            print(message)  # XXX

            if isinstance(message, GameOverMessage):
                self.running = False
                return
            elif isinstance(message, RemoveEntityMessage):
                self.entities.remove(message.entity)
            elif isinstance(message, SpawnFoodMessage):
                for _ in range(100):
                    new_food = Food(position=(random.randrange(self.width), random.randrange(self.height)))
                    ok = True
                    for entity in self.entities:
                        if entity.collides_with(new_food):
                            ok = False
                            break
                    if ok:
                        break
                else:
                    raise RuntimeError("Failed to put food into empty space")

                self.entities.append(new_food)

        self.message_queue.clear()


def main():
    WIDTH, HEIGHT = 120, 80
    SCALE = 8

    pygame.init()
    pygame.font.init()
    font = pygame.font.SysFont('Ubuntu Sans', 30)

    pygame.display.set_caption("Snake game")
    display = pygame.display.set_mode((SCALE*WIDTH, SCALE*HEIGHT))  # actual game window
    surface = pygame.Surface((WIDTH, HEIGHT))  # lower resolution surface to render into
    clock = pygame.time.Clock()

    # prepare world
    world = World(surface)
    snake = Snake(body=[(10, 10), (9, 10), (8, 10)], direction=(1, 0), max_length=3)
    wall = Wall([(x, 0) for x in range(WIDTH)] + [(x, HEIGHT-1) for x in range(WIDTH)] +
                [(0, x) for x in range(HEIGHT)] + [(WIDTH-1, x) for x in range(HEIGHT)])
    world.entities.append(snake)
    world.entities.append(wall)
    world.message_queue.append(SpawnFoodMessage())
    world.update()

    # for every frame
    while world.running:
        # handle game logic
        world.update()

        # render in low resolution
        surface.fill("white")
        world.render()

        # render in high resolution
        display.blit(pygame.transform.scale(surface, display.get_rect().size), (0, 0))
        display.blit(font.render(f"Snake Length: {snake.max_length}", True, (0, 0, 0)), (10, 10))
        if world.paused:
            text = font.render(f"PAUSE (press P to continue)", True, (0, 0, 0))
            display.blit(text, ((SCALE * WIDTH - text.get_width()) / 2, (SCALE * HEIGHT - text.get_height()) / 2))
        pygame.display.flip()

        # wait till next frame
        default_speed = 10  # fps
        speed_factor = min(3.0, 1.0 + 0.1*snake.max_length)
        clock.tick(int(default_speed * speed_factor))

    # end screen
    text = font.render("GAME OVER", True, (0, 0, 0))
    display.blit(text, ((SCALE * WIDTH - text.get_width()) / 2, (SCALE * HEIGHT - text.get_height()) / 2))
    pygame.display.flip()
    endscreen_running = True
    while endscreen_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                endscreen_running = False
        clock.tick(10)

    pygame.quit()


if __name__ == "__main__":
    main()
