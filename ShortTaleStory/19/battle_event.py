import pygame
from pygame.locals import *
import os
import random
from messageEngine import MessageEngine
import window

class Battle:
    """戦闘画面"""
    def __init__(self, player, msgwnd, msg_engine):
        self.player = player
        msgwnd = msgwnd
        self.msg_engine = msg_engine
        # 戦闘コマンドウィンドウ
        self.cmdwnd = BattleCommandWindow(Rect(96, 338, 136, 136), self.msg_engine)
        # モンスターのステータス
        self.monster_status = None
        # 戦闘ステータスウィンドウ
        self.status_wnd = BattleStatusWindow(Rect(90, 8, 104+32, 136), self.player, self.msg_engine)
        self.monster_img = window.load_image(os.path.join("data", "pipo-enemy046.png"))
        self.monster_img = pygame.transform.scale(self.monster_img, (240, 240))  # 縮小後のサイズを指定
        self.is_player_dead = False     # プレイヤー死亡
        self.return_field = False
        self.return_title = False
    def check_return_field(self):
        return self.return_field
    def check_return_title(self):
        return self.return_title
    def start(self):
        """戦闘の開始処理、モンスターの選択、配置など"""
        self.cmdwnd.hide()
        self.status_wnd.hide()
        self.is_player_dead = False
        self.return_field = False
        self.return_title = False
        # 戦闘ごとにモンスターのステータスをリセット
        self.monster_status = {"name": "とんでスライム",
            "hp": 6, "mp": 0,
            "attack": 2, "defense": 1, "speed": 5}  # HPや攻撃力をリセット
        msgwnd.set(f"{self.monster_status['name']}が　あらわれた！")
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

class BattleCommandWindow(window.Window):
    """戦闘のコマンドウィンドウ"""
    LINE_HEIGHT = 8  # 行間の大きさ
    ATTACK, SPELL, ITEM, ESCAPE = range(4)
    COMMAND = ["たたかう", "じゅもん", "どうぐ", "にげる"]
    def __init__(self, rect, msg_engine):
        window.Window.__init__(self, rect)
        self.text_rect = self.inner_rect.inflate(-32, -16)
        self.command = self.ATTACK  # 選択中のコマンド
        self.msg_engine = msg_engine
        self.cursor = window.load_image(os.path.join("data", "cursor2.png"))
        self.frame = 0
    def draw(self, screen):
        window.Window.draw(self, screen)
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

class BattleStatusWindow(window.Window):
    """戦闘画面のステータスウィンドウ"""
    LINE_HEIGHT = 8  # 行間の大きさ
    def __init__(self, rect, player, msg_engine):
        window.Window.__init__(self, rect)
        self.text_rect = self.inner_rect.inflate(-32, -16)
        self.player = player
        self.msg_engine = msg_engine
        self.frame = 0
    def draw(self, screen):
        window.Window.draw(self, screen)
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
            
def subscribe(event_manager):
    event_manager.subscribe("battle_update", on_battle_update)
    event_manager.subscribe("battle_draw", on_battle_draw)
    event_manager.subscribe("battle_start", on_battle_start)
    event_manager.subscribe("battle_init", on_battle_init)
    event_manager.subscribe("battle_command", on_battle_command)
    event_manager.subscribe("battle_proc", on_battle_proc)
    event_manager.subscribe("battle_player_dead", on_battle_player_dead)
    event_manager.subscribe("battle_monster_dead", on_battle_monster_dead)
    event_manager.subscribe("battle_end", on_battle_end)

def on_battle_update(battle):
    battle.update()
    return ""

def on_battle_draw(battle, screen):
    battle.draw(screen)
    return ""

def on_battle_start(battle, msgwnd):
    """戦闘の開始処理、モンスターの選択、配置など"""
    print("battle start---")
    battle.return_field = False
    battle.return_title = False
    battle.cmdwnd.hide()
    battle.status_wnd.hide()
    # 戦闘ごとにモンスターのステータスをリセット
    battle.monster_status = {"name": "とんでスライム",
        "hp": 6, "mp": 0,
        "attack": 2, "defense": 1, "speed": 5}  # HPや攻撃力をリセット
    msgwnd.set(f"{battle.monster_status['name']}が　あらわれた！")
    return "battle_init"
    
def on_battle_init(event, battle, msgwnd):
    """戦闘開始のイベントハンドラ"""
    print("battle init---")
    if event.type == KEYDOWN and event.key == K_SPACE:
        if not msgwnd.next():
            msgwnd.hide()
            #sounds["pi"].play()
            battle.cmdwnd.show()
            battle.status_wnd.show()
            ###game_state = BATTLE_COMMAND
            return "battle_command"
    return ""
    
def calculate_damage(attack, defense):
    # 基本ダメージ = (攻撃力 / 2) - (守備力 / 4)
    # 最終ダメージ = 基本ダメージ ± (0～4のランダムな値)
    # 但し、0以下にならないようにする
    damage = attack // 2 - defense // 4
    damage = max(damage + random.randint(0, 4) * random.choice([-1, 1]), 1)
    return damage
    
def on_battle_command(event, battle, msgwnd):
    """戦闘コマンドウィンドウが出ているときのイベントハンドラ"""
    print("battle command---")
    ###global game_state
    # バトルコマンドのカーソル移動
    if event.type == KEYUP and event.key == K_UP:
        if battle.cmdwnd.command == 0: return ""
        battle.cmdwnd.command -= 1
    elif event.type == KEYDOWN and event.key == K_DOWN:
        if battle.cmdwnd.command == 3: return ""
        battle.cmdwnd.command += 1
    # バトルコマンドの決定
    if event.type == KEYDOWN and event.key == K_SPACE:
        if not msgwnd.next():
            #sounds["pi"].play()
            if battle.cmdwnd.command == BattleCommandWindow.ATTACK:  # たたかう
                damage = calculate_damage(battle.player.player_status["attack"],
                    battle.monster_status["defense"])
                battle.monster_status["hp"] -= damage
                if battle.monster_status["hp"] < 0:  # 負にならないようにする
                    battle.monster_status["hp"] = 0
                msgwnd.set(f"{battle.monster_status['name']}に{damage}のダメージ！")
                if battle.monster_status["hp"] <= 0:
                    battle.is_player_turn = False
                    battle.cmdwnd.hide()
                    ###game_state = BATTLE_PROCESS
                    return "battle_monster_dead"
            elif battle.cmdwnd.command == BattleCommandWindow.SPELL:  # じゅもん
                msgwnd.set("じゅもんを　おぼえていない。")
            elif battle.cmdwnd.command == BattleCommandWindow.ITEM:  # どうぐ
                msgwnd.set("どうぐを　もっていない。")
            elif battle.cmdwnd.command == BattleCommandWindow.ESCAPE:  # にげる
                msgwnd.set("ゆうしゃは　にげだした。")
            battle.is_player_turn = False
            battle.cmdwnd.hide()
            ###game_state = BATTLE_PROCESS
            return "battle_proc"
    return ""
    
def on_battle_proc(event, battle, msgwnd):
    """戦闘の処理"""
    print("battle proc---")
    ###global game_state
    if event.type == KEYDOWN and event.key == K_SPACE:
        if not msgwnd.next():
            msgwnd.hide()
            if battle.monster_status["hp"] <= 0:
                msgwnd.set(f"{battle.monster_status['name']}をたおした！")
                ###game_state = BATTLE_END  # 戦闘終了してフィールドに戻る
                return "battle_end"
            elif battle.cmdwnd.command == BattleCommandWindow.ESCAPE:
                # フィールドへ戻る
                #self.fieldMap.play_bgm()
                ###game_state = FIELD
                battle.return_field = True
            else:
                if battle.is_player_turn:
                    ###game_state = BATTLE_COMMAND
                    battle.cmdwnd.show()
                    return "battle_command"
                else:
                    # モンスターが攻撃してくる
                    damage = calculate_damage(battle.monster_status["attack"],
                        battle.player.player_status["defense"])
                    battle.player.player_status["hp"] -= damage  # プレイヤーのHPを減らす
                    if battle.player.player_status["hp"] < 0:  # HPが負にならないようにする
                        battle.player.player_status["hp"] = 0
                    msgwnd.set(f"{battle.monster_status['name']}のこうげき！ ゆうしゃに{damage}のダメージ！")
                    if battle.player.player_status["hp"] <= 0:
                        ###game_state = BATTLE_END
                        battle.is_player_dead = False
                        return "battle_player_dead"
                    battle.is_player_turn = True
                    return ""
    return ""
    
def on_battle_player_dead(event, battle, msgwnd):
    """プレイヤーの死亡処理"""
    print("battle player dead---")
    if event.type == KEYDOWN and event.key == K_SPACE:
        if not msgwnd.next():
            if battle.is_player_dead:
                msgwnd.hide()
                ###game_state = TITLE  # ゲーム状態をとりあえずタイトルに戻す
                battle.return_title = True
                return None
            else:
                msgwnd.set("ゆうしゃはしんでしまった！")
                battle.is_player_dead = True
    return ""
    
def on_battle_monster_dead(event, battle, msgwnd):
    """モンスターの死亡処理"""
    print("battle monster dead---")
    if event.type == KEYDOWN and event.key == K_SPACE:
        if not msgwnd.next():
            msgwnd.set(f"{battle.monster_status['name']}をたおした！")
            return "battle_end"
    return ""
    
def on_battle_end(event, battle, msgwnd):
    """バトルが終了したときの処理を行う"""
    print("battle end---")
    ###global game_state
    if event.type == KEYDOWN and event.key == K_SPACE:
        if not msgwnd.next():
            # フィールドに戻る処理
            ###game_state = FIELD  # ゲーム状態をフィールドに戻す
            battle.cmdwnd.hide()  # コマンドウィンドウを隠す
            battle.return_field = True
            return None
    return ""
    