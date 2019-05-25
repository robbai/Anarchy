import math
from random import triangular as triforce, uniform
from typing import List
import getpass

from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.structures.ball_prediction_struct import BallPrediction, Slice
from rlbot.utils.game_state_util import GameState, BallState, CarState, Physics, Vector3 as Vec3, Rotator, GameInfoState

from utilities.actions import recover, dodge, halfflip
from utilities.calculations import invert_angle
from utilities.vectors import *
from utilities.render_mesh import unzip_and_make_mesh, ColoredWireframe
from utilities.quick_chat_handler import QuickChatHandler
from utilities.matrix import Matrix3D
from utilities.aerial import aerial_option_b as Aerial

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
        self.dodge_angle = 0
        self.time = 0
        self.next_dodge_time = 0
        self.quick_chat_handler: QuickChatHandler = QuickChatHandler(self)
        self.render_statue = ("wood3" not in getpass.getuser())
        self.zero_two: ColoredWireframe = (unzip_and_make_mesh("nothing.zip", "zerotwo.obj") if self.render_statue else None)
        self.aerial: Aerial = None
        self.steer_correction_radians: float = 0

    def initialize_agent(self):
        pass

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        self.quick_chat_handler.handle_quick_chats(packet)

        # Collect data from the packet
        self.time = packet.game_info.seconds_elapsed
        ball_location = Vector3(packet.game_ball.physics.location.x, packet.game_ball.physics.location.y, packet.game_ball.physics.location.z)
        ball_velocity = Vector3(packet.game_ball.physics.velocity.x, packet.game_ball.physics.velocity.y, packet.game_ball.physics.velocity.z)
        self.car = packet.game_cars[self.index]
        car_location = Vector3(self.car.physics.location.x, self.car.physics.location.y, self.car.physics.location.z)
        car_velocity = Vector3(self.car.physics.velocity.x, self.car.physics.velocity.y, self.car.physics.velocity.z)
        car_direction = get_car_facing_vector(self.car)
        car_to_ball = ball_location - car_location
        team_sign = (1 if self.car.team == 0 else -1)
        enemy_goal = Vector2(0, team_sign * 5120)
        kickoff = (ball_location.x == 0 and ball_location.y == 0)
        impact, impact_time = get_impact(self.get_ball_prediction_struct(), self.car, Vector3(packet.game_ball.physics.location.x, packet.game_ball.physics.location.y, packet.game_ball.physics.location.z), self.renderer)
        impact_projection = project_to_wall(car_location, impact.flatten() - car_location)
        rotation_matrix = Matrix3D([self.car.physics.rotation.pitch, self.car.physics.rotation.yaw, self.car.physics.rotation.roll])
        rotation_velocity = rotation_matrix.dot(self.car.physics.angular_velocity)
        # Hi robbie!

        '''
        # don't crash if winning by too much
        game_score = QuickChatHandler.get_game_score(packet)
        if game_score[self.car.team] - game_score[1 - self.car.team] >= 4:
            return self.controller
        '''

        # Handle bouncing
        ball_bounces: List[Slice] = get_ball_bounces(self.get_ball_prediction_struct())
        bounce_location = None
        for b in ball_bounces:
            time: float = b.game_seconds - self.time
            if time < impact_time - 0.3:
                continue
            bounce_location: Vector2 = Vector2(b.physics.location)
            break
        if bounce_location is None:
            time = 0

        # Handle aerials
        if self.aerial is not None:
            if self.car.has_wheel_contact and self.aerial.jt + 1 < self.time:
                # Give up on an aerial
                self.aerial = None
            else:
                # Get the output of the aerial
                aerial_output = self.aerial.execute(packet, self.index, self.get_ball_prediction_struct())
                if self.aerial.target is not None:
                    self.renderer.begin_rendering()
                    self.renderer.draw_line_3d(car_location, car_location + self.aerial.target, self.renderer.white())
                    self.renderer.end_rendering()
                return aerial_output
        if self.aerial is None and self.car.has_wheel_contact and impact.z - self.car.physics.location.z > 500 and car_velocity.length > 100 and\
           (self.car.boost > 20 or (abs(time - 0.6) < 0.1 and (impact - car_location).flatten().length < 1000))\
            and abs(self.steer_correction_radians) < 0.4 and impact_time < 5 and (impact_projection.y * team_sign > -5000 or abs(impact_projection.x) > 1000):
            # Start a new aerial
            self.aerial = Aerial(self.time)
            return self.aerial.execute(packet, self.index, self.get_ball_prediction_struct())

        # Set a destination for Anarchy to reach
        avoid_own_goal = impact_projection.y * team_sign < -5000
        wait = (ball_location.z > 200 and self.car.physics.location.z < 200)
        take_serious_shot = (not kickoff and car_velocity.length > 600 and car_to_ball.y * team_sign > 0 and ball_velocity.flatten().length < 3000 and ball_location.y * team_sign > -2000)
        if wait:
            destination = Vector3(bounce_location.x, bounce_location.y, 0)
        else:
            destination = impact
            time = 0
        if kickoff:
            destination = ball_location + Vector3(0, -92.75 * team_sign, 0)
        elif avoid_own_goal:
            offset = (impact_time * 200 + 100)
            destination += Vector2(offset * -sign(impact_projection.x), 140 if wait else 0)
        elif abs(ball_location.x) < 750 or team_sign * car_location.y > team_sign * ball_location.y or (abs(ball_location.x) > 3200 and abs(ball_location.x) + 100 > abs(car_location.x)):
            destination.y -= max(abs(car_to_ball.y) / 2.9, 70 if wait else 100) * team_sign
        else:
            destination += (destination - enemy_goal).normalized * max(car_to_ball.flatten().length / (1.7 if take_serious_shot else 3.3), 60 if wait else 100)
        if abs(car_location.y > 5120): destination.x = min(700, max(-700, destination.x)) #Don't get stuck in goal
        car_to_destination = (destination - car_location)

        # Rendering
        self.renderer.begin_rendering()
        # commented out due to performance concerns
        # self.renderer.draw_polyline_3d([[car_location.x+triforce(-20,20), car_location.y+triforce(-20,20), triforce(shreck(200),200)] for i in range(40)], self.renderer.cyan())
        '''self.renderer.draw_rect_2d(0, 0, 3840, 2160, True, self.renderer.create_color(64, 246, 74, 138))  # first bot that supports 4k resolution!
        self.renderer.draw_string_2d(triforce(20, 50), triforce(10, 20), 5, 5, 'ALICE NAKIRI IS BEST GIRL', self.renderer.white())
        self.renderer.draw_string_2d(triforce(20, 50), triforce(90, 100), 2, 2, '(zero two is a close second)', self.renderer.lime())'''
        self.renderer.draw_string_2d(20, 100, 2, 2, "Max Speed: " + str(int(estimate_max_speed(self.car))), self.renderer.white())
        if kickoff: self.renderer.draw_string_2d(20, 140, 2, 2, "Kickoff", self.renderer.white())
        if take_serious_shot: self.renderer.draw_string_2d(20, 140, 2, 2, "Shoot", self.renderer.white())
        self.renderer.draw_line_3d([destination.x, destination.y, impact.z], [impact.x, impact.y, impact.z], self.renderer.blue())
        if avoid_own_goal: self.renderer.draw_line_3d([car_location.x, car_location.y, 0], [impact_projection.x, impact_projection.y, 0], self.renderer.yellow())
        self.renderer.end_rendering()

        if self.render_statue: self.zero_two.render(self.renderer)

        # Choose whether to drive backwards or not
        wall_touch = (distance_from_wall(impact.flatten()) < 500 and team_sign * impact.y < 4000)
        local = rotation_matrix.dot(Vector3(car_to_destination.x, car_to_destination.y, (impact.z if wall_touch else 17.010000228881836) - self.car.physics.location.z))
        self.steer_correction_radians = math.atan2(local.y, local.x)
        slow_down = abs(self.steer_correction_radians > 0.3 and inside_turning_radius(local, car_velocity.length) and take_serious_shot)
        if slow_down:
            self.renderer.begin_rendering()
            self.renderer.draw_string_2d(triforce(20, 50), triforce(10, 20), 6, 6, 'Uh Oh', self.renderer.pink() if (self.time % 0.5) < 0.25 else self.renderer.red())
            self.renderer.end_rendering()
        turning_radians = self.steer_correction_radians
        backwards = (math.cos(turning_radians) < 0)
        if backwards:
            turning_radians = invert_angle(turning_radians)

        # Speed control
        target_velocity = (((bounce_location - car_location).length / time) if time > 0 else 2300)
        velocity_change = (target_velocity - car_velocity.flatten().length)
        if slow_down:
            self.controller.boost = False
            #self.controller.throttle = -clamp11(car_direction.correction_to(car_velocity.flatten()) * car_velocity.length)
            self.controller.throttle = 0
        if (velocity_change > 200 or target_velocity > 1410):
            self.controller.boost = (abs(turning_radians) < 0.2 and not self.car.is_super_sonic and not backwards)
            self.controller.throttle = (-1 if backwards else 1)
        elif velocity_change > -150:
            self.controller.boost = False
            self.controller.throttle = 0
        else:
            self.controller.boost = False
            self.controller.throttle = (1 if backwards else -1)

        # Steering
        turn = clamp11(turning_radians * 3)
        self.controller.steer = turn
        self.controller.handbrake = (abs(turn) > 1 and not self.car.is_super_sonic)

        # Dodging
        self.controller.jump = False
        dodge_for_speed = (velocity_change > 500 and not backwards and self.car.boost < 14 and self.time > self.next_dodge_time + 0.85 and car_to_destination.size > (2200 if take_serious_shot else 1200) and abs(turning_radians) < 0.1)
        if (((car_to_ball.flatten().size < 400 and ball_location.z < 300) or dodge_for_speed) and car_velocity.size > 1100) or self.dodging:
            dodge_at_ball = (impact_time < 0.4)
            dodge_angle = (car_direction.correction_to(car_to_ball) if dodge_at_ball else car_direction.correction_to(car_to_destination))
            dodge(self, dodge_angle, rotation_velocity, 4 if dodge_at_ball else 1)

        # Half-flips
        if backwards and (time if wait else impact_time) > 0.6 and car_velocity.size > 900 and abs(turning_radians) < 0.1 or self.halfflipping:
            halfflip(self, rotation_velocity)

        # Recovery
        if not (self.dodging or self.halfflipping):
            if not self.car.has_wheel_contact:
                #local = rotation_matrix.dot(car_to_ball)
                #self.steer_correction_radians = math.atan2(local.y, local.x)
        
                self.controller.steer = 0
                recover(self, rotation_velocity)
                self.controller.boost = False
            else:
                self.controller.roll = 0
                self.controller.pitch = 0
                self.controller.yaw = 0

        return self.controller


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

    bt = (bounce_time(car.physics.location.z - 17.010000228881836, -car.physics.velocity.z) if not car.has_wheel_contact else 0)
    u = Vector3(car.physics.velocity.x, car.physics.velocity.y, car.physics.velocity.z).length
    v = estimate_max_speed(car)
    for i in range(0, path.num_slices):
        current_slice: Vector3 = Vector3(path.slices[i].physics.location.x, path.slices[i].physics.location.y, path.slices[i].physics.location.z)

        s = ((current_slice - car_position).length - 92.75)
        t = (float(i) / 60) - bt
        a = (991.667 if car.boost > 0 else 0) + (0 if u > 1410 else 800) #Bad estimation
        t_a = (0 if a == 0 else (v - u) / a)
        mx_s = ((t + (t - t_a)) / 2 * v + u * t) 

        if mx_s > s:
            if renderer is not None:
                renderer.begin_rendering("Impact")
                renderer.draw_line_3d([ball_position.x, ball_position.y, ball_position.z], [current_slice.x, current_slice.y, current_slice.z], renderer.red())
                renderer.end_rendering()
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


def turning_radius(car_speed: float) -> float: # Thx Dom
    return 156+0.1*car_speed+0.000069*car_speed**2+0.000000164*car_speed**3-5.62E-11*car_speed**4


def inside_turning_radius(local: Vector3, car_speed: float) -> bool:
    turn_radius = turning_radius(car_speed)
    return turn_radius > min((local - Vector3(0, -turn_radius, 0)).length, (local - Vector3(0, turn_radius, 0)).length)
