from rlbot.agents.base_agent import SimpleControllerState, GameTickPacket, BaseAgent
from .action import ActionBase
from utilities.vectors import Vector2


class Dodge(ActionBase):
    def __init__(self, agent: BaseAgent, direction: Vector2, second_jump_time: float, first_jump_duration: float = 0.1):
        self.agent: BaseAgent = agent
        self.direction: Vector2 = direction
        self.second_jump_time: float = second_jump_time
        self.first_jump_duration: float = first_jump_duration
        self.start_time: float = 0
        self.finished: bool = False

    def step(self, packet: GameTickPacket) -> SimpleControllerState:
        if self.start_time == 0: self.start_time = packet.game_info.seconds_elapsed
        controller: SimpleControllerState = SimpleControllerState()
        if packet.game_info.seconds_elapsed < self.start_time + self.first_jump_duration: controller.jump = True
        if packet.game_info.seconds_elapsed - self.start_time > self.second_jump_time and not self.finished:
            controller.jump = True
            controller.pitch = self.direction.x
            controller.yaw = self.direction.y
        if packet.game_cars[self.agent.index].double_jumped:
            self.finished = True
            controller.jump = False
        return controller
