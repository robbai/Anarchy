import math

from rlbot.agents.base_agent import SimpleControllerState, GameTickPacket, BaseAgent
from .action import ActionBase
from utilities.vectors import Vector3


class Dodge(ActionBase):
    def __init__(
        self,
        agent: BaseAgent,
        direction: Vector3,
        second_jump_time: float = 0.175,
        first_jump_duration: float = 0.1,
        second_jump_duration: float = 1.2,
    ):
        self.agent: BaseAgent = agent
        self.direction = direction
        self.local = agent.rotation_matrix.dot(direction.normalized)
        self.second_jump_time: float = second_jump_time
        self.first_jump_duration: float = first_jump_duration
        self.second_jump_duration: float = second_jump_duration
        self.start_time: float = 0
        self.finished: bool = False

    def step(self, packet: GameTickPacket) -> SimpleControllerState:
        if self.start_time == 0:
            self.start_time = packet.game_info.seconds_elapsed
        controller: SimpleControllerState = SimpleControllerState()
        controller.boost = (
            self.agent.rotation_matrix.data[0].dot(self.direction.normalized) > 0.75
        )
        if (
            packet.game_info.seconds_elapsed
            < self.start_time + self.first_jump_duration
        ):
            controller.jump = True
        if (
            packet.game_info.seconds_elapsed > self.start_time + self.second_jump_time
            and not self.finished
        ):
            controller.jump = True
            if not packet.game_cars[self.agent.index].double_jumped:
                angle = math.atan2(self.local.y, self.local.x)
                controller.pitch = -math.cos(angle)
                controller.yaw = math.sin(angle)
        if (
            packet.game_info.seconds_elapsed - self.start_time
            > self.second_jump_time
            + self.second_jump_duration
            * (not packet.game_cars[self.agent.index].has_wheel_contact)
        ):
            self.finished = True
        return controller
