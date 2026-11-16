# 이 파일은 모듈 형태로 임포트됨
# 상위 파일에서 직접 호출함. 따라서 시간이 오래 필요한 작업은 필요시에만 별도의 쓰레드로 만들도록.
# 이 파일은 UI 렌더링용. 해당 함수가 실행되면 화면에 그 결과를 그려주는것임.

from tkinter import *
from tkinter import messagebox
import tkinter.font as tkfont
from enum import IntEnum


class GameResult(IntEnum):
    DRAW = 0
    WIN = 1
    LOSS = 2


def selectTeam(teamNames):
    """게임 시작 전에 사용자 팀과 상대 팀을 선택하고 (사용자 팀, 상대 팀)을 반환한다."""
    names = list(teamNames)
    if len(names) < 2:
        raise ValueError("팀을 선택하려면 최소 2개 이상의 팀이 필요합니다.")

    result = {"teams": None}
    root = Tk()
    root.title("팀 선택")
    root.geometry("420x300")
    root.resizable(False, False)

    Label(root, text="플레이할 팀을 선택하세요", font=("맑은 고딕", 15, "bold")).pack(pady=(18, 10))
    Label(root, text="선택한 팀이 사용자 팀이 됩니다.", fg="gray").pack()

    selected = StringVar(value=names[0])
    opponent = StringVar(value=names[1])

    body = Frame(root)
    body.pack(fill="both", expand=True, padx=30, pady=15)

    Label(body, text="나의 팀").grid(row=0, column=0, sticky="w", pady=7)
    my_menu = OptionMenu(body, selected, *names)
    my_menu.config(width=22)
    my_menu.grid(row=0, column=1, sticky="ew", pady=7)

    Label(body, text="상대 팀").grid(row=1, column=0, sticky="w", pady=7)
    enemy_menu = OptionMenu(body, opponent, *names)
    enemy_menu.config(width=22)
    enemy_menu.grid(row=1, column=1, sticky="ew", pady=7)

    def confirm():
        if selected.get() == opponent.get():
            messagebox.showwarning("팀 선택", "서로 다른 팀을 선택해주세요.", parent=root)
            return
        result["teams"] = (selected.get(), opponent.get())
        root.destroy()

    Button(root, text="확인", command=confirm, width=15).pack(pady=(0, 18))
    root.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()
    return result["teams"]


class GameScreen:
    FIELD_WIDTH = 900
    FIELD_HEIGHT = 520
    MODEL_WIDTH = 160
    MODEL_HEIGHT = 80

    def __init__(self, teamNames, changeTeam, availablePlayers=None, keepers=None):
        """경기 창과 경기장 UI를 초기화한다."""
        if not isinstance(teamNames, (tuple, list)) or len(teamNames) != 2:
            raise ValueError("teamNames는 두 팀 이름을 담은 튜플 또는 리스트여야 합니다.")

        self.teamNames = tuple(teamNames)
        self.changeTeamCallback = changeTeam
        self.availablePlayers = list(availablePlayers or [])
        keeper_data = list(keepers or ({}, {}))
        if len(keeper_data) != 2:
            raise ValueError("keepers에는 두 팀의 골키퍼 정보가 필요합니다.")
        self.keepers = [dict(keeper or {}) for keeper in keeper_data]
        self.root = Tk()
        self.root.title(f"{self.teamNames[0]} vs {self.teamNames[1]}")
        self.root.geometry("1100x760")
        self.root.minsize(950, 680)

        self.currentTime = "00:00"
        self.myScore = 0
        self.enemyScore = 0
        self.ballOwner = ""
        self.playerPositions = {}
        self.myPlayers = []
        self.enemyPlayers = []
        self._player_items = {}
        self._player_labels = {}
        self._keeper_items = {}
        self._keeper_labels = {}
        self._ball_item = None
        self._game_started = False

        self.root.configure(bg="#20252b")
        header = Frame(self.root, bg="#20252b")
        header.pack(fill="x", padx=18, pady=12)

        self.scoreLabel = Label(
            header, text=f"{self.teamNames[0]}  0 : 0  {self.teamNames[1]}",
            font=("맑은 고딕", 18, "bold"), fg="white", bg="#20252b"
        )
        self.scoreLabel.pack(side="left")

        self.timeLabel = Label(
            header, text="00:00", font=("맑은 고딕", 18, "bold"),
            fg="#ffd166", bg="#20252b"
        )
        self.timeLabel.pack(side="right")

        self.statusLabel = Label(
            self.root, text="경기 시작을 기다리는 중입니다.",
            font=("맑은 고딕", 11), fg="white", bg="#20252b", anchor="w"
        )
        self.statusLabel.pack(fill="x", padx=22, pady=(0, 8))

        self.canvas = Canvas(
            self.root, width=self.FIELD_WIDTH, height=self.FIELD_HEIGHT,
            bg="#278447", highlightthickness=0
        )
        self.canvas.pack(padx=18, pady=5, fill="both", expand=True)
        self._draw_field()
        self._draw_keepers()

        controls = Frame(self.root, bg="#20252b")
        controls.pack(fill="x", padx=18, pady=12)
        self.startButton = Button(controls, text="경기 시작", command=self.startGame, width=14)
        self.startButton.pack(side="left", padx=4)
        Button(controls, text="선수 교체", command=self._request_player_change, width=14).pack(side="left", padx=4)
        Button(controls, text="창 닫기", command=self.root.destroy, width=14).pack(side="right", padx=4)

        self.eventBox = Text(
            self.root, height=5, state="disabled", wrap="word",
            font=("맑은 고딕", 9), bg="#f3f4f6", fg="#20252b"
        )
        self.eventBox.pack(fill="x", padx=18, pady=(0, 15))

    def _draw_field(self):
        """축구 경기장과 기본 라인을 그린다."""
        self.canvas.delete("field")
        w, h = self.FIELD_WIDTH, self.FIELD_HEIGHT
        self.canvas.create_rectangle(8, 8, w - 8, h - 8, outline="white", width=3, tags="field")
        self.canvas.create_line(w / 2, 8, w / 2, h - 8, fill="white", width=2, tags="field")
        self.canvas.create_oval(w / 2 - 75, h / 2 - 75, w / 2 + 75, h / 2 + 75,
                                outline="white", width=2, tags="field")
        self.canvas.create_oval(w / 2 - 3, h / 2 - 3, w / 2 + 3, h / 2 + 3,
                                fill="white", outline="white", tags="field")
        self.canvas.create_rectangle(8, h / 2 - 110, 115, h / 2 + 110,
                                     outline="white", width=2, tags="field")
        self.canvas.create_rectangle(w - 115, h / 2 - 110, w - 8, h / 2 + 110,
                                     outline="white", width=2, tags="field")
        self.canvas.create_rectangle(8, h / 2 - 55, 48, h / 2 + 55,
                                     outline="white", width=2, tags="field")
        self.canvas.create_rectangle(w - 48, h / 2 - 55, w - 8, h / 2 + 55,
                                     outline="white", width=2, tags="field")
        self.canvas.create_rectangle(2, h / 2 - 36, 10, h / 2 + 36,
                                     outline="white", width=2, tags="field")
        self.canvas.create_rectangle(w - 10, h / 2 - 36, w - 2, h / 2 + 36,
                                     outline="white", width=2, tags="field")
        self.canvas.create_text(w / 2, 25, text="경기장", fill="white",
                                font=("맑은 고딕", 10, "bold"), tags="field")

    def _draw_keepers(self):
        """양 팀 골키퍼를 각 골문 앞에 고정 표시한다."""
        placements = (
            ("my", self.keepers[0], 4),
            ("enemy", self.keepers[1], self.MODEL_WIDTH - 4),
        )
        for side, keeper, model_x in placements:
            name = keeper.get("name") or "골키퍼"
            x, y = self._to_canvas_coordinates(model_x, self.MODEL_HEIGHT / 2)
            self._keeper_items[side] = self.canvas.create_oval(
                x - 14, y - 14, x + 14, y + 14,
                fill="#ffd166", outline="#20252b", width=3, tags=("keeper",)
            )
            self._keeper_labels[side] = self.canvas.create_text(
                x, y + 24, text=f"GK {name}", fill="white",
                font=("맑은 고딕", 8, "bold"), tags=("keeper",)
            )
        self.canvas.tag_raise("keeper")

    def _log(self, message):
        self.eventBox.configure(state="normal")
        self.eventBox.insert("end", message + "\n")
        self.eventBox.see("end")
        self.eventBox.configure(state="disabled")

    def _draw_player(self, playerName, x, y, is_mine=True):
        color = "#2878d0" if is_mine else "#d94343"
        radius = 13
        item = self.canvas.create_oval(
            x - radius, y - radius, x + radius, y + radius,
            fill=color, outline="white", width=2, tags=("player",)
        )
        label = self.canvas.create_text(
            x, y + 23, text=playerName, fill="white",
            font=("맑은 고딕", 8, "bold"), tags=("player",)
        )
        self._player_items[playerName] = item
        self._player_labels[playerName] = label
        self.playerPositions[playerName] = (x, y)

    def startGame(self):
        """경기 시작 상태를 화면에 표시한다."""
        if self._game_started:
            return
        self._game_started = True
        self.startButton.config(state="disabled")
        self.statusLabel.config(text="경기가 시작되었습니다!")
        self._log("경기 시작")
        self.root.update_idletasks()

    @staticmethod
    def selectInitialPlayers(players):
        """선수 목록에서 최대 10명을 선택하고 선수 이름 튜플을 반환한다."""
        players = list(players)
        if not players:
            return tuple()

        names = [str(p.get("name", "")) for p in players if p.get("name")]
        if not names:
            return tuple()

        result = {"selected": None}
        root = Tk()
        root.title("초기 출전 선수 선택")
        root.geometry("480x560")
        root.minsize(400, 400)

        Label(root, text="초기 출전 선수 선택 (최대 10명)",
              font=("맑은 고딕", 14, "bold")).pack(pady=12)

        container = Frame(root)
        container.pack(fill="both", expand=True, padx=18, pady=5)
        canvas = Canvas(container, highlightthickness=0)
        scrollbar = Scrollbar(container, orient="vertical", command=canvas.yview)
        list_frame = Frame(canvas)
        list_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=list_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        variables = {}
        for name in names:
            var = BooleanVar(value=(len(variables) < 10))
            variables[name] = var
            Checkbutton(list_frame, text=name, variable=var, anchor="w",
                        font=("맑은 고딕", 10)).pack(fill="x", pady=2)

        def confirm():
            chosen = tuple(name for name, var in variables.items() if var.get())
            if not chosen:
                messagebox.showwarning("선수 선택", "최소 한 명을 선택해주세요.", parent=root)
                return
            if len(chosen) > 10:
                messagebox.showwarning("선수 선택", "최대 10명까지 선택할 수 있습니다.", parent=root)
                return
            result["selected"] = chosen
            root.destroy()

        Button(root, text="선택 완료", command=confirm, width=16).pack(pady=12)
        root.protocol("WM_DELETE_WINDOW", root.destroy)
        root.mainloop()
        return result["selected"] if result["selected"] is not None else tuple()

    def updateStatus(self, currentTime, ballOwner, myTeamGoalCount, enemyGoalCount):
        """경기 시간, 공 소유 선수, 양 팀 점수를 갱신한다."""
        self.currentTime = str(currentTime)
        self.ballOwner = str(ballOwner) if ballOwner is not None else ""
        self.myScore = int(myTeamGoalCount)
        self.enemyScore = int(enemyGoalCount)
        self.timeLabel.config(text=self.currentTime)
        self.scoreLabel.config(
            text=f"{self.teamNames[0]}  {self.myScore} : {self.enemyScore}  {self.teamNames[1]}"
        )
        owner_text = f"현재 공 소유: {self.ballOwner}" if self.ballOwner else "현재 공 소유: 없음"
        self.statusLabel.config(text=owner_text)
        if self.ballOwner in self.playerPositions:
            self._move_ball(*self.playerPositions[self.ballOwner])

    def movePlayerLocation(self, playerName, x, y):
        """선수를 경기장 내 새 좌표로 이동한다."""
        x = max(0, min(self.MODEL_WIDTH, float(x)))
        y = max(0, min(self.MODEL_HEIGHT, float(y)))
        x, y = self._to_canvas_coordinates(x, y)
        if playerName not in self._player_items:
            is_mine = playerName in self.myPlayers
            self._draw_player(playerName, x, y, is_mine)
        else:
            item = self._player_items[playerName]
            label = self._player_labels[playerName]
            self.canvas.coords(item, x - 13, y - 13, x + 13, y + 13)
            self.canvas.coords(label, x, y + 23)
            self.playerPositions[playerName] = (x, y)
        if playerName == self.ballOwner:
            self._move_ball(x, y)

    def _to_canvas_coordinates(self, x, y):
        margin = 32
        canvas_x = margin + x / self.MODEL_WIDTH * (self.FIELD_WIDTH - margin * 2)
        canvas_y = margin + y / self.MODEL_HEIGHT * (self.FIELD_HEIGHT - margin * 2)
        return canvas_x, canvas_y

    def onfieldPlayerChanged(self, myTeamPlayers, enemyTeamPlayers):
        """양 팀의 현재 출전 선수 목록을 경기장에 반영한다."""
        self.myPlayers = list(myTeamPlayers)
        self.enemyPlayers = list(enemyTeamPlayers)
        active = set(self.myPlayers + self.enemyPlayers)

        for name in list(self._player_items):
            if name not in active:
                self.canvas.delete(self._player_items.pop(name))
                self.canvas.delete(self._player_labels.pop(name))
                self.playerPositions.pop(name, None)

        # 새로 투입된 선수는 팀별 기본 위치에 배치한다.
        for index, name in enumerate(self.myPlayers):
            if name not in self._player_items:
                model_x = 20 + (index // 4) * 14
                model_y = 10 + (index % 4) * 20
                x, y = self._to_canvas_coordinates(model_x, model_y)
                self._draw_player(name, x, y, True)

        for index, name in enumerate(self.enemyPlayers):
            if name not in self._player_items:
                model_x = self.MODEL_WIDTH - (20 + (index // 4) * 14)
                model_y = 10 + (index % 4) * 20
                x, y = self._to_canvas_coordinates(model_x, model_y)
                self._draw_player(name, x, y, False)

        self._log("출전 선수 명단이 변경되었습니다.")

    def passBall(self, playerName, wantedPlayerName, receivedPlayerName, successful):
        """패스 결과를 이벤트 로그와 공 위치로 표시한다."""
        if successful:
            message = f"{playerName} → {wantedPlayerName} 패스 성공"
        else:
            message = f"{playerName}의 패스 실패 (실제 공 소유: {receivedPlayerName})"
        self._log(message)

        if receivedPlayerName in self.playerPositions:
            x, y = self.playerPositions[receivedPlayerName]
            self._move_ball(x, y)
        self.ballOwner = receivedPlayerName

    def _move_ball(self, x, y):
        if self._ball_item is None:
            self._ball_item = self.canvas.create_oval(
                x - 6, y - 6, x + 6, y + 6,
                fill="white", outline="black", width=1, tags=("ball",)
            )
        else:
            self.canvas.coords(self._ball_item, x - 6, y - 6, x + 6, y + 6)
        self.canvas.tag_raise("ball")

    def tryShoot(self, playerName, success):
        """슛 시도 결과를 이벤트 로그로 표시한다."""
        if success:
            self._log(f"{playerName} 슛 성공! 골!")
        else:
            self._log(f"{playerName} 슛 실패")

    def GameOver(self, result):
        """경기를 종료하고 승·무·패 결과를 표시한다."""
        self._game_started = False
        title = "경기 종료"
        if isinstance(result, bool):
            result = GameResult.WIN if result else GameResult.LOSS
        else:
            result = GameResult(result)
        messages = {
            GameResult.DRAW: "무승부입니다.",
            GameResult.WIN: "승리했습니다!",
            GameResult.LOSS: "패배했습니다.",
        }
        message = messages[result]
        self.statusLabel.config(text=f"{title}: {message}")
        self._log(f"{title} - {message}")
        messagebox.showinfo(title, message, parent=self.root)
        self.root.destroy()

    def _request_player_change(self):
        """현재 출전 선수 목록을 교체 콜백에 전달하고 결과를 반영한다."""
        if not callable(self.changeTeamCallback):
            messagebox.showwarning("선수 교체", "선수 교체 기능이 연결되어 있지 않습니다.", parent=self.root)
            return

        players = [player.get("name") for player in self.availablePlayers if player.get("name")]
        if not players:
            messagebox.showwarning("선수 교체", "선수 목록이 없습니다.", parent=self.root)
            return

        dialog = Toplevel(self.root)
        dialog.title("출전 선수 교체")
        dialog.transient(self.root)
        dialog.grab_set()

        container = Frame(dialog)
        container.pack(fill="both", expand=True, padx=14, pady=12)
        canvas = Canvas(container, height=360, highlightthickness=0)
        scrollbar = Scrollbar(container, orient="vertical", command=canvas.yview)
        list_frame = Frame(canvas)
        window_id = canvas.create_window((0, 0), window=list_frame, anchor="nw")
        list_frame.bind(
            "<Configure>",
            lambda _event: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.bind(
            "<Configure>",
            lambda event: canvas.itemconfigure(window_id, width=event.width),
        )
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        variables = {}
        for name in players:
            variable = BooleanVar(master=dialog, value=name in self.myPlayers)
            variables[name] = variable
            Checkbutton(list_frame, text=name, variable=variable, anchor="w").pack(fill="x")

        def confirm():
            selected = tuple(name for name, variable in variables.items() if variable.get())
            if not selected:
                messagebox.showwarning("선수 교체", "최소 한 명을 선택해주세요.", parent=dialog)
                return
            if len(selected) > 10:
                messagebox.showwarning("선수 교체", "최대 10명까지 선택할 수 있습니다.", parent=dialog)
                return

            try:
                new_players = self.changeTeamCallback(selected)
            except TypeError:
                new_players = self.changeTeamCallback()
            if new_players:
                self.onfieldPlayerChanged(new_players, self.enemyPlayers)
            dialog.destroy()

        buttons = Frame(dialog)
        buttons.pack(fill="x", padx=14, pady=(0, 12))
        Button(buttons, text="적용", command=confirm, width=12).pack(side="right", padx=(6, 0))
        Button(buttons, text="취소", command=dialog.destroy, width=12).pack(side="right")
