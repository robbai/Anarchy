import math
from random import triangular as triforce, uniform
from typing import List
import getpass

from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.structures.ball_prediction_struct import BallPrediction, Slice

from utilities.actions import recover, dodge, halfflip
from utilities.calculations import invert_angle, get_car_facing_vector, get_ball_bounces, get_impact, distance_from_wall, inside_turning_radius, project_to_wall, estimate_max_speed, closest_boost
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
        teammate_going_for_ball: bool = False
        for index, car in enumerate(packet.game_cars[:8]):
            if car.team == self.team and index != self.index:
                teammate_to_ball: Vector3 = ball_location - Vector3(car.physics.location)
                vector = get_car_facing_vector(car)
                teammate_facing_direction: Vector3 = Vector3(vector.x, vector.y, 0)
                teammate_velocity_direction: Vector3 = car_velocity.normalized
                self_to_ball: Vector3 = ball_location - car_location
                if teammate_to_ball.length < self_to_ball.length and \
                        (teammate_to_ball.angle_between(teammate_facing_direction) < 0.35 or
                         teammate_to_ball.angle_between(teammate_velocity_direction) < 0.35 or
                         teammate_to_ball.length < 300):
                    teammate_going_for_ball = True
                    break

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
        elif teammate_going_for_ball:
            destination = closest_boost(car_location, self.get_field_info().boost_pads, packet.game_boosts)
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
