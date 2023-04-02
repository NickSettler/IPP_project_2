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
        return self.value


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
