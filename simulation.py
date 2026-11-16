"""축구 경기 액션 시뮬레이터. 메인 로직에서 임포트해 사용하는 모듈."""

import math
import random


FORMATION_POSITIONS = {
    'LCB': (27, 29), 'RCB': (27, 51), 'CB': (27, 40),
    'LB': (32, 12), 'RB': (32, 68),
    'DM': (45, 40), 'LCM': (54, 28), 'RCM': (54, 52), 'CM': (54, 40),
    'AM': (67, 40), 'LW': (81, 16), 'RW': (81, 64), 'ST': (91, 40),
}
DEFAULT_POSITIONS = ('LCB', 'RCB', 'LB', 'RB', 'DM', 'LCM', 'RCM', 'LW', 'RW', 'ST', 'AM')


def formation_position(player, is_my_team, fallback_index=0):
    position = str(player.get('position', '')).upper()
    if position not in FORMATION_POSITIONS:
        position = DEFAULT_POSITIONS[fallback_index % len(DEFAULT_POSITIONS)]
    x, y = FORMATION_POSITIONS[position]
    return (x if is_my_team else 160 - x), y


class Simulator:
    def __init__(self, myTeam, targetTeam):
        # 원본에서 정의한 공개 함수 이름과 콜백 규약을 유지합니다.
        self.myTeam = myTeam
        self.targetTeam = targetTeam
        self.my_roster = {p['name']: dict(p) for p in myTeam.get('players', [])}
        self.enemy_roster = {p['name']: dict(p) for p in targetTeam.get('players', [])}
        self.my_position_indices = {name: index for index, name in enumerate(self.my_roster)}
        self.enemy_position_indices = {name: index for index, name in enumerate(self.enemy_roster)}
        self.my_onfield = list(self.my_roster)
        self.enemy_onfield = list(self.enemy_roster)
        self.status = {}
        self._enemy_last_change = -1

    def setCurrentOnfield(self, myPlayerNames, enemyPlayerNames):
        # 전달된 이름만 실제 출전 선수로 사용합니다.
        self.my_onfield = [n for n in dict.fromkeys(myPlayerNames) if n in self.my_roster]
        self.enemy_onfield = [n for n in dict.fromkeys(enemyPlayerNames) if n in self.enemy_roster]

    def setCurrentStatus(self, gameStatus):
        # 입력 딕셔너리를 외부에서 수정하더라도 내부 상태가 달라지지 않게 복사합니다.
        self.status = dict(gameStatus)
        self.status['myPlayers'] = [dict(p) for p in gameStatus.get('myPlayers', [])]
        self.status['enemyPlayers'] = [dict(p) for p in gameStatus.get('enemyPlayers', [])]

    @staticmethod
    def _clamp(value, low, high):
        return max(low, min(high, value))

    @staticmethod
    def _distance(a, b):
        return math.hypot(a[0] - b[0], a[1] - b[1])

    def _stats(self, name, my_side):
        return (self.my_roster if my_side else self.enemy_roster).get(name, {})

    def _speed(self, name, my_side):
        return self._clamp(float(self._stats(name, my_side).get('speed', 50)), 0, 100)

    def _strength(self, name, my_side):
        return self._clamp(float(self._stats(name, my_side).get('strength', 50)), 0, 100)

    def _home_position(self, name, my_side):
        roster = self.my_roster if my_side else self.enemy_roster
        indices = self.my_position_indices if my_side else self.enemy_position_indices
        return formation_position(roster.get(name, {}), my_side, indices.get(name, 0))

    def _role(self, name, my_side):
        position = str(self._stats(name, my_side).get('position', '')).upper()
        if position not in FORMATION_POSITIONS:
            roster = self.my_roster if my_side else self.enemy_roster
            indices = self.my_position_indices if my_side else self.enemy_position_indices
            position = DEFAULT_POSITIONS[indices.get(name, 0) % len(DEFAULT_POSITIONS)]
        if position in ('LCB', 'RCB', 'CB', 'LB', 'RB'):
            return 'defender'
        if position in ('DM', 'LCM', 'RCM', 'CM', 'AM'):
            return 'midfielder'
        return 'forward'

    def _movement_target(self, name, pos, friends, opponents, owner, my_side, presser):
        direction = 1 if my_side else -1
        home_x, home_y = self._home_position(name, my_side)
        role = self._role(name, my_side)

        if owner == name:
            carry_distance = {'defender': 8, 'midfielder': 12, 'forward': 16}[role]
            return (pos[0] + direction * carry_distance, pos[1])

        if owner in friends:
            ball_x, ball_y = friends[owner]
            advance, tracking = {
                'defender': (1, 0.35),
                'midfielder': (8, 0.55),
                'forward': (15, 0.70),
            }[role]
            ball_progress = (ball_x - home_x) * direction
            support_run = self._clamp(ball_progress * tracking, -12, 24)
            lane_pull = self._clamp((ball_y - home_y) * 0.32, -12, 12)
            return (home_x + direction * (advance + support_run), home_y + lane_pull)

        if owner in opponents:
            ball_x, ball_y = opponents[owner]
            if name == presser:
                return (ball_x - direction * 4, ball_y)
            compact_x = self._clamp((ball_x - home_x) * 0.18, -10, 10)
            compact_y = self._clamp((ball_y - home_y) * 0.16, -8, 8)
            return (home_x + compact_x, home_y + compact_y)

        return (home_x, home_y)

    def _step_towards(self, old, target, max_step):
        dist = self._distance(old, target)
        if dist == 0:
            return old
        ratio = min(1.0, max_step / dist)
        return (self._clamp(old[0] + (target[0] - old[0]) * ratio, 0, 160),
                self._clamp(old[1] + (target[1] - old[1]) * ratio, 0, 80))

    def _pass_probability(self, start, end, opponents, passer, my_side):
        length = self._distance(start, end)
        chance = 0.95 - length * 0.006
        # 패스 경로 근처에 수비수가 있으면 차단될 가능성이 증가합니다.
        dx, dy = end[0] - start[0], end[1] - start[1]
        denom = dx * dx + dy * dy
        if denom > 0:
            nearest = 1000.0
            for point in opponents.values():
                t = self._clamp(((point[0]-start[0])*dx + (point[1]-start[1])*dy)/denom, 0, 1)
                projected = (start[0] + t*dx, start[1] + t*dy)
                nearest = min(nearest, self._distance(point, projected))
            if nearest < 10:
                chance -= (10-nearest)*0.025
        chance += (self._strength(passer, my_side)-50)*0.001
        return self._clamp(chance, 0.08, 0.98)

    def _shoot_probability(self, point, attacker, my_side, opponents):
        # 가정: 우리 팀은 +X 방향, 상대 팀은 -X 방향으로 공격합니다.
        goal = (160, 40) if my_side else (0, 40)
        dist = self._distance(point, goal)
        goal_rate = self._clamp(float(self._stats(attacker, my_side).get('goal_rate', .10)), 0, 1)
        keeper = (self.targetTeam if my_side else self.myTeam).get('keeper', {})
        defense_rate = self._clamp(float(keeper.get('defense_rate', .10)), 0, 1)
        # goal_rate는 공격 성공 성향, defense_rate는 골키퍼 방어 성향으로 적용.
        chance = (0.08 + 0.72*goal_rate + 0.36*(1-dist/160)) * (1-0.72*defense_rate)
        nearby = sum(self._distance(point, p) < 12 for p in opponents.values())
        chance *= max(.45, 1-.13*nearby)
        return self._clamp(chance, 0.01, 0.90)

    def _maybe_change_enemy(self, turn, callback):
        # 30분과 60분에 벤치가 있고 유효한 대체가 가능한 경우에만 자동 교체.
        if turn not in (30, 60) or self._enemy_last_change == turn:
            return
        bench = [n for n in self.enemy_roster if n not in self.enemy_onfield]
        if not bench or not self.enemy_onfield:
            return
        incoming = max(bench, key=lambda n: self._speed(n, False)+self._strength(n, False))
        outgoing = min(self.enemy_onfield, key=lambda n: self._speed(n, False)+self._strength(n, False))
        next_names = [incoming if n == outgoing else n for n in self.enemy_onfield]
        callback(next_names)
        self.enemy_onfield = next_names
        self._enemy_last_change = turn

    def startSimulation(self, turn, passToPlayer, shoot, movePlayerLocation, changeEnemyOnfieldStatus):
        if not isinstance(turn, int) or not 0 <= turn <= 89:
            raise ValueError('turn은 0부터 89까지의 정수여야 합니다.')
        if not self.status:
            raise ValueError('startSimulation 전에 setCurrentStatus를 호출해야 합니다.')

        self._maybe_change_enemy(turn, changeEnemyOnfieldStatus)
        mine = {p['playerName']: (self._clamp(float(p['playerX']), 0, 160),
                                  self._clamp(float(p['playerY']), 0, 80))
                for p in self.status['myPlayers'] if p['playerName'] in self.my_onfield}
        enemy = {p['playerName']: (self._clamp(float(p['playerX']), 0, 160),
                                    self._clamp(float(p['playerY']), 0, 80))
                 for p in self.status['enemyPlayers'] if p['playerName'] in self.enemy_onfield}
        owner = self.status.get('ballOwner')
        # 수비는 가장 가까운 한 명만 압박하고, 나머지는 포지션 간격을 유지합니다.
        for my_side, friends, opponents in ((True, mine, enemy), (False, enemy, mine)):
            presser = None
            if owner in opponents and friends:
                presser = min(friends, key=lambda name: self._distance(friends[name], opponents[owner]))
            for name, pos in list(friends.items()):
                target = self._movement_target(name, pos, friends, opponents, owner, my_side, presser)
                speed = self._speed(name, my_side)
                updated = self._step_towards(pos, target, 1 + speed*.03)
                movePlayerLocation(name, round(updated[0], 2), round(updated[1], 2))
                friends[name] = updated

        # 1분 턴 3회마다 한 번만 패스 또는 슛을 시도해 기존 행동 빈도를 유지합니다.
        if turn % 3 != 2:
            return

        # 실제 공 소유자만 패스 또는 슛을 시도할 수 있습니다.
        for my_side, friends, opponents in ((True, mine, enemy), (False, enemy, mine)):
            if owner not in friends:
                continue
            point = friends[owner]
            goal = (160, 40) if my_side else (0, 40)
            distance_to_goal = self._distance(point, goal)
            options = [(name, p) for name, p in friends.items() if name != owner]
            # 가까운 슛은 적극적으로 시도하고, 중거리 슛은 낮은 확률로 섞습니다.
            close_shot = distance_to_goal <= 42
            long_shot = distance_to_goal <= 62 and random.random() < 0.32
            if close_shot or long_shot or not options:
                chance = self._shoot_probability(point, owner, my_side, opponents)
                if distance_to_goal > 42:
                    chance *= max(0.25, 1 - (distance_to_goal - 42) * 0.025)
                chance = self._clamp(chance + random.uniform(-0.12, 0.12), 0.02, 0.90)
                success = random.random() < chance
                shoot(owner, success)
            else:
                forward = [(n, p) for n, p in options
                           if (p[0]-point[0])*(1 if my_side else -1) > 0]
                candidates = forward or options
                wanted, destination = min(candidates, key=lambda item: self._distance(item[1], goal))
                chance = self._pass_probability(point, destination, opponents, owner, my_side)
                success = random.random() < chance
                if success:
                    received = wanted
                elif opponents:
                    received = min(opponents, key=lambda n: self._distance(opponents[n], destination))
                else:
                    # 상대 선수가 없으면 실패한 패스의 수신자를 특정할 수 없습니다.
                    received = None
                passToPlayer(owner, wanted, received, success)
            break
