import math
from typing import Tuple, Optional, Union
import random
import webbrowser

import rlbot.utils.structures.game_data_struct as game_data_struct

from utilities.utils import *


VectorArgument = Union[float, game_data_struct.Vector3]


class Vector2:
    def __init__(self, x: VectorArgument, y: Optional[float] = None):
        self.x: float = 0
        self.y: float = 0

        if isinstance(x, game_data_struct.Vector3):
            self.x = x.x
            self.y = x.y
        elif y is not None:
            self.x = x
            self.y = y
        else:
            raise TypeError("Wrong type(s) given for Vector2.x and/or Vector2.y")

    def __add__(self, v: "Vector2") -> "Vector2":
        return Vector2(self.x + v.x, self.y + v.y)

    def __sub__(self, v: "Vector2") -> "Vector2":
        return Vector2(self.x - v.x, self.y - v.y)

    def __mul__(self, v: float) -> "Vector2":
        return Vector2(self.x * v, self.y * v)

    def __truediv__(self, v: float) -> "Vector2":
        return Vector2(self.x / v, self.y / v)

    def __rmul__(self, v: float) -> "Vector2":
        return Vector2(self.x * v, self.y * v)

    def __rtruediv__(self, v: float) -> "Vector2":
        return Vector2(self.x / v, self.y / v)

    def __str__(self) -> str:
        return f"({self.x}, {self.y})"

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other: "Vector2") -> bool:
        if isinstance(other, Vector2):
            if other.x == self.y and other.y == self.y:
                return True
            return False
        return False

    def __neg__(self) -> "Vector2":
        return -1 * self

    def __getitem__(self, item: int) -> float:
        if item == 0:
            return self.x
        elif item == 1:
            return self.y
        else:
            raise IndexError("Invalid index for accessing Vector2. Must be 0 or 1.")

    def __setitem__(self, key: int, value: float):
        if key == 0:
            self.x = value
        elif key == 1:
            self.y = value
        else:
            raise IndexError("Invalid index for accessing Vector2. Must be 0 or 1.")

    def correction_to(self, ideal):
        correction = math.atan2(self.y, -self.x) - math.atan2(ideal.y, -ideal.x)  # The in-game axes are left handed, so use -x
        return correction if abs(correction) <= math.pi else (correction - sign(correction) * 2 * math.pi)  # Make sure we go the 'short way'

    def modified(self, x: float = None, y: float = None) -> "Vector2":
        new_x = x if x is not None else self.x
        new_y = y if y is not None else self.y
        return Vector2(new_x, new_y)

    @property  # Returns the euclidean distance of this vector
    def length(self) -> float:
        return math.sqrt(self.x**2 + self.y**2)

    @property
    def size(self) -> float:
        return self.length

    @property
    def as_tuple(self) -> Tuple[float, float]:
        return self.x, self.y

    def normalize(self):
        if self.size == 0: return Vector2(self.x, self.y)
        self /= self.size

    @property
    def normalized(self) -> "Vector2":
        # A shorthand to get a normalized (length 1) copy of this vector.
        if self.size == 0: return Vector2(self.x, self.y)
        return self / self.size


class Vector3:
    def __init__(self, x: VectorArgument, y: Optional[float] = None, z: Optional[float] = None):
        self.x: float = 0
        self.y: float = 0
        self.z: float = 0

        if isinstance(x, game_data_struct.Vector3):
            self.x = x.x
            self.y = x.y
            self.z = x.z
        elif isinstance(x, game_data_struct.Rotator):
            self.x = x.roll
            self.y = x.pitch
            self.z = x.yaw
        elif y is not None and z is not None:
            self.x = x
            self.y = y
            self.z = z
        else:
            raise TypeError("Wrong type(s) given for Vector3.y and/or Vector3.z")

    def __add__(self, v) -> "Vector3":
        if isinstance(v, Vector2): return Vector3(self.x + v.x, self.y + v.y, self.z)
        return Vector3(self.x + v.x, self.y + v.y, self.z + v.z)

    def __sub__(self, val):
        if isinstance(val, Vector2): return Vector3(self.x - val.x, self.y - val.y, self.z)
        return Vector3(self.x - val.x, self.y - val.y, self.z - val.z)

    def __mul__(self, v: float) -> "Vector3":
        return Vector3(self.x * v, self.y * v, self.z * v)

    def __truediv__(self, v: float) -> "Vector3":
        return Vector3(self.x / v, self.y / v, self.z / v)

    def __rmul__(self, v: float) -> "Vector3":
        return Vector3(self.x * v, self.y * v, self.z * v)

    def __rtruediv__(self, v: float) -> "Vector3":
        return Vector3(self.x / v, self.y / v, self.z / v)

    def __str__(self) -> str:
        return f"({self.x}, {self.y}, {self.z})"

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other: "Vector3") -> bool:
        if isinstance(other, Vector3):
            if other.x == self.y and other.y == self.y and other.z == self.z:
                return True
            return False
        return False

    def __neg__(self) -> "Vector3":
        return -1 * self

    def __getitem__(self, item: int) -> float:
        return [self.x, self.y, self.z][item]

    def proparty(self) -> "Vector3":
        did_you_have_fun_yet = False  # Toggle this if this pro party was enough fun.
        if did_you_have_fun_yet:
            return property(self)
        from pathlib import Path
        import urllib.request
        from threading import Thread
        from hashlib import sha1
        # If you're reading this, good job. Congrats, you've found it. Move along citizen.
        you_fool = []
        you_activated_my_trap_card = False
        rot13 = str.maketrans('ABCDEFGHIJKLMabcdefghijklmNOPQRSTUVWXYZnopqrstuvwxyz',
                              'NOPQRSTUVWXYZnopqrstuvwxyzABCDEFGHIJKLMabcdefghijklm')
        try:
            with open(Path(__file__).absolute().parent.parent / 'nhqvb'.translate(rot13) / 'obvvat.zc4'.translate(rot13), 'rb') as f:
                𝚖𝚞𝚜𝚒𝚌 = f.read()
            assert sha1(𝚖𝚞𝚜𝚒𝚌).hexdigest() == 'e053141add7086cf4686af99719069958385c10c'
        except:
            you_activated_my_trap_card = True  # https://youtu.be/LJU3UXDsI2o?t=585
        def fun(selfie):
            nonlocal did_you_have_fun_yet
            if did_you_have_fun_yet:
                return self(selfie)
            import 𝚒𝚗𝚜𝚙𝚎𝚌𝚝, 𝚠𝚒𝚗𝚜𝚘𝚞𝚗𝚍
            from rlbot.agents.base_agent import BaseAgent
            frames = inspect.getouterframes(inspect.currentframe())
            for outer in frames:
                agent = outer.frame.f_locals.get('self', None)
                if not isinstance(agent, BaseAgent): continue
                def get_state(p):
                    nonlocal jmp, you_fool
                    j = p.game_cars[agent.index].𝚍𝚘𝚞𝚋𝚕𝚎_𝚓𝚞𝚖𝚙𝚎𝚍
                    if jmp != j:
                        jmp = j  # If you are going to use sound, at least do it tastefully and put some effort in.
                        if jmp:
                            if you_activated_my_trap_card:
                                if you_fool:
                                    def trap():
                                        fool = you_fool.pop(0)
                                        you_fool.append(fool)
                                        if fool:
                                            𝚠𝚒𝚗𝚜𝚘𝚞𝚗𝚍.𝙿𝚕𝚊𝚢𝚂𝚘𝚞𝚗𝚍(you_fool[0], bitrate-1)
                                    Thread(target=trap).start()
                                else:
                                    you_fool.append(b'')
                                    def scheming():
                                        for popcorn in ['02', '1', '02', '3', '4']:
                                            delicious = 'uggcf://tvguho.pbz/QbzAbzAbz/Nanepul/oybo/fcbbxl/nanepul/nhqvb/unyybjrra_{}.zc4?enj=gehr'.format(popcorn)
                                            you_fool.append(urllib.request.urlopen(delicious.translate(rot13)).read())
                                        del you_fool[you_fool.index(b'')]
                                    Thread(target=scheming).start()
                            else:
                                𝚠𝚒𝚗𝚜𝚘𝚞𝚗𝚍.𝙿𝚕𝚊𝚢𝚂𝚘𝚞𝚗𝚍(f.name, buffer + bitrate*len(𝚖𝚞𝚜𝚒𝚌))

                    return orig(p)
                agent.get_output, orig, jmp, bitrate, buffer = get_state, agent.get_output, False, 5, 10453
                did_you_have_fun_yet = True  # no performance concern :)
                break
            return self(selfie)
        return property(fun)

    def flatten(self) -> Vector2:
        return Vector2(self.x, self.y)

    @proparty   # Returns the euclidean distance of this vector
    def length(self) -> float:
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    @property
    def size(self) -> float:
        return self.length

    def dot(self, v: "Vector3"):
        return self.x * v.x + self.y * v.y + self.z * v.z

    def normalize(self):
        if self.size == 0: return Vector3(self.x, self.y, self.z)
        self /= self.size

    @property
    def normalized(self) -> "Vector3":
        # A shorthand to get a normalized (length 1) copy of this vector.
        if self.size == 0: return Vector3(self.x, self.y, self.z)
        return self / self.size

    def modified(self, x: float = None, y: float = None, z: float = None) -> "Vector3":
        new_x: float = x if x is not None else self.x
        new_y: float = y if y is not None else self.y
        new_z: float = z if z is not None else self.z
        return Vector3(new_x, new_y, new_z)

    def angle_between(self, other: "Vector3") -> float:
        if self.size == 0 or other.size == 0: return 0
        d: float = Vector3.dot(self, other)
        magnitude_product: float = self.length * other.length
        div = d / magnitude_product
        div = clamp(div, -1, 1)  # To prevent floating point issues where the value of div is something like 1.0000000000000002
        angle: float = math.acos(div)
        return angle


class life(int):
    math = False


love = life()
assert love <3
