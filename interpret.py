from typing import List
from xml.etree import ElementTree as ET

from abc import abstractmethod, ABC


class Argument(ABC):
    value: str

    def __init__(self, value: str):
        self.value = value

    @abstractmethod
    def get_value(self):
        pass


class ConstantArgument(Argument):
    def get_value(self):
        return self.value


class VariableArgument(Argument):
    def get_value(self):
        memory = Memory().get_frame(self.frame)

        if self.name not in memory:
            raise Exception("Variable not defined")
        else:
            return memory[self.name]


class Instruction(ABC):
    arguments: List[str]

    def __init__(self, arguments: List[str]):
        self.arguments = arguments

    @abstractmethod
    def execute(self):
        pass


class WriteInstruction(Instruction):
    def execute(self):
        print("Writing...")


class DefVarInstruction(Instruction):
    def execute(self):
        print("Defining variable...")


class MoveInstruction(Instruction):
    def execute(self):
        print("Moving...")


class MemoryMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        """
        Memory is singleton
        :param args:
        :param kwargs:
        :return:
        """
        if cls not in cls._instances:
            cls._instances[cls] = super(MemoryMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Memory(metaclass=MemoryMeta):
    def __init__(self):
        self._global_frame = {}
        self._local_frame = {}
        self._temporary_frame = {}
        self._stack = []

    def get_global_frame(self):
        return self._global_frame

    def get_local_frame(self):
        return self._local_frame

    def get_temporary_frame(self):
        return self._temporary_frame

    def get_stack(self):
        return self._stack

    def get_frame(self, frame_name: str) -> dict:
        if frame_name == "GF":
            return self.get_global_frame()
        elif frame_name == "LF":
            return self.get_local_frame()
        elif frame_name == "TF":
            return self.get_temporary_frame()
        else:
            raise Exception("Unknown frame name")

    def get_variable(self, frame_name: str, variable_name: str) -> VariableArgument | None:
        frame = self.get_frame(frame_name)

        return frame[variable_name]

    def create_variable(self, frame_name: str, variable_name: str) -> None:
        frame = self.get_frame(frame_name)

        if variable_name in frame:
            raise Exception("Variable already defined")

        frame[variable_name] = None

    def read_variable(self, frame_name: str, variable_name: str) -> VariableArgument:
        frame = self.get_frame(frame_name)

        if variable_name not in frame:
            raise Exception("Variable not defined")

        return frame[variable_name]

    def update_variable(self, frame_name: str, variable_name: str, value) -> None:
        frame = self.get_frame(frame_name)

        if variable_name not in frame:
            raise Exception("Variable not defined")

        frame[variable_name] = value


INSTRUCTION_MAP = {
    "DEFVAR": DefVarInstruction,
    "MOVE": MoveInstruction,
    "WRITE": WriteInstruction,
}


def main():
    xml = """<?xml version="1.0" encoding="UTF-8"?><program language="IPPcode23"><instruction order="1" opcode="DEFVAR"><arg1 type="var">GF@a</arg1></instruction><instruction order="2" opcode="MOVE"><arg1 type="var">GF@a</arg1><arg2 type="int">1</arg2></instruction><instruction order="3" opcode="WRITE"><arg1 type="var">GF@a</arg1></instruction></program>"""

    root = ET.fromstring(xml)

    for instruction_tag in root.findall("instruction"):
        opcode = instruction_tag.get("opcode")
        instruction_class = INSTRUCTION_MAP[opcode]

        arguments = instruction_tag.findall("arg1")

        instruction_tag = instruction_class([])
        instruction_tag.execute()

    print("Hello World")


if __name__ == '__main__':
    main()
