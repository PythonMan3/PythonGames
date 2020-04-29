import pygame
from pygame.locals import *
import sys

SCREEN_RECT = Rect(0, 0, 640, 480)
CS = 32
SCREEN_NCOL = SCREEN_RECT.width//CS
SCREEN_NROW = SCREEN_RECT.height//CS
SCREEN_CENTER_X = SCREEN_RECT.width//2//CS
SCREEN_CENTER_Y = SCREEN_RECT.height//2//CS

def load_image(filename):
    image = pygame.image.load(filename)
    image = image.convert_alpha()
    return image

def get_image(sheet, x, y, width, height, useColorKey=False):
    image = pygame.Surface([width, height])
    image.blit(sheet, (0, 0), (x, y, width, height))
    image = image.convert()
    if useColorKey:
        colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey, RLEACCEL)
    #image = pygame.transform.scale(image, (32*2, 32*2))
    return image

DIR_DOWN = 0
DIR_LEFT = 1
DIR_RIGHT = 2
DIR_UP = 3
ANIM_WAIT_COUNT = 24

class Player(pygame.sprite.Sprite):
    def __init__(self, filename):
        pygame.sprite.Sprite.__init__(self)
        sheet = load_image(filename)
        self.images = [[], [], [], []]
        for row in range(0, 4):
            for col in [0, 1, 2, 1]:
                self.images[row].append(get_image(sheet, 0 + 32 * col, 0 + 32 * row, 32, 32, True))
        self.image = self.images[DIR_DOWN][0]
        self.rect = self.image.get_rect()
        self.rect.x = SCREEN_CENTER_X * CS
        self.rect.y = SCREEN_CENTER_Y * CS
        self.frame = 0
        self.anim_count = 0
        self.dir = DIR_DOWN
        self.wx, self.wy = 1, 1
    def update(self):
        self.anim_count += 1
        if self.anim_count >= ANIM_WAIT_COUNT:
            self.anim_count = 0
            self.frame += 1
            if self.frame > 3:
                self.frame = 0
        self.image = self.images[self.dir][self.frame]

class Map:
    def __init__(self, screen, filename, player):
        self.ncol = 0
        self.nrow = 0
        self.screen = screen
        self.player = player
        self.mapData = []
        self.readMap(filename)
        self.sheet0 = load_image("pipo-map001.png")
        self.sheet1 = load_image("pipo-map001_at-umi.png")
        self.images = []
        self.images.append([self.sheet1, 0, 4])  # umi (0)
        self.images.append([self.sheet0, 0, 0])  # shiba (1)
        self.images.append([self.sheet0, 0, 1])  # shiba1 (2)
    def readMap(self, filename):
        with open(filename) as fi:
            line = fi.readline()
            self.ncol, self.nrow = [int(tok) for tok in line.split(",")]
            for row in range(self.nrow):
                line = fi.readline()
                self.mapData.append([int(tok) for tok in line.split(",")])
    def drawImage(self, idx, sx, sy):
        sheet, x, y = self.images[idx]
        self.screen.blit(sheet, (sx * 32, sy * 32), (x * 32, y * 32, 32, 32))
    def draw(self):
        screen_wx = self.player.wx - SCREEN_CENTER_X
        screen_wy = self.player.wy - SCREEN_CENTER_Y
        for sy in range(SCREEN_NROW):
            for sx in range(SCREEN_NCOL):
                wx = screen_wx + sx
                wy = screen_wy + sy
                if not (0 <= wx < self.ncol) or not (0 <= wy < self.nrow):
                    self.drawImage(0, sx, sy)  # umi
                else:
                    idx = self.mapData[wy][wx]
                    self.drawImage(1, sx, sy)  # shiba
                    self.drawImage(idx, sx, sy)
    def can_move_at(self, wx, wy):
        if not (0 <= wx < self.ncol) or not (0 <= wy < self.nrow):
            return False
        idx = self.mapData[wy][wx]
        if idx == 0:  # umi
            return False
        return True

def main():
    pygame.init()
    screen = pygame.display.set_mode(SCREEN_RECT.size)
    pygame.display.set_caption("Short Tale Story")
    player = Player("pipo-charachip021.png")
    group = pygame.sprite.RenderUpdates()
    group.add(player)
    fieldMap = Map(screen, "field01.map", player)
    clock = pygame.time.Clock()

    while True:
        clock.tick(60)
        screen.fill((0, 255, 0))
        fieldMap.draw()
        group.update()
        group.draw(screen)
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                elif event.key == K_DOWN:
                    if fieldMap.can_move_at(player.wx, player.wy + 1):
                        player.dir = DIR_DOWN
                        player.wy += 1
                elif event.key == K_LEFT:
                    if fieldMap.can_move_at(player.wx - 1, player.wy):
                        player.dir = DIR_LEFT
                        player.wx -= 1
                elif event.key == K_RIGHT:
                    if fieldMap.can_move_at(player.wx + 1, player.wy):
                        player.dir = DIR_RIGHT
                        player.wx += 1
                elif event.key == K_UP:
                    if fieldMap.can_move_at(player.wx, player.wy - 1):
                        player.dir = DIR_UP
                        player.wy -= 1

if __name__ == '__main__':
    main()