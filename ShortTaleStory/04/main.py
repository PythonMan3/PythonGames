import pygame
from pygame.locals import *
import sys

SCREEN_RECT = Rect(0, 0, 640, 480)

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
        self.rect.center = (SCREEN_RECT.width//2, SCREEN_RECT.height//2)
        self.frame = 0
        self.anim_count = 0
        self.dir = DIR_DOWN
    def update(self):
        self.anim_count += 1
        if self.anim_count >= ANIM_WAIT_COUNT:
            self.anim_count = 0
            self.frame += 1
            if self.frame > 3:
                self.frame = 0
        self.image = self.images[self.dir][self.frame]

class Map:
    def __init__(self, screen, filename):
        self.ncol = 0
        self.nrow = 0
        self.screen = screen
        self.mapData = []
        self.readMap(filename)
        self.sheet0 = load_image("pipo-map001.png")
        self.sheet1 = load_image("pipo-map001_at-umi.png")
        self.images = []
        self.images.append([self.sheet1, 0, 4])
        self.images.append([self.sheet0, 0, 0])
        self.images.append([self.sheet0, 0, 1])
    def readMap(self, filename):
        with open(filename) as fi:
            line = fi.readline()
            self.ncol, self.nrow = [int(tok) for tok in line.split(",")]
            for row in range(self.nrow):
                line = fi.readline()
                self.mapData.append([int(tok) for tok in line.split(",")])
    def draw(self):
        for row, rowData in enumerate(self.mapData):
            for col, colData in enumerate(rowData):
                sheet0, x0, y0 = self.images[1]
                sheet, x, y = self.images[colData]
                self.screen.blit(sheet0, (col * 32, row * 32), (x0 * 32, y0 * 32, 32, 32))  # background
                self.screen.blit(sheet, (col*32, row*32), (x*32, y*32, 32, 32))

def main():
    pygame.init()
    screen = pygame.display.set_mode(SCREEN_RECT.size)
    pygame.display.set_caption("Short Tale Story")
    player = Player("pipo-charachip021.png")
    group = pygame.sprite.RenderUpdates()
    group.add(player)
    fieldMap = Map(screen, "field01.map")
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

if __name__ == '__main__':
    main()