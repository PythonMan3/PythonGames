class EventManager:
    def __init__(self):
        self.events = {}

    def subscribe(self, event_name, handler):
        # イベントが未登録の場合のみ、ハンドラーを追加
        if event_name not in self.events:
            self.events[event_name] = handler
        else:
            print(f"Handler already registered for event: {event_name}")

    def trigger(self, event_name, *args, **kwargs):
        # ハンドラーが登録されている場合のみ実行
        if event_name in self.events:
            ret = self.events[event_name](*args, **kwargs)
            if ret is None:
                return None
            elif ret == "":
                return event_name
            else:
                return ret
        return None

if __name__ == "__main__":
    # 使用例
    def on_player_attack(enemy):
        print(f"Player attacks {enemy}!")
    
    event_manager = EventManager()
    event_manager.subscribe("player_attack", on_player_attack)
    
    # イベントをトリガー
    enemy = "Enemy"
    event_manager.trigger("player_attack", enemy)
