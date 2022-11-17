from time import sleep

import pygame, csv
from math import *
from random import*
from pygame import *


class Map():
    '''
    Class Correspondant à la map du jeu
    '''
    def __init__(self, level, screen, TILE_SIZE):
        '''
        Fonction initialisant la carte du jeu
        :param level: nom du fichier contenant le niveau
        :param screen: Display pygame
        :param TILE_SIZE: taille des textures de la map
        '''

        self.TILE_SIZE = TILE_SIZE
        self.TILE_TYPES = 75
        self.screen = screen
        self.background = pygame.image.load('Assets/bg/0.png')
        self.tile_img_list = []
        # Chargement de toute les textures du jeu
        for x in range(self.TILE_TYPES):
            img = pygame.image.load(f'Assets/Tiles/{x}.png').convert_alpha()
            img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
            self.tile_img_list.append(img)

        # Récupération du niveau à partir du fichier txt
        self.world_data = []
        for row in range(29):
            r = [-1] * 312
            self.world_data.append(r)
        with open(f'Levels/level{level}_data.txt', newline='') as txtfile:
            reader = csv.reader(txtfile, delimiter=',')
            for x, row in enumerate(reader):
                for y, tile in enumerate(row):
                    self.world_data[x][y] = int(tile)

    def set_mobs(self, ennemi_groupe):
        '''

        :param ennemi_groupe: le groupe de Sprite allant contenir les ennemis
        :return: le groupe de Spritte avec tout les ennemis
        '''
        y = 0
        #Parcour la liste conteant le niveau et ajoute un ennemis dans le groupe des ennemis a chaque fois qu'il y en a sur la carte
        for row in self.world_data:
            x = 0
            for tile in row:
                if tile == 75:
                    ennemi_groupe.add(Ennemi(20, 2, x * self.TILE_SIZE, y * self.TILE_SIZE, False))
                if tile == 76:
                    ennemi_groupe.add(Ennemi(20, 2, x * self.TILE_SIZE, y * self.TILE_SIZE, True))
                x += 1
            y += 1
        return ennemi_groupe

    def update(self, scroll):
        '''

        :param scroll: ENtier représentant le déplacement du fond relativement au déplacement du joeur
        :return: liste des textures à afficher ansi que la texture correspondante à la fin du niveau
        '''
        self.screen.fill((146, 244, 255))
        self.screen.blit(self.background, (0 - scroll[0] * 0.15, -200 - scroll[1] * 0.15))
        self.tile_rects = [] #Liste des textures présente dans le nievau
        self.end = [] #Liste des textures correspondante à la fin du niveau

        #Affichage des différentes textures du niveau sur l'écran
        y = 0
        for row in self.world_data:
            x = 0
            for tile in row:
                if tile != -1 and tile < 75:
                    self.screen.blit(self.tile_img_list[int(tile)],
                                     (x * self.TILE_SIZE - scroll[0], y * self.TILE_SIZE - scroll[1]))
                if tile != -1 and tile != 22 and tile < 75:
                    self.tile_rects.append(
                        pygame.Rect(x * self.TILE_SIZE, y * self.TILE_SIZE, self.TILE_SIZE, self.TILE_SIZE))
                if tile == 22:
                    self.end.append(pygame.Rect(x*self.TILE_SIZE, y * self.TILE_SIZE, self.TILE_SIZE, self.TILE_SIZE))
                x += 1
            y += 1

        return self.tile_rects, self.end


class Animations():
    '''
    Class correpondant à la gestion des animations
    '''

    def __init__(self):
        '''
        initalisation des animations
        '''
        global animation_frames
        self.animation_frames = {}

    def load_animation(self, path, frame_durations):
        '''
        Charge les différentes aniamtions en récupérents les textures correpondantes
        :param path: chemin d'accès au testures de l'animatiuon en question
        :param frame_durations: tableau contenant la durée de chaque testure pendant l'animations
        :return: tableau contenant les textures des aniamtions
        '''


        animation_name = path.split('/')[-1]
        animation_frame_data = []
        n = 0
        for frame in frame_durations:
            # Chargement des différentes textures corrpondante au animations
            animation_frame_id = animation_name + '_' + str(n)
            img_loc = path + "/" + animation_frame_id + '.png'
            animation_image = pygame.image.load(img_loc)
            self.animation_frames[animation_frame_id] = animation_image.copy()
            for i in range(frame):
                animation_frame_data.append(animation_frame_id)
            n += 1
        return animation_frame_data

    def change_action(self, action_var, frame, new_value):
        '''

        :param action_var: l'action actuelle
        :param frame: l'index de la frame actuelle
        :param new_value: nouvelle action
        :return: la nouvelle et sa frame
        '''
        if action_var != new_value:
            action_var = new_value
            frame = 0
        return action_var, frame


class Player(pygame.sprite.Sprite):

    '''
    Class correpondant au Joueur
    '''

    def __init__(self, health, lives, attack, nbr_grenade, nbr_ammo):
        '''
        Initialisation du joueur
        :param health: nombre de points de vie
        :param lives: nombre de vies
        :param attack: Valeur des dégats fait par le joueur au ennemis
        :param nbr_grenade: nombre de grenade que possède le joueur
        :param nbr_ammo: nombre de munition que possède le joueur
        '''
        super().__init__()
        # Chargement des différentes ressources
        self.player_img = pygame.image.load('Assets/Characters/Player/idle/idle_0.png')
        self.heart = pygame.image.load('Assets/life.gif')
        self.shoot_sound = pygame.mixer.Sound('Assets/Sounds/tir.wav')
        self.shoot_sound.set_volume(0.01)
        self.grenade_img = pygame.image.load('Assets/grenade/grenade_0.png')
        self.player_box = self.player_img.get_rect()
        self.myFont = pygame.font.SysFont("Arial", 14)
        self.health = health
        self.health_bar_under = pygame.Surface((20, 2))
        self.attack = attack
        self.lives = lives
        self.nbr_grenade = nbr_grenade
        self.nbr_ammo = nbr_ammo
        self.win = False

    def setLocation(self, x, y):
        '''
        Dénition de la posiution du joueur
        :param x: coordonnée horizontale
        :param y: coordonnée Verticale
        '''
        self.player_box.y = y
        self.player_box.x = x

    def move(self, movement, tile_rects, map, ennemis, end):
        '''
        Déplace le joeur et vérifie les collisions
        :param movement: Tableau contenant les mouvement du joeur selon l'axe x et y
        :param tile_rects: Tableau contenant tous les élèments de la map
        :param map: objet correpondant à la carte
        :param ennemis: groupe de sprite contenant les ennemis
        :param end: groupe de sprite contenant les textures correpondante à la fin du jeu
        :return: retourne le groupe contenant les ennemis
        '''
        self.movement = movement
        self.tiles = tile_rects
        self.collision_types = {'top': False, 'bottom': False, 'right': False, 'left': False}

        # Vérifie si le joeur n'a pas atteint la limte de la map puis le deplace selon l'axe x
        if self.player_box.x > 399:
            self.player_box.x += self.movement[0]
        else:
            self.player_box.x += 1

        # Vérifie si le joueur est entré en colision avec un élèment sur l'axe x
        hit_list = []
        for tile in self.tiles:
            if self.player_box.colliderect(tile):
                hit_list.append(tile)

        # Vérifie si la colision a lieu à gauche ou à droite et déplace le joueur en fonction
        for tile in hit_list:
            if self.movement[0] > 0:
                self.player_box.right = tile.left
                self.collision_types['right'] = True
            elif self.movement[0] < 0:
                self.player_box.left = tile.right
                self.collision_types['left'] = True

        # Déplace le joueur sur l'axe Y
        self.player_box.y += self.movement[1]

        # Vérifie si le joueur est entré en colision avec un élèment sur l'axe Y
        hit_list = []
        for tile in self.tiles:
            if self.player_box.colliderect(tile):
                hit_list.append(tile)

        # Vérifie si la colision à lieu en haut ou en bas et déplace le joueur en fonction
        for tile in hit_list:
            if self.movement[1] > 0:
                self.player_box.bottom = tile.top
                self.collision_types['bottom'] = True
            elif self.movement[1] < 0:
                self.player_box.top = tile.bottom
                self.collision_types['top'] = True

        # Vérifie si le joueur à atteint le bloc correspondant à la fin du niveau et si ou change l'état du jeu en victoire
        for bloc in end:
            if self.player_box.colliderect(bloc):
                self.win = True

        # Verifie que le joueur n'est pas tomber si oui reset le niveau
        if self.player_box.y > 900:
            sleep(0.5)
            for ennemi in ennemis:
                ennemi.kill()
            print(ennemis)
            self.lives -= 1
            self.player_box.x = 450
            self.player_box.y = 600
            return map.set_mobs(ennemis)
        else:
            return ennemis

    def update(self, player_img, display, scroll):
        '''

        :param player_img: texture du joueur a appliquer
        :param display: display pygame
        :param scroll: valeur du déplacement relativement au mouvcement du joueur
        :return: si le joueur est en vie
        '''

        #Affiche le joueur
        display.blit(player_img, (self.player_box.x - scroll[0], self.player_box.y - scroll[1]))

        # Affiche le nombre de vies
        for i in range(self.lives):
            display.blit(self.heart, (self.heart.get_width() * i + 10 + i * 5, 10))

        # Affiche le nombre de grenade
        for i in range(self.nbr_grenade):
            display.blit(pygame.transform.scale(self.grenade_img, (108, 110)),
                         (self.heart.get_width() * i - 33 + i * 5, -5))

        # affiche le nombre de munitions
        ammo_display = self.myFont.render(f"{self.nbr_ammo}", False, (255, 255, 255))
        display.blit(ammo_display,(15,70))


        if self.health < 1:
            self.health = 20
            self.lives -= 1

        # Affiche la bar de vie
        if self.health > 0:
            self.health_bar = pygame.Surface((self.health, 2))
            self.health_bar.fill((0, 255, 0))
            self.health_bar_under.fill((220, 220, 220))
            display.blit(self.health_bar_under, (self.player_box.x + 5 - scroll[0], self.player_box.y - 5 - scroll[1]))
            display.blit(self.health_bar, (self.player_box.x + 5 - scroll[0], self.player_box.y - 5 - scroll[1]))

        if self.lives > 0:
            return True
        else:
            return False

    def shoot(self, display, direction):
        '''
        Tire une balle
        :param display: Display Pygame
        :param direction: booléen indiquant Direction du tire
        :return: un objet de type bullet
        '''
        self.shoot_sound.play()
        self.nbr_ammo -= 1
        if direction:
            return BulletLeft(self.player_box.x - 25, self.player_box.y, self.attack, display, True)
        else:
            return BulletRight(self.player_box.x + 28, self.player_box.y, self.attack, display, True)

    def grenade(self, display, direction, v0):
        '''
        Lance une grenade
        :param display: Display Pygame
        :param direction: booléen indiquant Direction du tire
        :param v0: Vitesse initaile de la grenade
        :return: retourne un objet de type grenade
        '''
        if direction:
            self.nbr_grenade -= 1
            return GrenadeLeft(self.player_box.x - 60, self.player_box.y, display, v0)
        else:
            self.nbr_grenade -= 1
            return GrenadeRight(self.player_box.x - 10, self.player_box.y + 40, display, v0)


    def damage(self, damage):
        '''
        Inflige des dégats au joueur
        :param damage: nombre de damage infligé
        '''

        self.health -= damage



class BulletRight(pygame.sprite.Sprite):
    '''
    Class correspondante au balles allant vers la droite
    '''
    def __init__(self, pos_x, pos_y, damage, display, fromPlayer):
        '''
        Initialise une balle
        :param pos_x: position selon l'axe x
        :param pos_y: position selon l'axe y
        :param damage: nombre de dommage qu'inflige la balle
        :param display: display pygame
        :param fromPlayer: booléen indiquant si la balle viens d'un joueur
        '''
        super().__init__()
        self.display = display
        self.fromPlayer = fromPlayer
        self.damage = damage
        self.image = pygame.Surface((5, 2))
        self.image.fill((255, 255, 0))
        self.rect = self.image.get_rect(center=(pos_x + 15, pos_y + 24.5))

    def update(self, display, scroll, tiles, ennemi_groupe, player):
        '''
        Fonction mettant a jour la balle
        :param display: pygame display
        :param scroll: déplacement relatif au déplacement du joueur
        :param tiles: tableau contenant les élèments contenu dans la carte
        :param ennemi_groupe: groupe de sprite contenant les ennemis
        :param player: Objet de type player
        '''

        display.blit(self.image, (self.rect.x - scroll[0], self.rect.y - scroll[1]))
        self.rect.x += 25

        #détruit la balle si elle sort de l'écran
        if self.rect.x >= 1280 + scroll[0] + 200:
            self.kill()

        # Détruit la ball en cas de colision avec un bloc
        for tile in tiles:
            if self.rect.colliderect(tile):
                self.kill()

        # inflige des dégats au joueur en cas de collision avec
        if self.fromPlayer:
            for ennemi in ennemi_groupe.sprites():
                if self.rect.colliderect(ennemi.ennemi_box):
                    ennemi.damage(self.damage)
                    self.kill()
        # destruction de la balle en ca s de collision avec le joueur
        if self.rect.colliderect(player.player_box):
            player.damage(self.damage)
            self.kill()


class BulletLeft(pygame.sprite.Sprite):
    '''
    Class correspondante au balles allant vers la gauche
    '''
    def __init__(self, pos_x, pos_y, damage, display, fromPlayer):
        super().__init__()
        self.damage = damage
        self.display = display
        self.fromPlayer = fromPlayer
        self.image = pygame.Surface((5, 2))
        self.image.fill((255, 255, 0))
        self.rect = self.image.get_rect(center=(pos_x + 15, pos_y + 24))

    def update(self, display, scroll, tiles, ennemi_groupe, player):
        '''
                Initialise une balle
                :param pos_x: position selon l'axe x
                :param pos_y: position selon l'axe y
                :param damage: nombre de dommage qu'inflige la balle
                :param display: display pygame
                :param fromPlayer: booléen indiquant si la balle viens d'un joueur
                '''

        display.blit(self.image, (self.rect.x - scroll[0], self.rect.y - scroll[1]))
        self.rect.x -= 25

        # détruit la balle si elle sort de l'écran
        if self.rect.x <= 0 + scroll[0] - 200:
            self.kill()

        # Détruit la ball en cas de colision avec un bloc
        for tile in tiles:
            if self.rect.colliderect(tile):
                self.kill()

        # inflige des dégats au joueur en cas de collision avec
        if self.fromPlayer:
            for ennemi in ennemi_groupe.sprites():
                if self.rect.colliderect(ennemi.ennemi_box):
                    ennemi.damage(self.damage)
                    self.kill()

        # destruction de la balle en ca s de collision avec le joueur
        if self.rect.colliderect(player.player_box):
            player.damage(self.damage)
            self.kill()


class GrenadeRight(pygame.sprite.Sprite):
    '''
    Class corrrepondante à une grenade lancé vers la droite
    '''
    def __init__(self, pos_x, pos_y, display, v0):
        '''
        Initialisation de la grenade
        :param pos_x: Coordonnée initiale de la grenade selon l'axe x
        :param pos_y: Coordonnée initiale de la grenade selon l'axe y
        :param display: display pygame
        :param v0: vitesse initale de la grenade
        '''
        super().__init__()
        self.display = display
        self.v0 = v0
        self.animation = Animations()
        self.animation_list = self.animation.load_animation('Assets/grenade', [5, 5, 5])
        self.explosion_sound = pygame.mixer.Sound('Assets/Sounds/explosion.wav')
        self.explosion_sound.set_volume(0.01)
        self.image_id = 0
        self.alpha = 45
        self.hit = False
        self.animation_frame = 0
        self.cpt = 1
        self.image = pygame.image.load('Assets/grenade/grenade_0.png')
        self.rect = self.image.get_rect(center=(pos_x + 40, pos_y - 25))

    def update(self, display, scroll, tiles, ennemis):
        '''
        Mise a jour de la grenade
        :param display: display pygame
        :param scroll: valeur du déplacement relatif par rapport au déplacement du joueur
        :param tiles: tableau contenant tous les éléments
        :param ennemis: Groupe de Sprite contenant tous les ennemis
        '''
        display.blit(self.image, (self.rect.x - scroll[0], self.rect.y - scroll[1]))

        # Equation de trajectoir balistique calculant la postion de la grenade au fil du temps
        if not self.hit:
            x = (self.v0 * cos(self.alpha)) * self.cpt
            self.rect.x += x / 14
            self.rect.y -= (((-9.8 * (x ** 2))/(2 * (self.v0 ** 2)*(cos(self.alpha)**2))) + (
                    tan(self.alpha) * x))/14

            self.cpt += 0.5

        # En cas de contact avec un block la grenade explose
        for tile in tiles:
            if self.rect.colliderect(tile):
                if not self.hit:
                    self.explosion_sound.play()
                self.hit = True

        # Lancement de l'animation d'explosion quand l'état de la grenade pass au contact
        if self.hit:
            self.animation_frame += 1
            if self.animation_frame < len(self.animation_list):
                self.image_id = self.animation_list[self.animation_frame]
                self.image = self.animation.animation_frames[self.image_id]
            else:
                for ennemi in ennemis:
                    if abs(self.rect.x - ennemi.ennemi_box.x) < 100:
                        ennemi.damage(10)
                self.kill()


class GrenadeLeft(pygame.sprite.Sprite):
    '''
    Class corrrepondante à une grenade lancé vers la gauche
    '''
    def __init__(self, pos_x, pos_y, display, v0):
        '''
                Initialisation de la grenade
                :param pos_x: Coordonnée initiale de la grenade selon l'axe x
                :param pos_y: Coordonnée initiale de la grenade selon l'axe y
                :param display: display pygame
                :param v0: vitesse initale de la grenade
                '''

        super().__init__()
        self.display = display
        self.v0 = v0
        self.animation = Animations()
        self.explosion_sound = pygame.mixer.Sound('Assets/Sounds/explosion.wav')
        self.explosion_sound.set_volume(0.01)
        self.animation_list = self.animation.load_animation('Assets/grenade', [5, 5, 5])
        self.image_id = 0
        self.hit = False
        self.animation_frame = 0
        self.alpha = 45
        self.cpt = 1
        self.image = pygame.image.load('Assets/grenade/grenade_0.png')
        self.rect = self.image.get_rect(center=(pos_x + 40, pos_y + 35))

    def update(self, display, scroll, tiles, ennemis):
        '''
        Mise a jour de la grenade
        :param display: display pygame
        :param scroll: valeur du déplacement relatif par rapport au déplacement du joueur
        :param tiles: tableau contenant tous les éléments
        :param ennemis: Groupe de Sprite contenant tous les ennemis
        '''


        display.blit(self.image, (self.rect.x - scroll[0], self.rect.y - scroll[1]))
        # Equation de trajectoir balistique calculant la postion de la grenade au fil du temps dans le cas ou la grenade n'est pas dans l'état de contact
        if not self.hit:
            x = (self.v0 * cos(self.alpha)) * self.cpt
            self.rect.x -= x / 14
            self.rect.y -= (((-9.8 * (x ** 2)) / (2 * (self.v0 ** 2) * (cos(self.alpha) ** 2))) + (
                    tan(self.alpha) * x)) / 14

            self.cpt += 0.5

        # En cas de contact avec un block la grenade explose
        for tile in tiles:
            if self.rect.colliderect(tile):
                if not self.hit:
                    self.explosion_sound.play()
                self.hit = True

        # Lancement de l'animation d'explosion quand l'état de la grenade pass au contact
        if self.hit:
            self.animation_frame += 1
            if self.animation_frame < len(self.animation_list):
                self.image_id = self.animation_list[self.animation_frame]
                self.image = self.animation.animation_frames[self.image_id]
            else:
                for ennemi in ennemis:
                    if abs(self.rect.x - ennemi.ennemi_box.x) < 100:
                        ennemi.damage(10)
                self.kill()


class Ennemi(pygame.sprite.Sprite):
    '''
    Class correspondante au ennemi
    '''
    def __init__(self, health, attack, pos_x, pos_y, static):
        '''
        Initialisation de l'ennemi
        :param health: nombre de point de vie initiale de l'ennemi
        :param attack: nombre de dommage qu'inflige l'ennemi
        :param pos_x: position initiale selon l'axe X
        :param pos_y: position initiale selon l'axe y
        :param static: booléen indiquant le type d'ennemi
        '''
        super().__init__()
        self.ennemi_img = pygame.image.load('Assets/Characters/Ennemi/idle/idle_0.png')
        self.ennemi_box = self.ennemi_img.get_rect()
        self.ennemi_box.x = pos_x
        self.ennemi_box.y = pos_y
        self.animation = Animations()
        self.static = static
        self.animation_database = {}
        self.animation_database['walk'] = self.animation.load_animation('Assets/Characters/Ennemi/walk', [5, 5, 5, 5, 5, 5])
        if static:
            self.animation_database['idle'] = self.animation.load_animation('Assets/Characters/Ennemi_2/idle', [7, 7])
        else:
            self.animation_database['idle'] = self.animation.load_animation('Assets/Characters/Ennemi/idle', [7, 7])
        self.ennemi_action = 'idle'
        self.ennemi_frame = 0
        self.health = health
        self.health_bar_under = pygame.Surface((20, 2))
        self.attack = attack
        self.cpt = 0
        self.walk_distance = randint(50, 180)
        self.shootCooldown = 0
        self.direction = -1
        self.findPlayer = False
        self.ennemi_momentum = 0
        self.shoot_sound = pygame.mixer.Sound('Assets/Sounds/tir.wav')
        self.shoot_sound.set_volume(0.01)

    def shoot(self, display, direction):
        '''
        Tire une balle
        :param display: Display Pygame
        :param direction: booléen indiquant Direction du tire
        :return: un objet de type bullet
        '''
        if direction:
            return BulletLeft(self.ennemi_box.x - 30, self.ennemi_box.y - 7, self.attack, display, False)
        else:
            return BulletRight(self.ennemi_box.x + 30, self.ennemi_box.y - 7, self.attack, display, False)


    def update(self, display, scroll, tile_rects, player, bullet_groupe):

        '''
        Fonction qui met à jour l'ennemi
        :param display: display pygame
        :param scroll: valeur du déplacement relatif par rapport au déplacement du joueur
        :param tile_rects: tableau contenant tous les élémentsdu jeu
        :param player: objet de type player
        :param bullet_groupe: groupe de sprite conteant les balles
        '''


        display.blit(self.ennemi_img, (self.ennemi_box.x - scroll[0], self.ennemi_box.y - scroll[1]))

        # Détruit l'ennemi quant il n'a plus de point de vie
        if self.health < 1:
            self.kill()

        # Affiche la bar de vie
        self.health_bar_under.fill((220, 220, 220))
        display.blit(self.health_bar_under, (self.ennemi_box.x +10 - scroll[0], self.ennemi_box.y - scroll[1]))

        # Affiche la bar de vie au dessus de l'ennemi
        if self.health > 0:
            self.health_bar = pygame.Surface((self.health, 2))
            self.health_bar.fill((255, 0, 0))
            display.blit(self.health_bar, (self.ennemi_box.x + 10 - scroll[0], self.ennemi_box.y - scroll[1]))

        # Détecte la présence d'un joueur au alentour et tire vers lui
        if 450 > self.ennemi_box.x - player.player_box.x > 0 and player.player_box.y == self.ennemi_box.y:
            self.ennemi_action, self.ennemi_frame = self.animation.change_action(self.ennemi_action, self.ennemi_frame,
                                                                                 'idle')
            self.findPlayer = True
            self.direction = -1
            if self.shootCooldown == 0:
                self.shoot_sound.play()
                bullet_groupe.add(self.shoot(display, True))
                self.shootCooldown = 50

        elif 0 > self.ennemi_box.x - player.player_box.x > -450 and player.player_box.y == self.ennemi_box.y:
            self.ennemi_action, self.ennemi_frame = self.animation.change_action(self.ennemi_action, self.ennemi_frame,
                                                                                 'idle')
            self.findPlayer = True
            self.direction = 1
            if self.shootCooldown == 0:
                self.shoot_sound.play()
                bullet_groupe.add(self.shoot(display, False))
                self.shootCooldown = 50
        else:
            self.findPlayer = False

        # Animation de l'ennemi
        if not self.findPlayer and not self.static:
            self.ennemi_action, self.ennemi_frame = self.animation.change_action(self.ennemi_action, self.ennemi_frame, 'walk')
            self.tiles = tile_rects

            # Déplacement automatique de l'enemeie sur la map de manière aléatoire.
            if self.cpt > self.walk_distance:
                self.cpt = 0
                self.direction *= -1
            if self.direction == -1:
                self.ennemi_box.x -= 1
            if self.direction == 1:
                self.ennemi_box.x += 1
            self.cpt += 1

            # Vérification des collisions de l'ennemi selon l'axe x
            hit_list = []
            for tile in self.tiles:
                if self.ennemi_box.colliderect(tile):
                    hit_list.append(tile)

            # Change la direction du joueur en cas de contact
            for tile in hit_list:
                if self.direction == 1:
                    self.ennemi_box.right = tile.left
                elif self.direction == -1:
                    self.ennemi_box.left = tile.right

            # applique la gravité à l'ennemi
            self.ennemi_momentum += 0.6
            if self.ennemi_momentum > 6:
                self.ennemi_momentum = 6

            # Vérifie les colissions selon l'axe Y
            self.ennemi_box.y += self.ennemi_momentum
            hit_list = []
            for tile in self.tiles:
                if self.ennemi_box.colliderect(tile):
                    hit_list.append(tile)

            for tile in hit_list:
                self.ennemi_box.bottom = tile.top
                self.ennemi_momentum = 0

        # récupère la texture correspondate à l'animation actuelle
        ennemi_image_id = self.animation_database[self.ennemi_action][self.ennemi_frame]

        # affecte la texture correpondante a la'orientation de l'ennemi
        if self.direction == -1:
            self.ennemi_img = pygame.transform.flip(self.animation.animation_frames[ennemi_image_id],True,False)
        if self.direction == 1:
            self.ennemi_img = pygame.transform.flip(self.animation.animation_frames[ennemi_image_id],False,False)

        self.ennemi_frame += 1
        if self.ennemi_frame >= len(self.animation_database[self.ennemi_action]):
            self.ennemi_frame = 0

        # Définie un cooldown entre les tire
        if self.shootCooldown > 0:
            self.shootCooldown -= 1

        if self.ennemi_box.y > 800:
            self.kill()

    def damage(self, damage):
        '''
        Inflige des dégats à l'ennemie
        :param damage: nombre de dégats à infliger
        '''

        self.health -= damage


class Button:
    def __init__(self, x, y, image, scale):
        '''
        initialise le boutton
        :param x: coordonne selon l'axe x du boutton
        :param y: coordonne selon l'axe y du boutton
        :param image: image de fond du boutton
        :param scale: echelle du boutton
        '''
        width = image.get_width()
        height = image.get_height()
        self.image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.clicked = False

    def draw(self, surface):
        '''
        Affiche le boutton
        :param surface: surface pygame
        :return: booléen indiquant si le boutton à été cliqué
        '''
        action = False

        pos = pygame.mouse.get_pos()

        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
                action = True
                self.clicked = True

        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False

        surface.blit(self.image, (self.rect.x, self.rect.y))

        return action
