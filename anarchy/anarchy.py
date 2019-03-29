import math
import zipfile
from random import triangular as triforce
from typing import Optional, List

from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.structures.ball_prediction_struct import BallPrediction, Slice

from utils import *
from vectors import *
from render_mesh import *
from objects import *

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
Creeper, oh, man
So we back in the mine
Got our pickaxe swingin' from side to side, side, side to side
This task a grueling one, hope to find some diamonds tonight
Night, night, diamonds tonight
Heads up, you hear a sound, turn around and look up
Total shock fills your body
Oh, no, it's you again
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
        #self.state: State = State.NOT_AERIAL
        self.me = carObject(index)
        self.ball = ballObject()

    def initialize_agent(self):
        import os
        dirpath = os.path.dirname(os.path.realpath(__file__))
        with zipfile.ZipFile(dirpath + "/nothing.zip","r") as zip_ref:
            zip_ref.extractall(dirpath)
        self.triangles = parse_obj_mesh_file(dirpath + "/nothing.obj", 100)
        self.tris_rendered = 0
        pass

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        self.preprocess(packet) #Heyyyy ddthj here
        opponent = packet.game_cars[1 - self.index]
        if opponent.name == 'Self-driving car':
            # All hope is lost. At least by doing this, we can try to preserve our remaining shreds of dignity.
            return

        #Collect data from the packet
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
        # Hi robbie!

        '''
        #Set a destination for Anarchy to reach
        ball_location.y -= abs((ball_location - car_location).y) / 2 * (1 if self.team == 0 else - 1)

        '''        
        #Handle bouncing 
        ball_bounces: List[Slice] = get_ball_bounces(self.get_ball_prediction_struct())
        time: float = ball_bounces[0].game_seconds - self.time
        bounce_location: Vector2 = Vector2(ball_bounces[0].physics.location)

        #Set a destination for Anarchy to reach
        wait = packet.game_ball.physics.location.z > 200
        if wait:
            destination = bounce_location
        else:
            destination = ball_location
        if team_sign * car_location.y > team_sign * ball_location.y or (abs(ball_location.x) > 3200 and abs(ball_location.x) + 100 > abs(car_location.x)):
            destination.y -= max(abs(car_to_ball.y) / 2.5 * team_sign, 20 if wait else 90)
        else:
            destination += (destination - enemy_goal).normalized * max(car_to_ball.length / 4, 20 if wait else 100)
        if abs(car_location.y > 5120): destination.x = min(700, max(-700, destination.x)) #Don't get stuck in goal
        car_to_destination = (destination - car_location)

        #Rendering
        self.renderer.begin_rendering()
        # commented out due to performance concerns
        # self.renderer.draw_polyline_3d([[car_location.x+triforce(-20,20), car_location.y+triforce(-20,20), triforce(shreck(200),200)] for i in range(40)], self.renderer.cyan())
        self.renderer.draw_rect_2d(0, 0, 3840, 2160, True, self.renderer.create_color(64, 246, 74, 138))  # first bot that supports 4k resolution!
        self.renderer.draw_string_2d(triforce(20, 50), triforce(10, 20), 5, 5, 'ALICE NAKIRI IS BEST GIRL', self.renderer.white())
        self.renderer.draw_string_2d(triforce(20, 50), triforce(90, 100), 2, 2, '(zero two is a close second)', self.renderer.lime())
        self.renderer.end_rendering()

        for i in range(10):
            if self.tris_rendered < len(self.triangles):
                self.renderer.begin_rendering(str(self.tris_rendered))
                self.renderer.draw_polyline_3d(self.triangles[self.tris_rendered], self.renderer.yellow())
                self.tris_rendered += 1
                self.renderer.end_rendering()

        #Choose whether to drive backwards or not
        '''
        steer_correction_radians = car_direction.correction_to(car_to_ball)
        '''
        steer_correction_radians = car_direction.correction_to(car_to_destination)
        backwards = (math.cos(steer_correction_radians) < 0 and my_car.physics.location.z < 120)
        if backwards: steer_correction_radians = -(steer_correction_radians - sign(steer_correction_radians) * math.pi if steer_correction_radians != 0 else math.pi)

        #Speed control
        '''
        target_velocity = (bounce_location - car_location).length / time
        '''
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

        #Steering
        turn = clamp11(steer_correction_radians * 3)
        self.controller.steer = turn
        self.controller.handbrake = (abs(turn) > 1 and not my_car.is_super_sonic)

        #Dodging
        self.controller.jump = False
        if (car_to_ball.size < 300 and car_velocity.size > 1000 and packet.game_ball.physics.location.z < 400) or self.dodging:
            dodge(self, car_direction.correction_to(car_to_ball), ball_location)

        #Half-flips
        if backwards and car_velocity.size > 800 and steer_correction_radians < 0.1 or self.halfflipping:
            halfflip(self)
        
        if not self.car.has_wheel_contact and not (self.dodging or self.halfflipping):  # Recovery
            self.controller.roll = clamp11(self.car.physics.rotation.roll * -0.7)
            self.controller.pitch = clamp11(self.car.physics.rotation.pitch * -0.7)
            self.controller.boost = False

        return self.controller
    
    def preprocess(self,packet):
        self.me.update(packet.game_cars[self.index])
        self.ball.update(packet.game_ball)


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

class Matrix3D:
    def __init__(self,r):
        CR = math.cos(r[2])
        SR = math.sin(r[2])
        CP = math.cos(r[0])
        SP = math.sin(r[0])
        CY = math.cos(r[1])
        SY = math.sin(r[1])        
        self.data = [Vector3(CP*CY, CP*SY, SP),Vector3(CY*SP*SR-CR*SY, SY*SP*SR+CR*CY, -CP * SR),Vector3(-CR*CY*SP-SR*SY, -CR*SY*SP+SR*CY, CP*CR)]

    def dot(self,vector):
        return Vector3(self.data[0].dot(vector),self.data[1].dot(vector),self.data[2].dot(vector))

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


def bounce_time(s: float, u: float, a: float=650):
    try:
        return (math.sqrt(2 * a * s + u ** 2) - u) / a
    except: return 0


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
