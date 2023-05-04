import re

import pygame
import sys
from random import randint
import math
import random
import pandas as pd
from copy import copy

#  импорт данных о существах
data_h1 = pd.read_csv('heroes1_data1.csv', encoding='UTF-8', header=0)
data_h1 = data_h1.set_index('name')
data_h1.index.names = [None]
data_h1 = data_h1.transpose()
pack = data_h1.to_dict()

main_game = False
menu = True
select_screen = False

# окно программы
pygame.init()

screen = pygame.display.set_mode((1400, 800))
screen.fill('white')
font = pygame.font.SysFont('tahoma', 25)
font_logs = pygame.font.SysFont('tahoma', 16)
clock = pygame.time.Clock()
arrow = pygame.image.load(r'arrow/arrow.png').convert()

COLOR_INACTIVE = pygame.Color('lightskyblue3')
COLOR_ACTIVE = pygame.Color('dodgerblue2')
FONT = pygame.font.Font(None, 32)


class Hex(pygame.sprite.Sprite):
    """Определяет клетки поля"""

    def __init__(self, x=0, y=0, occupied=False):
        pygame.sprite.Sprite.__init__(self)
        if x < 0 or y < 0:
            raise ValueError('Координаты гекса должны быть больше 0')
        else:
            self.x = x
            self.y = y
            self.left_top = (0, 0)
            self.left_bottom = (0, 0)
            self.right_bottom = (0, 0)
            self.center = None
            self.image = None
            self.rect = None
            self.occupied = occupied
            self.occupied_by = None
            self.neighbours = [None, None, None, None, None, None]
            self.even = True if self.x % 2 == 0 else False
            self.board = None

    def __str__(self):
        return f'#({self.x}, {self.y})'

    def update(self):
        pass

    def show_neighbours(self):
        for bou in self.neighbours:
            print(bou)

    def is_neighbours(self, other):
        if abs(other.x - self.x) >= 2 or abs(other.y - self.y) >= 2:
            return False
        elif self.x == other.x and self.y == other.y:
            return False
        elif self.even:
            if other.y == self.y:
                if other.x == self.x - 1:
                    self.neighbours[1] = other
                else:
                    self.neighbours[3] = other
                return True
            elif other.y == self.y - 1:
                if other.x == self.x - 1:
                    self.neighbours[0] = other
                elif other.x == self.x:
                    self.neighbours[5] = other
                else:
                    self.neighbours[4] = other
                return True
            elif other.y == self.y + 1 and other.x == self.x:
                self.neighbours[2] = other
                return True
            else:
                return False
        else:
            if other.y == self.y:
                if other.x == self.x - 1:
                    self.neighbours[0] = other
                else:
                    self.neighbours[4] = other
                return True
            elif other.y == self.y + 1:
                if other.x == self.x - 1:
                    self.neighbours[1] = other
                elif other.x == self.x:
                    self.neighbours[2] = other
                else:
                    self.neighbours[3] = other
                return True
            elif other.y == self.y - 1 and other.x == self.x:
                self.neighbours[5] = other
                return True
            else:
                return False

    def front_hex(self, team1=True):
        if team1:
            return self.neighbours[2]
        else:
            return self.neighbours[5]

class Creature(pygame.sprite.Sprite):
    '''Существа с их численными данными и визуалом'''
    def __init__(self, name='random', number=1):
        pygame.sprite.Sprite.__init__(self)

        # pack = data_h1.to_dict()
        # имя
        if name == 'random':
            self.name = random.choice(list(pack.keys()))
        elif name in pack.keys():
            self.name = name
        else:
            raise ValueError(
                'Пожалуйста, введите название существа правильно. Для случайного существа - введите "random"')
        # статы
        self.offense = pack[self.name]['attack']
        self.defense = pack[self.name]['defense']
        self.min_dmg = pack[self.name]['min_dmg']
        self.max_dmg = pack[self.name]['max_dmg']
        self.health = pack[self.name]['hitp']
        self.power = pack[self.name]['power']
        self.cost = pack[self.name]['cost']
        self.abilities = pack[self.name]['abilities']
        self.current_health = self.health
        self.flyer = True if pack[self.name]['flying'] == 'Yes' else False
        self.ranged = True if pack[self.name]['shooter'] == 'Yes' else False
        self.arrows = int(pack[self.name]['arrows']) if self.ranged else None
        self.two_hex_strike = True if 'piercing' in self.abilities else False
        self.multiple_strike = True if 'multiple_attack' in self.abilities else False
        self.number = number
        self.fullhealth = (self.health * self.number - 1) + self.current_health
        self.speed = pack[self.name]['speed']
        self.two_hex = True if pack[self.name]['two-hex'] == 'Yes' else False
        self.moved_this_round = False
        self.actions = 1
        self.dualtap = True if '2_ranged' in self.abilities else False
        self.attack_numbers = 2 if '2_strikes' in self.abilities else 1
        self.retals = 1
        self.myturn = False
        self.regeneration = True if 'regeneration' in self.abilities else False

        # отсылки к другим классам
        self.team = None
        self.hex = None
        self.front_hex = None
        self.is_team1 = False
        self.is_team2 = False

        #графика
        self.main_image = pygame.image.load(f"{self.name.lower()}/tile006.png").convert()
        self.main_image.set_colorkey((0, 255, 255))
        self.image = self.main_image
        self.animation_set = []
        self.rect = self.image.get_rect()
        self.rect.center = (0, 0)
        self.anim_number = 0

        self.route_x = None
        self.route_y = None
        self.route_y_k = None
        self.point = None
        self.moving = False

    def __str__(self):
        return f'{self.number} {self.name} из команды {self.team.name}'

    def update(self):
        if self.route_y is None and self.route_x is None:
            pass
        elif self.number < 1:
            self.kill()
            del self

        elif self.myturn is False or self.moving is False:
            screen.fill((255, 255, 255))
            self.hex.board.draw()
            self.hex.board.render_logs()
            self.hex.board.skip_button.draw(screen)
            self.hex.board.group.draw(screen)
            clock.tick(40)
        else:
            screen.fill((255, 255, 255))
            self.hex.board.draw()
            self.hex.board.render_logs()
            self.hex.board.skip_button.draw(screen)
            self.image = self.animation_set[self.anim_number]
            self.image.set_colorkey((0, 255, 255))
            self.rect.x += self.point
            if self.route_y is not None:
                self.rect.y += self.route_y[self.route_y_k]

            self.hex.board.group.draw(screen)
            clock.tick(40)

    def animate_wound(self):
        # анимации получения урона
        old_bottomleft = self.rect.bottomleft
        # pygame.time.wait(100)

        if self.is_team1:
            target_sprite = pygame.image.load(f"{self.name.lower()}/target/tile000.png").convert()
            self.image = target_sprite
            self.rect = self.image.get_rect()
            self.rect.bottomleft = self.hex.left_bottom
        else:
            ats = pygame.image.load(f"{self.name.lower()}/target/tile000.png").convert()
            target_sprite = pygame.transform.flip(ats, True, False)
            self.image = target_sprite
            self.rect = self.image.get_rect()
            self.rect.bottomright = self.hex.right_bottom

        target_sprite.set_colorkey((0, 255, 255))
        screen.fill((255, 255, 255))
        self.hex.board.draw()
        self.hex.board.group.draw(screen)
        self.hex.board.render_logs()
        pygame.display.flip()
        pygame.time.wait(300)

        self.image = self.main_image
        self.rect = self.image.get_rect()
        self.rect.bottomleft = old_bottomleft
        screen.fill((255, 255, 255))
        self.hex.board.draw()
        self.hex.board.group.draw(screen)
        self.hex.board.render_logs()
        pygame.display.flip()
        clock.tick(40)

    def animate_attack(self, other, ranged=False):
        # выбор анимации в зависимости от расположения противника
        old_bottomleft = self.rect.bottomleft
        if ranged:
            if self.hex.left_top[0] > other.hex.left_top[0]:
                ats = pygame.image.load(f"{self.name.lower()}/ranged/tile000.png").convert()
                attack_sprite = pygame.transform.flip(ats, True, False)
                self.image = attack_sprite
                self.rect = self.image.get_rect()
                self.rect.bottomright = self.hex.right_bottom
            else:
                attack_sprite = pygame.image.load(f"{self.name.lower()}/ranged/tile000.png").convert()
                self.image = attack_sprite
                self.rect = self.image.get_rect()
                self.rect.bottomleft = self.hex.left_bottom
            # self.image = attack_sprite
            # self.rect = self.image.get_rect()
            # self.rect.bottomleft = self.hex.left_bottom
            attack_sprite.set_colorkey((0, 255, 255))
            screen.fill((255, 255, 255))
            self.hex.board.draw()
            self.hex.board.render_logs()
            self.hex.board.group.draw(screen)
            pygame.display.flip()

            pygame.time.wait(300)

            if self.hex.left_top[0] > other.hex.left_top[0]:
                ats = pygame.image.load(f"{self.name.lower()}/ranged/tile001.png").convert()
                attack_sprite = pygame.transform.flip(ats, True, False)
                self.image = attack_sprite
                self.rect = self.image.get_rect()
                self.rect.bottomright = self.hex.right_bottom
            else:
                attack_sprite = pygame.image.load(f"{self.name.lower()}/ranged/tile001.png").convert()
                self.image = attack_sprite
                self.rect = self.image.get_rect()
                self.rect.bottomleft = self.hex.left_bottom
            # self.image = attack_sprite
            # self.rect = self.image.get_rect()
            # self.rect.bottomleft = self.hex.left_bottom
            attack_sprite.set_colorkey((0, 255, 255))
            screen.fill((255, 255, 255))
            self.hex.board.draw()
            self.hex.board.render_logs()
            self.hex.board.group.draw(screen)
            pygame.display.flip()

            arrow = Arrow(self, other)
            self.hex.board.group.add(arrow)
            while arrow in self.hex.board.group:
                arrow.update()
                screen.fill((255, 255, 255))
                self.hex.board.draw()
                self.hex.board.group.draw(screen)
                self.hex.board.render_logs()
                pygame.display.flip()
                clock.tick(40)
        elif self.two_hex:
            targets_list = []
            other_hexes = (other.hex, other.front_hex) if other.two_hex else (other.hex,)
            if self.is_team2:
                targets_list.extend(self.hex.neighbours[:5])
                targets_list.extend(self.front_hex.neighbours[4:])
                targets_list.append(self.front_hex.neighbours[0])
            else:
                targets_list.extend(self.front_hex.neighbours[:5])
                targets_list.extend(self.hex.neighbours[4:])
                targets_list.append(self.hex.neighbours[0])
            if targets_list[0] in other_hexes:
                attack_sprite = pygame.image.load(f"{self.name.lower()}/attack_top/tile001.png").convert()
                self.image = attack_sprite
                self.rect = self.image.get_rect()
                self.rect.bottomleft = self.hex.left_bottom if self.is_team1 else self.front_hex.left_bottom
            elif targets_list[1] in other_hexes:
                attack_sprite = pygame.image.load(f"{self.name.lower()}/attack_top/tile001.png").convert()
                self.image = attack_sprite
                self.rect = self.image.get_rect()
                self.rect.bottomleft = self.hex.left_bottom if self.is_team1 else self.front_hex.left_bottom
            elif targets_list[2] in other_hexes:
                attack_sprite = pygame.image.load(f"{self.name.lower()}/attack_right/tile001.png").convert()
                self.image = attack_sprite
                self.rect = self.image.get_rect()
                self.rect.bottomleft = self.hex.left_bottom if self.is_team1 else self.front_hex.left_bottom
            elif targets_list[3] in other_hexes:
                attack_sprite = pygame.image.load(f"{self.name.lower()}/attack_bottom/tile001.png").convert()
                self.image = attack_sprite
                self.rect = self.image.get_rect()
                self.rect.bottomleft = self.hex.left_bottom if self.is_team1 else self.front_hex.left_bottom
            elif targets_list[4] in other_hexes:
                attack_sprite = pygame.image.load(f"{self.name.lower()}/attack_bottom/tile001.png").convert()
                self.image = attack_sprite
                self.rect = self.image.get_rect()
                self.rect.bottomleft = self.hex.left_bottom if self.is_team1 else self.front_hex.left_bottom
            elif targets_list[5] in other_hexes:
                ats = pygame.image.load(f"{self.name.lower()}/attack_bottom/tile001.png").convert()
                attack_sprite = pygame.transform.flip(ats, True, False)
                self.image = attack_sprite
                self.rect = self.image.get_rect()
                self.rect.bottomright = self.hex.right_bottom if self.is_team2 else self.front_hex.right_bottom
            elif targets_list[6] in other_hexes:
                ats = pygame.image.load(f"{self.name.lower()}/attack_right/tile001.png").convert()
                attack_sprite = pygame.transform.flip(ats, True, False)
                self.image = attack_sprite
                self.rect = self.image.get_rect()
                self.rect.bottomright = self.hex.right_bottom if self.is_team2 else self.front_hex.right_bottom
            else:
                ats = pygame.image.load(f"{self.name.lower()}/attack_top/tile001.png").convert()
                attack_sprite = pygame.transform.flip(ats, True, False)
                self.image = attack_sprite
                self.rect = self.image.get_rect()
                self.rect.bottomright = self.hex.right_bottom if self.is_team2 else self.front_hex.right_bottom

            attack_sprite.set_colorkey((0, 255, 255))
            screen.fill((255, 255, 255))
            self.hex.board.draw()
            self.hex.board.render_logs()
            self.hex.board.group.draw(screen)

            pygame.display.flip()
            clock.tick(40)
        else:
            other_hexes = (other.hex, other.front_hex) if other.two_hex else (other.hex,)
            if self.hex.neighbours[3] in other_hexes:
                attack_sprite = pygame.image.load(f"{self.name.lower()}/attack_bottom/tile001.png").convert()
                self.image = attack_sprite
                self.rect = self.image.get_rect()
                self.rect.bottomleft = (self.hex.left_bottom[0] - 10, self.hex.left_bottom[1] + 10)
            elif self.hex.neighbours[1] in other_hexes:
                attack_sprite = pygame.image.load(f"{self.name.lower()}/attack_top/tile001.png").convert()
                self.image = attack_sprite
                self.rect = self.image.get_rect()
                self.rect.bottomleft = self.hex.left_bottom
            elif self.hex.neighbours[0] in other_hexes:
                ats = pygame.image.load(f"{self.name.lower()}/attack_top/tile001.png").convert()
                attack_sprite = pygame.transform.flip(ats, True, False)
                self.image = attack_sprite
                self.rect = self.image.get_rect()
                self.rect.bottomright = self.hex.right_bottom
            elif self.hex.neighbours[4] in other_hexes:
                ats = pygame.image.load(f"{self.name.lower()}/attack_bottom/tile001.png").convert()
                attack_sprite = pygame.transform.flip(ats, True, False)
                self.image = attack_sprite
                self.rect = self.image.get_rect()
                self.rect.bottomright = (self.hex.right_bottom[0] + 10, self.hex.right_bottom[1] + 10)
            elif self.hex.neighbours[2] in other_hexes:
                attack_sprite = pygame.image.load(f"{self.name.lower()}/attack_right/tile001.png").convert()
                self.image = attack_sprite
                self.rect = self.image.get_rect()
                self.rect.bottomleft = self.hex.left_bottom
            else:
                ats = pygame.image.load(f"{self.name.lower()}/attack_right/tile001.png").convert()
                attack_sprite = pygame.transform.flip(ats, True, False)
                self.image = attack_sprite
                self.rect = self.image.get_rect()
                self.rect.bottomright = self.hex.right_bottom
            attack_sprite.set_colorkey((0, 255, 255))
            screen.fill((255, 255, 255))
            self.hex.board.draw()
            self.hex.board.render_logs()
            self.hex.board.group.draw(screen)

            pygame.display.flip()
            clock.tick(40)

        pygame.time.wait(300)

        self.image = self.main_image
        self.rect = self.image.get_rect()
        self.rect.bottomleft = old_bottomleft
        screen.fill((255, 255, 255))
        self.hex.board.draw()
        self.hex.board.render_logs()
        self.hex.board.group.draw(screen)
        pygame.display.flip()
        clock.tick(40)

    def show_number(self):
        text = font.render(f'{self.number}', True, 'black')
        screen.blit(text, (self.rect.midbottom[0] - 20, self.rect.midbottom[1] - 10))

    def update_animation_data(self):
        # использовать один раз, чтобы настроить анимации и главный спрайт.
        # Можно использовать только после того, как у существа появилась команда
        if self.is_team2:
            im = pygame.image.load(f"{self.name.lower()}/tile006.png").convert()
            self.main_image = pygame.transform.flip(im, True, False)
            self.main_image.set_colorkey((0, 255, 255))
            for l in range(6):
                im = pygame.image.load(f"{self.name.lower()}/tile00{l}.png").convert()
                im.set_colorkey((0, 255, 255))
                another_image = pygame.transform.flip(im, True, False)
                self.animation_set.append(another_image)
            # флип модели существа
        else:
            # self.main_image = pygame.image.load(f"{self.name.lower()}/tile006.png").convert()
            # self.main_image.set_colorkey((0, 255, 255))
            for l in range(6):
                another_image = pygame.image.load(f"{self.name.lower()}/tile00{l}.png").convert()
                another_image.set_colorkey((0, 255, 255))
                self.animation_set.append(another_image)
        self.image = self.main_image

    def is_blocked(self):
        if self.ranged is False:
            return False
        else:
            all_neigh = []
            all_neigh.extend(self.hex.neighbours)
            if self.two_hex:
                all_neigh.extend(self.front_hex.neighbours)
            for hexe in all_neigh:
                if hexe is not None and type(hexe.occupied_by) is Creature and hexe.occupied_by.team != self.team:
                    return True
                else:
                    pass
        return False

    def calculate_damage(self, other):
        if self.offense >= other.defense:
            mod = min((1 + 0.1 * (self.offense - other.defense)), 3)
        else:
            mod = max(1 + 0.1 * (self.offense - other.defense), 0.3)
        total_dmg = max(1, math.floor(self.number *
                                      (random.randint(self.min_dmg * 100, self.max_dmg * 100) / 100) * mod))
        if self.is_blocked():
            return max(1, total_dmg // 2)
        else:
            return total_dmg

    def do_damage(self, other):
        dmg = self.calculate_damage(other)
        number_before = other.number
        other.fullhealth = other.health * (number_before - 1) + other.current_health
        fh_after_dmg = other.fullhealth - dmg
        other.number = max(fh_after_dmg // other.health + int(bool(fh_after_dmg % other.health)), 0)
        other.current_health = fh_after_dmg - (other.number - 1) * other.health

        # print(f'{self.name} наносят {dmg} урона.\n')
        self.hex.board.update_logs(f'{self.name} наносят {dmg} урона.')
        other.animate_wound()
        if other.number < number_before:
            # print(f'Погибает {number_before - other.number} {other.name}')
            self.hex.board.update_logs(f'Погибает {number_before - other.number} {other.name}')
            self.hex.board.killed[other.team][other.name] = self.hex.board.killed[other.team].get(other.name, 0) +\
                                                            number_before - other.number
            other.team.update()

        if other.number > 0:
            # print(f'Осталось {other.number} {other.name}, здоровье - {other.current_health} из {other.health}\n')
            self.hex.board.update_logs(f'Осталось {other.number} {other.name}, здоровье - {other.current_health} из {other.health}')
        else:
            # print(f'{other.name} из {other.team.name} пали\n')
            self.hex.board.update_logs(f'{other.name} из {other.team.name} пали')
            other.team.destroy(other)
            other.kill()
            del other
            screen.fill((255, 255, 255))
            self.hex.board.draw()
            self.hex.board.group.draw(screen)
            pygame.display.flip()
            clock.tick(40)

    def set_hex(self, hex: Hex):
        # Помещает существо на данный гекс (как в плане занятости, так и подключит модельку)

        if self.hex is not None:
            self.hex.occupied = False
            self.hex.occupied_by = None
        self.hex = hex
        self.hex.occupied = True
        self.hex.occupied_by = self
        if self.two_hex:
            if self.is_team1:
                self.front_hex = self.hex.neighbours[2]
                self.front_hex.occupied = True
                self.front_hex.occupied_by = self
            else:
                self.front_hex = self.hex.neighbours[5]
                self.front_hex.occupied = True
                self.front_hex.occupied_by = self
        self.rect = self.image.get_rect()
        if self.is_team1:
            self.rect.bottomleft = self.hex.left_bottom
        else:
            self.rect.bottomright = self.hex.right_bottom
        self.anim_number = 0

    def attackable_find_hex(self, other):
        # возвращает гекс, с которого можно атаковать выбранную цель. Если таких гексов нет, вернёт False
        # эта штука должна использоваться только для компа, чтобы вычислить гекс для атаки
        # print(self.ranged)
        # print(self.arrows)
        # print(self.is_blocked())
        if self.ranged and self.is_blocked() is False and self.arrows > 0:
            return self.hex
        elif other.hex in self.hex.neighbours:
            return self.hex
        elif self.two_hex and other.hex in self.front_hex.neighbours:
            return self.hex
        elif self.two_hex and other.two_hex and other.front_hex in self.front_hex.neighbours:
            return self.hex
        # elif self.two_hex:
        #     two_hex_neighbours = []
        #     two_hex_neighbours.extend(other.hex.neighbours)
        #     if other.two_hex:
        #         two_hex_neighbours.extend(other.front_hex.neighbours)
        #     possible = [i for i in two_hex_neighbours if self.hex.board.calculate_distance(self.hex, i) is not None]
        elif self.flyer:
            if other.two_hex:
                two_hex_neighbours = []
                two_hex_neighbours.extend(other.hex.neighbours)
                two_hex_neighbours.extend(other.front_hex.neighbours)
            else:
                two_hex_neighbours = other.hex.neighbours
            for i in two_hex_neighbours:
                if i is not None:
                    if not self.two_hex and not i.occupied:
                        return i
                    elif self.two_hex and self.is_team1 and not i.occupied and i.neighbours[5] is not None and not i.neighbours[5].occupied:
                        return i.neighbours[5]
                    elif self.two_hex and self.is_team2 and not i.occupied and i.neighbours[2] is not None and not i.neighbours[2].occupied:
                        return i.neighbours[2]
            return False
        elif other.two_hex:
            two_hex_neighbours = []
            two_hex_neighbours.extend(other.hex.neighbours)
            two_hex_neighbours.extend(other.front_hex.neighbours)
            if self.two_hex and self.is_team1:
                possible = [i for i in two_hex_neighbours if i is not None and i.neighbours[5] is not None and self.hex.board.calculate_distance(self.hex, i.neighbours[5]) is not None]
            elif self.two_hex and self.is_team2:
                possible = [i for i in two_hex_neighbours if i is not None and i.neighbours[2] is not None and self.hex.board.calculate_distance(self.hex, i.neighbours[2]) is not None]
            else:
                possible = [i for i in two_hex_neighbours if self.hex.board.calculate_distance(self.hex, i) is not None]
            if not possible:
                return False
            # print(possible)
            if self.two_hex and self.is_team1:
                possible.sort(key=lambda x: self.hex.board.calculate_distance(self.hex, x.neighbours[5]))
            elif self.two_hex and self.is_team2:
                possible.sort(key=lambda x: self.hex.board.calculate_distance(self.hex, x.neighbours[2]))
            else:
                possible.sort(key=lambda x: self.hex.board.calculate_distance(self.hex, x))
            # if self.flyer:
            #     return possible[0]
            if self.two_hex:
                if self.is_team1 and self.hex.board.calculate_distance(self.hex, possible[0].neighbours[5]) <= self.speed:
                    return possible[0].neighbours[5]
                elif self.is_team2 and self.hex.board.calculate_distance(self.hex,
                                                                        possible[0].neighbours[2]) <= self.speed:
                    return possible[0].neighbours[2]
                else:
                    return False
            elif self.hex.board.calculate_distance(self.hex, possible[0]) <= self.speed:
                return possible[0]
            else:
                return False
        else:
            if self.two_hex and self.is_team1:
                possible = [i for i in other.hex.neighbours if i is not None and not i.occupied and i.neighbours[5] is not None and self.hex.board.calculate_distance(self.hex, i.neighbours[5]) is not None]
                possible2 = [i for i in other.hex.neighbours if i not in possible and i is not None and not i.occupied and i.neighbours[2] is not None and self.hex.board.calculate_distance(self.hex, i) is not None]
            elif self.two_hex and self.is_team2:
                possible = [i for i in other.hex.neighbours if i is not None and not i.occupied and i.neighbours[2] is not None and self.hex.board.calculate_distance(self.hex, i.neighbours[2]) is not None]
                possible2 = [i for i in other.hex.neighbours if i not in possible and i is not None and not i.occupied and i.neighbours[5] is not None and self.hex.board.calculate_distance(self.hex, i) is not None]
            else:
                possible = [i for i in other.hex.neighbours if self.hex.board.calculate_distance(self.hex, i) is not None]
            # print(f'нужная инфо {possible}')
            if not possible:
                return False
            if self.two_hex and self.is_team1:
                possible.sort(key=lambda x: self.hex.board.calculate_distance(self.hex, x.neighbours[5]))
                possible2.sort(key=lambda x: self.hex.board.calculate_distance(self.hex, x))
            elif self.two_hex and self.is_team2:
                possible.sort(key=lambda x: self.hex.board.calculate_distance(self.hex, x.neighbours[2]))
                possible2.sort(key=lambda x: self.hex.board.calculate_distance(self.hex, x))
            else:
                possible.sort(key=lambda x: self.hex.board.calculate_distance(self.hex, x))

            if self.two_hex:
                if self.is_team1:
                    if possible:
                        if self.hex.board.calculate_distance(self.hex, possible[0].neighbours[5]):
                            if self.hex.board.calculate_distance(self.hex, possible[0].neighbours[5]) <= self.speed:
                                # print(f' гекс атаки{possible[0]}')
                                # print(possible[0].neighbours[5])
                                return possible[0].neighbours[5]
                            else:
                                return False
                    elif possible2:
                        if self.hex.board.calculate_distance(self.hex, possible2[0]):
                            if self.hex.board.calculate_distance(self.hex, possible2[0]) <= self.speed:
                                # print(f' гекс атаки{possible[0]}')
                                # print(possible[0].neighbours[5])
                                return possible[0]
                            else:
                                return False
                    else:
                        return False
                else:
                    if possible:
                        if self.hex.board.calculate_distance(self.hex, possible[0].neighbours[2]):
                            if self.hex.board.calculate_distance(self.hex, possible[0].neighbours[2]) <= self.speed:
                                # print(f' гекс атаки{possible[0]}')
                                # print(possible[0].neighbours[5])
                                return possible[0].neighbours[2]
                            else:
                                return False
                    elif possible2:
                        if self.hex.board.calculate_distance(self.hex, possible2[0]):
                            if self.hex.board.calculate_distance(self.hex, possible2[0]) <= self.speed:
                                # print(f' гекс атаки{possible[0]}')
                                # print(possible[0].neighbours[5])
                                return possible[0]
                            else:
                                return False
                    else:
                        return False
            elif self.hex.board.calculate_distance(self.hex, possible[0]) <= self.speed:
                return possible[0]
            if self.flyer:
                return possible[0]
            else:
                return False

            # for h in other.hex.neighbours:
            #     # if h is not None and self.ranged and self.is_blocked() is False and self.arrows > 0:
            #     #     return h
            #     if h is not None and self.hex.board.calculate_distance(self.hex, h) is not None and \
            #             self.hex.board.calculate_distance(self.hex, h) <= self.speed:
            #         return h
            #     elif h is not None and self.hex.board.distance(self.hex, h) is not None and self.flyer:
            #         return h
            # return False

    def best_attack_choice(self, team):
        # сформировать пул доступных для атаки, из них - существ с ответкой. Если их несколько или 0 - выбираем того,
        # по кому наш удар приведёт к снижению ударной мощи
        all_targets = [creature for creature in team.comp if self.attackable_find_hex(creature)]
        if self.ranged is False or self.is_blocked() or self.arrows < 1:
            no_retal = [creature for creature in all_targets if creature.retals == 0]
        elif 'no_retaliation' in self.abilities:
            no_retal = all_targets
        else:
            no_retal = []
        if len(all_targets) > 0:
            if len(no_retal) == 1:
                return no_retal[0]
            elif len(no_retal) > 1:
                targets_dict = {}
                for c in no_retal:
                    our_dmg = self.calculate_damage(c)
                    enemy_hp_after = max(0, c.fullhealth - our_dmg)
                    enemy_number_after = enemy_hp_after // c.health + min(1, enemy_hp_after % c.health)
                    lost_power = math.floor((c.max_dmg + c.min_dmg) / 2 * c.number) \
                        - math.floor((c.max_dmg + c.min_dmg) / 2 * enemy_number_after)
                    targets_dict[c] = lost_power
                result = sorted(targets_dict.items(), key=lambda a: a[1], reverse=True)
                return result[0][0]
            else:
                targets_dict = {}
                for c in all_targets:
                    our_dmg = self.calculate_damage(c)
                    enemy_hp_after = max(0, c.fullhealth - our_dmg)
                    enemy_number_after = enemy_hp_after // c.health + min(1, enemy_hp_after % c.health)
                    lost_power = math.floor((c.max_dmg + c.min_dmg) / 2 * c.number) \
                        - math.floor((c.max_dmg + c.min_dmg) / 2 * enemy_number_after)
                    targets_dict[c] = lost_power
                result = sorted(targets_dict.items(), key=lambda a: a[1], reverse=True)
                return result[0][0]
        else:
            targets_dict = {}
            for c in team.comp:
                our_dmg = self.calculate_damage(c)
                enemy_hp_after = max(0, c.fullhealth - our_dmg)
                enemy_number_after = enemy_hp_after // c.health + min(1, enemy_hp_after % c.health)
                lost_power = math.floor((c.max_dmg + c.min_dmg) / 2 * c.number) \
                    - math.floor((c.max_dmg + c.min_dmg) / 2 * enemy_number_after)
                targets_dict[c] = lost_power
            result = sorted(targets_dict.items(), key=lambda a: a[1], reverse=True)
            for i in result:
                for j in i[0].hex.neighbours:
                    if j is not None and j.occupied is False:
                        return i[0]
            return False

    def find_xy_route(self, target: Hex):
        dist = abs(target.left_top[0] - self.hex.left_top[0])
        speed = 12
        if dist != 0:
            sg = (target.left_top[0] - self.hex.left_top[0]) / abs(target.left_top[0] - self.hex.left_top[0])
            result_x = []
            if dist // speed >= dist % speed:
                for j in range(dist % speed):
                    result_x.append((speed + 1) * sg)
                for k in range(dist // speed - dist % speed):
                    result_x.append(speed * sg)
            else:
                for j in range(speed - dist % speed):
                    result_x.append((speed - 1) * sg)
                for k in range(dist // speed + 1 - speed + dist % speed):
                    result_x.append(speed * sg)

            if self.hex.left_top[1] == target.left_top[1]:
                result_y = None
            else:
                dist_y = abs(target.left_top[1] - self.hex.left_top[1])
                result_y = []
                length = len(result_x)
                speed_y = dist_y // length
                sg_y = (target.left_top[1] - self.hex.left_top[1]) / abs(target.left_top[1] - self.hex.left_top[1])
                for n in range(dist % length):
                    result_y.append((speed_y + 1) * sg_y)
                for r in range(length - dist % length):
                    result_y.append(speed_y * sg_y)
        else:
            dist_y = abs(target.left_top[1] - self.hex.left_top[1])
            sg = (target.left_top[1] - self.hex.left_top[1]) / abs(target.left_top[1] - self.hex.left_top[1])
            result_x = []
            result_y = []
            if dist_y // speed >= dist_y % speed:
                for j in range(dist_y % speed):
                    result_y.append((speed + 1) * sg)
                for k in range(dist_y // speed - dist_y % speed):
                    result_y.append(speed * sg)
            else:
                for j in range(speed - dist_y % speed):
                    result_y.append((speed - 1) * sg)
                for k in range(dist_y // speed + 1 - speed + dist_y % speed):
                    result_y.append(speed * sg)
            for i in result_y:
                result_x.append(0)
        self.route_x = result_x
        self.route_y = result_y


    def new_move(self, target: Hex):
        # это для передвижения на соседний гекс
        self.moving = True
        if target is None or self.flyer is False and self.hex.board.distance(self.hex, target) is None:
            # print('Цель недостижима')
            pass
        elif self.flyer is False and self.hex.board.distance(self.hex, target) is None:
            # print('Цель недостижима')
            pass
        elif isinstance(target, Hex):
            self.find_xy_route(target)
            # print(f'x {self.route_x}')
            # print(f'y {self.route_y}')
            for i, point in enumerate(self.route_x):
                if self.anim_number == 5:
                    self.anim_number = 0
                else:
                    self.anim_number += 1
                self.point = point
                if self.route_y is not None:
                    self.route_y_k = i
                self.update()
                # self.hex.board.draw()
                # self.hex.board.group.draw(screen)
                pygame.display.flip()
                clock.tick(40)
            self.set_hex(target) # восстановить для правильного движения по гексам
            # screen.fill((255, 255, 255))
            # self.hex.board.draw()
            # # self.image = self.main_image
            # # self.image.set_colorkey((0, 255, 255))
            # self.hex.board.group.draw(screen)
            # pygame.display.flip()
            # clock.tick(40)
        else:
            # print('Это не гекс!')
            text_un = font.render('Это не гекс', True, 'black')
            screen.blit(text_un, (850, 450))
        # self.moving = False
        # self.hex.board.draw()
        # # self.image = self.main_image
        # # self.image.set_colorkey((0, 255, 255))
        # self.hex.board.group.draw(screen)
        # pygame.display.flip()
        # clock.tick(40)

    def move(self, target: Hex):
        if self.hex == target:
            # print(f'{self.name} не двигается\n')
            pass
        elif self.flyer:
            self.moving = True
            self.hex.occupied = False
            self.hex.occupied_by = None
            if self.two_hex:
                self.front_hex.occupied = False
                self.front_hex.occupied_by = None
            self.new_move(target=target)
            self.hex = target
            target.occupied = True
            target.occupied_by = self
            if self.two_hex:
                self.front_hex = self.hex.neighbours[2] if self.is_team1 else self.hex.neighbours[5]
                self.front_hex.occupied = True
                self.front_hex.occupied_by = self
            # pygame.time.delay(20)

            self.moving = False
            self.moved_this_round = True
            # print(f'{self.name} перелетает на гекс {target}\n')
            self.hex.board.update_logs(f'{self.name} перелетает на гекс {target}')
        else:
            self.moving = True
            # print('Вот дистанция')
            for part in self.hex.board.distance(self.hex, target):
                # print(part)
                self.hex.occupied = False
                self.hex.occupied_by = None
                if self.two_hex:
                    self.front_hex.occupied = False
                    self.front_hex.occupied_by = None
                self.new_move(target=part)
                self.hex = part
                part.occupied = True
                part.occupied_by = self
                if self.two_hex:
                    self.front_hex = self.hex.neighbours[2] if self.is_team1 else self.hex.neighbours[5]
                    self.front_hex.occupied = True
                    self.front_hex.occupied_by = self
            # pygame.time.delay(20)

            self.moving = False
            self.moved_this_round = True


            # print(f'{self.name} переходит на гекс {target}\n')
            self.hex.board.update_logs(f'{self.name} переходит на гекс {target}')

        clock.tick(40)


        self.image = self.main_image
        self.update()
        self.hex.board.group.draw(screen)
        self.hex.board.render_logs()
        for creature in self.hex.board.creatures_list:
            if creature.number > 0:
                creature.show_number()
        pygame.display.flip()
        clock.tick(40)

    def attack(self, other, retal=False, second=False, ranged=False): # предлагается переделать, разделив на атаку и ответ (надо ли?)

        # enemy_team = self.hex.board.team1 if self.team != self.hex.board.team1 else self.hex.board.team2
        if other.two_hex and self.two_hex:
            target_hex = other.hex if other.hex.is_neighbours(self.hex) or other.hex.is_neighbours(self.front_hex) else other.front_hex
        elif other.two_hex:
            target_hex = other.hex if other.hex.is_neighbours(self.hex) else other.front_hex
        else:
            target_hex = other.hex

        attacking_hex = self.front_hex if self.two_hex and self.front_hex.is_neighbours(target_hex) else self.hex

        if self.ranged and self.moved_this_round is False and self.is_blocked() is False and self.arrows > 0:
            ranged = True

        if retal:
            # print(f'{self.number} {self.name} отвечает {other.number} {other.name}\n')
            self.hex.board.update_logs(f'{self.number} {self.name} отвечает {other.number} {other.name}')
        elif ranged:
            # print(f'{self.number} {self.name} атакуте {other.number} {other.name} в дальнем бою\n')
            self.hex.board.update_logs(f'{self.number} {self.name} атакует {other.number} {other.name} в дальнем бою')
        else:
            # print(f'{self.number} {self.name} атакует {other.number} {other.name}\n')
            self.hex.board.update_logs(f'{self.number} {self.name} атакует {other.number} {other.name}')
        if retal or second:
            pygame.time.wait(200)
        self.animate_attack(other=other, ranged=ranged)
        self.do_damage(other)

        if not other or other.number < 1:
            screen.fill((255, 255, 255))
            self.hex.board.draw()
            self.hex.board.group.draw(screen)
            pygame.display.flip()
            clock.tick(40)

        if retal and 'infinite_retaliation' not in self.abilities:
            self.retals = 0
        elif second:
            self.attack_numbers = 0
            if self.ranged:
                self.arrows -= 1
        elif ranged:
            self.attack_numbers = 1 if self.dualtap else 0
            self.arrows -= 1
        else:
            self.attack_numbers = 1 if '2_strikes' in self.abilities else 0

        if self.two_hex_strike:
            for n in target_hex.neighbours:
                if n is not None and abs(
                        target_hex.neighbours.index(n) - target_hex.neighbours.index(attacking_hex)) == 3 and type(
                        n.occupied_by) == Creature and n.occupied_by != other and n.occupied_by.number > 0:
                    db_target = n.occupied_by
                    # print(f'Атака {self.name} поражает дополнительную цель {db_target}!\n')
                    self.hex.board.update_logs(f'Атака {self.name} поражает дополнительную цель!')
                    self.do_damage(db_target)
        if self.multiple_strike:
            if self.two_hex:
                targets_set = set([n.occupied_by for n in self.hex.neighbours + self.front_hex.neighbours if n is not None and isinstance(n.occupied_by, Creature) and n.occupied_by.team != self.team and n.occupied_by != other])
            else:
                targets_set = set([n.occupied_by for n in self.hex.neighbours if n is not None and isinstance(n.occupied_by, Creature) and n.occupied_by.team != self.team and n.occupied_by != other])
            for db_target in targets_set:
                # print(f'Атака {self.name} поражает дополнительную цель {db_target}!\n')
                self.hex.board.update_logs(f'Атака {self.name} поражает дополнительную цель!')
                self.do_damage(db_target)
        if other.number > 0:
            if ranged and second is False and self.dualtap:
                self.attack(other, ranged=True, second=True)
            if other.retals > 0 and retal is False and second is False and ranged is False and \
                    'no_retaliation' not in self.abilities:
                other.attack(self, retal=True)
            elif retal and other.attack_numbers > 0:
                other.attack(self, second=True)
            elif second and ranged is False and other.retals > 0 and 'no_retaliation' not in self.abilities:
                other.attack(self, retal=True)
            else:
                pass
        else:
            screen.fill((255, 255, 255))
            self.hex.board.draw()
            self.hex.board.group.draw(screen)
            pygame.display.flip()
            clock.tick(40)

    def move_without_attack(self, target):
        closest_dict = {}
        for hex1 in target.hex.neighbours:
            if hex1 is not None and hex1.occupied is False and \
                    self.hex.board.calculate_distance(self.hex, hex1) is not None:
                closest_dict[hex1] = self.hex.board.calculate_distance(self.hex, hex1)
        potential_hex = sorted(closest_dict.items(), key=lambda a: a[1])[-1][0]
        closest_hex = [h for h in self.hex.board.hexes if
                       self.hex.board.calculate_distance(self.hex, h) == self.speed and
                       self.hex.board.calculate_distance(h, potential_hex) == self.hex.board.calculate_distance
                       (self.hex, potential_hex) - self.speed]
        # print(closest_hex)
        self.move(closest_hex[0])

    def do_something(self): #  это функция для компа

        enemy_team = self.hex.board.team1 if self.is_team2 else self.hex.board.team2
        target = self.best_attack_choice(enemy_team)
        if self.attackable_find_hex(target):
            self.move(self.attackable_find_hex(target))
            self.attack(target)
        else:
            self.move_without_attack(target)

    def restore(self):
        # восстанавливает некоторые параметры в начале каждого раунда
        self.retals = 1
        self.actions = 1
        self.attack_numbers = 2 if '2_strikes' in self.abilities else 1
        self.moved_this_round = False
        if self.regeneration:
            self.current_health = self.health
            self.hex.board.update_logs(f'{self.name} восстановили здоровье до максимума!')

    def __del__(self):
        # self.model.destroy()
        # current_board = self.hex.board
        # self.update()
        self.kill()
        # self.hex.board.group.draw(screen)
        # pygame.display.flip()
        # clock.tick(40)
        del self


class Team:

    def __init__(self, *crs, name='default', player='human', number=1):
        self.comp = []
        for cr in crs:
            self.comp.append(cr)
        # print(self.comp)
        try:
            self.info = [(i.number, i.name, i.hex) for i in self.comp]
        except:
            self.info = [(i.number, i.name) for i in self.comp]
        self.name = name
        self.board = None
        self.player = player
        self.number = number
        # print(f'Создана команда {self.name}:\n')

        for j in self.comp:
            j.team = self
            if self.number == 1:
                j.is_team1 = True
            elif self.number == 2:
                j.is_team2 = True

    def __add__(self, other, nick='sum'):
        summcomp = self.comp + other.comp
        result = Team((i for i in summcomp), name=nick)
        return result

    def destroy(self, creat): # здесь должны быть все апдейты
        # if creature not in self.comp:
        #     raise KeyError('Это существо не из этой команды!')
        # else:
        creat.hex.occupied = False
        creat.hex.occupied_by = None
        creat.hex = None
        if creat.two_hex:
            creat.front_hex.occupied = False
            creat.front_hex.occupied_by = None
            creat.front_hex = None
        self.comp.remove(creat)
        del creat
        self.update()
        self.board.group.update()
        screen.fill((255, 255, 255))
        self.board.draw()
        self.board.group.draw(screen)
        pygame.display.flip()
        clock.tick(40)

    def update(self):
        self.info = [(i.number, i.name, i.hex) for i in self.comp]

    def __str__(self):
        result = f'Состав команды {self.name}:\n'
        for i in self.info:
            result += f'{i[0]} {i[1]} {i[2]}\n'
        result += '\n================================================================\n'
        return result

class Board:
    """Поле"""

    def __init__(self, rows=1, cols=1, first_team=None, second_team=None):
        if type(rows) is not int or type(cols) is not int or rows < 1 or cols < 1:
            raise TypeError('Число колонок и строк должно быть целым и больше нуля')
        else:
            self.rows = rows
            self.cols = cols
        self.hexes = []
        self.team1 = first_team
        self.team2 = second_team
        self.group = pygame.sprite.Group()
        self.numbers_list = pygame.sprite.Group()
        self.screen = screen
        self.creatures_list = self.team1.comp + self.team2.comp
        first_team.board = self
        second_team.board = self
        self.killed = {first_team: {}, second_team: {}}
        # count = 0
        # color = (0, 0, 19)
        # root2 = math.sqrt(2)
        # side = 80
        # start_point = 80
        for i in range(rows):
            # y = i * (side * root2 / 2 + side)
            # shivt = -1 * side * root2 / 2 if i % 2 == 1 else 0
            for j in range(cols):
                another_hex = Hex(i + 1, j + 1)
                self.hexes.append(another_hex)
                another_hex.board = self

                # записываем соседей
                for n in self.hexes[:-1]:
                    n.is_neighbours(another_hex)
                    another_hex.is_neighbours(n)
        self.teams = []
        self.logs = ['Логи боя']

    def __str__(self):
        result = f'Игровое поле с {len(self.hexes)} полями\n'

        return result

    def distance(self, start: Hex, end: Hex, two_hex=False):
        if start.occupied_by is not None and start.occupied_by.two_hex:
            two_hex = True
        if start not in self.hexes or end not in self.hexes:
            return None
        elif start == end:
            return []
        elif end.occupied and not two_hex:
            return None
        elif end in start.neighbours and two_hex is False:
            return [end]
        elif two_hex and end == start.occupied_by.front_hex and start.occupied_by.is_team1\
                and end.neighbours[2] is not None and end.neighbours[2].occupied is False:
            return [end]
        elif two_hex and end == start.occupied_by.front_hex and start.occupied_by.is_team2\
                and end.neighbours[5] is not None and end.neighbours[5].occupied is False:
            return [end]
        elif two_hex:
            if start.occupied_by.is_team1:
                dist_dict = {ne: 1 for ne in start.neighbours if ne is not None and ne.occupied is False and ne.neighbours[2] is not None and ne.neighbours[2].occupied is False}
                way_dict = {p: [] for p in start.neighbours if p is not None and p.occupied is False and p.neighbours[2] is not None and p.neighbours[2].occupied is False}
                dist_dict[start.neighbours[2]] = 1
                way_dict[start.neighbours[2]] = []
                if start.neighbours[5]:
                    dist_dict[start.neighbours[5]] = 1
                    way_dict[start.neighbours[5]] = []

            else:
                dist_dict = {ne: 1 for ne in start.neighbours if
                             ne is not None and ne.occupied is False and ne.neighbours[5] is not None and ne.neighbours[
                                 5].occupied is False}
                way_dict = {p: [] for p in start.neighbours if
                            p is not None and p.occupied is False and p.neighbours[5] is not None and p.neighbours[
                                5].occupied is False}
                if start.neighbours[2]:
                    dist_dict[start.neighbours[2]] = 1
                    way_dict[start.neighbours[2]] = []
                dist_dict[start.neighbours[5]] = 1
                way_dict[start.neighbours[5]] = []
            dist_dict[start] = 0  # эту строчку можно убрать
            k = 1
            while True:
                if k not in dist_dict.values():
                    break
                else:
                    new_dict = {key: value for key, value in dist_dict.items() if value == k}
                    for key in new_dict.keys():  # следует итерировать по другому набору.
                        for n in key.neighbours:
                            if n is None:
                                pass
                            if start.occupied_by.is_team1:
                                if n is not None and n not in dist_dict.keys() and n.occupied is False and n.neighbours[2] is not None and n.neighbours[2].occupied is False:
                                    dist_dict[n] = k + 1
                                    way_dict[n] = copy(way_dict[key])
                                    way_dict[n].append(key)
                                elif n is not None and n not in dist_dict.keys():
                                    dist_dict[n] = None
                                    way_dict[n] = None
                            elif start.occupied_by.is_team2:
                                if n is not None and n not in dist_dict.keys() and n.occupied is False and n.neighbours[5] is not None and n.neighbours[5].occupied is False:
                                    dist_dict[n] = k + 1
                                    way_dict[n] = copy(way_dict[key])
                                    way_dict[n].append(key)
                                elif n is not None and n not in dist_dict.keys():
                                    dist_dict[n] = None
                                    way_dict[n] = None


                k += 1
            if end in dist_dict.keys() and end is not None and way_dict[end] is not None:
                way_dict[end].append(end)
                return way_dict[end]
            else:
                return None
        else:
            # for i in end.neighbours: # что делать, если группа из n гексов, связанных между собой, недоступна?
            # можно действовать по нашему алгоритму, но. Некий итерейбл должен накапливать всех соседей и их значение.
            # Оно мб либо числом, либо None, либо ключа нет - тогда добавить в словарь.
            # Надо понять, в какой момент прекращать цикл. Это должно происходить, когда
            # любой числовой гекс выдаёт только таких соседей,
            # чьё значение - None или число. Т.е. среди соседей числовых гексов нет
            # ни одного гекса без значения.
            dist_dict = {ne: 1 for ne in start.neighbours if ne is not None and ne.occupied is False}
            dist_dict[start] = 0  # эту строчку можно убрать
            way_dict = {p: [] for p in start.neighbours if p is not None and p.occupied is False}
            k = 1
            while True:
                if k not in dist_dict.values():
                    break
                else:
                    new_dict = {key: value for key, value in dist_dict.items() if value == k}
                    for key in new_dict.keys():  # следует итерировать по другому набору.
                        for n in key.neighbours:
                            if n is None:
                                pass
                            elif n not in dist_dict.keys() and n.occupied is False:
                                dist_dict[n] = k + 1
                                way_dict[n] = copy(way_dict[key])
                                way_dict[n].append(key)
                            elif n.occupied and n not in dist_dict.keys():
                                dist_dict[n] = None
                                way_dict[n] = None
                k += 1
            if end in dist_dict.keys():
                way_dict[end].append(end)
                return way_dict[end]
            else:
                return None



    def calculate_distance(self, start: Hex, end: Hex):
        if self.distance(start=start, end=end) is None:
            return None
        else:
            return len(self.distance(start=start, end=end))

    def draw(self):
        count = 0
        color = (0, 0, 19)
        root2 = math.sqrt(2)
        side = 80
        start_point_x = 80
        start_point_y = 47
        for h in range(self.rows):
            y = h * (side * root2 / 2 + side) + start_point_y
            shivt = -1 * side * root2 / 2 if h % 2 == 1 else 0
            for k in range(self.cols):
                hex = self.hexes[count]
                x = k * side * root2 + start_point_x + shivt
                coords = ((side * root2 / 2 + x, 0 + y), (side * root2 + x, side * root2 / 2 + y),
                          (side * root2 + x, side * root2 / 2 + side + y),
                          (side * root2 / 2 + x, side * root2 + side + y), (0 + x, side * root2 / 2 + side + y),
                          (0 + x, side * root2 / 2 + y))
                hex.image = pygame.draw.polygon(screen, color, coords, 5)
                self.hexes[count].center = (math.floor(side * root2 / 2 + x), math.floor((side * root2 + side) / 2 + y))
                self.hexes[count].left_top = (
                    math.floor((side * root2 / 2 + 2 * x) / 2), math.floor((side * root2 / 2 + 2 * y) / 2))
                self.hexes[count].right_bottom = (
                    math.floor((side * root2 + x + side * root2 / 2 + x) / 2), math.floor((side * root2 / 2 + side + y + side * root2 + side + y) / 2))
                self.hexes[count].left_bottom = (
                    math.floor((side * root2 / 2 + x + x) / 2), math.floor((side * root2 + side + y + side * root2 / 2 + side + y) / 2))
                count += 1

    def start(self, team1, team2):
        nc_1 = len(team1.comp)
        nc_2 = len(team2.comp)
        # all_units = team1.comp + team2.comp
        # расстановка юнитов команды 1
        self.draw()
        first_const = (self.rows - nc_1) // (nc_1 + 1)
        if first_const >= 1:
            for i, creature in enumerate(team1.comp):
                current_hex = self.hexes[first_const * self.cols + (first_const + 1) * i * self.cols]
                creature.set_hex(current_hex)
                creature.update_animation_data()
                self.group.add(creature)
                creature.show_number()
        else:
            second_const = (self.rows - nc_1) // (nc_1 - 1)
            for i, creature in enumerate(team1.comp):
                current_hex = self.hexes[(second_const + 1) * i * self.cols]
                creature.set_hex(current_hex)
                creature.update_animation_data()
                self.group.add(creature)
                creature.show_number()

        # то же для второй команды
        first_const = (self.rows - nc_2) // (nc_2 + 1)
        if first_const >= 1:
            for i, creature in enumerate(team2.comp):
                current_hex = self.hexes[first_const * self.cols + (first_const + 1) * i * self.cols - 1 + self.cols]
                creature.set_hex(current_hex)
                creature.update_animation_data()
                self.group.add(creature)
                creature.show_number()

        else:
            second_const = (self.rows - nc_2) // (nc_2 - 1)
            for i, creature in enumerate(team2.comp):
                current_hex = self.hexes[(second_const + 1) * i * self.cols - 1 + self.cols]
                creature.set_hex(current_hex)
                creature.update_animation_data()
                self.group.add(creature)
                creature.show_number()

        screen.fill((255, 255, 255))
        self.skip_button = MenuBox(1050, 700, 185, 30, text='Пропустить ход')
        self.group.draw(screen)
        self.render_logs()
        self.skip_button.draw(screen)
        pygame.display.flip()

    def activate_hex(self, cr, event):
        for hex in self.hexes:
            if hex.left_top[0] < event.pos[0] < hex.right_bottom[0] \
                    and hex.left_top[1] < event.pos[1] < hex.right_bottom[1]:
                # print(f'выбран гекс {hex}')
                if hex.occupied is False:
                    if cr.two_hex:
                        if cr.flyer:
                            if cr.is_team1:
                                if hex.neighbours[2] is not None and hex.neighbours[2].occupied is False:
                                    cr.move(hex)
                                    cr.myturn = False
                                    return
                                elif hex.neighbours[5] is not None and hex.neighbours[5].occupied is False:
                                    cr.move(hex.neighbours[5])
                                    cr.myturn = False
                                    return
                            elif cr.is_team2:
                                if hex.neighbours[5] is not None and hex.neighbours[5].occupied is False:
                                    cr.move(hex)
                                    cr.myturn = False
                                    return
                                elif hex.neighbours[2] is not None and hex.neighbours[2].occupied is False:
                                    cr.move(hex.neighbours[2])
                                    cr.myturn = False
                                    return
                        else:
                            if cr.is_team1:
                                if hex.neighbours[2] and hex.neighbours[2].occupied is False and self.calculate_distance(cr.hex, hex) is not None \
                                            and self.calculate_distance(cr.hex, hex) <= cr.speed:

                                    cr.move(hex)
                                    cr.myturn = False
                                    return

                                elif hex.neighbours[2] is not None and hex.neighbours[2] == cr.hex and self.calculate_distance(cr.hex, hex) is not None \
                                            and self.calculate_distance(cr.hex, hex) <= cr.speed:

                                    cr.move(hex)
                                    cr.myturn = False
                                    return

                                elif hex.neighbours[5] is not None and hex.neighbours[5].occupied is False and self.calculate_distance(cr.hex, hex.neighbours[5]) is not None \
                                            and self.calculate_distance(cr.hex, hex.neighbours[5]) <= cr.speed:
                                    cr.move(hex.neighbours[5])
                                    cr.myturn = False
                                    return

                                elif hex.neighbours[5] is not None and hex.neighbours[5].occupied_by == cr and self.calculate_distance(cr.hex, hex.neighbours[5]) is not None \
                                            and self.calculate_distance(cr.hex, hex.neighbours[5]) <= cr.speed:

                                    cr.move(hex.neighbours[5])
                                    cr.myturn = False
                                    return

                                else:
                                    return
                            else:
                                if hex.neighbours[5] and hex.neighbours[5].occupied is False and self.calculate_distance(cr.hex, hex) is not None \
                                            and self.calculate_distance(cr.hex, hex) <= cr.speed :

                                    cr.move(hex)
                                    cr.myturn = False
                                    return

                                elif hex.neighbours[5] is not None and hex.neighbours[5] == cr.hex and self.calculate_distance(cr.hex, hex) is not None \
                                            and self.calculate_distance(cr.hex, hex) <= cr.speed:

                                    cr.move(hex)
                                    cr.myturn = False
                                    return

                                elif hex.neighbours[2] is not None and hex.neighbours[2].occupied is False and self.calculate_distance(cr.hex, hex.neighbours[2]) is not None \
                                            and self.calculate_distance(cr.hex, hex.neighbours[2]) <= cr.speed:

                                    cr.move(hex.neighbours[2])
                                    cr.myturn = False
                                    return

                                elif hex.neighbours[2] is not None and hex.neighbours[2].occupied_by == cr and self.calculate_distance(cr.hex, hex.neighbours[2]) is not None \
                                            and self.calculate_distance(cr.hex, hex.neighbours[2]) <= cr.speed:

                                    cr.move(hex.neighbours[2])
                                    cr.myturn = False
                                    return
                                    # else:
                                    #     return
                                else:
                                    return
                    else:
                        if cr.flyer:
                            cr.move(hex)
                            cr.myturn = False
                            return
                        elif self.calculate_distance(cr.hex, hex) is not None\
                            and self.calculate_distance(cr.hex, hex) <= cr.speed:
                            cr.move(hex)
                            cr.myturn = False
                            return

                elif isinstance(hex.occupied_by, Creature) and cr.team != hex.occupied_by.team:
                    attack_hex = cr.attackable_find_hex(hex.occupied_by)  # ИСПРАВИТЬ, НУЖНО НАЗНАЧИТЬ СЮДА БЛИЖАЙШИЙ К МЫШИ ГЕКС
                    # print(f'гекс для атаки:{attack_hex}')
                    if cr.ranged and cr.is_blocked() is False and cr.arrows > 0:
                        cr.attack(hex.occupied_by)
                        cr.myturn = False
                        return
                    elif attack_hex:

                        # if cr.two_hex:
                        if cr.flyer:
                            # if cr.two_hex:
                            #     if cr.is_team1:
                            #         cr.move(attack_hex.)
                            cr.move(attack_hex)
                            cr.attack(hex.occupied_by)
                            cr.myturn = False
                            return
                        elif attack_hex:
                            if not cr.two_hex:
                                cr.move(attack_hex)
                                cr.attack(hex.occupied_by)
                                cr.myturn = False
                                return
                            elif cr.two_hex and cr.is_team1:
                                cr.move(attack_hex)
                                cr.attack(hex.occupied_by)
                                cr.myturn = False
                                return
                            elif cr.two_hex and cr.is_team2:
                                cr.move(attack_hex)
                                cr.attack(hex.occupied_by)
                                cr.myturn = False
                                return
        if self.skip_button.rect.collidepoint(event.pos) :
            cr.myturn = False
            return


    def update_logs(self, new_string: str):
        if len(self.logs) > 15:
            self.logs.pop(1)
        self.logs.append(new_string)

    def render_logs(self):
        current_log_y = 30

        for log in self.logs:
            if 'Начинается' in log:
                text_un = font_logs.render(log, True, 'green')
            elif 'Логи' in log:
                text_un = font_logs.render(log, True, 'orange')
            elif 'на гекс' in log:
                text_un = font_logs.render(log, True, 'blue')
            elif 'атаку' in log:
                text_un = font_logs.render(log, True, 'gold')
            else:
                text_un = font_logs.render(log, True, 'black')
            self.screen.blit(text_un, (950, current_log_y + 20))
            # pygame.display.flip()
            current_log_y += 30

    def play(self, team1, team2):


        if type(team1) is not Team or type(team2) is not Team:
            raise KeyError('аргументы функции должны быть командами')

        if team1.comp[0].hex is None:
            raise ValueError('Сначала нужно запустить игру и расставить юнитов!')

        for c in team1.comp:
            # print(c, c.hex)
            pass
        for c in team2.comp:
            # print(c, c.hex)
            pass

        rounds = 0

        while True:
            # creatures_list = team1.comp + team2.comp
            if team1.comp and team2.comp:
                # creatures_list = team1.comp + team2.comp
                # print(creatures_list)
                rounds += 1
                # print(f'Начинается {rounds} раунд\n')
                self.update_logs(f'Начинается {rounds} раунд')
                for cr in self.creatures_list:
                    cr.restore()
                team1.update()
                team2.update()
                # print(f'{team1}\n')
                # print(f'{team2}\n')
                new_list = [j for j in self.creatures_list if j.number >= 1]
                # print(new_list)
                self.creatures_list = copy(new_list)
                self.creatures_list.sort(key=lambda x: (x.speed, -(x.team.comp.index(x) + 1) / len(x.team.comp)), reverse=True)
                # print(f'Порядок ходов:\n')
                # for number, creature in enumerate(self.creatures_list):
                #     print(number + 1, creature.name)

                for cr in self.creatures_list:
                    if team1.comp and team2.comp and cr.number > 0:
                        # print(cr.name)
                        cr.myturn = True
                        # выделить анимацией существо

                        if cr.team.player == 'human':
                            while True:
                                for event in pygame.event.get():
                                    if not cr.myturn:
                                        break
                                    elif event.type == pygame.QUIT:
                                        pygame.quit()
                                        sys.exit()
                                    elif event.type == pygame.MOUSEBUTTONDOWN:
                                        if event.button == 1:
                                            self.activate_hex(cr, event)
                                            break


                                screen.fill((255, 255, 255))
                                screen.blit(arrow, (cr.rect.x, cr.rect.y - 100))
                                self.draw()
                                self.group.draw(screen)
                                for creature in self.creatures_list:
                                    if creature.number > 0:
                                        creature.show_number()
                                self.render_logs()
                                self.skip_button.draw(screen)
                                pygame.display.flip()
                                # clock.tick(40)
                                if not cr.myturn:
                                    break
                        else:
                            pygame.time.wait(100)
                            cr.do_something()
                            cr.myturn = False

                        for creature in self.creatures_list:
                            if creature.number > 0:
                                creature.show_number()
                        # pygame.display.flip()
                        # clock.tick(40)

                        cr.actions = 0
                        cr.myturn = False

            else:
                winners = team1.name if len(team1.comp) > 0 else team2.name
                # print(f'Сражение окончено за {rounds} раундов. Победили {winners}')
                self.update_logs(f'Сражение окончено за {rounds} раундов. Победили {winners}')
                results_screen = True
                to_menu_button = MenuBox(950, 700, 50, 32, text='ОК')
                # results_text = f'Сражение окончено за {rounds} раундов. Победили {winners}'
                # text_un = font_logs.render(results_text, True, 'black')
                killed_team1 = [f'Потери {team1.name}']
                killed_team2 = [f'Потери {team2.name}']
                # print(self.killed)
                for keys, values in self.killed[team1].items():
                    killed_team1.append(f'{keys}: {values}')
                for keys, values in self.killed[team2].items():
                    killed_team2.append(f'{keys}: {values}')
                line_list1 = []
                line_list2 = []
                for lines in killed_team1:
                    # print(lines)
                    if 'Потери' in lines:
                        text = font_logs.render(lines, True, 'black')
                    else:
                        text = font_logs.render(lines, True, 'brown')
                    line_list1.append(text)
                for lines in killed_team2:
                    # print(lines)
                    if 'Потери' in lines:
                        text = font_logs.render(lines, True, 'black')
                    else:
                        text = font_logs.render(lines, True, 'brown')
                    line_list2.append(text)
                lines_y = 540
                for i in line_list1:
                    screen.blit(i, (950, lines_y))
                    lines_y += 20
                lines_y = 540
                for i in line_list2:
                    screen.blit(i, (1200, lines_y))
                    lines_y += 20
                while results_screen:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit()
                            sys.exit()
                        elif event.type == pygame.MOUSEBUTTONDOWN:
                            if to_menu_button.rect.collidepoint(event.pos):
                                results_screen = False
                        # else:
                        #     pass
                    screen.fill((255, 255, 255))
                    self.render_logs()
                    # self.skip_button.draw(screen)
                    # screen.blit(text_un, (950, 600))

                    self.draw()
                    self.group.update()
                    self.group.draw(screen)
                    to_menu_button.draw(screen)
                    lines_y = 540
                    for i in line_list1:
                        screen.blit(i, (950, lines_y))
                        lines_y += 15
                    lines_y = 540
                    for i in line_list2:
                        screen.blit(i, (1200, lines_y))
                        lines_y += 15
                    for creature in self.creatures_list:
                        if creature.number > 0:
                            creature.show_number()
                    pygame.display.flip()
                    clock.tick(40)
                break
        show_menu()

class Arrow(pygame.sprite.Sprite):
    '''Спрайт стрелы для стрелков'''

    def __init__(self, creature, target):
        pygame.sprite.Sprite.__init__(self)
        self.creature = creature
        self.target = target
        self.target_coords = target.hex.center
        self.x_move = (self.target_coords[0] - self.creature.rect.midright[0]) / 30
        self.y_move = (self.target_coords[1] - self.creature.rect.midright[1]) / 30
        self.image = pygame.image.load(f"{self.creature.name.lower()}/ranged/arrow.png").convert()
        if self.x_move < 0:
            self.image = pygame.transform.flip(self.image, True, False)
        self.image.set_colorkey((0, 255, 255))
        self.rect = self.image.get_rect()
        self.rect.midleft = self.creature.rect.midright


    def update(self):
        if self.rect.colliderect(self.target.rect):
            self.kill()
            del self
        else:
            self.rect.x += self.x_move
            self.rect.y += self.y_move

    def draw(self, screen):
        screen.draw()



class MenuBox:

    def __init__(self, x, y, w, h, text='', function=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = COLOR_INACTIVE
        self.text = text
        self.txt_surface = FONT.render(text, True, self.color)
        self.active = False
        self.function = function
        self.input_boxes, self.input_boxes2, self.check_box1, self.check_box2 = [], [], None, None
        self.mode = None
        self.bound = None

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # If the user clicked on the input_box rect.
            if self.rect.collidepoint(event.pos) and self.function is not None:
                # Toggle the active variable.
                self.active = not self.active
                self.color = COLOR_ACTIVE if self.active else COLOR_INACTIVE
                if self.function == 'exit':
                    pygame.quit()
                    sys.exit()
                elif self.function == 'play':
                    select_menu()
                elif self.function == 'play_power':
                    select_menu(mode='power')
                elif self.function == 'play_cost':
                    select_menu(mode='cost')
                elif self.function == 'select_game_modes':
                    global menu
                    menu = False
                    select_game_modes()
                elif self.function == 'about':
                    about()
                elif self.function == 'menu':
                    global modes_menu
                    modes_menu = False
                    show_menu()
                elif self.function == 'rules':
                    rules()
                elif self.function == 'board':
                    if self.mode and self.bound.content:
                        start(self.input_boxes, self.input_boxes2, self.check_box1, self.check_box2, mode=self.mode, bound=int(self.bound.content))
                    elif not self.mode:
                        start(self.input_boxes, self.input_boxes2, self.check_box1, self.check_box2)
                    else:
                        pass
                else:
                    pass
            else:
                self.active = False
            # Change the current color of the input box.

    def update(self):
        pass

    def draw(self, screen):
        # Blit the text.
        screen.blit(self.txt_surface, (self.rect.x+5, self.rect.y+5))
        # Blit the rect.
        pygame.draw.rect(screen, self.color, self.rect, 2)

class SlideBox:

    def __init__(self, x, y, w, h, data: list, base_option=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.l_arr = ((self.rect.topleft[0] - 1, self.rect.topleft[1]),
                                  (self.rect.bottomleft[0] - 1, self.rect.bottomleft[1]),
                                  (self.rect.midleft[0] - 10, self.rect.midleft[1]))
        self.r_arr = ((self.rect.topright[0] - 1, self.rect.topright[1]),
                                  (self.rect.bottomright[0] - 1, self.rect.bottomright[1]),
                                  (self.rect.midright[0] + 10, self.rect.midright[1]))
        self.color = COLOR_INACTIVE
        self.option = base_option
        self.option_number = 0
        self.options = [base_option]
        self.options.extend(data)
        self.txt_surface = FONT.render(self.option, True, self.color)
        self.data, self.data2, self.data3 = '', '', ''
        self.data_surface = FONT.render(self.data, True, self.color)
        self.data_surface2 = FONT.render(self.data2, True, self.color)
        self.data_surface3 = FONT.render(self.data3, True, self.color)
        self.image = None
        self.left_rect = pygame.Rect(self.rect.topleft[0] - 10, self.rect.topleft[1], 10, h)
        self.right_rect = pygame.Rect(self.rect.topright[0], self.rect.topleft[1], 10, h)

    def collide(self, pos, mode='left'):
        arr = self.l_arr if mode == 'left' else self.r_arr
        area = abs((arr[1][0] - arr[0][0]) * (arr[2][1] - arr[0][1]) - (
                    arr[2][0] - arr[0][0]) * (arr[1][1] - arr[0][1]))
        area1 = abs((arr[0][0] - pos[0]) * (arr[1][1] - pos[1]) - (arr[1][0] - pos[0]) * (
                    arr[0][1] - pos[1]))
        area2 = abs((arr[1][0] - pos[0]) * (arr[2][1] - pos[1]) - (arr[2][0] - pos[0]) * (
                    arr[1][1] - pos[1]))
        area3 = abs((arr[2][0] - pos[0]) * (arr[0][1] - pos[1]) - (arr[0][0] - pos[0]) * (
                arr[2][1] - pos[1]))
        areatotal = (area1 + area2 + area3) / 2
        if areatotal == area:
            return True
        else:
            return False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # If the user clicked on the input_box rect.
            if self.left_rect.collidepoint(event.pos):
                # Toggle the active variable.
                if self.option_number == 0:
                    self.option_number = len(self.options) - 1
                else:
                    self.option_number -= 1
            elif self.right_rect.collidepoint(event.pos):
                # Toggle the active variable.
                if self.option_number == len(self.options) - 1:
                    self.option_number = 0
                else:
                    self.option_number += 1
            self.option = self.options[self.option_number]
            # Re-render the text.
            self.txt_surface = FONT.render(self.option, True, self.color)
            self.update_data()
            self.data_surface = FONT.render(self.data, True, self.color)
            self.data_surface2 = FONT.render(self.data2, True, self.color)
            self.data_surface3 = FONT.render(self.data3, True, self.color)
            # self.image = pygame.image.load(f'{self.option}//small.png')

    def update(self):
        # Resize the box if the text is too long.
        # width = max(200, self.txt_surface.get_width()+10)
        # self.rect.w = width
        pass

    def update_data(self):
        #  нужна для показа в меню выбора данных о существах
        self.data3 = ''
        self.image = None
        if self.option:
            self.data = f"Атака: {pack[self.option]['attack']} Защита: {pack[self.option]['defense']}"
            self.data2 = f"Урон: {pack[self.option]['min_dmg']}-{pack[self.option]['max_dmg']} Здоровье: {pack[self.option]['hitp']}"
            self.image = pygame.image.load(f'{self.option.lower()}//little.png')
            self.image.set_colorkey((0, 255, 255))

            if pack[self.option]['flying'] == 'Yes':
                self.data3 += 'летает '
            if pack[self.option]['shooter'] == 'Yes':
                self.data3 += 'стрелок '
            if 'piercing' in pack[self.option]['abilities']:
                self.data3 += 'атака поражает две клетки '
            if '2_strikes' in pack[self.option]['abilities']:
                self.data3 += 'бьёт дважды '
            if 'no_retaliation' in pack[self.option]['abilities']:
                self.data3 += 'безответная атака '
            if 'infinite_retaliation' in pack[self.option]['abilities']:
                self.data3 += 'отвечает на все атаки '
            if '2_ranged' in pack[self.option]['abilities']:
                self.data3 += 'два выстрела'
            if 'multiple_attack' in pack[self.option]['abilities']:
                self.data3 += 'атакует всех вокруг'
            if 'regeneration' in pack[self.option]['abilities']:
                self.data3 += 'регенерирует здоровье каждый раунд'

        else:
            self.data = ''
            self.data2 = ''


    def draw(self, screen):
        # рисует способности и статистику существ, а также опции выбора существ на этапе выбора
        screen.blit(self.txt_surface, (self.rect.x+5, self.rect.y+5))
        screen.blit(self.data_surface, (self.rect.x+5, self.rect.y + 35))
        screen.blit(self.data_surface2, (self.rect.x+5, self.rect.y+55))
        screen.blit(self.data_surface3, (self.rect.x+5, self.rect.y + 75))
        if self.image:
            screen.blit(self.image, (self.rect.x-45, self.rect.y+35))
        # Blit the rect.
        pygame.draw.rect(screen, self.color, self.rect, 2)
        pygame.draw.polygon(screen, self.color, self.l_arr)
        pygame.draw.polygon(screen, self.color, self.r_arr)


class InputBox:

    '''Нужен для ввода текстовых данных (в данном случае чисел)'''

    def __init__(self, x, y, w, h, text='', takes='int'):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = COLOR_INACTIVE
        self.text = text
        self.txt_surface = FONT.render(text, True, self.color)
        self.active = False
        self.type = takes
        self.content = ''
        self.content_surface = FONT.render(self.content, True, self.color)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # If the user clicked on the input_box rect.
            if self.rect.collidepoint(event.pos):
                # Toggle the active variable.
                self.active = not self.active
            else:
                self.active = False
            # Change the current color of the input box.
            self.color = COLOR_ACTIVE if self.active else COLOR_INACTIVE
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    # print(self.text)
                    if self.type == 'int':
                        try:
                            self.content = int(self.text)
                            self.content_surface = FONT.render(self.text, True, self.color)
                        except:
                            pass
                    elif self.type == 'str':
                        self.content = self.text
                        self.content_surface = FONT.render(self.text, True, self.color)
                    self.text = ''
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
                # Re-render the text.
                self.txt_surface = FONT.render(self.text, True, self.color)

    def update(self):
        # Resize the box if the text is too long.
        width = max(200, self.txt_surface.get_width()+10)
        self.rect.w = width

    def draw(self, screen):
        # Blit the text.
        screen.blit(self.txt_surface, (self.rect.x+5, self.rect.y+5))
        screen.blit(self.content_surface, (self.rect.x, self.rect.y + 40))
        # Blit the rect.
        pygame.draw.rect(screen, self.color, self.rect, 2)


class CheckBox:

    '''Нужен для выбора типа игрока - человек или компьютер'''

    def __init__(self, x, y, w, h, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = COLOR_ACTIVE
        self.text = text
        self.txt_surface = FONT.render(text, True, self.color)
        self.active = True
        self.content = 'X'
        self.content_surface = FONT.render(self.content, True, self.color)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # If the user clicked on the input_box rect.
            if self.rect.collidepoint(event.pos):
                # Toggle the active variable.
                self.active = not self.active
                # Change the current color of the input box.
                self.color = COLOR_ACTIVE if self.active else COLOR_INACTIVE
                if self.active:
                    self.text = 'Человек'
                    self.content = 'X'
                else:
                    self.text = 'Компьютер'
                    self.content = ''
                self.content_surface = FONT.render(self.content, True, self.color)
                self.txt_surface = FONT.render(self.text, True, self.color)


    def update(self):
        pass

    def draw(self, screen):
        # Blit the text.
        screen.blit(self.txt_surface, (self.rect.x+50, self.rect.y+5))
        screen.blit(self.content_surface, (self.rect.x+5, self.rect.y+5))
        # Blit the rect.
        pygame.draw.rect(screen, self.color, self.rect, 2)




def show_menu():
    '''Показывает главное меню'''
    text = font.render(f'Это главное меню. Выберите нужную опцию для старта', True, 'black')
    option1 = MenuBox(560, 400, 200, 30, text='Начать игру', function='select_game_modes')
    option4 = MenuBox(560, 450, 200, 30, text='Правила игры', function='rules')
    option3 = MenuBox(560, 500, 200, 30, text='О программе', function='about')
    option2 = MenuBox(560, 550, 200, 30, text='Выход', function='exit')
    options = [option1, option2, option3, option4]
    global menu
    menu = True
    while menu:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            for option in options:
                # pygame.time.wait(500)
                option.handle_event(event)
        screen.fill((255, 255, 255))
        screen.blit(text, (360, 325))
        for option in options:
            option.draw(screen)
        pygame.display.flip()

def select_game_modes():
    '''Окно выбора режима'''
    text = font.render(f'Пожалуйста, выберите нужный режим', True, 'black')
    option1 = MenuBox(510, 400, 360, 30, text='Свободный режим', function='play')
    option4 = MenuBox(510, 450, 360, 30, text='Отряды равны по силе', function='play_power')
    option3 = MenuBox(510, 500, 360, 30, text='Отряды равны по стоимости', function='play_cost')
    option5 = MenuBox(510, 550, 360, 30, text='Испытания', function='challenge')
    option2 = MenuBox(510, 600, 360, 30, text='Назад', function='menu')
    options = [option1, option2, option3, option4, option5]
    global modes_menu
    modes_menu = True
    while modes_menu:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            for option in options:
                # pygame.time.wait(500)
                option.handle_event(event)
        screen.fill((255, 255, 255))
        screen.blit(text, (460, 325))
        for option in options:
            option.draw(screen)
        pygame.display.flip()

def start(input_boxes, input_boxes2, check_box1, check_box2, mode=None, bound:int=0):
    '''Срабатывает в момент нажатия кнопки начать в меню выбора, позволяет старотовать матч'''
    selected = []
    selected2 = []
    if mode:
        bound = int(input_boxes[-1].content)
        bound1, bound2 = 0, 0
    global select_screen
    for i, n in enumerate(input_boxes[:5]):
        if n.option and input_boxes[i+5].content:
            creature = Creature(name=n.option, number=input_boxes[i+5].content)
            selected.append(creature)
            if mode == 'cost':
                bound1 += creature.cost * creature.number
            elif mode == 'power':
                bound1 += int(creature.power / 18 * creature.number)

    for i, n in enumerate(input_boxes2[:5]):
        if n.option and input_boxes2[i+5].content:
            creature = Creature(name=n.option, number=input_boxes2[i+5].content)
            selected2.append(creature)
            if mode == 'cost':
                bound2 += creature.cost * creature.number
            elif mode == 'power':
                bound2 += int(creature.power / 18 * creature.number)

    player1 = 'human' if check_box1.active else 'computer'
    player2 = 'human' if check_box2.active else 'computer'

    if selected and selected2:
        if mode and (bound1 > bound or bound2 > bound): # если превышено ограничение
            pass
        else:
            if mode:
                print(bound)
            team1 = Team(*selected, name='Team1', number=1, player=player1)
            team2 = Team(*selected2, name='Team2', number=2, player=player2)
            board1 = Board(rows=5, cols=7, first_team=team1, second_team=team2)
            select_screen = False
            screen.fill((255, 255, 255))
            board1.draw()
            board1.start(team1=team1, team2=team2)
            board1.play(team1=team1, team2=team2)
    else:
        pass

def select_menu(mode=None):

    '''Показывает меню выбора отрядов'''

    text = font.render(f'Это меню выбора персонажей. Наберите свою команду и нажмите кнопку Начать', True, 'black')
    text2 = font.render(f'Внимание! Для установки количества существ нужно ввести число в окно и нажать энтер', True, 'black')
    # pygame.display.flip()
    select_screen = True
    cr_data = [name for name in data_h1.columns]

    if mode:
        bound_box = InputBox(530, 620, 60, 32)
        bound_text = 'Ограничение по цене' if mode == 'cost' else 'Ограничение по силе'
        b_rendertext = font.render(bound_text, True, 'black')
    quantity_box1 = InputBox(350, 120, 60, 32)
    quantity_box2 = InputBox(350, 220, 60, 32)
    quantity_box3 = InputBox(350, 320, 60, 32)
    quantity_box4 = InputBox(350, 420, 60, 32)
    quantity_box5 = InputBox(350, 520, 60, 32)
    check_box1 = CheckBox(100, 70, 30, 30, text='Человек')
    slide_box1 = SlideBox(100, 120, 200, 32, data=cr_data, base_option='')
    slide_box2 = SlideBox(100, 220, 200, 32, data=cr_data, base_option='')
    slide_box3 = SlideBox(100, 320, 200, 32, data=cr_data, base_option='')
    slide_box4 = SlideBox(100, 420, 200, 32, data=cr_data, base_option='')
    slide_box5 = SlideBox(100, 520, 200, 32, data=cr_data, base_option='')

    input_boxes = [slide_box1, slide_box2, slide_box3, slide_box4, slide_box5,
                   quantity_box1, quantity_box2, quantity_box3, quantity_box4, quantity_box5, check_box1]
    if mode:
        input_boxes.append(bound_box)
    # print(slide_box1.options)

    slide_box6 = SlideBox(700, 120, 200, 32, data=cr_data, base_option='')
    slide_box7 = SlideBox(700, 220, 200, 32, data=cr_data, base_option='')
    slide_box8 = SlideBox(700, 320, 200, 32, data=cr_data, base_option='')
    slide_box9 = SlideBox(700, 420, 200, 32, data=cr_data, base_option='')
    slide_box10 = SlideBox(700, 520, 200, 32, data=cr_data, base_option='')
    quantity_box6 = InputBox(950, 120, 60, 32)
    quantity_box7 = InputBox(950, 220, 60, 32)
    quantity_box8 = InputBox(950, 320, 60, 32)
    quantity_box9 = InputBox(950, 420, 60, 32)
    quantity_box10 = InputBox(950, 520, 60, 32)

    check_box2 = CheckBox(700, 70, 30, 30, text='Человек')
    input_boxes2 = [slide_box6, slide_box7, slide_box8, slide_box9, slide_box10,
                   quantity_box6, quantity_box7, quantity_box8, quantity_box9, quantity_box10, check_box2]

    back_button = MenuBox(100, 700, 100, 32, text='Назад', function='menu')
    start_button = MenuBox(1050, 700, 100, 32, text='Начать', function='board')
    start_button.input_boxes = input_boxes
    start_button.input_boxes2 = input_boxes2
    start_button.check_box1 = check_box1
    start_button.check_box2 = check_box2
    if mode:
        start_button.mode = mode
        start_button.bound = bound_box
    buttons = [back_button, start_button]

    while select_screen:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    select_screen = False
                    show_menu()

            for box in input_boxes + input_boxes2 + buttons:
                box.handle_event(event)


        for box in input_boxes + input_boxes2 + buttons:
            box.update()


        screen.fill((250, 250, 250))
        for box in input_boxes + input_boxes2 + buttons:
            box.draw(screen)
        screen.blit(text, (225, 0))
        screen.blit(text2, (225, 25))
        info1 = 'Команда 1'
        info2 = 'Команда 2'
        team1_bound, team2_bound = 0, 0
        for number, i in enumerate(input_boxes[5:10]):
            try:
                multi = pack[input_boxes[number].option][mode]
                team1_bound += int(int(i.content) * multi / 18)
            except:
                pass
        for number, i in enumerate(input_boxes2[5:10]):
            try:
                multi = pack[input_boxes2[number].option][mode]
                team2_bound += int(int(i.content) * multi / 18)
            except:
                pass
        team1_boundtext = font.render(str(team1_bound), True, 'black')
        team2_boundtext = font.render(str(team2_bound), True, 'black')
        if mode:
            screen.blit(b_rendertext, (500, 570))
            screen.blit(team1_boundtext, (350, 70))
            screen.blit(team2_boundtext, (950, 70))
        pygame.display.flip()
        clock.tick(30)

def rules():
    rules_font = pygame.font.Font(None, 26)
    back_button = MenuBox(100, 700, 100, 32, text='Назад', function='menu')
    text = 'Вот правила игры'
    text2 = ['Игра имитирует сражения из игры "Герои меча и магии-1".',
             'В пошаговом сражении участвует 2 армии, каждая состоит из не более чем 5 видов сказочных существ.',
             'Тип и количество существ можно настроить в меню выбора в начале игры.',
             'У вас есть опции играть против другого человека, компьютера и самого себя.',
             'Каждое существо в армии игрока обладает количеством и боевыми параметрами, определяющими его мощь (см ниже).',
             'Сражение делится на раунды.',
             'В рамках каждого раунда каждое существо получает ход только один раз, очерёдность зависит от параметра скорости.',
             'В рамках своего хода существо может: ',
             '1) передвинуться на количество клеток, равное скорости (у летающих существ нет ограничений): кликните на свободную клетку',
             '2) атаковать противника (в т.ч. после перемещения): кликните на противника',
             '3) а также атаковать в дальнем бою (доступно стрелкам): кликните на противника',
             'В ходе атаки существа наносят урон, могут уничтожить одно или несколько существ команды противника',
             'Команда, оставшаяся без существ, проигрывает.']
    text3 = 'Параметры существ'
    text5 = ['1) Атака', ' - определяет способность существа к нападению. За каждое очко разницы между атакой атакующего',
             'и защитой обороняющегося наносимый урон увеличивается на 10% (максимум - на 200%).',
             '2) Защита', ' - определяет способность существа к обороне. За каждое очко разницы между защитой обороняющегося',
             'и атакой атакующего наносимый урон уменьшается на 10% (максимум - на 70%).',
             '3) Урон', ' - определяет количество повреждений, наносимых одним существом в отряде.',
             '4) Здоровье', ' - определяет количество повреждений, которое может выдержать существо.',
             '5) Скорость', ' - определяет количество клеток, которое существо способно пройти за один ход. Летающие существа могут передвигаться на любую дистанцию.',
             'Также от скорости зависит порядок хода существ в ходе раунда.']
    ...
    data_surface = rules_font.render(text, True, 'blue')
    all_text_surfaces = []
    for string in text2:
        if 'В рамках своего хода' in string or 'раунды' in string:
            all_text_surfaces.append(rules_font.render(string, True, 'red'))
        else:
            all_text_surfaces.append(rules_font.render(string, True, 'black'))
    all_text_surfaces.append(rules_font.render(text3, True, 'purple'))
    for string in text5:
        if re.findall(r'\d\)', string):
            all_text_surfaces.append(rules_font.render(string, True, 'red'))
        else:
            all_text_surfaces.append(rules_font.render(string, True, 'black'))
    rules_screen = True
    while rules_screen:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    rules_screen = False
                    show_menu()


            back_button.handle_event(event)
            back_button.update()
        screen.fill((255, 255, 255))
        screen.blit(data_surface, (525, 50))
        k = 85
        for line in all_text_surfaces:
            screen.blit(line, (60, k))
            k += 22
        back_button.draw(screen)
        pygame.display.flip()

def about():
    rules_font = pygame.font.Font(None, 26)
    back_button = MenuBox(100, 700, 100, 32, text='Назад', function='menu')
    text = 'О программе'
    text2 = ['Hex Battles.',
             'Версия 0.28',
             '@ Daniel Sukhan (thakavur), 2023',
             ]
    ...
    data_surface = rules_font.render(text, True, 'blue')
    all_text_surfaces = []
    for string in text2:
        if 'О программе' in string:
            all_text_surfaces.append(rules_font.render(string, True, 'red'))
        else:
            all_text_surfaces.append(rules_font.render(string, True, 'black'))
    a_screen = True
    while a_screen:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    a_screen = False
                    show_menu()


            back_button.handle_event(event)
            back_button.update()
        screen.fill((255, 255, 255))
        screen.blit(data_surface, (525, 50))
        k = 125
        for line in all_text_surfaces:
            screen.blit(line, (360, k))
            k += 25
        back_button.draw(screen)
        pygame.display.flip()

show_menu()


    # board1.draw()
    # board1.render_logs()
    # pygame.display.flip()
