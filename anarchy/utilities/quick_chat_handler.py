import random
from typing import List, Tuple
import time
import threading

from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.structures.quick_chats import QuickChats
from rlbot.agents.base_agent import BaseAgent


_SCORED_ON: List[int] = [QuickChats.Compliments_NiceShot, QuickChats.Compliments_NiceOne, QuickChats.Custom_Compliments_proud,
                         QuickChats.Custom_Compliments_GC, QuickChats.Custom_Compliments_Pro, QuickChats.Reactions_Noooo]
_HAS_SCORED: List[int] = [QuickChats.Reactions_Whew, QuickChats.Compliments_WhatASave, QuickChats.Reactions_Calculated]
_HAS_DEMOED: List[int] = [QuickChats.Apologies_Whoops, QuickChats.Custom_Useful_Demoing]
_GOT_DEMOED: List[int] = [QuickChats.Custom_Toxic_DeAlloc, QuickChats.Apologies_Cursing, QuickChats.Reactions_Wow,
                          QuickChats.Compliments_Thanks]
_MINE: List[int] = [32, 49, 53, 0]
_BOOST: List[int] = [4, 6, 8, 1]


class Spam(threading.Thread):
    def __init__(self, handler: 'QuickChatHandler', chats: List[int]):
        super(Spam, self).__init__()
        self.handler = handler
        self.chats = chats
        self.count = random.randint(2, 5)  # How many quick-chats to send
        self.pause = random.uniform(0.4, 0.8)  # How long to pause between chats

    def run(self):
        for i in range(self.count):
            self.handler.agent.send_quick_chat(QuickChats.CHAT_EVERYONE, random.choice(self.chats))
            time.sleep(self.pause)


class QuickChatHandler:
    def __init__(self, agent: BaseAgent) -> None:
        self.agent: BaseAgent = agent
        self.prev_frame_demos: int = 0
        self.prev_frame_score: Tuple[int, int] = (0, 0)

    def handle_quick_chats(self, packet: GameTickPacket) -> None:
        current_score: Tuple[int, int] = QuickChatHandler.get_game_score(packet)

        spam = None

        if current_score[self.agent.team] > self.prev_frame_score[self.agent.team]:
            spam = Spam(self, _HAS_SCORED)
        if current_score[not self.agent.team] > self.prev_frame_score[not self.agent.team]:
            spam = Spam(self, _SCORED_ON)
        if packet.game_cars[self.agent.index].is_demolished:
            spam = Spam(self, _GOT_DEMOED)
        if packet.game_cars[self.agent.index].score_info.demolitions > self.prev_frame_demos:
            spam = Spam(self, _HAS_DEMOED)
        if spam is None:
            try:
                spam=Spam(self, _MINE) if (''+self.packet.game_ball.latest_touch.player_name)==self.agent.name else (Spam(self, _BOOST) if self.packet.game_cars[self.agent.index].boost==13 else None)
            except:
                print("oops")
        if spam is not None:
            spam.start()

        self.prev_frame_demos = packet.game_cars[self.agent.index].score_info.demolitions
        self.prev_frame_score = current_score

    @staticmethod
    def get_game_score(packet: GameTickPacket) -> Tuple[int, int]:
        score: List[int] = [0, 0]  # Index 0 is blue, index 1 is orange

        for car in packet.game_cars:
            score[car.team] += car.score_info.goals

        return score[0], score[1]
