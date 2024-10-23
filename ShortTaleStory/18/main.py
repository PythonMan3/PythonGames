import pygame
from pygame.locals import *
import os
import sys
import random
from messageEngine import MessageEngine
import player_level_data

SCREEN_RECT = Rect(0, 0, 640, 480)
CS = 32
SCREEN_NCOL = SCREEN_RECT.width//CS
SCREEN_NROW = SCREEN_RECT.height//CS
SCREEN_CENTER_X = SCREEN_RECT.width//2//CS
SCREEN_CENTER_Y = SCREEN_RECT.height//2//CS
# ゲーム全体のデータ
TITLE, FIELD, TALK, COMMAND, BATTLE_INIT, BATTLE_COMMAND, BATTLE_PROCESS, BATTLE_END = range(8)
game_state = TITLE
PROB_ENCOUNT = 0.05  # エンカウント率(5%)

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
    def __init__(self, name, filename, dir_, pos, move_type, message):
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
        self.message = message
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
        self.start()
    def get_player_level_status(self, level):
        return {"name": "ゆうしゃ",
            "lv": level,
            "hp": player_level_data.level_stats[level]["hp"],
            "mp": player_level_data.level_stats[level]["mp"],
            "attack": player_level_data.level_stats[level]["attack"],
            "defense": player_level_data.level_stats[level]["defense"],
            "speed": player_level_data.level_stats[level]["speed"]}
    def start(self):
        # プレイヤーのステータス
        self.player_status = self.get_player_level_status(1)  # HPや攻撃力をリセット
    def set_map(self, map_):
        self.map = map_
    def handle_keys(self, battle):
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
                    self.check_encounter(battle)
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
    def update(self, battle):
        self.handle_keys(battle)
        self.anim_count += 1
        if self.anim_count >= ANIM_WAIT_COUNT:
            self.anim_count = 0
            self.frame += 1
            if self.frame > 3:
                self.frame = 0
        self.image = self.images[self.dir][self.frame]
    def check_encounter(self, battle):
        global game_state
        # エンカウント発生
        if self.map.name == "field" and random.random() < PROB_ENCOUNT:
            game_state = BATTLE_INIT
            battle.start()
    def talk(self, map):
        """キャラクターが向いている方向のとなりにキャラクターがいるか調べる"""
        # 向いている方向のとなりの座標を求める
        nextx, nexty = self.wx, self.wy
        if self.dir == DIR_DOWN:
            nexty = self.wy + 1
            event = self.map.get_event(nextx, nexty)
            if isinstance(event, Object) and event.paletteIdx == 2 and event.idx == 803:  # テーブル
                nexty += 1  # テーブルがあったらさらに隣
        elif self.dir == DIR_LEFT:
            nextx = self.wx - 1
            event = self.map.get_event(nextx, nexty)
            if isinstance(event, Object) and event.paletteIdx == 2 and event.idx == 803:  # テーブル
                nextx -= 1  # テーブルがあったらさらに隣
        elif self.dir == DIR_RIGHT:
            nextx = self.wx + 1
            event = self.map.get_event(nextx, nexty)
            if isinstance(event, Object) and event.paletteIdx == 2 and event.idx == 803:  # テーブル
                nextx += 1  # テーブルがあったらさらに隣
        elif self.dir == DIR_UP:
            nexty = self.wy - 1
            event = self.map.get_event(nextx, nexty)
            if isinstance(event, Object) and event.paletteIdx == 2 and event.idx == 803:  # テーブル
                nexty -= 1  # テーブルがあったらさらに隣
        # その方向にキャラクターがいるか？
        chara = map.get_chara(nextx, nexty)
        # キャラクターがいればプレイヤーの方向へ向ける
        if chara != None:
            if self.dir == DIR_DOWN:
                chara.dir = DIR_UP
            elif self.dir == DIR_LEFT:
                chara.dir = DIR_RIGHT
            elif self.dir == DIR_RIGHT:
                chara.dir = DIR_LEFT
            elif self.dir == DIR_UP:
                chara.dir = DIR_DOWN
            chara.update(map)  # 向きを変えたので更新
        return chara
    def search(self):
        """足もとに宝箱があるか調べる"""
        event = self.map.get_event(self.wx, self.wy)
        if isinstance(event, Treasure):
            return event
        return None
    def open(self):
        """目の前にとびらがあるか調べる"""
        # 向いている方向のとなりの座標を求める
        nextx, nexty = self.wx, self.wy
        if self.dir == DIR_DOWN:
            nexty = self.wy + 1
        elif self.dir == DIR_LEFT:
            nextx = self.wx - 1
        elif self.dir == DIR_RIGHT:
            nextx = self.wx + 1
        elif self.dir == DIR_UP:
            nexty = self.wy - 1
        # その場所にとびらがあるか？
        event = self.map.get_event(nextx, nexty)
        if isinstance(event, Door):
            return event
        return None

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
        self.name = ""  # マップの名前(ファイル名)
        self.loadMap(filename)
        self.loadEvent(filename)
    def update(self):
        # マップにいるキャラクターの更新
        for chara in self.charas:
            chara.update(self)  # mapを渡す
    def add_chara(self, chara):
        self.charas.append(chara)
    def loadMap(self, mapFileName):
        # set map name
        self.name = os.path.splitext(os.path.basename(mapFileName))[0]
        # load map file
        mapchipDefFiles = []
        with open(mapFileName, "r", encoding="utf-8") as fi:
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
            with open(mapchipDefFile, "r", encoding="utf-8") as fi:
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
        with open(eventFileName, "r", encoding="utf-8") as fi:
            for line in fi:
                if line.startswith("#"): continue
                toks = [tok.strip() for tok in line.split(",")]
                if len(toks) == 0: continue
                event_type = toks[0]
                if event_type == "MOVE":
                    self.add_move_event(toks)
                elif event_type == "CHARA":
                    self.create_chara(toks)
                elif event_type == "TREASURE":  # 宝箱
                    self.create_treasure(toks)
                elif event_type == "DOOR":  # とびら
                    self.create_door(toks)
                elif event_type == "OBJECT":  # 一般オブジェクト（玉座など）
                    self.create_obj(toks)
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
        message = toks[7]
        filepath = os.path.join("data", filename)
        if not os.path.exists(filepath):
            return
        chara = Character(name, filepath, dir_, (pos_x, pos_y), move_type, message)
        self.add_chara(chara)
    def create_treasure(self, data):
        """宝箱を作成してeventsに追加する"""
        x, y = int(data[1]), int(data[2])
        item_name = data[3]
        treasure = Treasure((x,y), self, item_name)
        self.event_map[(treasure.wx, treasure.wy)] = treasure
    def create_door(self, data):
        """とびらを作成してeventsに追加する"""
        x, y = int(data[1]), int(data[2])
        door = Door((x,y), self)
        self.event_map[(door.wx, door.wy)] = door
    def create_obj(self, data):
        """一般オブジェクトを作成してeventsに追加する"""
        x, y = int(data[1]), int(data[2])
        paletteIdx = int(data[3])
        idx = int(data[4])
        is_show = bool(int(data[5]))
        is_collision = bool(int(data[6]))
        obj = Object((x,y), self, paletteIdx, idx, is_show, is_collision)
        self.event_map[(obj.wx, obj.wy)] = obj
    def get_event(self, wx, wy):
        if (wx, wy) in self.event_map:
            return self.event_map[(wx, wy)]
        return None
    def remove_event(self, event):
        """eventを削除する"""
        if (event.wx, event.wy) in self.event_map:
            self.event_map.pop((event.wx, event.wy))
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
        # このマップにあるイベントを描画
        for event in self.event_map.values():
            if isinstance(event, (Door, Treasure, Object)):
                event.draw(self.screen, self.player.wx, self.player.wy, px, py)
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
                break
        # プレイヤーと衝突しないか？
        if self.player.wx == wx and self.player.wy == wy:
            movable = False
        # イベントと衝突しないか？
        for event in self.event_map.values():
            if (isinstance(event, Door) and not event.is_opened) or \
                (isinstance(event, Object) and event.is_collision):
                event_data = self.mapchipDatas[event.paletteIdx]
                event_movable = event_data.mapchipData[event.idx]
                if not event_movable and (event.wx == wx and event.wy == wy):
                    movable = False
                    break
        return movable
    def get_chara(self, x, y):
        """(x,y)にいるキャラクターを返す。いなければNone"""
        for chara in self.charas:
            if chara.wx == x and chara.wy == y:
                return chara
        return None

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

class Treasure():
    """宝箱"""
    def __init__(self, pos, map_, item_name):
        self.wx, self.wy = pos[0], pos[1]  # 宝箱座標
        self.paletteIdx = 2
        self.idx = 990  # 閉じた宝箱
        self.paletteIdx2 = 2
        self.idx2 = 998  # 開いた宝箱
        self.map = map_
        self.is_opened = False
        self.item_name = item_name  # アイテム名
    def open(self):
        """宝箱をあける"""
        self.is_opened = True
        # TODO: アイテムを追加する処理
    def draw(self, screen, pwx, pwy, px, py):
        """宝箱を描画"""
        screen_wx = self.wx - pwx + SCREEN_CENTER_X
        screen_wy = self.wy - pwy + SCREEN_CENTER_Y
        paletteIdx = self.paletteIdx
        idx = self.idx
        if self.is_opened:
            paletteIdx = self.paletteIdx2
            idx = self.idx2
        self.map.drawImage(paletteIdx, idx, screen_wx, screen_wy, px, py)
    def __str__(self):
        return "TREASURE,%d,%d,%s" % (self.wx, self.wy, self.item_name)

class Door:
    """とびら"""
    def __init__(self, pos, map_):
        self.wx, self.wy = pos[0], pos[1]
        self.paletteIdx = 0
        self.idx = 5
        self.map = map_
        self.is_opened = False
    def open(self):
        """とびらをあける"""
        self.is_opened = True
    def draw(self, screen, pwx, pwy, px, py):
        """ドアを描画"""
        screen_wx = self.wx - pwx + SCREEN_CENTER_X
        screen_wy = self.wy - pwy + SCREEN_CENTER_Y
        if not self.is_opened:
            self.map.drawImage(self.paletteIdx, self.idx, screen_wx, screen_wy, px, py)
    def __str__(self):
        return "DOOR,%d,%d" % (self.wx, self.wy)

class Object:
    """一般オブジェクト"""
    def __init__(self, pos, map_, paletteIdx, idx, is_show, is_collision):
        self.wx, self.wy = pos[0], pos[1]
        self.paletteIdx = paletteIdx
        self.idx = idx
        self.map = map_
        self.is_show = is_show
        self.is_collision = is_collision
    def draw(self, screen, pwx, pwy, px, py):
        """オフセットを考慮してイベントを描画"""
        screen_wx = self.wx - pwx + SCREEN_CENTER_X
        screen_wy = self.wy - pwy + SCREEN_CENTER_Y
        if self.is_show:
            self.map.drawImage(self.paletteIdx, self.idx, screen_wx, screen_wy, px, py)
    def __str__(self):
        return "OBJECT,%d,%d,%d" % (self.wx, self.wy)

class Window:
    """ウィンドウの基本クラス"""
    EDGE_WIDTH = 4  # 白枠の幅
    def __init__(self, rect):
        self.rect = rect  # 一番外側の白い矩形
        self.inner_rect = self.rect.inflate(-self.EDGE_WIDTH*2, -self.EDGE_WIDTH*2)  # 内側の黒い矩形
        self.is_visible = False  # ウィンドウを表示中か？
    def draw(self, screen):
        """ウィンドウを描画"""
        if self.is_visible == False: return
        pygame.draw.rect(screen, (255,255,255), self.rect, 0)
        pygame.draw.rect(screen, (0,0,0), self.inner_rect, 0)
    def show(self):
        """ウィンドウを表示"""
        self.is_visible = True
    def hide(self):
        """ウィンドウを隠す"""
        self.is_visible = False

class MessageWindow(Window):
    """メッセージウィンドウ"""
    MAX_CHARS_PER_LINE = 20    # 1行の最大文字数
    MAX_LINES_PER_PAGE = 3     # 1行の最大行数（4行目は▼用）
    MAX_CHARS_PER_PAGE = 20*3  # 1ページの最大文字数
    MAX_LINES = 30             # メッセージを格納できる最大行数
    LINE_HEIGHT = 8            # 行間の大きさ
    animcycle = 24
    def __init__(self, rect, msg_engine):
        Window.__init__(self, rect)
        self.text_rect = self.inner_rect.inflate(-32, -32)  # テキストを表示する矩形
        self.text = []  # メッセージ
        self.cur_page = 0  # 現在表示しているページ
        self.cur_pos = 0  # 現在ページで表示した最大文字数
        self.next_flag = False  # 次ページがあるか？
        self.hide_flag = False  # 次のキー入力でウィンドウを消すか？
        self.msg_engine = msg_engine  # メッセージエンジン
        self.cursor = load_image(os.path.join("data", "cursor.png"))  # カーソル画像
        self.frame = 0
    def set(self, message):
        """メッセージをセットしてウィンドウを画面に表示する"""
        self.cur_pos = 0
        self.cur_page = 0
        self.next_flag = False
        self.hide_flag = False
        # 全角スペースで初期化
        self.text = ['　'] * (self.MAX_LINES*self.MAX_CHARS_PER_LINE)
        # メッセージをセット
        p = 0
        for i in range(len(message)):
            ch = message[i]
            if ch == "/":  # /は改行文字
                self.text[p] = "/"
                p += self.MAX_CHARS_PER_LINE
                p = (p//self.MAX_CHARS_PER_LINE)*self.MAX_CHARS_PER_LINE
            elif ch == "%":  # \fは改ページ文字
                self.text[p] = "%"
                p += self.MAX_CHARS_PER_PAGE
                p = (p//self.MAX_CHARS_PER_PAGE)*self.MAX_CHARS_PER_PAGE
            else:
                self.text[p] = ch
                p += 1
        self.text[p] = "$"  # 終端文字
        self.show()
    def update(self):
        """メッセージウィンドウを更新する
        メッセージが流れるように表示する"""
        if self.is_visible:
            if self.next_flag == False:
                self.cur_pos += 1  # 1文字流す
                # テキスト全体から見た現在位置
                p = self.cur_page * self.MAX_CHARS_PER_PAGE + self.cur_pos
                if self.text[p] == "/":  # 改行文字
                    self.cur_pos += self.MAX_CHARS_PER_LINE
                    self.cur_pos = (self.cur_pos//self.MAX_CHARS_PER_LINE) * self.MAX_CHARS_PER_LINE
                elif self.text[p] == "%":  # 改ページ文字
                    self.cur_pos += self.MAX_CHARS_PER_PAGE
                    self.cur_pos = (self.cur_pos//self.MAX_CHARS_PER_PAGE) * self.MAX_CHARS_PER_PAGE
                elif self.text[p] == "$":  # 終端文字
                    self.hide_flag = True
                # 1ページの文字数に達したら▼を表示
                if self.cur_pos % self.MAX_CHARS_PER_PAGE == 0:
                    self.next_flag = True
        self.frame += 1
    def draw(self, screen):
        """メッセージを描画する
        メッセージウィンドウが表示されていないときは何もしない"""
        Window.draw(self, screen)
        if self.is_visible == False: return
        # 現在表示しているページのcur_posまでの文字を描画
        for i in range(self.cur_pos):
            ch = self.text[self.cur_page*self.MAX_CHARS_PER_PAGE+i]
            if ch == "/" or ch == "%" or ch == "$": continue  # 制御文字は表示しない
            dx = self.text_rect[0] + MessageEngine.FONT_WIDTH * (i % self.MAX_CHARS_PER_LINE)
            dy = self.text_rect[1] + (self.LINE_HEIGHT+MessageEngine.FONT_HEIGHT) * (i // self.MAX_CHARS_PER_LINE)
            self.msg_engine.draw_character(screen, (dx,dy), ch)
        # 最後のページでない場合は▼を表示
        if (not self.hide_flag) and self.next_flag:
            if self.frame // self.animcycle % 2 == 0:
                dx = self.text_rect[0] + (self.MAX_CHARS_PER_LINE//2) * MessageEngine.FONT_WIDTH - MessageEngine.FONT_WIDTH//2
                dy = self.text_rect[1] + (self.LINE_HEIGHT + MessageEngine.FONT_HEIGHT) * 3
                screen.blit(self.cursor, (dx,dy))
    def next(self):
        """メッセージを先に進める"""
        # 現在のページが最後のページだったらウィンドウを閉じる
        if self.hide_flag:
            self.hide()
            return False
        # ▼が表示されてれば次のページへ
        if self.next_flag:
            self.cur_page += 1
            self.cur_pos = 0
            self.next_flag = False
        return True

class CommandWindow(Window):
    LINE_HEIGHT = 8  # 行間の大きさ
    TALK, STATUS, EQUIPMENT, DOOR, SPELL, ITEM, TACTICS, SEARCH = range(0, 8)
    COMMAND = ["はなす", "つよさ", "そうび", "とびら",
               "じゅもん", "どうぐ", "さくせん", "しらべる"]
    def __init__(self, rect, msg_engine):
        Window.__init__(self, rect)
        self.text_rect = self.inner_rect.inflate(-32, -32)
        self.command = self.TALK  # 選択中のコマンド
        self.msg_engine = msg_engine
        self.cursor = load_image(os.path.join("data", "cursor2.png"))
        self.frame = 0
    def draw(self, screen):
        Window.draw(self, screen)
        if self.is_visible == False: return
        # はなす、つよさ、そうび、とびらを描画
        for i in range(0, 4):
            dx = self.text_rect[0] + MessageEngine.FONT_WIDTH
            dy = self.text_rect[1] + (self.LINE_HEIGHT+MessageEngine.FONT_HEIGHT) * (i % 4)
            self.msg_engine.draw_string(screen, (dx,dy), self.COMMAND[i])
        # じゅもん、どうぐ、さくせん、しらべるを描画
        for i in range(4, 8):
            dx = self.text_rect[0] + MessageEngine.FONT_WIDTH * 6
            dy = self.text_rect[1] + (self.LINE_HEIGHT+MessageEngine.FONT_HEIGHT) * (i % 4)
            self.msg_engine.draw_string(screen, (dx,dy), self.COMMAND[i])
        # 選択中のコマンドの左側に矢印を描画
        dx = self.text_rect[0] + MessageEngine.FONT_WIDTH * 5 * (self.command // 4)
        dy = self.text_rect[1] + (self.LINE_HEIGHT+MessageEngine.FONT_HEIGHT) * (self.command % 4)
        screen.blit(self.cursor, (dx,dy))
    def show(self):
        """オーバーライド"""
        self.command = self.TALK  # 追加
        self.is_visible = True

class PyRPG:
    def __init__(self):
        global game_state
        pygame.init()
        self.screen = pygame.display.set_mode(SCREEN_RECT.size)
        #self.screen = pygame.display.set_mode(SCREEN_RECT.size, DOUBLEBUF | HWSURFACE | FULLSCREEN)
        pygame.display.set_caption("Short Tale Story")
        # メッセージエンジン
        self.msg_engine = MessageEngine()
        # メッセージウィンドウ
        self.msgwnd = MessageWindow(Rect(140,334,360,140), self.msg_engine)
        # コマンドウィンドウ
        self.cmdwnd = CommandWindow(Rect(16,16,216,160), self.msg_engine)
        # タイトル画面
        self.title = Title(self.msg_engine)
        self.player = Player(os.path.join("data", "pipo-charachip021.png"))
        self.group = pygame.sprite.RenderUpdates()
        self.group.add(self.player)
        self.fieldMap = Map(self.screen, "field.map", self.player)
        self.player.set_map(self.fieldMap)
        clock = pygame.time.Clock()
        self.is_finish = False
        # 戦闘画面
        self.battle = Battle(self.player, self.msgwnd, self.msg_engine)
        # メインループを起動
        game_state = TITLE
        self.mainloop()
    def mainloop(self):
        """メインループ"""
        clock = pygame.time.Clock()
        while True:
            clock.tick(60)
            self.screen.fill((0, 255, 0))
            self.update()             # ゲーム状態の更新
            self.render()             # ゲームオブジェクトのレンダリング
            pygame.display.update()   # 画面に描画
            self.check_event()        # イベントハンドラ
            if self.is_finish:
                break
    def update(self):
        """ゲーム状態の更新"""
        if game_state == TITLE:
            self.title.update()
        elif game_state == FIELD:
            self.fieldMap.update()
            self.group.update(self.battle)
        elif game_state == TALK:
            self.msgwnd.update()
        elif game_state == BATTLE_INIT or game_state == BATTLE_COMMAND or game_state == BATTLE_PROCESS or \
            game_state == BATTLE_END:
            self.battle.update()
            self.msgwnd.update()
    def render(self):
        """ゲームオブジェクトのレンダリング"""
        if game_state == TITLE:
            self.title.draw(self.screen)
        elif game_state == FIELD or game_state == TALK or game_state == COMMAND:
            self.fieldMap.draw()
            self.group.draw(self.screen)
            self.msgwnd.draw(self.screen)
            self.cmdwnd.draw(self.screen)
            #self.show_info()  # デバッグ情報を画面に表示
        elif game_state in (BATTLE_INIT, BATTLE_COMMAND, BATTLE_PROCESS, BATTLE_END):
            self.battle.draw(self.screen)
            self.msgwnd.draw(self.screen)
    def check_event(self):
        """イベントハンドラ"""
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                #sys.exit()
                self.is_finish = True
                return
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                pygame.quit()
                #sys.exit()
                self.is_finish = True
                return
            # 表示されているウィンドウに応じてイベントハンドラを変更
            if game_state == TITLE:
                self.title_handler(event)
            elif game_state == FIELD:
                self.field_handler(event)
            elif game_state == COMMAND:
                self.cmd_handler(event)
            elif game_state == TALK:
                self.talk_handler(event)
            elif game_state == BATTLE_INIT:
                self.battle_init_handler(event)
            elif game_state == BATTLE_COMMAND:
                self.battle_cmd_handler(event)
            elif game_state == BATTLE_PROCESS:
                self.battle_proc_handler(event)
            elif game_state == BATTLE_END:
                self.battle_end_handler(event)
    def title_handler(self, event):
        """タイトル画面のイベントハンドラ"""
        global game_state
        if event.type == KEYUP and event.key == K_UP:
            self.title.menu -= 1
            if self.title.menu < 0:
                self.title.menu = 0
        elif event.type == KEYDOWN and event.key == K_DOWN:
            self.title.menu += 1
            if self.title.menu > 2:
                self.title.menu = 2
        if event.type == KEYDOWN and event.key == K_SPACE:
            #sounds["pi"].play()
            if self.title.menu == Title.START:
                self.player.start()  # Playerを初期化
                game_state = FIELD
                #self.fieldMap.create("field")  # フィールドマップへ
            elif self.title.menu == Title.CONTINUE:
                pass
            elif self.title.menu == Title.EXIT:
                pygame.quit()
                #sys.exit()
                self.is_finish = True
    def field_handler(self, event):
        """フィールド画面のイベントハンドラ"""
        global game_state
        # スペースキーでコマンドウィンドウ表示
        if event.type == KEYDOWN and event.key == K_SPACE:
            #sounds["pi"].play()
            self.cmdwnd.show()
            game_state = COMMAND
    def cmd_handler(self, event):
        """コマンドウィンドウが開いているときのイベント処理"""
        global game_state
        # 矢印キーでコマンド選択
        if event.type == KEYDOWN and event.key == K_LEFT:
            if self.cmdwnd.command <= 3: return
            self.cmdwnd.command -= 4
        elif event.type == KEYDOWN and event.key == K_RIGHT:
            if self.cmdwnd.command >= 4: return
            self.cmdwnd.command += 4
        elif event.type == KEYUP and event.key == K_UP:
            if self.cmdwnd.command == 0 or self.cmdwnd.command == 4: return
            self.cmdwnd.command -= 1
        elif event.type == KEYDOWN and event.key == K_DOWN:
            if self.cmdwnd.command == 3 or self.cmdwnd.command == 7: return
            self.cmdwnd.command += 1
        # スペースキーでコマンド実行
        if event.type == KEYDOWN and event.key == K_SPACE:
            if self.cmdwnd.command == CommandWindow.TALK:  # はなす
                #sounds["pi"].play()
                self.cmdwnd.hide()
                chara = self.player.talk(self.fieldMap)
                if chara != None:
                    self.msgwnd.set(chara.message)
                    game_state = TALK
                else:
                    self.msgwnd.set("そのほうこうには　だれもいない。")
                    game_state = TALK
            elif self.cmdwnd.command == CommandWindow.STATUS:  # つよさ
                # TODO: ステータスウィンドウ表示
                #sounds["pi"].play()
                self.cmdwnd.hide()
                self.msgwnd.set("つよさウィンドウが　ひらくよてい。")
                game_state = TALK
            elif self.cmdwnd.command == CommandWindow.EQUIPMENT:  # そうび
                # TODO: そうびウィンドウ表示
                #sounds["pi"].play()
                self.cmdwnd.hide()
                self.msgwnd.set("そうびウィンドウが　ひらくよてい。")
                game_state = TALK
            elif self.cmdwnd.command == CommandWindow.DOOR:  # とびら
                #sounds["pi"].play()
                self.cmdwnd.hide()
                # とびらを開ける
                door = self.player.open()
                if door and not door.is_opened:
                    door.open()
                    #door.map.remove_event(door)
                    game_state = FIELD
                else:
                    self.msgwnd.set("そのほうこうに　とびらはない。")
                    game_state = TALK
            elif self.cmdwnd.command == CommandWindow.SPELL:  # じゅもん
                # TODO: じゅもんウィンドウ表示
                #sounds["pi"].play()
                self.cmdwnd.hide()
                self.msgwnd.set("じゅもんウィンドウが　ひらくよてい。")
                game_state = TALK
            elif self.cmdwnd.command == CommandWindow.ITEM:  # どうぐ
                # TODO: どうぐウィンドウ表示
                #sounds["pi"].play()
                self.cmdwnd.hide()
                self.msgwnd.set("どうぐウィンドウが　ひらくよてい。")
                game_state = TALK
            elif self.cmdwnd.command == CommandWindow.TACTICS:  # さくせん
                # TODO: さくせんウィンドウ表示
                #sounds["pi"].play()
                self.cmdwnd.hide()
                self.msgwnd.set("さくせんウィンドウが　ひらくよてい。")
                game_state = TALK
            elif self.cmdwnd.command == CommandWindow.SEARCH:  # しらべる
                #sounds["pi"].play()
                self.cmdwnd.hide()
                # 宝箱を調べる
                treasure = self.player.search()
                if treasure and not treasure.is_opened:
                    treasure.open()
                    self.msgwnd.set("{}　をてにいれた。".format(treasure.item_name))
                    game_state = TALK
                else:
                    self.msgwnd.set("しかし　なにもみつからなかった。")
                    game_state = TALK
    def talk_handler(self, event):
        """会話中のイベントハンドラ"""
        global game_state
        # スペースキーでメッセージウィンドウを次のページへ
        # なかった場合、フィールド状態へ戻る
        if event.type == KEYDOWN and event.key == K_SPACE:
            if not self.msgwnd.next():
                game_state = FIELD
    def battle_init_handler(self, event):
        """戦闘開始のイベントハンドラ"""
        global game_state
        if event.type == KEYDOWN and event.key == K_SPACE:
            if not self.msgwnd.next():
                self.msgwnd.hide()
                #sounds["pi"].play()
                self.battle.cmdwnd.show()
                self.battle.status_wnd.show()
                game_state = BATTLE_COMMAND
    def calculate_damage(self, attack, defense):
        # 基本ダメージ = (攻撃力 / 2) - (守備力 / 4)
        # 最終ダメージ = 基本ダメージ ± (0～4のランダムな値)
        # 但し、0以下にならないようにする
        damage = attack // 2 - defense // 4
        damage = max(damage + random.randint(0, 4) * random.choice([-1, 1]), 1)
        return damage
    def battle_cmd_handler(self, event):
        """戦闘コマンドウィンドウが出ているときのイベントハンドラ"""
        global game_state
        # バトルコマンドのカーソル移動
        if event.type == KEYUP and event.key == K_UP:
            if self.battle.cmdwnd.command == 0: return
            self.battle.cmdwnd.command -= 1
        elif event.type == KEYDOWN and event.key == K_DOWN:
            if self.battle.cmdwnd.command == 3: return
            self.battle.cmdwnd.command += 1
        # バトルコマンドの決定
        if event.type == KEYDOWN and event.key == K_SPACE:
            if not self.msgwnd.next():
                #sounds["pi"].play()
                if self.battle.cmdwnd.command == BattleCommandWindow.ATTACK:  # たたかう
                    damage = self.calculate_damage(self.battle.player.player_status["attack"],
                        self.battle.monster_status["defense"])
                    self.battle.monster_status["hp"] -= damage
                    if self.battle.monster_status["hp"] < 0:  # 負にならないようにする
                        self.battle.monster_status["hp"] = 0
                    self.msgwnd.set(f"{self.battle.monster_status['name']}に{damage}のダメージ！")
                    if self.battle.monster_status["hp"] <= 0:
                        self.battle.is_monster_dead = True
                        self.battle.is_player_turn = False
                        self.battle.cmdwnd.hide()
                        game_state = BATTLE_PROCESS
                        return
                elif self.battle.cmdwnd.command == BattleCommandWindow.SPELL:  # じゅもん
                    self.msgwnd.set("じゅもんを　おぼえていない。")
                elif self.battle.cmdwnd.command == BattleCommandWindow.ITEM:  # どうぐ
                    self.msgwnd.set("どうぐを　もっていない。")
                elif self.battle.cmdwnd.command == BattleCommandWindow.ESCAPE:  # にげる
                    self.msgwnd.set("ゆうしゃは　にげだした。")
                self.battle.is_player_turn = False
                self.battle.cmdwnd.hide()
                game_state = BATTLE_PROCESS
    def battle_proc_handler(self, event):
        """戦闘の処理"""
        global game_state
        if event.type == KEYDOWN and event.key == K_SPACE:
            if not self.msgwnd.next():
                self.msgwnd.hide()
                if self.battle.is_monster_dead:
                    self.msgwnd.set(f"{self.battle.monster_status['name']}をたおした！")
                    game_state = BATTLE_END  # 戦闘終了してフィールドに戻る
                    return
                elif self.battle.cmdwnd.command == BattleCommandWindow.ESCAPE:
                    # フィールドへ戻る
                    #self.fieldMap.play_bgm()
                    game_state = FIELD
                else:
                    if self.battle.is_player_turn:
                        game_state = BATTLE_COMMAND
                        self.battle.cmdwnd.show()
                    else:
                        # モンスターが攻撃してくる
                        damage = self.calculate_damage(self.battle.monster_status["attack"],
                            self.battle.player.player_status["defense"])
                        self.battle.player.player_status["hp"] -= damage  # プレイヤーのHPを減らす
                        if self.battle.player.player_status["hp"] < 0:  # HPが負にならないようにする
                            self.battle.player.player_status["hp"] = 0
                        self.msgwnd.set(f"{self.battle.monster_status['name']}のこうげき！ ゆうしゃに{damage}のダメージ！")
                        if self.battle.player.player_status["hp"] <= 0:
                            self.battle.is_player_deading = True
                            game_state = BATTLE_END
                        self.battle.is_player_turn = True
    def battle_end_handler(self, event):
        global game_state
        """バトルが終了したときの処理を行う"""
        # フィールドに戻る処理
        if event.type == KEYDOWN and event.key == K_SPACE:
            if not self.msgwnd.next():
                if self.battle.is_player_deading:
                    if self.battle.is_player_dead:
                        self.msgwnd.hide()
                        game_state = TITLE  # ゲーム状態をとりあえずタイトルに戻す
                    else:
                        # 一度に１回しか文字列を設定出来ないのでis_player_deadingとis_player_deadの２つに分ける
                        self.msgwnd.set("ゆうしゃはしんでしまった！")
                        self.battle.is_player_dead = True
                else:
                    game_state = FIELD  # ゲーム状態をフィールドに戻す
                    self.battle.cmdwnd.hide()  # コマンドウィンドウを隠す

class Title:
    """タイトル画面"""
    START, CONTINUE, EXIT = 0, 1, 2
    def __init__(self, msg_engine):
        self.msg_engine = msg_engine
        self.title_img = load_image(os.path.join("data", "ShortTaleStory_Title.png"))
        self.cursor_img = load_image(os.path.join("data", "cursor2.png"))
        self.menu = self.START
        self.play_bgm()
    def update(self):
        pass
    def draw(self, screen):
        screen.fill((0,0,128))
        # タイトルの描画
        screen.blit(self.title_img, (0,0))
        # メニューの描画
        self.msg_engine.draw_string(screen, (260,240), "ＳＴＡＲＴ")
        self.msg_engine.draw_string(screen, (260,280), "ＣＯＮＴＩＮＵＥ")
        self.msg_engine.draw_string(screen, (260,320), "ＥＸＩＴ")
        # クレジットの描画
        self.msg_engine.draw_string(screen, (190,420), "２０２１　まいにちＰＹＴＨＯＮ")
        # メニューカーソルの描画
        if self.menu == self.START:
            screen.blit(self.cursor_img, (240, 240))
        elif self.menu == self.CONTINUE:
            screen.blit(self.cursor_img, (240, 280))
        elif self.menu == self.EXIT:
            screen.blit(self.cursor_img, (240, 320))
    def play_bgm(self):
        #bgm_file = "title.mp3"
        #bgm_file = os.path.join("bgm", bgm_file)
        #pygame.mixer.music.load(bgm_file)
        #pygame.mixer.music.play(-1)
        pass

class Battle:
    """戦闘画面"""
    def __init__(self, player, msgwnd, msg_engine):
        self.player = player
        self.msgwnd = msgwnd
        self.msg_engine = msg_engine
        # 戦闘コマンドウィンドウ
        self.cmdwnd = BattleCommandWindow(Rect(96, 338, 136, 136), self.msg_engine)
        # モンスターのステータス
        self.monster_status = None
        # 戦闘ステータスウィンドウ
        self.status_wnd = BattleStatusWindow(Rect(90, 8, 104+32, 136), self.player, self.msg_engine)
        self.monster_img = load_image(os.path.join("data", "pipo-enemy046.png"))
        self.monster_img = pygame.transform.scale(self.monster_img, (240, 240))  # 縮小後のサイズを指定
        self.is_player_turn = True  # プレイヤー攻撃中
        self.is_monster_dead = False
        self.is_player_deading = False  # プレイヤー死に途中
        self.is_player_dead = False     # プレイヤー死亡
    def start(self):
        """戦闘の開始処理、モンスターの選択、配置など"""
        self.cmdwnd.hide()
        self.status_wnd.hide()
        self.is_player_turn = True  # プレイヤーの先制攻撃
        self.is_monster_dead = False
        self.is_player_deading = False
        self.is_player_dead = False
        # 戦闘ごとにモンスターのステータスをリセット
        self.monster_status = {"name": "とんでスライム",
            "hp": 6, "mp": 0,
            "attack": 2, "defense": 1, "speed": 5}  # HPや攻撃力をリセット
        self.msgwnd.set(f"{self.monster_status['name']}が　あらわれた！")
        self.play_bgm()
    def update(self):
        pass
    def draw(self, screen):
        screen.fill((0,0,0))
        screen.blit(self.monster_img, (200, 100))
        self.cmdwnd.draw(screen)
        self.status_wnd.draw(screen)
    def play_bgm(self):
        #bgm_file = "battle.mp3"
        #bgm_file = os.path.join("bgm", bgm_file)
        #pygame.mixer.music.load(bgm_file)
        #pygame.mixer.music.play(-1)
        pass

class BattleCommandWindow(Window):
    """戦闘のコマンドウィンドウ"""
    LINE_HEIGHT = 8  # 行間の大きさ
    ATTACK, SPELL, ITEM, ESCAPE = range(4)
    COMMAND = ["たたかう", "じゅもん", "どうぐ", "にげる"]
    def __init__(self, rect, msg_engine):
        Window.__init__(self, rect)
        self.text_rect = self.inner_rect.inflate(-32, -16)
        self.command = self.ATTACK  # 選択中のコマンド
        self.msg_engine = msg_engine
        self.cursor = load_image(os.path.join("data", "cursor2.png"))
        self.frame = 0
    def draw(self, screen):
        Window.draw(self, screen)
        if self.is_visible == False: return
        # コマンドを描画
        for i in range(0, 4):
            dx = self.text_rect[0] + MessageEngine.FONT_WIDTH
            dy = self.text_rect[1] + (self.LINE_HEIGHT+MessageEngine.FONT_HEIGHT) * (i % 4)
            self.msg_engine.draw_string(screen, (dx,dy), self.COMMAND[i])
        # 選択中のコマンドの左側に▶を描画
        dx = self.text_rect[0]
        dy = self.text_rect[1] + (self.LINE_HEIGHT+MessageEngine.FONT_HEIGHT) * (self.command % 4)
        screen.blit(self.cursor, (dx,dy))
    def show(self):
        """オーバーライド"""
        self.command = self.ATTACK  # 追加
        self.is_visible = True

class BattleStatusWindow(Window):
    """戦闘画面のステータスウィンドウ"""
    LINE_HEIGHT = 8  # 行間の大きさ
    def __init__(self, rect, player, msg_engine):
        Window.__init__(self, rect)
        self.text_rect = self.inner_rect.inflate(-32, -16)
        self.player = player
        self.msg_engine = msg_engine
        self.frame = 0
    def draw(self, screen):
        Window.draw(self, screen)
        if self.is_visible == False: return
        # ステータスを描画
        status_str = [self.player.player_status["name"],
            "H  %3d" % self.player.player_status["hp"],
            "M  %3d" % self.player.player_status["mp"],
            "LV %3d" % self.player.player_status["lv"]]
        for i in range(0, 4):
            dx = self.text_rect[0]
            dy = self.text_rect[1] + (self.LINE_HEIGHT+MessageEngine.FONT_HEIGHT) * (i % 4)
            self.msg_engine.draw_string(screen, (dx,dy), status_str[i])

if __name__ == '__main__':
    PyRPG()
