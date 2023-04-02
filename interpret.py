from typing import List
from xml.etree import ElementTree as ET

from abc import abstractmethod, ABC


class Argument(ABC):
    value: str
    name: str
    frame: str

    def __init__(self, value: str, frame: str = "", name: str = ""):
        self.value = value
        self.frame = frame
        self.name = name

    def get_name(self):
        return self.name

    def get_frame(self):
        return self.frame

    @abstractmethod
    def get_value(self):
        pass


class IntegerArgument(Argument):
    def get_value(self):
        return int(self.value)


class StringArgument(Argument):
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
    arguments: List[Argument]

    def __init__(self, arguments: List[Argument]):
        """
        :param arguments: List of arguments
        """
        self.arguments = arguments

    @abstractmethod
    def execute(self):
        """
        Execute instruction
        """
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


def parse_variable_argument(argument: str):
    frame, name = argument.split("@")
    return VariableArgument("", frame, name)


def main():
    xml = """<?xml version="1.0" encoding="UTF-8"?><program language="IPPcode23"><instruction order="1" opcode="DEFVAR"><arg1 type="var">GF@a</arg1></instruction><instruction order="2" opcode="MOVE"><arg1 type="var">GF@a</arg1><arg2 type="int">1</arg2></instruction><instruction order="3" opcode="WRITE"><arg1 type="var">GF@a</arg1></instruction></program>"""

    root = ET.fromstring(xml)

    for instruction_tag in root.findall("instruction"):
        opcode = instruction_tag.get("opcode")
        instruction_class = INSTRUCTION_MAP[opcode]

        arguments = []
        for argument_tag in instruction_tag.findall("./*"):
            argument_type = argument_tag.get("type")
            argument_value = argument_tag.text

            if argument_type == "var":
                argument = parse_variable_argument(argument_value)
            elif argument_type == "int":
                argument = IntegerArgument(argument_value)
            elif argument_type == "string":
                argument = StringArgument(argument_value)
            else:
                raise Exception("Unknown argument type")

            arguments.append(argument)

        instruction = instruction_class(arguments)
        instruction.execute()


if __name__ == '__main__':
    main()
