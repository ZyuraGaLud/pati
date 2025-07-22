import pygame
import random
import math
import colorsys 

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)


pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("パチ")
clock = pygame.time.Clock()
font_small = pygame.font.Font(None, 36)
font_large = pygame.font.Font(None, 72)


class Ball(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((10, 10))
        self.image.fill(WHITE)
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.top = 0
        self.position = pygame.math.Vector2(self.rect.centerx, self.rect.centery)
        self.velocity = pygame.math.Vector2(random.uniform(-3, 3), 0)
        self.gravity = pygame.math.Vector2(0, 0.5)
        self.elasticity = 0.7

    def update(self):
        self.velocity += self.gravity
        self.position += self.velocity
        self.rect.center = (int(self.position.x), int(self.position.y))

        if self.rect.left < 0 or self.rect.right > SCREEN_WIDTH:
            self.velocity.x *= -1 * self.elasticity
            if self.rect.left < 0:
                self.position.x = self.rect.width / 2
            if self.rect.right > SCREEN_WIDTH:
                self.position.x = SCREEN_WIDTH - self.rect.width / 2

        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

class Pin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((8, 8))
        self.image.fill(BLUE)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.radius = self.rect.width // 2

class Pocket(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, is_big_win_pocket=False):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(RED if not is_big_win_pocket else GREEN)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.is_big_win_pocket = is_big_win_pocket

# --- 衝突処理関数 ---
def collide_ball_pin(ball, pin):
    distance_vec = ball.position - pygame.math.Vector2(pin.rect.center)
    distance = distance_vec.length()

    if distance < ball.rect.width / 2 + pin.radius:
        overlap = (ball.rect.width / 2 + pin.radius) - distance
        if distance != 0:
            ball.position += distance_vec.normalize() * overlap

        normal = distance_vec.normalize()
        incident_vector = ball.velocity
        reflected_vector = incident_vector - 2 * incident_vector.dot(normal) * normal
        ball.velocity = reflected_vector * ball.elasticity
        return True
    return False

all_sprites = pygame.sprite.Group()
balls = pygame.sprite.Group()
pins = pygame.sprite.Group()
pockets = pygame.sprite.Group()

for row in range(15):
    for col in range(15):
        x = 50 + col * 45 + (row % 2) * 22.5
        y = 50 + row * 30
        pin = Pin(x, y)
        all_sprites.add(pin)
        pins.add(pin)

pocket_width = 80
pocket_height = 20
num_pockets = 5
pocket_spacing = (SCREEN_WIDTH - pocket_width * num_pockets) // (num_pockets + 1)
big_win_pocket_index = random.randint(0, num_pockets - 1)

for i in range(num_pockets):
    x = pocket_spacing * (i + 1) + pocket_width * i
    is_big_win = (i == big_win_pocket_index)
    pocket = Pocket(x, SCREEN_HEIGHT - 50, pocket_width, pocket_height, is_big_win)
    all_sprites.add(pocket)
    pockets.add(pocket)

score = 0

GAME_STATE_NORMAL = 0
GAME_STATE_BIG_WIN = 1
game_state = GAME_STATE_NORMAL

# 大当たり関連変数
big_win_start_time = 0
BIG_WIN_DURATION = 7000 # 7秒

ball_spawn_timer = 0
BALL_SPAWN_INTERVAL_NORMAL = 30
BALL_SPAWN_INTERVAL_BIG_WIN = 5

# --- 大当たりメッセージリスト ---
BIG_WIN_MESSAGES = [
    "yuki die",
    "sukisoudana",
    "nanisitennno",
    "LOSER",
    "CSC die",
]
current_big_win_message = "" # 現在表示するメッセージ

rainbow_hue = 0.0 # 0.0から1.0までの色相


running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.K_SPACE:
            new_ball = Ball()
            all_sprites.add(new_ball)
            balls.add(new_ball)

    ball_spawn_timer += 1
    current_spawn_interval = BALL_SPAWN_INTERVAL_NORMAL

    if game_state == GAME_STATE_BIG_WIN:
        current_spawn_interval = BALL_SPAWN_INTERVAL_BIG_WIN

    if ball_spawn_timer >= current_spawn_interval:
        new_ball = Ball()
        all_sprites.add(new_ball)
        balls.add(new_ball)
        ball_spawn_timer = 0

    # スプライトの更新
    all_sprites.update()

    # 玉とピンの衝突判定
    for ball in balls:
        for pin in pins:
            collide_ball_pin(ball, pin)

        # 入賞口との衝突
        hit_pockets = pygame.sprite.spritecollide(ball, pockets, False)
        for pocket in hit_pockets:
            score += 1
            ball.kill()

            if pocket.is_big_win_pocket and game_state == GAME_STATE_NORMAL:
                print("大当たり！")
                game_state = GAME_STATE_BIG_WIN
                big_win_start_time = pygame.time.get_ticks()
                current_big_win_message = random.choice(BIG_WIN_MESSAGES) 

    if game_state == GAME_STATE_BIG_WIN:
        current_time = pygame.time.get_ticks()


        rainbow_hue = (current_time / 1000.0 * 0.1) % 1.0 
        r, g, b = colorsys.hsv_to_rgb(rainbow_hue, 1.0, 1.0) 
        background_color = (int(r * 255), int(g * 255), int(b * 255))
        screen.fill(background_color) 

        if current_time - big_win_start_time > BIG_WIN_DURATION:
            game_state = GAME_STATE_NORMAL
            print("大当たり終了")
    else:
        screen.fill(BLACK)

    all_sprites.draw(screen)


    score_text = font_small.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (10, 10))


    if game_state == GAME_STATE_BIG_WIN:
        big_win_message_rendered = font_large.render(current_big_win_message, True, BLACK) # メッセージは黒字に
        message_rect = big_win_message_rendered.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(big_win_message_rendered, message_rect)


    pygame.display.flip()


    clock.tick(FPS)

pygame.quit()