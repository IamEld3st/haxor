import math

from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.game_state_util import GameState, BallState, CarState, Physics, Vector3, Rotator, GameInfoState

from util.orientation import Orientation
from util.vec import Vec3


class PythonExample(BaseAgent):

    def initialize_agent(self):
        self.ball_status = 3
        self.timer = 0.0
        self.controller_state = SimpleControllerState()

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        ball_location = Vec3(packet.game_ball.physics.location)

        my_car = packet.game_cars[self.index]
        car_location = Vec3(my_car.physics.location)
        team_mul = (my_car.team * 2 - 1) * -1

        car_to_ball = ball_location - car_location

        car_orientation = Orientation(my_car.physics.rotation)
        car_direction = car_orientation.forward

        steer_correction_radians = find_correction(car_direction, car_to_ball)

        if steer_correction_radians > 0:
            turn = -1.0
        else:
            turn = 1.0

        self.controller_state.throttle = 0.0
        self.controller_state.steer = turn

        if packet.game_info.is_round_active:
            if self.ball_status == 0:
                ballstate = BallState(Physics(location=Vector3(car_location.x, car_location.y, car_location.z + 50.0)))
                self.set_game_state(GameState(ball=ballstate))
                self.timer = packet.game_info.game_time_remaining
                self.ball_status = 1
            elif self.ball_status == 1:
                if self.timer - 1.0 > packet.game_info.game_time_remaining:
                    self.ball_status = 2
            elif self.ball_status == 2:
                ballstate = BallState(Physics(location=Vector3(0.0, 4500 * team_mul, 350.0), velocity=Vector3(0.0, 1000 * team_mul, 0.0)))
                self.set_game_state(GameState(ball=ballstate))
                self.ball_status = 3
            elif self.ball_status == 3:
                if packet.game_info.is_kickoff_pause:
                    self.ball_status = 0

        return self.controller_state


def find_correction(current: Vec3, ideal: Vec3) -> float:
    current_in_radians = math.atan2(current.y, -current.x)
    ideal_in_radians = math.atan2(ideal.y, -ideal.x)

    diff = ideal_in_radians - current_in_radians

    if abs(diff) > math.pi:
        if diff < 0:
            diff += 2 * math.pi
        else:
            diff -= 2 * math.pi

    return diff
