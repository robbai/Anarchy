import math
from random import triangular as triforce, uniform, randint
from typing import List

from rlbot.agents.base_agent import (
    BaseAgent,
    SimpleControllerState,
    BOT_CONFIG_AGENT_HEADER,
)
from rlbot.parsing.custom_config import ConfigObject
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.structures.ball_prediction_struct import BallPrediction, Slice

from utilities.actions import recover, dodge, halfflip
from utilities.calculations import (
    invert_angle,
    get_car_facing_vector,
    get_ball_bounces,
    get_impact,
    distance_from_wall,
    inside_turning_radius,
    project_to_wall,
    closest_boost,
)
from utilities.vectors import *
from utilities.render_mesh import unzip_and_build_zero_two, ColoredWireframe
from utilities.quick_chat_handler import QuickChatHandler
from utilities.matrix import Matrix3D
from utilities.aerial import aerial_option_b as Aerial
from utilities.demo import Demolition, max_time as max_demo_time
from utilities.utils import *
from utilities.jukebox import Jukebox
from utilities.action.action import ActionBase
from utilities.action.dodge import Dodge
from utilities.action.recover import Recover

# first!
# WELCOME ROBBIE

"""
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
"""


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
        self.zero_two: Optional[ColoredWireframe] = None
        self.aerial: Optional[Aerial] = None
        self.steer_correction_radians: float = 0
        self.demo: Optional[Demolition] = None
        self.gamemode: Gamemode = Gamemode.SOCCAR
        self.jukebox: Jukebox = Jukebox(self)
        self.action: ActionBase = None
        self.rotation_matrix: Matrix3D = None
        self.rotation_velocity: Vector3 = None
        self.car_direction: Vector3 = None
        self.impact: Vector3 = None

    def load_config(self, config_header):
        render_statue = config_header.getboolean("render_statue")
        if render_statue:
            self.zero_two = unzip_and_build_zero_two()

    @staticmethod
    def create_agent_configurations(config: ConfigObject):
        params = config.get_header(BOT_CONFIG_AGENT_HEADER)
        params.add_value("render_statue", bool, default=False)

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        self.quick_chat_handler.handle_quick_chats(packet)
        self.jukebox.update(packet)

        # Collect data from the packet
        self.mode = (
            Gamemode.DROPSHOT
            if self.get_field_info().num_boosts == 0
            else Gamemode.SOCCAR
        )
        self.time = packet.game_info.seconds_elapsed
        ball_location = Vector3(packet.game_ball.physics.location)
        self.car = packet.game_cars[self.index]
        car_location = Vector3(self.car.physics.location)
        car_velocity = Vector3(self.car.physics.velocity)
        car_direction = get_car_facing_vector(self.car)
        self.car_direction = car_direction
        car_to_ball = ball_location - car_location
        is_1v1 = (
            packet.num_cars == 2
            and packet.game_cars[not self.index].team != self.car.team
        )
        team_sign = (
            1
            if self.car.team
            == (
                is_1v1
                and packet.teams[self.car.team].score == 7
                and packet.teams[not self.car.team].score == 0
            )
            else -1
        )
        enemy_goal = Vector2(0, team_sign * 5120)
        kickoff = packet.game_info.is_kickoff_pause
        ball_prediction = self.get_ball_prediction_struct()
        impacts = [
            get_impact(ball_prediction, car, self.time, self.renderer)
            for car in packet.game_cars[: packet.num_cars]
        ]
        impact, impact_time = impacts[self.index]
        self.impact = impact
        impact_projection = project_to_wall(
            car_location, impact.flatten() - car_location
        )
        rotation_matrix = Matrix3D(
            [
                self.car.physics.rotation.pitch,
                self.car.physics.rotation.yaw,
                self.car.physics.rotation.roll,
            ]
        )
        self.rotation_matrix = rotation_matrix
        rotation_velocity = rotation_matrix.dot(self.car.physics.angular_velocity)
        self.rotation_velocity = rotation_velocity
        car_local_velocity = rotation_matrix.dot(car_velocity)
        correct_side_of_ball: bool = (
            (impact_projection.y - car_location.y) * team_sign > 0
        )
        # Hi robbie!
        if self.time == packet.game_ball.latest_touch.time_seconds:
            print(
                "\a"
            )  # for all the people who mute anarchy because they dont like 'boing' :)

        # this kinda kills the anime and idk what to do about it
        self.renderer.begin_rendering("disco")
        for i in range(100):
            hmmm = ball_location + Vector3(
                random.randint(-1000, 1000),
                random.randint(-1000, 1000),
                random.randint(-1000, 1000),
            )
            self.renderer.draw_line_3d(
                [ball_location.x, ball_location.y, ball_location.z],
                [hmmm.x, hmmm.y, hmmm.z],
                self.renderer.create_color(
                    255,
                    random.randint(0, 255),
                    random.randint(0, 255),
                    random.randint(0, 255),
                ),
            )
        self.renderer.end_rendering()

        # Action.
        if self.action:
            print(self.action.__class__.__name__)
            if not hasattr(self.action, "finished") or not self.action.finished:
                return self.action.step(packet)
            self.action = None

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
            if self.car.has_wheel_contact and self.aerial.jt + 0.5 < self.time:
                # Give up on an aerial
                self.aerial = None
            else:
                # Get the output of the aerial
                aerial_output = self.aerial.execute(
                    packet, self.index, self.get_ball_prediction_struct()
                )
                if self.aerial.target is not None:
                    self.renderer.begin_rendering()
                    self.renderer.draw_line_3d(
                        car_location,
                        car_location + self.aerial.target,
                        self.renderer.white(),
                    )
                    self.renderer.end_rendering()
                return aerial_output
        if (
            self.aerial is None
            and self.car.has_wheel_contact
            and impact.z - self.car.physics.location.z > 500
            and car_velocity.length > 100
            and self.demo is None
            and (
                self.car.boost > 20
                or (
                    abs(time - 0.6) < 0.1
                    and (impact - car_location).flatten().length < 1000
                )
            )
            and abs(self.steer_correction_radians) < 0.4
            and impact_time < 2.5
            and (
                impact_projection.y * team_sign > -5000
                or abs(impact_projection.x) > 1000
            )
            and math.cos(car_velocity.angle_between(impact - car_location))
            * car_velocity.flatten().length
            > 400
        ):
            # Start a new aerial
            self.aerial = Aerial(self.time)
            return self.aerial.execute(
                packet, self.index, self.get_ball_prediction_struct()
            )

        # Set a destination for Anarchy to reach
        teammate_going_for_ball: bool = False
        for index, car in enumerate(packet.game_cars[: packet.num_cars]):
            if car.team == self.team and index != self.index:
                teammate_location = Vector3(car.physics.location)
                teammate_correct_side_of_ball: bool = (
                    (impacts[index][0].y - teammate_location.y) * team_sign > 0
                )
                if correct_side_of_ball and not teammate_correct_side_of_ball:
                    continue
                if impacts[index][1] + 0.1 < impact_time or (
                    not correct_side_of_ball and teammate_correct_side_of_ball
                ):
                    teammate_going_for_ball = True
                    self.renderer.begin_rendering("teammate")
                    self.renderer.draw_line_3d(
                        car_location, teammate_location, self.renderer.black()
                    )
                    self.renderer.draw_rect_3d(
                        teammate_location, 4, 4, True, self.renderer.black()
                    )
                    self.renderer.end_rendering()
                    break

        avoid_own_goal = impact_projection.y * team_sign < -5000
        wait = ball_location.z > 200 and self.car.physics.location.z < 200
        take_serious_shot = False
        obey_turning_radius = True  # Slow down if the target is in the turning radius
        demoing = self.demo is not None
        close_boost = closest_boost(
            Vector3(-impact.x, impact.y, 0)
            if teammate_going_for_ball and impact_time < 2.5 and not kickoff
            else car_location,
            self.get_field_info().boost_pads,
            packet.game_boosts,
        )
        convenient_boost = (
            close_boost
            and (close_boost - car_location).flatten().length * (5 if is_1v1 else 3)
            < (impact - car_location).flatten().length
        )
        need_boost = not self.car.is_super_sonic and self.car.boost < (
            40 if convenient_boost else 30
        )
        park_car = False
        not_our_kickoff = kickoff and teammate_going_for_ball

        if wait and bounce_location is not None:
            destination = Vector3(bounce_location.x, bounce_location.y, 0)
        else:
            destination = impact
            time = 0
        if kickoff and not not_our_kickoff:
            destination = ball_location + Vector3(0, -92.75 * team_sign, 0)
            obey_turning_radius = False
        elif (
            avoid_own_goal
            and not kickoff
            and not demoing
            and (not teammate_going_for_ball or impact.y * team_sign > -4000)
        ):
            offset = max(0, impact_time - 0.5) * 160 + 110
            destination += Vector2(
                offset * -sign(impact_projection.x), (140 if wait else 0) * -team_sign
            )
        elif (
            not_our_kickoff
            or teammate_going_for_ball
            or demoing
            or (close_boost and need_boost and (not is_1v1 or convenient_boost))
        ):
            if close_boost:
                destination = close_boost

            demo_location = None
            if (demoing or not need_boost) and not kickoff:
                if not demoing:
                    self.demo = Demolition.start_demo(self, packet)
                demo_location, demo_time = (
                    self.demo.get_destination(packet)
                    if self.demo is not None
                    else (None, 0)
                )
                if demo_location is not None:
                    destination = demo_location
                    obey_turning_radius = False
                    demoing = True
                    time = 0
            if demo_location is None:
                self.demo = None
                demoing = False
                if (
                    (not need_boost and car_to_ball.length > 2500)
                    if not not_our_kickoff
                    else (abs(car_location.x) < 50)
                ):  # Middle
                    park_car = True
                    destination = Vector2(0, -4900 * team_sign)
                    destination += (impact.flatten() - destination) / 8
                    destination = Vector3(destination.x, destination.y, 17)
        elif team_sign * (car_location.y - ball_location.y) > 0:
            destination.x += max(car_to_ball.length / 3, 80 if wait else 120) * -sign(
                impact_projection.x
            )
        else:
            destination += (destination - enemy_goal).normalized * max(
                (destination - car_location).length
                / ((2.1 + impact_time / 1.9) if take_serious_shot else 3.7),
                60 if wait else 110,
            )
            take_serious_shot = True
        if abs(car_location.y) > 5120:
            destination.x = min(
                700, max(-700, destination.x)
            )  # Don't get stuck in goal
        car_to_destination = destination - car_location

        # Rendering
        self.renderer.begin_rendering()
        if kickoff:
            self.renderer.draw_string_2d(
                20, 140, 2, 2, "Kickoff", self.renderer.white()
            )
        if take_serious_shot:
            self.renderer.draw_string_2d(20, 140, 2, 2, "Shoot", self.renderer.white())
        self.renderer.draw_line_3d(
            [destination.x, destination.y, impact.z],
            [impact.x, impact.y, impact.z],
            self.renderer.blue(),
        )
        if avoid_own_goal:
            self.renderer.draw_line_3d(
                [car_location.x, car_location.y, 0],
                [impact_projection.x, impact_projection.y, 0],
                self.renderer.yellow(),
            )
        if not demoing:
            self.renderer.clear_screen(Demolition.get_render_name(self))
        if park_car:
            self.renderer.draw_string_2d(
                20, 140, 2, 2, "Parking!", self.renderer.yellow()
            )
        self.renderer.end_rendering()

        if self.zero_two is not None and self.time > 10.0:
            self.zero_two.render(self.renderer)

        # Choose whether to drive backwards or not
        wall_touch = (
            distance_from_wall(impact.flatten()) < 500 and team_sign * impact.y < 4000
        )
        local = rotation_matrix.dot(
            Vector3(
                car_to_destination.x,
                car_to_destination.y,
                (impact.z if wall_touch else 17.010000228881836)
                - self.car.physics.location.z,
            )
        )
        self.steer_correction_radians = math.atan2(local.y, local.x)
        slow_down = (
            abs(self.steer_correction_radians) > 0.2
            and inside_turning_radius(local, car_velocity.length)
            and obey_turning_radius
        )
        if slow_down:
            self.renderer.begin_rendering()
            self.renderer.draw_string_2d(
                triforce(20, 50),
                triforce(10, 20),
                6,
                6,
                "Uh Oh",
                self.renderer.pink()
                if (self.time % 0.5) < 0.25
                else self.renderer.red(),
            )
            self.renderer.end_rendering()
        turning_radians = self.steer_correction_radians
        backwards = (
            math.cos(turning_radians) < 0
            and not demoing
            and not self.car.is_super_sonic
        )
        if backwards:
            turning_radians = invert_angle(turning_radians)
        throttle_sign = -1 if backwards else 1

        # Speed control
        target_velocity = (
            ((bounce_location - car_location).length / time) if time > 0 else 2300
        )
        velocity_change = target_velocity - car_velocity.flatten().length
        if park_car:
            self.controller.boost = False
            self.controller.throttle = (
                clamp11((destination - car_location).length / 2000) * throttle_sign
            )
        elif slow_down:
            if car_velocity.length > 400:
                self.controller.throttle = -sign(
                    rotation_matrix.data[0].dot(destination - car_location)
                )
                self.controller.boost = self.controller.throttle > 0
            else:
                self.controller.throttle = 0
        elif velocity_change > 300 or target_velocity > 1410 or demoing:
            self.controller.boost = (
                abs(turning_radians) < 0.2
                and not self.car.is_super_sonic
                and not backwards
            )
            if self.controller.boost and self.mode is Gamemode.DROPSHOT:
                self.controller.boost = 30 < self.car.boost - (
                    2200 - car_velocity.length
                ) / ((911 + (2 / 3)) if self.car.has_wheel_contact else 1000) * (
                    100 / 3
                )
            self.controller.throttle = throttle_sign
        elif velocity_change > -150:
            self.controller.boost = False
            self.controller.throttle = 0
        else:
            self.controller.boost = False
            self.controller.throttle = -throttle_sign

        # Steering
        turn = clamp11(turning_radians * 4)
        self.controller.steer = turn
        self.controller.handbrake = (
            abs(turning_radians) > 1.1
            and not self.car.is_super_sonic
            and not (slow_down or park_car)
        )

        # prevent inefficient powerslides
        if sign(rotation_velocity.z) != sign(self.controller.steer) or sign(
            car_local_velocity.x
        ) != sign(self.controller.throttle):
            self.controller.handbrake = False

        # Dodging
        self.controller.jump = False
        dodge_for_speed = (
            velocity_change > 500
            and not backwards
            and self.car.boost < 14
            and self.time > self.next_dodge_time + 0.85
            and car_to_destination.size > (2000 if take_serious_shot else 1200)
            and abs(turning_radians) < 0.1
            and not demoing
        )
        if kickoff:
            dodge_for_speed = car_velocity.size > 1250
        if (
            (
                (car_to_ball.flatten().size < 400 and ball_location.z < 300)
                or dodge_for_speed
            )
            and car_velocity.size > 1100
        ) or self.dodging:
            dodge_at_ball = impact_time < 0.4
            dodge_direction = car_to_ball if dodge_at_ball else car_to_destination
            self.action = Dodge(self, dodge_direction)
            return self.action.step(packet)

        # Half-flips
        if (
            backwards
            and not park_car
            and (time if wait else impact_time) > 0.6
            and car_velocity.size > 900
            and abs(turning_radians) < 0.1
            or self.halfflipping
        ):
            halfflip(self, rotation_velocity)

        # Recovery
        if not (self.dodging or self.halfflipping) and not self.car.has_wheel_contact:
            self.action = Recover(
                self, rotation_velocity, allow_yaw_wrap=(car_location.z > 250)
            )
            return self.action.step(packet)

        return self.controller

        # To be fair, you have to have a very high IQ to understand this bot. The logic is extremely subtle,
        # and without a solid grasp of rocket league physics most of the mechanics will go over a typical coders head.
        # There's also Anarchy's nihilistic outlook, which is deftly woven into his characterisation- his personal
        # philosophy draws heavily from ATBA literature, for instance. The fans understand this stuff; they have the
        # intellectual capacity to truly appreciate the depths of these mechanics, to realise that they're not just
        # solid- they say something deep about RLBOT. As a consequence people who dislike this bot ARE idiots-
        # of course they wouldn't appreciate, for instance, the mechanics in Anarchy's existential catchphrase "boiing.mp4"
        # which itself is a cryptic reference to tareharts epic Fathers and Sons. I'm smirking right now just imagining
        # one of those addlepated simpletons scratching their heads in confusion as proparty's genius wit unfolds itself
        # in this bot. What fools.. How I pity them. 😂

        # And yes, by the way, i DO have an Anarchy tattoo. And no, you cannot see it. It's for the ladies' eyes only-
        # and even then they have to demonstrate that they're within 5 IQ points of my own (preferably lower)
        # beforehard. Nothin personnel botmaker 😎
