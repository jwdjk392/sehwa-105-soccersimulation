# 이 파일은 모듈 형태로 임포트됨
# 상위 파일에서 직접 호출함. 따라서 시간이 오래 필요한 작업은 필요시에만 별도의 쓰레드로 만들도록.
# 사용자가 요청시 작성한 파일을 테스트할 별도의 파이썬 코드를 제공하도록.
# 이 파일은 UI 렌더링용. 해당 함수가 실행되면 화면에 그 결과를 그려주는것임.

from tkinter import *

def selectTeam(teamNames):
	# TODO
	# 초기화면: 팀을 선택하는 화면. 이 창은 게임 실행 전에 실행됨.
	# 예상 입력값 dict_keys(['Sample Team', 'Sample Team 2', 'Sample Team 3'])
	# 이러한 입력값에서 팀을 2개를 선택해서 Tuple 형태로 팀 이름 반환
	# 튜플에서 0번 항목이 사용자가 플레이할 팀임 - 즉, 사용자한테서 어떠한 팀으로 플레이 할지 선택을 받아서 0번 항목으로 반환할것.
	# 예시 반환
	return  ('Sample Team', 'Sample Team 2')

class GameScreen():
	def __init__(self, teamNames, changeTeam):
		# TODO
		# 게임 화면 초기화 - 게임 창을 띄움. 이후에 이 창을 화면을 계속 업데이트 할것임.
		# teamNames는 튜플 형태로 두개의 문자열임. 예) ('Sample Team', 'Sample Team 2')
		# 0번 항목은 사용자가 플레이하는 팀 / 1번 항목은 상대팀
		# 팀 이름은 UI 등에서 현재 상대하는 팀을 표기하는데 사용
		# changeTeam은 함수임. 이 함수를 호출하면 현재 출전중인 선수를 변경할 수 있음.
		# changeTeam(playerNames) => Tuple 형태로 새로 출전할 선수 이름 목록 반환할것.
		pass

	def startGame():
		# TODO
		# 게임 시작했음을 화면에 보여주기
		pass

	def selectInitialPlayers(players):
		# TODO
		# 초기 플레이어 선택
		# players 값은 다음과 같은 형태의 딕셔너리.
		#[
		#	{
		#		"name": "Player 01",
		#			"speed": 75, => 0~100 사이의 값
		#		"goal_rate": 0.1, => 0~1 사이의 값
		#		"strength": 57 => 0 ~ 100 사이의 값
		#	}
		#	... 비슷한 형태의 선수 데이터 반복
		#]
		# 선수 이름만 Tuple로 반환하기
		return ("Player 01", "Player 02", "Player 03", "Player 04", "Player 05", "Player 06", "Player 07", "Player 08", "Player 09", "Player 10")


	# 아래 함수들은 호출되면 해당 이벤트를 화면에 호출하면 됨.
	def updateStatus(currentTime, ballOwner, myTeamGoalCount, enemyGoalCount):
		# TODO
		# 남은 시간 표시 업데이트
		# currentTime은 문자열 값.
		# ballOWner는 현재 공을 가지고 있는 선수 이름
		# myTeamGoalCount는 우리팀의 골 넣은 횟수. 정수
		# enemyGoalCount는 상대팀의 골 넣은 횟수. 정수.
		pass


	def movePlayerLocation(playerName, x, y):
		# TODO
		# 선수 이동함.
		pass

	def onfieldPlayerChanged(myTeamPlayers, enemyTeamPlayers):
		# TOOD
		# 출전중인 선수 목록이 변경됨. 상대팀일수도, 우리팀일수도.
		# myTeamPlayers, enemyTeamPlayers에 출전중인 선수 이름 목록이 Array로 저장되어있음.
		pass

	def passBall(playerName, wantedPlayerName, receivedPlayerName, successful):
		# TODO
		# playerName이 wantedPlayerName으로 공 패스함
		# 실제로 받게 된 선수는  receivedPlayerName에 이름이 있음.
		# successful은 성공 여부.
		pass

	def tryShoot(playerName, success):
		# playerName이 슛을 시도함.
		# 성공시 success가 True.
		pass

	def GameOver(result):
		# TODO
		# Game over. result가 True이면 승리한것.
		pass