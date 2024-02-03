import sqlite3

import pygame
import sys
import random

# Инициализация Pygame
pygame.init()

# Ускорение игры
acceleration_timer = 0
acceleration_interval = 300

# Определение основных констант
WIDTH, HEIGHT = 800, 670
FPS = 60
WHITE = (255, 255, 255)
RED = (255, 0, 0)
FRUIT_COLORS = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]  # Цвета фруктов

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ловля шаров")

basket_image = pygame.Surface((50, 50), pygame.SRCALPHA)
pygame.draw.rect(basket_image, WHITE, (0, 0, 50, 50))
pygame.draw.rect(basket_image, RED, (10, 10, 30, 10))
pygame.draw.rect(basket_image, RED, (10, 30, 30, 10))

fruit_images = [
    pygame.Surface((30, 30), pygame.SRCALPHA),
    pygame.Surface((30, 30), pygame.SRCALPHA),
    pygame.Surface((30, 30), pygame.SRCALPHA)
]

for i, color in enumerate(FRUIT_COLORS):
    pygame.draw.circle(fruit_images[i], color, (15, 15), 15)

basket_speed = 10
fruit_speed = 5
fruit_spawn_interval = 60  # Количество кадров между появлениями фруктов

conn = sqlite3.connect('game_scores.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        score INTEGER,
        level INTEGER
    )
''')
conn.commit()


def save_score_to_database(score, level):
    cursor.execute('INSERT INTO scores (score, level) VALUES (?, ?)', (score, level))
    conn.commit()


def get_scores_from_database():
    cursor.execute('SELECT * FROM scores ORDER BY score DESC, level DESC LIMIT 10')
    return cursor.fetchall()


class Basket(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = basket_image
        self.rect = self.image.get_rect(center=(WIDTH // 2, HEIGHT - 50))

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= basket_speed
        if keys[pygame.K_RIGHT] and self.rect.right < WIDTH:
            self.rect.x += basket_speed


class Fruit(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = random.choice(fruit_images)
        self.rect = self.image.get_rect(center=(random.randint(0, WIDTH), 0))

    def update(self):
        self.rect.y += fruit_speed
        if self.rect.top > HEIGHT:
            self.rect.y = 0
            self.rect.centerx = random.randint(0, WIDTH)


def restart_game():
    global basket, fruits, score, lives, level
    basket = Basket()
    fruits.empty()
    score = 0
    lives = 3
    level = 1


def show_game_over_screen():
    font_big = pygame.font.Font(None, 72)
    game_over_text = font_big.render("Игра окончена", True, RED)
    score_text = font.render(f'Ваши очки: {score}', True, WHITE)
    level_text = font.render(f'Ваш уровень: {level}', True, WHITE)
    restart = font.render(f'Чтобы начать игру заново, нажмите пробел', True, (100, 100, 100))

    screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 4))
    screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2))
    screen.blit(level_text, (WIDTH // 2 - level_text.get_width() // 2, HEIGHT // 2 + 50))
    screen.blit(restart, (WIDTH // 4 - level_text.get_width() // 4, HEIGHT // 2 + 100))

    pygame.display.flip()

    save_score_to_database(score, level)

    scores_table = get_scores_from_database()
    font_big = pygame.font.Font(None, 36)
    scores_text = font_big.render("Топ 5 набранных очков", True, (0, 255, 0))
    screen.blit(scores_text, (WIDTH // 2 - scores_text.get_width() // 2, HEIGHT // 2 + 140))

    for i, (saved_id, saved_score, saved_level) in enumerate(scores_table):
        score_line = font.render(f'{i + 1}. Очки: {saved_score}, Уровень: {saved_level}', True, WHITE)
        screen.blit(score_line, (WIDTH // 2 - score_line.get_width() // 2, HEIGHT // 2 + 190 + i * 30))

    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    restart_game()
                    return


basket = Basket()
fruits = pygame.sprite.Group()

fruit_spawn_timer = 0

score = 0
lives = 3
level = 1

font = pygame.font.Font(None, 36)

clock = pygame.time.Clock()
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    basket.update()

    # Генерация фруктов
    fruit_spawn_timer += 1
    if fruit_spawn_timer == fruit_spawn_interval:
        fruit = Fruit()
        fruits.add(fruit)
        fruit_spawn_timer = 0

    # Ускорение игры
    acceleration_timer += 1
    if acceleration_timer == acceleration_interval:
        fruit_speed += 1  # Увеличиваем скорость фруктов
        basket_speed += 0.55  # Увеличиваем скорость корзины
        acceleration_timer = 0  # Сбрасываем таймер
        level += 1

    fruits.update()

    # Проверка столкновения корзинки с фруктами
    fruit_collision = pygame.sprite.spritecollide(basket, fruits, True)
    for fruit in fruit_collision:
        score += 1

    # Проверка пропущенных фруктов
    for fruit in fruits:
        if fruit.rect.bottom >= HEIGHT:
            fruits.remove(fruit)
            lives -= 1

    # Проверка окончания игры
    if lives == 0:
        show_game_over_screen()
        restart_game()
        basket_speed = 10
        fruit_speed = 5
        fruit_spawn_interval = 60
        level = 1

    screen.fill((0, 0, 0))
    screen.blit(basket.image, basket.rect)

    for fruit in fruits:
        screen.blit(fruit.image, fruit.rect)

    # Отображение счета и жизней
    score_text = font.render(f'Очки: {score}', True, (0, 255, 0))
    lives_text = font.render(f'Жизни: {lives}', True, (0, 0, 255))
    level_text = font.render(f'Уровень: {level}', True, (255, 0, 0))
    screen.blit(score_text, (10, 10))
    screen.blit(lives_text, (10, 50))
    screen.blit(level_text, (10, 90))

    pygame.display.flip()
    clock.tick(FPS)

conn.close()
pygame.quit()
sys.exit()
