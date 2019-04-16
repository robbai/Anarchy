import tempfile
import zipfile
import math
from pathlib import Path
from random import triangular as triforce
from typing import List

from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.structures.ball_prediction_struct import BallPrediction, Slice

from utilities.vectors import *
from utilities.render_mesh import *
from utilities.quick_chat_handler import QuickChatHandler
from utilities.matrix import Matrix3D

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
        self.controller = SimpleControllerState()
        self.dodging = False
        self.halfflipping = False
        self.dodge_pitch = 0
        self.dodge_roll = 0
        self.time = 0
        self.next_dodge_time = 0
        self.quick_chat_handler: QuickChatHandler = QuickChatHandler(self)

    def initialize_agent(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            tmpdir = Path(tmpdirname)
            try:
                with zipfile.ZipFile(Path(__file__).absolute().parent / 'nothing.zip', 'r') as zip_ref: zip_ref.extractall(tmpdir)
            except:
                with zipfile.ZipFile(str(Path(__file__).absolute().parent / 'nothing.zip'), 'r') as zip_ref: zip_ref.extractall(tmpdir)
            self.color_groups = parse_obj_mesh_file(tmpdir / 'zerotwo.obj', 70)
        self.polygons_rendered = 0
        self.current_color_group = 0
        pass

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        self.quick_chat_handler.handle_quick_chats(packet)

        # Collect data from the packet
        self.time = packet.game_info.seconds_elapsed
        ball_location = Vector2(packet.game_ball.physics.location.x, packet.game_ball.physics.location.y)
        my_car = packet.game_cars[self.index]
        self.car = my_car
        car_location = Vector2(my_car.physics.location.x, my_car.physics.location.y)
        car_velocity = Vector3(my_car.physics.velocity.x, my_car.physics.velocity.y, my_car.physics.velocity.z)
        car_direction = get_car_facing_vector(my_car)
        car_to_ball = ball_location - car_location
        team_sign = (1 if my_car.team == 0 else -1)
        enemy_goal = Vector2(0, team_sign * 5120)
        kickoff = (ball_location.x == 0 and ball_location.y == 0)
        impact, impact_time = get_impact(self.get_ball_prediction_struct(), self.car, Vector3(packet.game_ball.physics.location.x, packet.game_ball.physics.location.y, packet.game_ball.physics.location.z), self.renderer)
        rotation_matrix = Matrix3D([my_car.physics.rotation.pitch, my_car.physics.rotation.yaw, my_car.physics.rotation.roll])
        # Hi robbie!
        
        # don't crash if winning by too much
        game_score = QuickChatHandler.get_game_score(packet)
        if game_score[team_sign] - game_score[not team_sign] >= 4:
            return self.controller

        # Handle bouncing
        ball_bounces: List[Slice] = get_ball_bounces(self.get_ball_prediction_struct())
        bounce_location = None
        for b in ball_bounces:
            time: float = b.game_seconds - self.time
            if time < impact_time - 0.5:
                continue
            bounce_location: Vector2 = Vector2(b.physics.location)
            break
        if bounce_location is None:
            time = 0

        # Set a destination for Anarchy to reach
        impact_projection = project_to_wall(car_location, impact.flatten() - car_location)
        avoid_own_goal = impact_projection.y * team_sign < -5000
        wait = (packet.game_ball.physics.location.z > 200 and my_car.physics.location.z < 200)
        if wait:
            destination = bounce_location
        else:
            destination = impact.flatten()
        if kickoff:
            pass
        elif avoid_own_goal:
            offset = (impact_time * 200 + 100)
            destination += Vector2(offset * -sign(impact_projection.x), 140 if wait else 0)
        elif abs(ball_location.x) < 750 or team_sign * car_location.y > team_sign * ball_location.y or (abs(ball_location.x) > 3200 and abs(ball_location.x) + 100 > abs(car_location.x)):
            destination.y -= max(abs(car_to_ball.y) / 2.9, 70 if wait else 110) * team_sign
        else:
            destination += (destination - enemy_goal).normalized * max(car_to_ball.length / 3.4, 60 if wait else 100)
        if abs(car_location.y > 5120): destination.x = min(700, max(-700, destination.x)) #Don't get stuck in goal
        car_to_destination = (destination - car_location)

        # Rendering
        self.renderer.begin_rendering()
        # commented out due to performance concerns
        # self.renderer.draw_polyline_3d([[car_location.x+triforce(-20,20), car_location.y+triforce(-20,20), triforce(shreck(200),200)] for i in range(40)], self.renderer.cyan())
        self.renderer.draw_rect_2d(0, 0, 3840, 2160, True, self.renderer.create_color(64, 246, 74, 138))  # first bot that supports 4k resolution!
        self.renderer.draw_string_2d(triforce(20, 50), triforce(10, 20), 5, 5, 'ALICE NAKIRI IS BEST GIRL', self.renderer.white())
        self.renderer.draw_string_2d(triforce(20, 50), triforce(90, 100), 2, 2, '(zero two is a close second)', self.renderer.lime())
        self.renderer.draw_string_2d(20, 100, 2, 2, "Max Speed: " + str(int(estimate_max_speed(self.car))), self.renderer.white())
        self.renderer.draw_line_3d([destination.x, destination.y, impact.z], [impact.x, impact.y, impact.z], self.renderer.blue())
        if avoid_own_goal: self.renderer.draw_line_3d([car_location.x, car_location.y, 0], [impact_projection.x, impact_projection.y, 0], self.renderer.yellow())
        self.renderer.end_rendering()

        render_mesh(self)

        # Choose whether to drive backwards or not
        wall_touch = (distance_from_wall(impact.flatten()) < 250 and team_sign * impact.y < 4000)
        local = rotation_matrix.dot(Vector3(car_to_destination.x, car_to_destination.y, (impact.z if wall_touch else 17.010000228881836) - my_car.physics.location.z))
        steer_correction_radians = math.atan2(local.y, local.x)
        backwards = (math.cos(steer_correction_radians) < 0)
        if backwards:
            if steer_correction_radians != 0:
                steer_correction_radians = -(steer_correction_radians - sign(steer_correction_radians) * math.pi)
            else:
                steer_correction_radians = math.pi

        # Speed control
        target_velocity = (((bounce_location - car_location).length / time) if time > 0 else 2300)
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

        # Steering
        turn = clamp11(steer_correction_radians * 2)
        self.controller.steer = turn
        self.controller.handbrake = (abs(turn) > 1 and not my_car.is_super_sonic)

        # Dodging
        self.controller.jump = False
        dodge_for_speed = (velocity_change > 700 and not backwards and my_car.boost < 10 and car_to_destination.size > 1000 and abs(steer_correction_radians) < 0.1)
        if (((car_to_ball.size < 300 and packet.game_ball.physics.location.z < 300) or dodge_for_speed) and car_velocity.size > 1200) or self.dodging:
            dodge(self, car_direction.correction_to(car_to_destination if impact_time > 0.8 else car_to_ball), ball_location)

        # Half-flips
        if backwards and impact_time > 0.6 and car_velocity.size > 900 and abs(steer_correction_radians) < 0.1 or self.halfflipping:
            halfflip(self)

        if not self.car.has_wheel_contact and not (self.dodging or self.halfflipping):  # Recovery
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


def halfflip(self):
    if not self.halfflipping and self.car.has_wheel_contact:
        self.halfflipping = True
        self.controller.jump = True
        self.next_dodge_time = self.time
    elif self.time > self.next_dodge_time + 1.0:
        self.halfflipping = False
    elif self.time > self.next_dodge_time + 0.6:
        self.controller.pitch = -1
        self.controller.roll = 1
        if self.car.has_wheel_contact:
            self.halfflipping = False
    elif self.time > self.next_dodge_time + 0.3:
        self.controller.jump = True
        self.controller.pitch = 1


def get_car_facing_vector(car):
    pitch = float(car.physics.rotation.pitch)
    yaw = float(car.physics.rotation.yaw)

    facing_x = math.cos(pitch) * math.cos(yaw)
    facing_y = math.cos(pitch) * math.sin(yaw)

    return Vector2(facing_x, facing_y)


def bounce_time(s: float, u: float, a: float = 650):
    try:
        return (math.sqrt(2 * a * s + u ** 2) - u) / a
    except ZeroDivisionError:
        return 0


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


def estimate_max_speed(car, cap_at_sonic: bool = True):
    velocity_vec = Vector2(car.physics.velocity.x, car.physics.velocity.y)
    velocity = velocity_vec.length
    boost = float(car.boost)

    return min(2200.0 if cap_at_sonic else 2300.0, 1410.0 + boost / 33.3 * 991.667)


def get_impact(path: BallPrediction, car, ball_position: Vector3, renderer = None) -> Tuple[Vector3, float]:
    car_position = Vector3(car.physics.location.x, car.physics.location.y, car.physics.location.z)
    prev_slice = ball_position

    u = Vector3(car.physics.velocity.x, car.physics.velocity.y, car.physics.velocity.z).length
    v = estimate_max_speed(car)
    for i in range(0, path.num_slices):
        current_slice: Vector3 = Vector3(path.slices[i].physics.location.x, path.slices[i].physics.location.y, path.slices[i].physics.location.z)

        s = ((current_slice - car_position).length - 92.75)
        t = (float(i) / 60)
        a = (991.667 if car.boost > 0 else 0) + (0 if u > 1410 else 1000) #Bad estimation
        t_a = (0 if a == 0 else (v - u) / a)
        mx_s = ((t + (t - t_a)) / 2 * v + u * t) 

        if mx_s > s:
            if renderer is not None: renderer.begin_rendering("Impact")
            renderer.draw_line_3d([ball_position.x, ball_position.y, ball_position.z], [current_slice.x, current_slice.y, current_slice.z], renderer.red())
            if renderer is not None: renderer.end_rendering()
            return current_slice, t

    return ball_position, 0 #Couldn't find a point of impact


def project_to_wall(point: Vector2, direction: Vector2) -> Vector2:
    wall = Vector2(sign(direction.x) * 4096, sign(direction.y) * 5120)
    dir_normal = direction.normalized

    x_difference = (abs((wall.x - point.x) / dir_normal.x) if dir_normal.x != 0 else 10000)
    y_difference = (abs((wall.y - point.y) / dir_normal.y) if dir_normal.y != 0 else 10000)

    if x_difference < y_difference:
        # Side wall is closer
        return Vector2(wall.x, point.y + dir_normal.y * x_difference)
    else:
        # Back wall is closer
        return Vector2(point.x + dir_normal.x * y_difference, wall.y)


def distance_from_wall(point: Vector2) -> float:
    return min(4096 - abs(point.x), 5120 - abs(point.y))
