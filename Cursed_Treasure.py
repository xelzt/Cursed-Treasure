import pygame
import os
import time
import random
from pygame import mixer
import button


#LINKI
# https://rvros.itch.io/animated-pixel-hero - GŁÓWNY BOHATER
# https://astrobob.itch.io/arcane-archer - ŁUCZNICY
# https://jesse-m.itch.io/skeleton-pack - SZKIELETY
# https://alexs-assets.itch.io/16x16-rpg-item-pack - ITEM PACK

mixer.init()
pygame.init()


SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Cursed Treasure')

#ŁADOWANIE MUZYKI I EFEKTÓW DŹWIĘKOWYCH

arrow_sound = pygame.mixer.Sound('audio/arrow_sound.flac')
arrow_sound.set_volume(0.7)

archer_death = pygame.mixer.Sound('audio/archer_death.mp3')
archer_death.set_volume(0.2)

hit_sound = pygame.mixer.Sound('audio/hit02.mp3.flac')
hit_sound.set_volume(0.2)

boost_effect = pygame.mixer.Sound('audio/boost_effect.mp3')

skeleton_hit = pygame.mixer.Sound('audio/axe.mp3')
skeleton_death = pygame.mixer.Sound('audio/skeleton_death.mp3')
skeleton_death.set_volume(0.4)

reward_effect = pygame.mixer.Sound('audio/reward.wav')
reward_effect.set_volume(0.3)

get_star_effect = pygame.mixer.Sound('audio/get_star.mp3')
get_star_effect.set_volume(0.3)

potion_effect = pygame.mixer.Sound('audio/potion_effect.mp3')
potion_effect.set_volume(0.4)

evil_laugh = pygame.mixer.Sound('audio/laugh.mp3')
evil_laugh.set_volume(0.2)

#OBRAZ PLATFORM
list_of_platforms = []
num_of_frames = len(os.listdir(f"images/Platform"))
for i in range(num_of_frames):
    img = pygame.image.load(f"images/Platform/platform{i}.png").convert_alpha()
    list_of_platforms.append(img)

#OBRAZY ITEMÓW
list_of_items = []
num_of_frames = len(os.listdir(f"images/Items"))
for i in range(num_of_frames):
    img = pygame.image.load(f"images/Items/item{i}.png").convert_alpha()
    list_of_items.append(img)

#OBRAZY PRZYCISKÓW
in_button = pygame.image.load('images/start_button.png').convert_alpha()
out_button = pygame.image.load('images/stop_button.png').convert_alpha()


#USTAWIANIE FRAMERATE
clock = pygame.time.Clock()
FPS = 60

#ZDEFINIOWANE WARUNKI GRY
GRAVITY = 0.75
start_game = False
restart_game = False

#DEFINIOWANIE AKCJI GRACZA
moving_left = False
moving_right = False
hitting = False

#TŁO
BG = pygame.image.load("images/Background/Background.png").convert()


def draw_bg():
    screen.blit(BG, (0, 0))



#------------------KLASA GRACZA-------------------------------
class Warrior(pygame.sprite.Sprite):
    def __init__(self, char_type, x, y, scale, speed):
        pygame.sprite.Sprite.__init__(self)
        self.alive = True
        self.char_type = char_type
        self.speed = speed
        self.health = 100
        self.max_health = self.health
        self.hit_cooldown = 0
        self.boost_cooldown = 0
        self.points = 0
        self.stars = 0
        self.throw_status = False
        self.direction = 1
        self.vel_y = 0
        self.animation_list = []
        self.frame_index = 0
        self.action = 0
        self.items = {}
        self.update_time = pygame.time.get_ticks()

        #ŁADUJEMY OBRAZY GRACZA
        animation_types = ['Idle', 'Run', 'Jump', 'Hit', 'Death']
        for animation in animation_types:
            temp_list = []
            num_of_frames = len(os.listdir(f"images/{self.char_type}/{animation}"))
            for i in range(num_of_frames):
                img = pygame.image.load(f"images/{self.char_type}/{animation}/adventure_0{i}.png").convert_alpha()
                img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
                temp_list.append(img)
            self.animation_list.append(temp_list)

        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)


        self.jump = False
        self.in_air = True
        self.flip = False
        self.level = None
        self.dx = 0
        self.dy = 0


    def update(self):
        self.update_animation()
        self.check_alive()
        #AKTUALIZACJA COOLDOWNU
        if self.hit_cooldown > 0:
            self.hit_cooldown -= 1

        if self.boost_cooldown > 0:
            self.boost_cooldown -= 1
        elif self.boost_cooldown == 0:
            self.speed = 5

        # wykrywamy kolizje z przedmiotami
        colliding_items = pygame.sprite.spritecollide(self, self.level.set_of_items, False)

        for item in colliding_items:
            if item.name == "life":
                potion_effect.play()
                if self.health <=80:
                    self.health += 20
                    item.kill()
                else:
                    self.health = 100
                    item.kill()

            if item.name == 'boost':
                boost_effect.play()
                self.boost_cooldown = 100
                self.speed = 8
                item.kill()

            if item.name == 'jewell':
                reward_effect.play()
                self.points += 100
                item.kill()

            if item.name == 'star':
                get_star_effect.play()
                self.stars += 1
                item.kill()

            if item.name == 'graal':
                pygame.mixer.music.fadeout(5000)
                evil_laugh.play()
                player.alive = False
                item.kill()
                self.update_action(4)



    #PORUSZANIE SIĘ W LEWO
    def turn_left(self):
        self.dx = -self.speed
        self.flip = True
        self.direction = -1

    #PORUSZANIE SIĘ W PRAWO
    def turn_right(self):
        self.dx = self.speed
        self.flip = False
        self.direction = 1

    #SKAKANIE
    def jump_logic(self):
        self.vel_y = -17
        self.jump = False
        self.in_air = True


    #UDERZEENIE MIECZEM
    def hit(self):
        if self.hit_cooldown == 0:
            hit_sound.play()
            self.hit_cooldown = 40
            self.update_action(3)
            hit = Hit(self.rect.centerx + (self.rect.size[0] * 0.3 * self.direction), self.rect.centery,
                      self.direction, 90, 80)
            hit_group.add(hit)

    #RZUCANIE GWIAZDKAMI
    def throw(self):
        if self.stars > 0:
            s = Shoot(list_of_items[6], self.rect.centerx, self.rect.centery, self.direction, 10)
            hit_group.add(s)
            self.stars -= 1
            self.throw_status = False
            if pygame.sprite.spritecollide(s,current_level.set_of_enemies, True):
                s.kill()


    #DZIAŁANIE GRAWITACJI
    def gravity(self):
        self.vel_y += GRAVITY
        if self.vel_y > 10:
            self.vel_y = 10
        self.dy += self.vel_y

    def move(self, moving_left, moving_right):
        #RESETOWANIE WARTOŚCI RUCHU
        self.dx = 0
        self.dy = 0

        #SPRAWDZENIE CZY GRACZ PORUSZA SIĘ W LEWO LUB W PRAWO
        if moving_left:
            self.turn_left()
        elif moving_right:
            self.turn_right()

        #SKAKANIE
        if self.jump == True and self.in_air == False:
            self.jump_logic()

        #URUCHOMIENIE GRAWITACJI
        self.gravity()


        #AKTUALIZACJA POŁOŻENIA GRACZA

        #PORUSZANIE SIĘ I KOLIZJA Z PLATFORMAMI W PIONIE
        self.rect.x += self.dx

        colliding_platforms = pygame.sprite.spritecollide(self, player.level.set_of_platforms, False)
        for p in colliding_platforms:
            if self.dx > 0:
                self.rect.right = p.rect.left
                if self.dx == 0:
                    self.update_action(0)
            if self.dx < 0:
                self.rect.left = p.rect.right


        #PORUSZANIE SIĘ I KOLIZJA Z PLATFOMAMI W POZIOMIE
        self.rect.y += self.dy
        colliding_platforms = pygame.sprite.spritecollide(self, self.level.set_of_platforms, False)
        for p in colliding_platforms:
            if self.dy > 0:
                self.rect.bottom = p.rect.top
                self.in_air = False
            if self.dy < 0:
                self.rect.top = p.rect.bottom
                self.dy = 0

        if self.rect.y > SCREEN_HEIGHT:
            self.health = 0
            self.alive = False

    def update_animation(self):
        #AKTUALIZACJA COOLDOWNU
        ANIMATION_COOLDOWN = 115
        #AKTUALIZACJA OBRAZU ZALEŻNIE OD DANEJ KLATKI
        self.image = self.animation_list[self.action][self.frame_index]
        #SPRAWDZENIE CZY UPŁYNĘŁA WYSTARCZAJĄCA ILOŚĆ CZASU OD OSTATNIEJ AKTUALIZACJI
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
            #JEŚLI ANIMACJA SIĘ SKOŃCZYŁA RESETUJEMY I ZACZYNAMY OD NOWA
            if self.frame_index >= len(self.animation_list[self.action]):
                if self.action == 4 or self.action == 2:
                    self.frame_index = len(self.animation_list[self.action]) - 1
                else:
                    self.frame_index = 0

    def update_action(self, new_action):
        #SPRAWDZANIE CZY AKCJA JEST INNA OD TRWAJĄCEJ
        if new_action != self.action:
            self.action = new_action
            #UPDATOWANIE INFORMACJI
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def check_alive(self):
        if self.health <= 0:
            pygame.mixer.music.fadeout(10000)
            self.health = 0
            self.speed = 0
            self.alive = False
            self.update_action(4)

    def draw(self):
        screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)
        # pygame.draw.rect(screen, (0,0,0), self.rect, 2)

#------------------KLASA PASKA ŻYCIA--------------------------
class LifeBar():
    def __init__(self, x, y, health, max_health):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = max_health

    def draw(self, health):
        self.health = health
        #OBLICZANIE ILE JEST ŻYCIA
        ratio = self.health / self.max_health
        pygame.draw.rect(screen, (0,0,0), (self.x - 2, self.y - 2, 204, 24))
        pygame.draw.rect(screen, (57, 57, 57), (self.x, self.y, 200, 20))
        pygame.draw.rect(screen, (240, 5, 5), (self.x, self.y, 200 * ratio, 20))


#------------------KLASA UDERZENIA----------------------------
class Hit(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, height_range, width_range):
        super().__init__()
        self.image = pygame.Surface([width_range, height_range], pygame.SRCALPHA)
        self.speed = 0
        self.rect = self.image.get_rect()
        self.rect.center = [x, y + 2]
        self.direction = direction
        self.spawned_time = time.time()

    def update(self):
        #KASOWANIE CIOSU PO CHWILI
        if time.time() > self.spawned_time + 0.2:
            self.kill()
        elif pygame.sprite.groupcollide(hit_group, current_level.set_of_enemies, False, False):
            self.kill()
        elif pygame.sprite.spritecollide(player, current_level.set_of_hits, False):
            self.kill()
            player.health -= 10


#------------------OGÓLNA KLASA RZUCANIA----------------------
class Shoot(pygame.sprite.Sprite):
    def __init__(self, image, x, y, direction, speed):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction
        self.speed = speed

    def update(self):
        self.rect.x += (self.speed * self.direction)

        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()

        if pygame.sprite.spritecollide(player, current_level.set_of_hits, False):
            player.health -= 10
            self.kill()



#------------------KLASA PLATFORMY----------------------------
class Platform(pygame.sprite.Sprite):
    def __init__(self, image_list, width, height, pos_x, pos_y):
        super().__init__()
        self.image_list = image_list
        self.width = width
        self.height = height
        self.image = pygame.Surface((width, height))
        self.rect = self.image.get_rect()
        self.rect.x = pos_x
        self.rect.y = pos_y

    def draw(self, surface):
        if self.width == 70:
            surface.blit(self.image_list[1], self.rect)
        else:
            surface.blit(self.image_list[1], self.rect)
            for i in range(70, self.width - 70, 70):
                surface.blit(self.image_list[1], [self.rect.x + i, self.rect.y])
            surface.blit(self.image_list[1], [self.rect.x + self.width - 70, self.rect.y])
        # pygame.draw.rect(surface, (255, 255, 255), self.rect, 2)


#------------------OGÓLNA KLASA WROGA-------------------------
class Enemy(pygame.sprite.Sprite):
    def __init__(self, height_range, widht_range, enemy_type, cd, movement_x = 0, movement_y = 0):
        super().__init__()

        self.enemy_type = enemy_type

        self.height_range = height_range
        self.width_range = widht_range
        self.movement_x = movement_x
        self.movement_y = movement_y

        self.update_time = pygame.time.get_ticks()
        self.alive = True

        self.frame_index = 0
        self.action = 0

        self.health = 50

        self.direction = 1
        self.vision = pygame.Rect(0, 0, 150, 20)
        self.idling = False
        self.time_elapsed = 0
        self.hit_cooldown = cd

        self.frame_index = 0
        self.action = 0
        animation_types = ['Idle', 'Walk_L', 'Walk_R', 'Death', 'Attack_R', 'Attack_L']
        self.enemy_animation_list = []
        for animation in animation_types:
            temp_list = []
            num_of_frames = len(os.listdir(f"images/{self.enemy_type}/{animation}"))
            for i in range(num_of_frames):
                img = pygame.image.load(f"images/{self.enemy_type}/{animation}/animation_{i}.png").convert_alpha()
                img = pygame.transform.scale(img, (int(img.get_width() * 2), int(img.get_height() * 2)))
                temp_list.append(img)
            self.enemy_animation_list.append(temp_list)
        self.image = self.enemy_animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()


    #OTRZYMYWANIE OBRAŻEŃ
    def damage(self):
        if pygame.sprite.spritecollide(self, hit_group, False):
            self.health -= 25

    #TWORZENIE UDZERZENIA LUB STRZELANIA Z ŁUKU
    def hit(self, x):
        if self.hit_cooldown == 0:
            if self.enemy_type == "Skeleton":
                self.hit_cooldown = 90
                h = Hit(x, self.rect.centery, self.direction, self.height_range, self.width_range)
                h.add(current_level.set_of_hits)
                skeleton_hit.play()
            elif self.enemy_type == "Archer":
                arrow_sound.play()
                self.hit_cooldown = 60
                if self.direction == -1:
                    arrow = pygame.image.load("images/arrow_L.png").convert_alpha()
                    s = Shoot(arrow, self.rect.centerx, self.rect.centery, self.direction, 2)
                    s.add(current_level.set_of_hits)
                if self.direction == 1:
                    arrow = pygame.image.load("images/arrow_R.png").convert_alpha()
                    s = Shoot(arrow, self.rect.centerx, self.rect.centery, self.direction, 2)
                    s.add(current_level.set_of_hits)

    #DECYZJA JAK I KIEDY ODDAJE SIĘ CIOS LUB STRZELA
    def hit_logic(self):
        if self.alive and player.alive:
            if self.vision.colliderect(player.rect):
                if self.hit_cooldown > 0:
                    self.hit_cooldown -= 1
                self.movement_x = 0
                if self.direction == -1:
                    self.update_action(5)
                    self.hit(self.rect.centerx)
                elif self.direction == 1:
                    self.update_action(4)
                    self.hit(self.rect.centerx + 40)
            else:
                # pygame.draw.rect(screen, (0, 0, 0), self.vision)
                if self.enemy_type == "Skeleton":
                    self.hit_cooldown = 90
                self.vision.center = (self.rect.centerx + 75 * self.direction, self.rect.centery)
                if self.direction == -1:
                    self.movement_x = -2
                    self.update_action(1)
                elif self.direction == 1:
                    self.movement_x = 2
                    self.update_action(2)


    #SPRAWDZANIE CZY ENEMY ŻYJE
    def check_alive(self):
        if self.health <= 0:
            self.alive = False
            self.movement_x = 0
            self.update_action(3)

    #UPDATOWANIE ZACHOWANIA
    def update(self):
        self.check_alive()
        self.damage()
        self.update_animation()
        self.rect.x += self.movement_x


    def update_animation(self):
        #AKTUALIZACJA COOLDOWNU
        ANIMATION_COOLDOWN = 115
        #AKTUALIZACJA OBRAZU ZALEŻNIE OD DANEJ KLATKI
        self.image = self.enemy_animation_list[self.action][self.frame_index]

        #SPRAWDZENIE CZY UPŁYNĘŁA WYSTARCZAJĄCA ILOŚĆ CZASU OD OSTATNIEJ AKTUALIZACJI
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1

            if self.action == 3 and self.enemy_type == "Skeleton" and self.frame_index == 1:
                skeleton_death.play()
            elif self.action == 3 and self.enemy_type == "Archer" and self.frame_index == 1:
                archer_death.play()

            #JEŚLI ANIMACJA SIĘ SKOŃCZYŁA RESETUJEMY I ZACZYNAMY OD NOWA
            if self.frame_index >= len(self.enemy_animation_list[self.action]):
                if self.action == 3:
                    self.frame_index = len(self.enemy_animation_list[self.action]) - 1

                    if self.enemy_type == "Skeleton":
                        player.points += 10
                        self.kill()
                    elif self.enemy_type == "Archer":
                        player.points += 20
                        self.kill()
                else:
                    self.frame_index = 0



    def update_action(self, new_action):
        #SPRAWDZANIE CZY AKCJA JEST INNA OD TRWAJĄCEJ
        if new_action != self.action:
            self.action = new_action
            #UPDATOWANIE INFORMACJI
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()


#------------------PLATFORMA WROGA----------------------------
class PlatformEnemy(Enemy):
    def __init__(self, platform, height_range, width_range, enemy_type, cd, movement_x=0, movement_y=0):
        super().__init__(height_range, width_range, enemy_type, cd, movement_x, movement_y)
        self.action = 1
        self.direction = 1
        self.platform = platform
        self.rect.bottom = self.platform.rect.top
        self.rect.centerx = random.randint(self.platform.rect.left + self.rect.width//2,
                                           self.platform.rect.right - self.rect.width//2)

    def update(self):
        super().update()

        if player.alive:
            if self.rect.left < self.platform.rect.left:
                self.update_action(1)
                self.movement_x *= -1
            elif self.rect.right > self.platform.rect.right:
                self.movement_x *= -1
                self.update_action(2)

            if self.movement_x < 0:
                self.direction = -1
            elif self.movement_x > 0:
                self.direction = 1
            self.hit_logic()
        else:
            self.movement_x = 0
            self.update_action(0)

#------------------KLASA PRZEDMIOTU---------------------------
class Item(pygame.sprite.Sprite):
    def __init__(self, image, name, x, y):
        super().__init__()
        self.image = image
        self.name = name
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]


#------------------OGÓLNA KLASA POZIOMU-----------------------
class Level:
    def __init__(self, player):
        self.set_of_platforms = set()
        self.set_of_enemies = pygame.sprite.Group()
        self.set_of_arrow = pygame.sprite.Group()
        self.set_of_items = pygame.sprite.Group()
        self.set_of_hits = pygame.sprite.Group()
        self.player = player
        self.world_shift = 0


    #WYŚWIETLANIE ILOŚCI PUNKTÓW GRACZA
    def display_points(self):
        font = pygame.font.Font('freesansbold.ttf', 32)
        points = font.render("Score : " + str(player.points), True, (255, 255, 255))
        screen.blit(points, (30, 40))


    def draw(self, surface):
        for p in self.set_of_platforms:
            p.draw(surface)

        self.set_of_enemies.draw(surface)
        self.set_of_items.draw(surface)
        self.set_of_arrow.draw(surface)
        self.set_of_hits.draw(surface)


    def update(self):
        self.display_points()
        self.set_of_enemies.update()
        self.set_of_hits.update()
        if self.player.rect.right >= 1100:
            diff = self.player.rect.right - 1100
            self.player.rect.right = 1100
            self._shift_world(-diff)

        if self.player.rect.left <= 200:
            diff = 200 - self.player.rect.left
            self.player.rect.left = 200
            self._shift_world(diff)


    def _shift_world(self, shift_x):
        self.world_shift += shift_x

        for p in self.set_of_platforms:
            p.rect.x += shift_x

        for e in self.set_of_enemies:
            e.rect.x += shift_x

        for item in self.set_of_items:
            item.rect.x += shift_x

        for hits in self.set_of_hits:
            hits.rect.x += shift_x

#------------------PIERWSZY POZIOM----------------------------
class Level_1(Level):
    def __init__(self, player):
        super().__init__(player)
        self._create_platforms()
        self._create_enemy_platforms()
        self._create_items()

    def _create_platforms(self):
        ws_static_platforms = [[6*70, 70, 800, 350], [40*70, 70, -70, SCREEN_HEIGHT - 70], [2*70, 70, 2000, 500], [70, 70, 1850, 340], [70, 70, 3500, 350], [70, 70, 5330, 500], [70, 70, 5540, 450], [2*70, 70, 5300, 270], [20*70, 70, 7170, SCREEN_HEIGHT - 70], [70, 70, 8500, 580], [70, 70, 8500, 510], [70, 70, 8500, 440], [70, 70, 8500, 370], [70, 70, 8500, 300], [70, 70, 8500, 230], [70, 70, 8500, 160], [70, 70, 8500, 90], [70, 70, 8500, 20]]
        for ws in ws_static_platforms:
            p = Platform(list_of_platforms, *ws)  # *ws rozpakowanie listy
            self.set_of_platforms.add(p)

    def _create_enemy_platforms(self):
        ws_static_platforms = [[5*70, 70, 500, 500], [5*70, 70, 1000, SCREEN_HEIGHT - 210], [10 * 70, 70, 2700, 510], [10 * 70, 70, 4410, 510], [10*70, 70, 5570, 100]]
        archer_static_platforms = [[5*70, 70, 1450, 200], [6*70, 70, 2500, SCREEN_HEIGHT - 70], [6*70, 70, 3860, 600], [9*70, 70, 6340, 360]]
        for ws in ws_static_platforms:
            p = Platform(list_of_platforms, *ws)
            self.set_of_platforms.add(p)
            pe = PlatformEnemy(p,50, 50, "Skeleton", 0, 2, 0)
            self.set_of_enemies.add(pe)

        for ws in archer_static_platforms:
            p = Platform(list_of_platforms, *ws)
            self.set_of_platforms.add(p)
            pe = PlatformEnemy(p,50, 50, "Archer", 0, 2, 0)
            self.set_of_enemies.add(pe)


    def _create_items(self):
        boost = Item(list_of_items[3], 'boost', 600, 475)
        self.set_of_items.add(boost)

        boost = Item(list_of_items[3], 'boost', 3950, 550)
        self.set_of_items.add(boost)

        life = Item(list_of_items[0], 'life', 1100, 488)
        self.set_of_items.add(life)

        life = Item(list_of_items[0], 'life', 4550, 475)
        self.set_of_items.add(life)

        jewell = Item(list_of_items[5], 'jewell', 900, 300)
        self.set_of_items.add(jewell)

        jewell = Item(list_of_items[5], 'jewell', 1500, 150)
        self.set_of_items.add(jewell)

        star = Item(list_of_items[6], 'star', 1600, 150)
        self.set_of_items.add(star)

        star = Item(list_of_items[6], 'star', 2100, 450)
        self.set_of_items.add(star)

        star = Item(list_of_items[6], 'star', 6440, 325)
        self.set_of_items.add(star)

        graal = Item(list_of_items[7], 'graal', 8400, SCREEN_HEIGHT - 110)
        self.set_of_items.add(graal)



#GRUPY SPRITE
hit_group = pygame.sprite.Group()
player = Warrior("Player", 200, 200, 1.2, 5)
current_level = Level_1(player)
player.level = current_level
health_bar = LifeBar(10, 10, player.health, player.health)

#PRZYCISKI
start_button = button.Button(SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2.5 , in_button, 0.52)
exit_button = button.Button(SCREEN_WIDTH // 4 + 450, SCREEN_HEIGHT // 2.37, out_button, 0.72)

running = True
while running:
    dt = clock.tick()
    clock.tick(FPS)
    if start_game == False:
        #MENU GŁÓWNE GRY

        #RYSOWANIE MENU GŁÓWNEGO
        screen.fill((57,57,57))
        #DODANIE PRZYCISKÓW
        if start_button.draw(screen):
            start_game = True
            pygame.mixer.music.load('audio/bg_music.mp3')
            pygame.mixer.music.set_volume(0.3)
            pygame.mixer.music.play(3, 0.0)
        if exit_button.draw(screen):
            running = False

    else:


        draw_bg()
        current_level.update()
        current_level.draw(screen)
        player.update()
        player.draw()
        health_bar.draw(player.health)


        #AKTUALIZACJA I RYSOWANIE UDERZEŃ
        hit_group.update()
        hit_group.draw(screen)


        #AKTUALIZACJA ANIMACJI GRACZA
        if player.alive:
            if hitting:
                player.hit()
            elif player.in_air:
                player.update_action(2) # 2 TO SKAKANIE
            elif moving_left or moving_right:
                player.update_action(1)  # 1 TO CHODZENIE W PRAWO
            elif player.throw_status:
                player.throw()
            else:
                player.update_action(0)  # 0 TO ODPOCZYWANIE
            player.move(moving_left, moving_right)


    for event in pygame.event.get():
        #WYCHODZENIE Z GRY
        if event.type == pygame.QUIT:
            running = False

        #SPRAWDZENIE EVENTÓW, PRZYCISKI WCIŚNIĘTE
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                moving_left = True
            if event.key == pygame.K_d:
                moving_right = True
            if event.key == pygame.K_f:
                hitting = True
            if event.key == pygame.K_e and player.stars > 0:
                player.throw_status = True
            if event.key == pygame.K_SPACE and player.alive:
                player.jump = True
            if event.key == pygame.K_ESCAPE:
                running = False

        #PRZYCISKI PUSZCZONE
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_a:
                moving_left = False
            if event.key == pygame.K_d:
                moving_right = False
            if event.key == pygame.K_f:
                hitting = False

    pygame.display.update()