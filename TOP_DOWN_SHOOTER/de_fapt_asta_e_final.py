import pygame
import sys
import math
import random

# Inițializare Pygame și configurare ecran, fonturi, etc.
pygame.init()
WIDTH, HEIGHT = 800, 600
display = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 24)
big_font = pygame.font.SysFont("Arial", 72)
small_font = pygame.font.SysFont("Arial", 36)

# Încărcare imagini pentru animația jucătorului și imaginea armei
player_walk_images = [pygame.image.load(f"player_walk_{i}.png") for i in range(4)]
player_weapon = pygame.image.load("shotgun.png").convert()
player_weapon.set_colorkey((255, 255, 255))  # Setare culoare transparentă pentru armă

# Funcție utilitară pentru afișarea unui text centrat pe ecran
def draw_center_text(text, size=72, color=(255, 255, 255), y_offset=0):
    font_obj = pygame.font.SysFont("Arial", size)
    txt = font_obj.render(text, True, color)
    rect = txt.get_rect(center=(WIDTH // 2, HEIGHT // 2 + y_offset))
    display.blit(txt, rect)

# Clasa principală a jucătorului - poziție, viață, mișcare, arme, inventar
class Player:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.width, self.height = 32, 32
        self.hp = 10
        self.max_hp = 10
        self.speed = 5
        self.cooldown = 500
        self.last_shot = 0
        self.inventory = []
        self.shield_active = False
        self.shield_timer = 0
        self.anim_count = 0
        self.moving_right = False
        self.moving_left = False

    # Mișcarea jucătorului pe baza tastelor WASD
    def move(self, keys):
        if keys[pygame.K_a]: self.x -= self.speed; self.moving_left = True
        if keys[pygame.K_d]: self.x += self.speed; self.moving_right = True
        if keys[pygame.K_w]: self.y -= self.speed
        if keys[pygame.K_s]: self.y += self.speed

    # Desenarea jucătorului (inclusiv animație, armă, viață, inventar, scut)
    def draw(self):
        img = player_walk_images[self.anim_count//4]
        if self.moving_left:
            img = pygame.transform.flip(img, True, False)
        display.blit(pygame.transform.scale(img, (32, 42)), (self.x, self.y))
        self.draw_weapon()
        self.draw_hp()
        self.draw_inventory()
        if self.shield_active:
            pygame.draw.circle(display, (0,255,255), (self.x + 16, self.y + 16), 25, 2)
        self.moving_right = self.moving_left = False
        self.anim_count = (self.anim_count + 1) % 16

    # Desenarea armei rotite spre cursorul mouse-ului
    def draw_weapon(self):
        mx, my = pygame.mouse.get_pos()
        angle = math.degrees(-math.atan2(my - self.y, mx - self.x))
        rotated = pygame.transform.rotate(player_weapon, angle)
        display.blit(rotated, (self.x + 15 - rotated.get_width()//2, self.y + 25 - rotated.get_height()//2))

    # Desenarea barei de viață deasupra jucătorului
    def draw_hp(self):
        pygame.draw.rect(display, (255,0,0), (self.x, self.y - 10, 32, 5))
        pygame.draw.rect(display, (0,255,0), (self.x, self.y - 10, 32 * self.hp / self.max_hp, 5))

    # Desenarea inventarului jos pe ecran
    def draw_inventory(self):
        for i, item in enumerate(self.inventory):
            pygame.draw.rect(display, (50, 50, 50), (10 + i*60, 540, 50, 50))
            pygame.draw.rect(display, (255,255,255), (10 + i*60, 540, 50, 50), 2)
            txt = font.render(item["name"], True, (255,255,0))
            display.blit(txt, (12 + i*60, 550))

    # Verifică dacă jucătorul poate trage în funcție de cooldown
    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot >= self.cooldown:
            self.last_shot = now
            return True
        return 

    # Aplică un upgrade jucătorului în funcție de alegerea făcută
    def apply_upgrade(self, code):
        if code == "hp":
            self.max_hp += 2
            self.hp = self.max_hp
        elif code == "speed":
            self.speed += 0.5
        elif code == "cd":
            self.cooldown = max(100, self.cooldown - 50)

    # Adaugă un item în inventar
    def add_item(self, item):
        if len(self.inventory) < 3:
            self.inventory.append(item)

    # Folosește un item din inventar (ex. activează scutul)
    def use_item(self, index):
        if index < len(self.inventory):
            item = self.inventory.pop(index)
            if item["name"] == "Scut":
                self.shield_active = True
                self.shield_timer = pygame.time.get_ticks()

    # Returnează un "dreptunghi de coliziune" al jucătorului
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

# Proiectil tras de jucător, se deplasează în direcția cursorului
class Bullet:
    def __init__(self, x, y, mx, my):
        angle = math.atan2(y - my, x - mx)
        self.x, self.y = x, y
        self.vx, self.vy = math.cos(angle)*15, math.sin(angle)*15

    def update(self):
        self.x -= self.vx
        self.y -= self.vy
        pygame.draw.circle(display, (0,0,0), (int(self.x), int(self.y)), 5)

# Clasa inamicilor (Slime și Boss), se mișcă spre jucător și au animație
class Slime:
    def __init__(self, x, y, boss=False):
        self.x, self.y = x, y
        self.hp = 3 if not boss else 15
        self.max_hp = self.hp
        self.speed = 1 if not boss else 0.6
        self.size = 32 if not boss else 64
        self.anim = [pygame.transform.scale(pygame.image.load(f"slime_animation_{i}.png"), (self.size,self.size)) for i in range(4)]
        self.anim_count = 0

    def update(self, player):
        dx, dy = player.x - self.x, player.y - self.y
        dist = max(1, math.hypot(dx, dy))
        self.x += dx / dist * self.speed
        self.y += dy / dist * self.speed
        display.blit(self.anim[self.anim_count//4], (self.x, self.y))
        self.draw_hp_bar()
        self.anim_count = (self.anim_count + 1) % 16

    def draw_hp_bar(self):
        bar_w = self.size
        bar_h = 5
        fill = bar_w * self.hp / self.max_hp
        pygame.draw.rect(display, (255, 0, 0), (self.x, self.y - 10, bar_w, bar_h))
        pygame.draw.rect(display, (0, 255, 0), (self.x, self.y - 10, fill, bar_h))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.size, self.size)

# Creează o listă de inamici pentru un anumit nivel (include boss pe nivele multiplu de 3)
def spawn_enemies(level):
    enemies = [Slime(random.randint(0, 700), random.randint(0, 500)) for _ in range(level*2)]
    if level % 3 == 0:
        enemies.append(Slime(400, 100, True))
    return enemies

# Returnează un item aleator (momentan doar "Scut")
def random_item():
    return {"name": "Scut"}

# Meniu de upgrade după trecerea unui nivel
def upgrade_menu():
    while True:
        display.fill((0,0,0))
        draw_center_text("Alege un upgrade:", 48, (255,255,255), -50)
        draw_center_text("1) +2 HP     2) +Viteză     3) -Cooldown", 36, (255,255,255), 30)
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1: return "hp"
                if event.key == pygame.K_2: return "speed"
                if event.key == pygame.K_3: return "cd"

# Afișează meniul de start
def show_start_menu():
    while True:
        display.fill((10,10,40))
        draw_center_text("TOP-DOWN SHOOTER", 72, (255,255,0), -100)
        draw_center_text("Apasă SPACE pentru a începe", 36, (255,255,255), 20)
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                return

# Afișează tranziția între nivele
def show_level_transition(level):
    display.fill((0,0,0))
    draw_center_text(f"Nivelul {level}", 64, (255,255,255))
    pygame.display.update()
    pygame.time.delay(2000)

# Ecranul final când jucătorul pierde
def game_over_screen():
    display.fill((0,0,0))
    draw_center_text("GAME OVER", 72, (255,0,0))
    pygame.display.update()
    pygame.time.delay(3000)

# =======================
# LOOP PRINCIPAL AL JOCULUI
# =======================
show_start_menu()
player = Player(400, 300)
bullets = []
level = 1
score = 0
enemies = spawn_enemies(level)
show_level_transition(level)

while True:
    display.fill((24,164,86))
    keys = pygame.key.get_pressed()

    # Gestionarea evenimentelor de intrare
    for e in pygame.event.get():
        if e.type == pygame.QUIT: pygame.quit(); sys.exit()
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and player.shoot():
            bullets.append(Bullet(player.x, player.y, *pygame.mouse.get_pos()))
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_1: player.use_item(0)
            if e.key == pygame.K_2: player.use_item(1)
            if e.key == pygame.K_3: player.use_item(2)

    player.move(keys)
    player.draw()

    # Dezactivare scut după 5 secunde
    if player.shield_active and pygame.time.get_ticks() - player.shield_timer > 5000:
        player.shield_active = False

    # Actualizare gloanțe
    for b in bullets[:]:
        b.update()
        if not (0 <= b.x <= WIDTH and 0 <= b.y <= HEIGHT): bullets.remove(b)

    # Actualizare inamici și verificare coliziuni
    for s in enemies[:]:
        s.update(player)
        if player.get_rect().colliderect(s.get_rect()) and not player.shield_active:
            player.hp -= 0.1
        for b in bullets[:]:
            if s.get_rect().collidepoint(b.x, b.y):
                s.hp -= 1
                bullets.remove(b)
                if s.hp <= 0:
                    enemies.remove(s)
                    score += 100 if s.size < 64 else 500
                    if random.random() < 0.2:
                        player.add_item(random_item())
                break

    # Trecere la următorul nivel
    if not enemies:
        level += 1
        code = upgrade_menu()
        player.apply_upgrade(code)
        enemies = spawn_enemies(level)
        show_level_transition(level)

    # Afișare scor și nivel
    display.blit(font.render(f"Nivel: {level}", True, (255,255,255)), (10, 10))
    display.blit(font.render(f"Scor: {score}", True, (255,255,0)), (10, 40))

    # Verificare Game Over
    if player.hp <= 0:
        game_over_screen()
        pygame.quit(); sys.exit()

    clock.tick(60)
    pygame.display.update()
