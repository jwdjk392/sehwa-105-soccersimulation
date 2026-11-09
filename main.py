import json
from pathlib import Path
from uirenderer import GameScreen, selectTeam
from simulation import Simulator

data_dir = Path("./data")

team_dict = {}

# ./data 디렉터리 내의 모든 JSON 파일 순회
for json_file in data_dir.glob("*.json"):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    team_name = data["teamName"]
    team_dict[team_name] = data

print(team_dict.keys())

teamAboutToPlay = selectTeam(team_dict)

myTeam = teamAboutToPlay[0]
enemyTeam = teamAboutToPlay[1]