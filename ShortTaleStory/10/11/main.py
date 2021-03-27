import pygame
from pygame.locals import *
import os
import sys
import random

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
MOVE_VELOCITY = 4
TYPE_STOP, TYPE_MOVE = 0, 1  # 移動タイプ
PROB_MOVE = 0.005  # 移動確率 (1フレーム当たり0.5%)

class Character:
    def __init__(self, name, filename, dir_, pos, move_type):
        sheet = load_image(filename)
        self.images = [[], [], [], []]
        for row in range(0, 4):
            for col in [0, 1, 2, 1]:
                self.images[row].append(get_image(sheet, 0 + 32 * col, 0 + 32 * row, 32, 32, True))
        self.image = self.images[dir_][0]
        self.frame = 0
        self.anim_count = 0
        self.name = name
        self.dir = dir_
        self.wx, self.wy = pos
        self.moving = False
        self.vx, self.vy = 0, 0
        self.px, self.py = 0, 0
        self.move_type = move_type
    def update(self, map_):
        if self.moving:
            self.px += self.vx
            self.py += self.vy
            if self.px % CS == 0 and self.py % CS == 0:
                self.moving = False
                self.wx += self.px // CS
                self.wy += self.py // CS
                self.vx, self.vy = 0, 0
                self.px, self.py = 0, 0
        elif self.move_type == TYPE_MOVE and random.random() < PROB_MOVE:
            # 移動中でないならPROB_MOVEの確率でランダム移動開始
            self.dir = random.randint(0, 3)  # 0-3のいずれか
            if self.dir == DIR_DOWN:
                if map_.can_move_at(self.wx, self.wy + 1):
                    self.moving = True
                    self.vy = MOVE_VELOCITY
            elif self.dir == DIR_LEFT:
                if map_.can_move_at(self.wx - 1, self.wy):
                    self.moving = True
                    self.vx = -MOVE_VELOCITY
            elif self.dir == DIR_RIGHT:
                if map_.can_move_at(self.wx + 1, self.wy):
                    self.moving = True
                    self.vx = MOVE_VELOCITY
            elif self.dir == DIR_UP:
                if map_.can_move_at(self.wx, self.wy - 1):
                    self.moving = True
                    self.vy = -MOVE_VELOCITY
        # キャラクターアニメーション（frameに応じて描画イメージを切り替える）
        self.anim_count += 1
        if self.anim_count >= ANIM_WAIT_COUNT:
            self.anim_count = 0
            self.frame += 1
            if self.frame > 3:
                self.frame = 0
        self.image = self.images[self.dir][self.frame]
    def draw(self, screen, pwx, pwy, px, py):
        screen_wx = self.wx - pwx  + SCREEN_CENTER_X
        screen_wy = self.wy - pwy  + SCREEN_CENTER_Y
        offset_x = px + self.px
        offset_y = py + self.py
        screen.blit(self.image, (screen_wx * CS + offset_x, screen_wy * CS + offset_y))

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
        self.wx, self.wy = 11, 93
        self.map = None
        self.moving = False
        self.vx, self.vy = 0, 0
        self.px, self.py = 0, 0
    def set_map(self, map_):
        self.map = map_
    def handle_keys(self):
        if self.moving:
            self.px += self.vx
            self.py += self.vy
            if self.px % CS == 0 and self.py % CS == 0:
                self.moving = False
                self.wx += self.px // CS
                self.wy += self.py // CS
                self.vx, self.vy = 0, 0
                self.px, self.py = 0, 0
                evt = self.map.get_event(self.wx, self.wy)
                if evt:
                    if isinstance(evt, MoveEvent):
                        self.wx = evt.dest_wx
                        self.wy = evt.dest_wy
                        self.dir = evt.dest_dir
                        mapFileName = evt.dest_map_name + ".map"
                        self.map.create_map(mapFileName)
        else:
            pressed_keys = pygame.key.get_pressed()
            if pressed_keys[K_DOWN]:
                self.dir = DIR_DOWN
                if self.map.can_move_at(self.wx, self.wy + 1):
                    self.moving = True
                    self.vy = MOVE_VELOCITY
            elif pressed_keys[K_LEFT]:
                self.dir = DIR_LEFT
                if self.map.can_move_at(self.wx - 1, self.wy):
                    self.moving = True
                    self.vx = -MOVE_VELOCITY
            elif pressed_keys[K_RIGHT]:
                self.dir = DIR_RIGHT
                if self.map.can_move_at(self.wx + 1, self.wy):
                    self.moving = True
                    self.vx = MOVE_VELOCITY
            elif pressed_keys[K_UP]:
                self.dir = DIR_UP
                if self.map.can_move_at(self.wx, self.wy - 1):
                    self.moving = True
                    self.vy = -MOVE_VELOCITY
    def update(self):
        self.handle_keys()
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
        self.defaultPaletteIdx = 0
        self.defaultIdx = 0
        self.mapDataBottom = []
        self.mapDataTop = []
        self.mapchipDatas = []
        self.event_map = {}
        self.charas = []
        self.loadMap(filename)
        self.loadEvent(filename)
    def update(self):
        # マップにいるキャラクターの更新
        for chara in self.charas:
            chara.update(self)  # mapを渡す
    def add_chara(self, chara):
        self.charas.append(chara)
    def loadMap(self, mapFileName):
        # load map file
        mapchipDefFiles = []
        with open(mapFileName, "r") as fi:
            num_def_file = int(fi.readline())
            for i in range(num_def_file):
                def_f = fi.readline().strip()
                mapchipDefFiles.append(def_f)
            self.defaultPaletteIdx, self.defaultIdx = [int(tok) for tok in fi.readline().split(",")]
            self.ncol, self.nrow = [int(tok) for tok in fi.readline().split(",")]
            def readMapData(mapData):
                for row in range(self.nrow):
                    colDatas = [tuple(int(tok2) for tok2 in tok.split(":")) for tok in fi.readline().split(",")]
                    for col, colData in enumerate(colDatas):
                        mapData[row][col] = colData
            # bottom
            line = fi.readline()
            if not line.startswith("Bottom"):
                print("Format Error!")
            self.mapDataBottom = [[(self.defaultPaletteIdx, self.defaultIdx) for col in range(self.ncol)] for row in range(self.nrow)]
            readMapData(self.mapDataBottom)
            # top
            line = fi.readline()
            if not line.startswith("Top"):
                print("Format Error!")
            self.mapDataTop = [[(self.defaultPaletteIdx, self.defaultIdx) for col in range(self.ncol)] for row in range(self.nrow)]
            readMapData(self.mapDataTop)
        # load mapchip definition file
        self.mapchipDatas = []
        for mapchipDefFile in mapchipDefFiles:
            with open(mapchipDefFile, "r") as fi:
                png_f = fi.readline().strip()
                data = MapchipData()
                data.mapchipFile = png_f
                self.mapchipDatas.append(data)
                data.sheet = load_image(os.path.join("data", png_f))
                data.ncol, data.nrow = [int(tok) for tok in fi.readline().split(",")]
                for row in range(data.nrow):
                    for col in range(data.ncol):
                        idx, movable = [int(tok) for tok in fi.readline().split(",")]
                        data.mapchipData[idx] = movable
    def loadEvent(self, mapFileName):
        self.event_map = {}
        self.charas = []
        eventFileName = os.path.splitext(mapFileName)[0] + ".evt"
        if not os.path.exists(eventFileName):
            print("Event file '{}' is not found!".format(eventFileName))
        with open(eventFileName) as fi:
            for line in fi:
                if line.startswith("#"): continue
                toks = [tok.strip() for tok in line.split(",")]
                if len(toks) == 0: continue
                event_type = toks[0]
                if event_type == "MOVE":
                    self.add_move_event(toks)
                elif event_type == "CHARA":
                    self.create_chara(toks)
    def add_move_event(self, toks):
        if len(toks) < 7:
            return
        wx, wy = int(toks[1]), int(toks[2])
        dest_map_name = toks[3]
        dest_wx, dest_wy = int(toks[4]), int(toks[5])
        dest_dir = int(toks[6])
        evt = MoveEvent(wx, wy, dest_map_name, dest_wx, dest_wy, dest_dir)
        self.event_map[(wx, wy)]= evt
    def create_chara(self, toks):
        if len(toks) < 7:
            return
        name = toks[1]
        filename = toks[2]
        dir_ = int(toks[3])
        pos_x = int(toks[4])
        pos_y = int(toks[5])
        move_type = int(toks[6])
        filepath = os.path.join("data", filename)
        if not os.path.exists(filepath):
            return
        chara = Character(name, filepath, dir_, (pos_x, pos_y), move_type)
        self.add_chara(chara)
    def get_event(self, wx, wy):
        if (wx, wy) in self.event_map:
            return self.event_map[(wx, wy)]
        return None
    def create_map(self, mapFileName):
        self.loadMap(mapFileName)
        self.loadEvent(mapFileName)
    def to_xy(self, data, idx):
        return (idx % data.ncol, idx // data.ncol)
    def drawImage(self, paletteIdx, idx, sx, sy, px, py):
        data = self.mapchipDatas[paletteIdx]
        x, y = self.to_xy(data, idx)
        self.screen.blit(data.sheet, (sx * CS + px, sy * CS + py), (x * CS, y * CS, CS, CS))
    def draw(self):
        px = -self.player.px
        py = -self.player.py
        screen_wx = self.player.wx - SCREEN_CENTER_X
        screen_wy = self.player.wy - SCREEN_CENTER_Y
        for sy in range(-1, SCREEN_NROW+1):
            for sx in range(-1, SCREEN_NCOL+1):
                wx = screen_wx + sx
                wy = screen_wy + sy
                if not (0 <= wx < self.ncol) or not (0 <= wy < self.nrow):
                    self.drawImage(self.defaultPaletteIdx, self.defaultIdx, sx, sy, px, py)
                else:
                    paletteIdx, idx = self.mapDataBottom[wy][wx]
                    self.drawImage(paletteIdx, idx, sx, sy, px, py)
                    paletteIdx, idx = self.mapDataTop[wy][wx]
                    self.drawImage(paletteIdx, idx, sx, sy, px, py)
        # このマップにいるキャラクターを描画
        for chara in self.charas:
            chara.draw(self.screen, self.player.wx, self.player.wy, px, py)
    def can_move_at(self, wx, wy):
        if not (0 <= wx < self.ncol) or not (0 <= wy < self.nrow):
            return False
        paletteIdx, idx = self.mapDataTop[wy][wx]
        data = self.mapchipDatas[paletteIdx]
        movable = data.mapchipData[idx]
        # キャラクターと衝突しないか？
        for chara in self.charas:
            if chara.wx == wx and chara.wy == wy:
                movable = False
        # プレイヤーと衝突しないか？
        if self.player.wx == wx and self.player.wy == wy:
            movable = False
        if movable:
            return True
        else:
            return False

class MapchipData:
    def __init__(self):
        self.sheet = None
        self.mapchipFile = ""
        self.ncol = 0
        self.nrow = 0
        self.mapchipData = {}
        self.startRow = 0

class MoveEvent:
    def __init__(self, wx, wy, dest_map_name, dest_wx, dest_wy, dest_dir):
        self.wx, self.wy = wx, wy  # イベント座標
        self.dest_map_name = dest_map_name  # 移動先マップ名
        self.dest_wx, self.dest_wy = dest_wx, dest_wy  # 移動先座標
        self.dest_dir = dest_dir  # 移動先方向

def main():
    pygame.init()
    screen = pygame.display.set_mode(SCREEN_RECT.size)
    pygame.display.set_caption("Short Tale Story")
    player = Player(os.path.join("data", "pipo-charachip021.png"))
    group = pygame.sprite.RenderUpdates()
    group.add(player)
    fieldMap = Map(screen, "field.map", player)
    player.set_map(fieldMap)
    clock = pygame.time.Clock()

    while True:
        clock.tick(60)
        screen.fill((0, 255, 0))
        fieldMap.update()
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