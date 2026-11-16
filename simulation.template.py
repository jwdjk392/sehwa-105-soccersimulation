# 이 파일은 액션 연산용 파일
# 입력된 매개변수에 따라 행동을 결정하고 실행할것.
# 필요시 이 파일을 테스트하기 위한 별도의 코드를 제공할것
# 이 파일은 모듈. 단독 실행되지 아니함.

class Simulator():
	def __init__(self, myTeam, targetTeam):
		# 팀 정보는 아래와 같은 딕셔너리를 myTeam, targetTeam받게됨.
		#{
		#"teamName": "Sample Team",
		#"players": [
		#	{
		#		"name": "Player 01",
		#		"position": "ST", => 포지션 코드 (LCB, RCB, CB, LB, RB, DM, LCM, RCM, CM, AM, LW, RW, ST)
		#		"speed": 57, => 0~100 사이 정수
		#		"goal_rate": 0.1, => 0 ~ 1 사이 float
		#		"strength": 48 => => 0~100 사이 정수
		#	},
		#	.. 비슷한 내용의 선수 정보 반복
		# ],
		# "keeper": {
		#	"name": "Keeper 0",
		#	"defense_rate": 0.1 => 0~1사이 float
		#  }
		#}
		# myTeam은 내 팀임. 이 팀을 제어하게 됨. 사용자가 제어하는것: 팀 출전 선수 교체. 교체시 setCurrentOnfield 호출됨.
		# 이 데이터를 저장하거나 필요한 세팅을 여기서 준비하면됨.

	def setCurrentOnfield(myPlayerNames, enemyPlayerNames):
		# 우리팀 혹은 상대팀의 현재 출전 상태의 선수를 변경되었다. 이 정보로 연산할것.
		# myPlayerNames는 Array 형태로, 우리팀의 출전중인 선수 이름이 지정되어있음.
		# enemyPlayerNames는 Array 형태로 상대팀의 출전중인 선수 이름이 지정되어있음.
		# startSimulation에서는 이 선수들만 연산하는것임.

	def startSimulation(turn, passToPlayer, shoot, movePlayerLocation, changeEnemyOnfieldStatus):
		# 시뮬레이션을 시작함.
		# turn: 현재 턴 수. 0 ~ 89턴이며 1턴은 1분입니다.
		# 선수 이동은 매 턴 진행하고 패스/슛은 3턴마다 진행합니다.
		# passToPlayer, shoot, movePlayerLocation, changeEnemyOnfieldStatus는 함수임
		# 패스 시
		# passToPlayer(playerName, wantedPlayerName, receivedPlayerName, successful) 
		# => playerName에 패스릃 하는 사람의 이름
		# => wantedPlayerName에 패스를 원래 받기로 의도한 사람의 이름
		# => receivedPlayerName에 실제로 받는 사람의 이름
		# => successful에 패스 성공 여부에 대한 boolean.

		# 슛 시도.
		# shoot(playerName, successful)
		# => playerName에 슛을 시도하는 플레이어 이름을.
		# => successful에 슛 성공 여부
		# movePlayerLocation(playerName, x, y)

		# 선수 위치 이동
		# => playerName에 선수이름
		# => x, y에 좌푯값. X 0~160 / Y 0~80
		# 우리팀과 상대팀의 모든 선수에 대해서 시뮬레이션을 하고 적절한 함수를 호출할 것.
		
		# changeEnemyOnfieldStatus
		# => 상대팀의 출전중인 선수를 변경
		# => 상대팀의 출전 선수 변경은 자동적으로 이루어짐. 따라서 이 함수를 통해서 변경할 수 있음.
		# => Array 형태로 선수 이름을 반환할것.
		# 각 선수에 대해서 진행하고 적절한 함수를 호출할 것.
	def setCurrentStatus(gameStatus):
		# 현재 상태에 대한 신규 정보 수신. 앞으로 여기서 수신한 정보를 이용하여 연산할것이기에 저장할것.
		# gameStatus는 다음과 같은 구조의 딕셔너리
		# {
		#	"time": 현재 턴 수 (0~89턴) / 숫자
		#	"ballOwner": 현재 공을 가지고 있는 플레이어 이름. 상대 팀 일수도 있음.,
		#	"myTeamGoalCount": 우리팀의 골 횟수. 정수.
		# 	"enemyTeamGoalCount": 상대팀의 골 횟수. 정수.
		#	"myPlayers": [
		#		{
		#			"playerName": 선수 이름
		#			"playerX": 선수 X 좌표
		#			"playerY": 선수 Y 좌표
		#		} ... 출전중인 우리팀의 모든 선수에 대한 정보. 출전중이 아닌 선수는 이 목록에 없음
		#	]
		# 	"enemyPlayers": [
		#		{
		#			"playerName": 선수 이름
		#			"playerX": 선수 X 좌표
		#			"playerY": 선수 Y 좌표
		#		} ... 출전중인 상대팀의 모든 선수에 대한 정보. 출전중이 아닌 선수는 이 목록에 없음.
		#	]
		# }