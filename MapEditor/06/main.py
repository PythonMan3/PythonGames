import pygame
from pygame.locals import *
import sys
import settings as st
from messageEngine import MessageEngine

CS = 32
SCREEN_RECT = Rect(0, 0, CS*25, CS*20)
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
    showGrid = False
    def __init__(self, screen, cursor, palette):
        self.ncol = 0
        self.nrow = 0
        self.screen = screen
        self.cursor = cursor
        self.palette = palette
        self.defaultPaletteIdx = 0
        self.defaultIdx = 4
        self.mapData = []
        self.createNewMap()
        #self.readMap(filename)
    def createNewMap(self):
        self.ncol = st.ncol
        self.nrow = st.nrow
        self.mapData = [[(self.defaultPaletteIdx, self.defaultIdx) for col in range(self.ncol)] for row in range(self.nrow)]
    def readMap(self, filename):
        with open(filename) as fi:
            line = fi.readline()
            self.ncol, self.nrow = [int(tok) for tok in line.split(",")]
            for row in range(self.nrow):
                line = fi.readline()
                self.mapData.append([int(tok) for tok in line.split(",")])
    def handle_keys(self):
        mouse_pressed = pygame.mouse.get_pressed()
        px, py = pygame.mouse.get_pos()
        sx = px // CS
        sy = py // CS
        screen_wx = self.cursor.wx - SCREEN_CENTER_X
        screen_wy = self.cursor.wy - SCREEN_CENTER_Y
        wx = screen_wx + sx
        wy = screen_wy + sy
        if not (0 <= wx < self.ncol) or not (0 <= wy < self.nrow):
            return
        if mouse_pressed[0]:  # left button
            self.mapData[wy][wx] = self.palette.selected_mapchip
        elif mouse_pressed[2]:  # right button
            self.palette.selected_mapchip = self.mapData[wy][wx]
    def update(self):
        self.handle_keys()
    def drawOutImage(self, sx, sy):
        pygame.draw.rect(self.screen, self.COLOR, (CS*sx, CS*sy, CS, CS), self.WIDTH)
        pygame.draw.line(self.screen, self.COLOR, (sx*CS, sy*CS), ((sx+1)*CS, (sy+1)*CS), self.WIDTH)
    def drawImage(self, paletteIdx, idx, sx, sy):
        data = self.palette.mapchipDatas[paletteIdx]
        x, y, movable = data.mapchipData[idx]
        self.screen.blit(data.sheet, (sx * CS, sy * CS), (x * CS, y * CS, CS, CS))
    def draw(self):
        screen_wx = self.cursor.wx - SCREEN_CENTER_X
        screen_wy = self.cursor.wy - SCREEN_CENTER_Y
        for sy in range(SCREEN_NROW):
            for sx in range(SCREEN_NCOL):
                wx = screen_wx + sx
                wy = screen_wy + sy
                if not (0 <= wx < self.ncol) or not (0 <= wy < self.nrow):
                    self.drawOutImage(sx, sy)  # out
                else:
                    paletteIdx, idx = self.mapData[wy][wx]
                    #self.drawImage(1, sx, sy)  # shiba
                    self.drawImage(paletteIdx, idx, sx, sy)
                    # show grid
                    if self.showGrid:
                        pygame.draw.rect(self.screen, (0, 0, 0), (sx * CS, sy * CS, CS, CS), 1)

class MapchipData:
    def __init__(self):
        self.sheet = None
        self.ncol = 0
        self.nrow = 0
        self.mapchipData = {}
        self.mapchipIdx = {}
        self.startRow = 0

class MapchipPalette:
    OUT_COLOR = (255, 255, 255)
    OUT_WIDTH = 1
    CURSOR_COLOR = (0, 255, 0)
    CURSOR_WIDTH = 3
    def __init__(self, screen):
        self.screen = screen
        self.mapchipDatas = []
        self.paletteIdx = 0
        self.numPalette = len(st.mapchipFiles)
        for filename in st.mapchipFiles:
            self.mapchipDatas.append(self.readMapchipFile(filename))
        self.selected_mapchip = (0, 0)  # paletteIdx, mapIdx
    def readMapchipFile(self, filename):
        data = MapchipData()
        data.sheet = load_image(filename)
        data.ncol = data.sheet.get_width() // CS
        data.nrow = data.sheet.get_height() // CS
        idx = 0
        for row in range(data.nrow):
            for col in range(data.ncol):
                data.mapchipData[idx] = (col, row, 1)  # x, y, movable
                data.mapchipIdx[(col, row)] = idx
                idx += 1
        return data
    def handle_mouse(self, button):
        data = self.mapchipDatas[self.paletteIdx]
        if button == 4:
            if data.startRow > 0:
                data.startRow -= 1
        elif button == 5:
            if data.startRow - 1 < data.nrow:
                data.startRow += 1
    def handle_keys(self):
        data = self.mapchipDatas[self.paletteIdx]
        pressed_keys = pygame.key.get_pressed()
        if pressed_keys[K_UP]:
            if data.startRow > 0:
                data.startRow -= 1
        elif pressed_keys[K_DOWN]:
            if data.startRow - 1 < data.nrow:
                data.startRow += 1
        mouse_pressed = pygame.mouse.get_pressed()
        if mouse_pressed[0]:  # left button
            px, py = pygame.mouse.get_pos()
            sx = px // CS
            sy = py // CS
            if 0 <= sx < data.ncol and 0 <= sy < data.nrow:
                sy2 = data.startRow + sy
                try:
                    idx = data.mapchipIdx[(sx, sy2)]
                    self.selected_mapchip = (self.paletteIdx, idx)
                    self.paletteIdx = 0
                    pygame.time.wait(500)
                    return True
                except:
                    pass
        return False
    def update(self):
        return self.handle_keys()
    def drawOutImage(self, sx, sy):
        pygame.draw.rect(self.screen, self.OUT_COLOR, (CS*sx, CS*sy, CS, CS), self.OUT_WIDTH)
        pygame.draw.line(self.screen, self.OUT_COLOR, (sx*CS, sy*CS), ((sx+1)*CS, (sy+1)*CS), self.OUT_WIDTH)
    def drawImage(self, sheet, x, y, sx, sy):
        self.screen.blit(sheet, (sx * 32, sy * 32), (x * 32, y * 32, 32, 32))
    def draw(self):
        # draw out
        for sy in range(SCREEN_NROW):
            for sx in range(SCREEN_NCOL):
                self.drawOutImage(sx, sy)
        # draw mapchip
        data = self.mapchipDatas[self.paletteIdx]
        for sy in range(data.nrow):
            for sx in range(data.ncol):
                sy2 = data.startRow + sy
                try:
                    idx = data.mapchipIdx[(sx, sy2)]
                    x, y, movable = data.mapchipData[idx]
                    self.drawImage(data.sheet, x, y, sx, sy)
                except:
                    pass
        # draw mouse cursor
        px, py = pygame.mouse.get_pos()
        sx = px // CS
        sy = py // CS
        pygame.draw.rect(self.screen, self.CURSOR_COLOR, (CS * sx, CS * sy, CS, CS), self.CURSOR_WIDTH)

def draw_selection(messageEngine, screen, palette, cursor):
    # draw mapchip
    paletteIdx, idx = palette.selected_mapchip
    data = palette.mapchipDatas[paletteIdx]
    x, y, movable = data.mapchipData[idx]
    screen.blit(data.sheet, (10, 10), (x*CS, y*CS, CS, CS))
    pygame.draw.rect(screen, (0, 255, 0), (10, 10, CS, CS), 3)
    # draw mouse position
    px, py = pygame.mouse.get_pos()
    sx = px // CS
    sy = py // CS
    screen_wx = cursor.wx - SCREEN_CENTER_X
    screen_wy = cursor.wy - SCREEN_CENTER_Y
    wx = screen_wx + sx
    wy = screen_wy + sy
    messageEngine.draw_string(screen, (10, 56), "{} {}".format(wx, wy))

STATE_MAP = 0
STATE_PALETTE = 1

def main():
    pygame.init()
    screen = pygame.display.set_mode(SCREEN_RECT.size)
    pygame.display.set_caption("Map Editor")
    palette = MapchipPalette(screen)
    cursor = Cursor()
    fieldMap = Map(screen, cursor, palette)
    cursor.set_map(fieldMap)
    messageEngine = MessageEngine()
    clock = pygame.time.Clock()
    state = STATE_MAP

    while True:
        clock.tick(60)
        screen.fill((0, 0, 0))
        if state == STATE_MAP:
            cursor.update()
            fieldMap.update()
            fieldMap.draw()
            draw_selection(messageEngine, screen, palette, cursor)
        elif state == STATE_PALETTE:
            if palette.update():
                state = STATE_MAP
                pygame.event.clear()
                continue
            palette.draw()
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                elif event.key == K_SPACE:
                    if state == STATE_MAP:
                        state = STATE_PALETTE
                    elif state == STATE_PALETTE:
                        palette.paletteIdx = (palette.paletteIdx + 1) % palette.numPalette
                        if palette.paletteIdx == 0:
                            state = STATE_MAP
                elif event.key == K_g:
                    fieldMap.showGrid = not fieldMap.showGrid
            elif event.type == MOUSEBUTTONDOWN:
                if event.button in [4, 5]:  # mouse scroll
                    palette.handle_mouse(event.button)

if __name__ == '__main__':
    main()