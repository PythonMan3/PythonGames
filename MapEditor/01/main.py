import pygame
from pygame.locals import *
import sys
import settings as st

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

class Cursor:
    def __init__(self):
        self.wx, self.wy = 1, 1
        self.map = None
    def set_map(self, map_):
        self.map = map_
    def handle_keys(self):
        pressed_keys = pygame.key.get_pressed()
        if pressed_keys[K_DOWN] and self.wy < self.map.nrow:
            self.wy += 1
        elif pressed_keys[K_LEFT] and self.wx > 0:
            self.wx -= 1
        elif pressed_keys[K_RIGHT] and self.wx < self.map.ncol:
            self.wx += 1
        elif pressed_keys[K_UP] and self.wy > 0:
            self.wy -= 1
    def update(self):
        self.handle_keys()

class Map:
    COLOR = (255, 0, 0)
    WIDTH = 1
    def __init__(self, screen, cursor):
        self.ncol = 0
        self.nrow = 0
        self.screen = screen
        self.cursor = cursor
        self.mapData = []
        self.defaultIdx = 0
        self.createNewMap()
        #self.readMap(filename)
        self.sheet0 = load_image("pipo-map001.png")
        self.sheet1 = load_image("pipo-map001_at-umi.png")
        self.images = []
        self.images.append([self.sheet1, 0, 4])  # umi (0)
        self.images.append([self.sheet0, 0, 0])  # shiba (1)
        self.images.append([self.sheet0, 0, 1])  # shiba1 (2)
    def createNewMap(self):
        self.ncol = st.ncol
        self.nrow = st.nrow
        self.mapData = [[self.defaultIdx for col in range(self.ncol)] for row in range(self.nrow)]
    def readMap(self, filename):
        with open(filename) as fi:
            line = fi.readline()
            self.ncol, self.nrow = [int(tok) for tok in line.split(",")]
            for row in range(self.nrow):
                line = fi.readline()
                self.mapData.append([int(tok) for tok in line.split(",")])
    def drawOutImage(self, sx, sy):
        pygame.draw.rect(self.screen, self.COLOR, (CS*sx, CS*sy, CS, CS), self.WIDTH)
        pygame.draw.line(self.screen, self.COLOR, (sx*CS, sy*CS), ((sx+1)*CS, (sy+1)*CS), self.WIDTH)
    def drawImage(self, idx, sx, sy):
        sheet, x, y = self.images[idx]
        self.screen.blit(sheet, (sx * 32, sy * 32), (x * 32, y * 32, 32, 32))
    def draw(self):
        screen_wx = self.cursor.wx - SCREEN_CENTER_X
        screen_wy = self.cursor.wy - SCREEN_CENTER_Y
        for sy in range(-1, SCREEN_NROW+1):
            for sx in range(-1, SCREEN_NCOL+1):
                wx = screen_wx + sx
                wy = screen_wy + sy
                if not (0 <= wx < self.ncol) or not (0 <= wy < self.nrow):
                    self.drawOutImage(sx, sy)  # out
                else:
                    idx = self.mapData[wy][wx]
                    #self.drawImage(1, sx, sy)  # shiba
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
    pygame.display.set_caption("Map Editor")
    cursor = Cursor()
    fieldMap = Map(screen, cursor)
    cursor.set_map(fieldMap)
    clock = pygame.time.Clock()

    while True:
        clock.tick(60)
        screen.fill((0, 0, 0))
        fieldMap.draw()
        cursor.update()
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