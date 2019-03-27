import base64
import math
import random
from random import triangular as triforce
import webbrowser
from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.structures.ball_prediction_struct import BallPrediction, Slice
# Anarchy requires the newest rlutilities which cannot be pip installed via `pip install rlutilities` because it is not on PyPI. You must install it via `pip install -e .` after cloning the RLUtilities repository at: https://github.com/samuelpmish/RLUtilities.
'''from rlutilities.linear_algebra import *
from rlutilities.mechanics import Aerial
from rlutilities.simulation import Game, Ball'''
from utils import *
from vectors import *
from typing import Optional

from typing import List

# first!

'''
⠄⠄⠄⠄⠄⣧⣼⣯⠄⣸⣠⣶⣶⣦⣾⠄⠄⠄⠄⡀⠄⢀⣿⣿⠄⠄⠄⢸⡇⠄
⠄⠄⠄⠄⣾⣿⠿⠿⠶⠿⢿⣿⣿⣿⣿⣦⣤⣄⢀⡅⢠⣾⣛⡉⠄⠄⠄⠸⢀⣿⠄
 ⠄⠄⢀⡋⣡⣴⣶⣶⡀⠄⠄⠙⢿⣿⣿⣿⣿⣿⣴⣿⣿⣿⢃⣤⣄⣀⣥⣿⣿⠄
 ⠄⠄⢸⣇⠻⣿⣿⣿⣧⣀⢀⣠⡌⢻⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠿⠿⣿⣿⣿⠄
 ⠄⢀⢸⣿⣷⣤⣤⣤⣬⣙⣛⢿⣿⣿⣿⣿⣿⣿⡿⣿⣿⡍⠄⠄⢀⣤⣄⠉⠋⣰
 ⠄⣼⣖⣿⣿⣿⣿⣿⣿⣿⣿⣿⢿⣿⣿⣿⣿⣿⢇⣿⣿⡷⠶⠶⢿⣿⣿⠇⢀⣤
 ⠘⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣽⣿⣿⣿⡇⣿⣿⣿⣿⣿⣿⣷⣶⣥⣴⣿⡗
 ⢀⠈⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡟⠄
 ⢸⣿⣦⣌⣛⣻⣿⣿⣧⠙⠛⠛⡭⠅⠒⠦⠭⣭⡻⣿⣿⣿⣿⣿⣿⣿⣿⡿⠃⠄
 ⠘⣿⣿⣿⣿⣿⣿⣿⣿⡆⠄⠄⠄⠄⠄⠄⠄⠄⠹⠈⢋⣽⣿⣿⣿⣿⣵⣾⠃⠄
 ⠄⠘⣿⣿⣿⣿⣿⣿⣿⣿⠄⣴⣿⣶⣄⠄⣴⣶⠄⢀⣾⣿⣿⣿⣿⣿⣿⠃⠄⠄
 ⠄⠄⠈⠻⣿⣿⣿⣿⣿⣿⡄⢻⣿⣿⣿⠄⣿⣿⡀⣾⣿⣿⣿⣿⣛⠛⠁⠄⠄⠄
 ⠄⠄⠄⠄⠈⠛⢿⣿⣿⣿⠁⠞⢿⣿⣿⡄⢿⣿⡇⣸⣿⣿⠿⠛⠁⠄⠄⠄⠄⠄
 ⠄⠄⠄⠄⠄⠄⠄⠉⠻⣿⣿⣾⣦⡙⠻⣷⣾⣿⠃⠿⠋⠁⠄⠄⠄⠄⠄⢀⣠⣴
 ⣿⣿⣿⣶⣶⣮⣥⣒⠲⢮⣝⡿⣿⣿⡆⣿⡿⠃⠄⠄⠄⠄⠄⠄⠄⣠⣴⣿⣿⣿
'''

class Anarchy(BaseAgent):
    def __init__(self, name, team, index):
        super().__init__(name, team, index)
        self.controller: SimpleControllerState = SimpleControllerState()
        self.dodging = False
        self.dodge_pitch = 0
        self.dodge_roll = 0
        self.time = 0
        self.next_dodge_time = 0
        #self.state: State = State.NOT_AERIAL

    def initialize_agent(self):
        pass

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        opponent = packet.game_cars[1 - self.index]
        if opponent.name == 'Self-driving car':
            # All hope is lost. At least by doing this, we can try to preserve our remaining shreds of dignity.
            return

        self.time = packet.game_info.seconds_elapsed
        ball_location = Vector2(packet.game_ball.physics.location.x, packet.game_ball.physics.location.y)

        my_car = packet.game_cars[self.index]
        self.car = my_car
        car_location = Vector2(my_car.physics.location.x, my_car.physics.location.y)
        car_velocity = Vector3(my_car.physics.velocity.x, my_car.physics.velocity.y, my_car.physics.velocity.z)
        car_direction = get_car_facing_vector(my_car)
        ball_location.y -= abs((ball_location - car_location).y) / 2 * (1 if self.team == 0 else - 1)
        car_to_ball = ball_location - car_location
        # Hi robbie!
        """ I don't have enough deletions to remove the two lines below for `time` and `bounce_location`. If a kind soul could delete these few lines, I'd be eternally grateful.
        time = (bounce_time(packet.game_ball.physics.location.z - 92.75, -packet.game_ball.physics.velocity.z) if packet.game_ball.physics.location.z > 200 else 0.00001)
        bounce_location = Vector2(packet.game_ball.physics.location.x, packet.game_ball.physics.location.y) #FEEL FREE TO CHANGE THIS TO ACTUALLY GET THE BOUNCE FROM PREDICTION
        """

        ball_bounces: List[Slice] = get_ball_bounces(self.get_ball_prediction_struct())
        time: float = ball_bounces[0].game_seconds - self.time
        bounce_location: Vector2 = Vector2(ball_bounces[0].physics.location)
        target_velocity = (bounce_location - car_location).length / time

        self.renderer.begin_rendering()
        # commented out due to performance concerns
        # self.renderer.draw_polyline_3d([[car_location.x+triforce(-20,20), car_location.y+triforce(-20,20), triforce(shreck(200),200)] for i in range(40)], self.renderer.cyan())
        self.renderer.draw_rect_2d(0, 0, 3840, 2160, True, self.renderer.create_color(64, 246, 74, 138))  # first bot that supports 4k resolution!
        self.renderer.draw_string_2d(triforce(20, 50), triforce(10, 20), 5, 5, 'ALICE NAKIRI IS BEST GIRL', self.renderer.white())
        self.renderer.draw_string_2d(triforce(20, 50), triforce(90, 100), 2, 2, '(zero two is a close second)', self.renderer.lime())
        self.renderer.end_rendering()

        steer_correction_radians = car_direction.correction_to(car_to_ball)
        backwards = (math.cos(steer_correction_radians) < 0 and my_car.physics.location.z < 120)
        if backwards: steer_correction_radians = -(steer_correction_radians - sign(steer_correction_radians) * math.pi if steer_correction_radians != 0 else math.pi)

        velocity_change = (target_velocity - car_velocity.flatten().length)
        if velocity_change > 200 or target_velocity > 1410:
            self.controller.boost = (abs(steer_correction_radians) < 0.2 and not my_car.is_super_sonic and not backwards)
            self.controller.throttle = (1 if not backwards else -1)
        elif velocity_change > -50:
            self.controller.boost = False
            self.controller.throttle = 0
        else:
            self.controller.boost = False
            self.controller.throttle = (-1 if not backwards else 1)

        turn = clamp11(steer_correction_radians * 3)

        self.controller.steer = turn
        self.controller.handbrake = (abs(turn) > 1 and not my_car.is_super_sonic)
        self.controller.jump = False

        if (car_to_ball.size < 300 and car_velocity.size > 1000 and packet.game_ball.physics.location.z < 400) or self.dodging:
            dodge(self, car_direction.correction_to(car_to_ball), ball_location)
        if not self.car.has_wheel_contact and not self.dodging:  # Recovery
            self.controller.roll = clamp11(self.car.physics.rotation.roll * -0.7)
            self.controller.pitch = clamp11(self.car.physics.rotation.pitch * -0.7)
            self.controller.boost = False

        return self.controller


def dodge(self, angle_to_ball: float, target=None):
    if self.car.has_wheel_contact and not self.dodging:
        if target is None:
            roll = 0
            pitch = 1
        else:
            roll = math.sin(angle_to_ball)
            pitch = math.cos(angle_to_ball)
        self.dodge_pitch = -pitch
        self.dodge_roll = roll
        self.dodging = True
        self.controller.jump = True
        self.next_dodge_time = self.time + 0.1

    elif self.time > self.next_dodge_time:
        self.controller.jump = True
        self.controller.pitch = clamp11(self.dodge_pitch)
        self.controller.roll = clamp11(self.dodge_roll)
        if self.car.has_wheel_contact or self.time > self.next_dodge_time + 1:
            self.dodging = False


def get_car_facing_vector(car):
    pitch = float(car.physics.rotation.pitch)
    yaw = float(car.physics.rotation.yaw)

    facing_x = math.cos(pitch) * math.cos(yaw)
    facing_y = math.cos(pitch) * math.sin(yaw)

    return Vector2(facing_x, facing_y)


def bounce_time(s: float, u: float, a: float=650):
    try:
        return (math.sqrt(2 * a * s + u ** 2) - u) / a
    except: return 0.000000001


def get_ball_bounces(path: BallPrediction) -> List[Slice]:
    """
    Calculates when the ball bounces.

    :param path: The BallPrediction object given by the framework
    :return: BallPrediction Slices when the ball bounces
    """
    bounces: List[Slice] = []

    # Skip the first 10 frames because they cause issues with finding bounces
    for i in range(10, path.num_slices):
        prev_slice: Slice = path.slices[i - 1]
        current_slice: Slice = path.slices[i]
        acceleration: Vector3 = (Vector3(current_slice.physics.velocity) - Vector3(prev_slice.physics.velocity)) / \
                                (current_slice.game_seconds - prev_slice.game_seconds)
        # The ball's Z acceleration will not be around -650 if it is bouncing.
        if not (-600 > acceleration.z > -680):
            bounces.append(current_slice)

    return bounces
