import json
from pathlib import Path
from uirenderer import GameResult, GameScreen, selectTeam
from simulation import Simulator

DATA_DIR = Path(__file__).parent / "data"
FIELD_WIDTH = 160
FIELD_HEIGHT = 80
TURN_COUNT = 90
TURN_MINUTES = 1
MAX_FIELD_PLAYERS = 10
TURN_INTERVAL_MS = 500


def load_teams(data_dir=DATA_DIR):
    """JSON 파일에서 팀 정보를 읽고 팀 이름으로 조회할 수 있게 반환합니다."""
    teams = {}
    for json_file in sorted(data_dir.glob("*.json")):
        with open(json_file, "r", encoding="utf-8") as team_file:
            team = json.load(team_file)

        team_name = team.get("teamName")
        if not team_name or not isinstance(team.get("players"), list):
            raise ValueError(f"팀 데이터 형식이 올바르지 않습니다: {json_file}")
        if team_name in teams:
            raise ValueError(f"중복된 팀 이름입니다: {team_name}")
        teams[team_name] = team
    return teams


def _valid_player_names(requested_names, team):
    available = {player["name"] for player in team.get("players", []) if "name" in player}
    names = []
    for name in requested_names or ():
        if name in available and name not in names:
            names.append(name)
        if len(names) == MAX_FIELD_PLAYERS:
            break
    return names


def _initial_positions(player_names, is_my_team):
    positions = {}
    for index, name in enumerate(player_names):
        # 4명씩 한 줄에 배치하고, 상대 팀은 X축을 기준으로 반대편에 둡니다.
        x = 20 + (index // 4) * 14
        y = 10 + (index % 4) * 20
        if not is_my_team:
            x = FIELD_WIDTH - x
        positions[name] = {"playerName": name, "playerX": x, "playerY": y}
    return positions


def _format_time(minutes):
    return f"{minutes:02d}:00"


def run_match(my_team, enemy_team):
    """한 경기를 90개의 1분 턴으로 진행하고 변경 사항을 화면에 전달합니다."""
    simulator = Simulator(my_team, enemy_team)

    my_requested = GameScreen.selectInitialPlayers(my_team.get("players", []))
    my_onfield = _valid_player_names(my_requested, my_team)
    if not my_onfield:
        my_onfield = _valid_player_names(
            [player.get("name") for player in my_team.get("players", [])], my_team
        )

    enemy_players = sorted(
        enemy_team.get("players", []),
        key=lambda player: (
            float(player.get("speed", 50)) + float(player.get("strength", 50))
        ),
        reverse=True,
    )
    enemy_onfield = _valid_player_names(
        [player.get("name") for player in enemy_players], enemy_team
    )
    if not my_onfield or not enemy_onfield:
        raise ValueError("양 팀 모두 출전 가능한 선수가 한 명 이상 필요합니다.")

    my_roster_names = [
        player["name"] for player in my_team.get("players", []) if player.get("name")
    ]
    enemy_roster_names = [
        player["name"] for player in enemy_team.get("players", []) if player.get("name")
    ]
    my_positions = _initial_positions(my_roster_names, is_my_team=True)
    enemy_positions = _initial_positions(enemy_roster_names, is_my_team=False)
    game_status = {
        "time": 0,
        "ballOwner": my_onfield[0],
        "myTeamGoalCount": 0,
        "enemyTeamGoalCount": 0,
        "myPlayers": [],
        "enemyPlayers": [],
    }

    def change_my_onfield(player_names):
        nonlocal my_onfield
        selected = _valid_player_names(player_names, my_team)
        if selected:
            if game_status["ballOwner"] in my_onfield and game_status["ballOwner"] not in selected:
                game_status["ballOwner"] = selected[0]
            my_onfield = selected
            simulator.setCurrentOnfield(my_onfield, enemy_onfield)
        return tuple(my_onfield)

    screen = GameScreen(
        (my_team["teamName"], enemy_team["teamName"]),
        change_my_onfield,
        availablePlayers=my_team.get("players", []),
        keepers=(my_team.get("keeper", {}), enemy_team.get("keeper", {})),
    )
    screen.startGame()
    simulator.setCurrentOnfield(my_onfield, enemy_onfield)
    screen.onfieldPlayerChanged(my_onfield, enemy_onfield)
    screen.updateStatus(
        _format_time(TURN_COUNT * TURN_MINUTES),
        game_status["ballOwner"],
        game_status["myTeamGoalCount"],
        game_status["enemyTeamGoalCount"],
    )
    for player_name in my_onfield:
        position = my_positions[player_name]
        screen.movePlayerLocation(player_name, position["playerX"], position["playerY"])
    for player_name in enemy_onfield:
        position = enemy_positions[player_name]
        screen.movePlayerLocation(player_name, position["playerX"], position["playerY"])

    def move_player(player_name, x, y):
        position = {
            "playerName": player_name,
            "playerX": max(0, min(FIELD_WIDTH, x)),
            "playerY": max(0, min(FIELD_HEIGHT, y)),
        }
        positions = my_positions if player_name in my_positions else enemy_positions
        positions[player_name] = position
        screen.movePlayerLocation(player_name, position["playerX"], position["playerY"])

    def pass_to_player(player_name, wanted_name, received_name, successful):
        game_status["ballOwner"] = received_name
        screen.passBall(player_name, wanted_name, received_name, successful)

    def shoot(player_name, successful):
        if successful:
            scoring_for_us = player_name in my_positions
            score_key = "myTeamGoalCount" if scoring_for_us else "enemyTeamGoalCount"
            game_status[score_key] += 1
            kickoff_players = enemy_onfield if scoring_for_us else my_onfield
            game_status["ballOwner"] = kickoff_players[0]
        else:
            opposing_positions = enemy_positions if player_name in my_positions else my_positions
            if opposing_positions:
                game_status["ballOwner"] = min(
                    opposing_positions,
                    key=lambda name: (
                        (opposing_positions[name]["playerX"] -
                         (my_positions if player_name in my_positions else enemy_positions)[player_name]["playerX"]) ** 2
                        + (opposing_positions[name]["playerY"] -
                           (my_positions if player_name in my_positions else enemy_positions)[player_name]["playerY"]) ** 2
                    ),
                )
        screen.tryShoot(player_name, successful)

    def change_enemy_onfield(player_names):
        nonlocal enemy_onfield
        previous_onfield = enemy_onfield
        enemy_onfield = _valid_player_names(player_names, enemy_team)
        if (game_status["ballOwner"] in previous_onfield
                and game_status["ballOwner"] not in enemy_onfield):
            game_status["ballOwner"] = enemy_onfield[0]
        game_status["enemyPlayers"] = [dict(enemy_positions[name]) for name in enemy_onfield]
        simulator.setCurrentStatus(game_status)
        simulator.setCurrentOnfield(my_onfield, enemy_onfield)
        screen.onfieldPlayerChanged(my_onfield, enemy_onfield)

    def play_turn(turn):
        game_status["time"] = turn
        game_status["myPlayers"] = [dict(my_positions[name]) for name in my_onfield]
        game_status["enemyPlayers"] = [dict(enemy_positions[name]) for name in enemy_onfield]
        simulator.setCurrentStatus(game_status)
        simulator.startSimulation(
            turn,
            pass_to_player,
            shoot,
            move_player,
            change_enemy_onfield,
        )
        minutes_remaining = max(0, TURN_COUNT * TURN_MINUTES - (turn + 1) * TURN_MINUTES)
        screen.updateStatus(
            _format_time(minutes_remaining),
            game_status["ballOwner"],
            game_status["myTeamGoalCount"],
            game_status["enemyTeamGoalCount"],
        )
        if turn + 1 < TURN_COUNT:
            screen.root.after(TURN_INTERVAL_MS, lambda: play_turn(turn + 1))
        else:
            screen.root.after(TURN_INTERVAL_MS, finish_match)

    def finish_match():
        my_score = game_status["myTeamGoalCount"]
        enemy_score = game_status["enemyTeamGoalCount"]
        if my_score > enemy_score:
            result = GameResult.WIN
        elif my_score < enemy_score:
            result = GameResult.LOSS
        else:
            result = GameResult.DRAW
        game_status["result"] = int(result)
        screen.GameOver(result)

    screen.root.after(0, lambda: play_turn(0))
    screen.root.mainloop()
    return game_status


def main():
    teams = load_teams()
    if len(teams) < 2:
        raise ValueError("경기를 시작하려면 data 폴더에 팀 JSON 파일이 두 개 이상 필요합니다.")

    selected_teams = selectTeam(teams)
    if (not isinstance(selected_teams, (tuple, list)) or len(selected_teams) != 2
            or selected_teams[0] not in teams or selected_teams[1] not in teams
            or selected_teams[0] == selected_teams[1]):
        raise ValueError("서로 다른 두 팀을 선택해야 합니다.")
    return run_match(teams[selected_teams[0]], teams[selected_teams[1]])


if __name__ == "__main__":
    main()
