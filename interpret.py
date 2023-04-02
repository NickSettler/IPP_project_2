from __future__ import annotations
import sys
from typing import List, Dict
from xml.etree import ElementTree
from abc import abstractmethod, ABC


class Argument(ABC):
    value: str
    name: str
    frame: str

    def __init__(self, value: str | None, frame: str = "", name: str = ""):
        self.value = value
        self.frame = frame
        self.name = name

    def get_name(self) -> str:
        return self.name

    def get_frame(self) -> str:
        return self.frame

    @abstractmethod
    def get_value(self):
        pass


class IntegerArgument(Argument):
    def get_value(self) -> int:
        return int(self.value)


class BooleanArgument(Argument):
    def get_value(self) -> bool:
        if self.value == "true":
            return True
        else:
            return False


class StringArgument(Argument):
    def get_value(self) -> str:
        return self.value


class NilArgument(Argument):
    def get_value(self) -> None:
        return None


class LabelArgument(Argument):
    def get_value(self) -> str:
        return self.value


class TypeArgument(Argument):
    def get_value(self) -> str:
        return self.value


class VariableArgument(Argument):
    def __init__(self, value: str):
        frame, name = value.split("@", 1)
        super().__init__(None, frame, name)

    def get_value(self) -> str:
        memory = Memory().get_frame(self.frame)

        if self.name not in memory:
            raise Exception("Variable not defined")
        else:
            return memory[self.name] if memory[self.name] is not None else ""


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


class MoveInstruction(Instruction):
    def execute(self):
        variable = self.arguments[0]
        value = self.arguments[1].get_value()

        Memory().update_variable(variable.get_frame(), variable.get_name(), value)


class CreateFrameInstruction(Instruction):
    def execute(self):
        Memory().get_temporary_frame().clear()


class PushFrameInstruction(Instruction):
    def execute(self):
        Memory().get_stack().append(Memory().get_temporary_frame())
        Memory().get_temporary_frame().clear()


class PopFrameInstruction(Instruction):
    def execute(self):
        Memory().get_temporary_frame().update(Memory().get_stack().pop())


class DefVarInstruction(Instruction):
    def execute(self):
        variable = self.arguments[0]
        Memory().create_variable(variable.get_frame(), variable.get_name())


class CallInstruction(Instruction):
    def execute(self):
        label = self.arguments[0]
        Memory().get_stack().append(label)


class ReturnInstruction(Instruction):
    def execute(self):
        Memory().get_stack().pop()


class PushSInstruction(Instruction):
    def execute(self):
        value = self.arguments[0].get_value()
        Memory().get_stack().append(value)


class PopSInstruction(Instruction):
    def execute(self):
        Memory().get_stack().pop()


class AddInstruction(Instruction):
    def execute(self):
        variable = self.arguments[0]
        value1 = self.arguments[1].get_value()
        value2 = self.arguments[2].get_value()

        Memory().update_variable(variable.get_frame(), variable.get_name(), value1 + value2)


class SubInstruction(Instruction):
    def execute(self):
        variable = self.arguments[0]
        value1 = self.arguments[1].get_value()
        value2 = self.arguments[2].get_value()

        Memory().update_variable(variable.get_frame(), variable.get_name(), value1 - value2)


class MulInstruction(Instruction):
    def execute(self):
        variable = self.arguments[0]
        value1 = self.arguments[1].get_value()
        value2 = self.arguments[2].get_value()

        Memory().update_variable(variable.get_frame(), variable.get_name(), value1 * value2)


class IDivInstruction(Instruction):
    def execute(self):
        variable = self.arguments[0]
        value1 = self.arguments[1].get_value()
        value2 = self.arguments[2].get_value()

        Memory().update_variable(variable.get_frame(), variable.get_name(), value1 // value2)


class LTInstruction(Instruction):
    def execute(self):
        variable = self.arguments[0]
        value1 = self.arguments[1].get_value()
        value2 = self.arguments[2].get_value()

        Memory().update_variable(variable.get_frame(), variable.get_name(), value1 < value2)


class GTInstruction(Instruction):
    def execute(self):
        variable = self.arguments[0]
        value1 = self.arguments[1].get_value()
        value2 = self.arguments[2].get_value()

        Memory().update_variable(variable.get_frame(), variable.get_name(), value1 > value2)


class EQInstruction(Instruction):
    def execute(self):
        variable = self.arguments[0]
        value1 = self.arguments[1].get_value()
        value2 = self.arguments[2].get_value()

        Memory().update_variable(variable.get_frame(), variable.get_name(), value1 == value2)


class AndInstruction(Instruction):
    def execute(self):
        variable = self.arguments[0]
        value1 = self.arguments[1].get_value()
        value2 = self.arguments[2].get_value()

        Memory().update_variable(variable.get_frame(), variable.get_name(), value1 and value2)


class OrInstruction(Instruction):
    def execute(self):
        variable = self.arguments[0]
        value1 = self.arguments[1].get_value()
        value2 = self.arguments[2].get_value()

        Memory().update_variable(variable.get_frame(), variable.get_name(), value1 or value2)


class NotInstruction(Instruction):
    def execute(self):
        variable = self.arguments[0]
        value = self.arguments[1].get_value()

        Memory().update_variable(variable.get_frame(), variable.get_name(), not value)


class Int2CharInstruction(Instruction):
    def execute(self):
        variable = self.arguments[0]
        value = self.arguments[1].get_value()

        Memory().update_variable(variable.get_frame(), variable.get_name(), chr(value))


class Stri2IntInstruction(Instruction):
    def execute(self):
        variable = self.arguments[0]
        string = self.arguments[1].get_value()
        index = self.arguments[2].get_value()

        Memory().update_variable(variable.get_frame(), variable.get_name(), ord(string[index]))


class ReadInstruction(Instruction):
    def execute(self):
        variable = self.arguments[0]
        var_type = self.arguments[1].get_value()
        value = input()

        if var_type == "int":
            value = int(value)
        elif var_type == "bool":
            value = value.lower() == "true"
        elif var_type == "string":
            value = str(value)

        Memory().update_variable(variable.get_frame(), variable.get_name(), value)


class WriteInstruction(Instruction):
    def execute(self):
        for argument in self.arguments:
            print(argument.get_value(), end=" ")


class ConcatInstruction(Instruction):
    def execute(self):
        variable = self.arguments[0]
        string1 = self.arguments[1].get_value()
        string2 = self.arguments[2].get_value()

        Memory().update_variable(variable.get_frame(), variable.get_name(), string1 + string2)


class StrLenInstruction(Instruction):
    def execute(self):
        variable = self.arguments[0]
        string = self.arguments[1].get_value()

        Memory().update_variable(variable.get_frame(), variable.get_name(), len(string))


class GetCharInstruction(Instruction):
    def execute(self):
        variable = self.arguments[0]
        string = self.arguments[1].get_value()
        index = self.arguments[2].get_value()

        Memory().update_variable(variable.get_frame(), variable.get_name(), string[index])


class SetCharInstruction(Instruction):
    def execute(self):
        variable = self.arguments[0]
        index = self.arguments[1].get_value()
        replace_string = self.arguments[2].get_value()

        string = variable.get_value()

        string = string[:index] + replace_string[0] + string[index + 1:]
        Memory().update_variable(variable.get_frame(), variable.get_name(), string)


class TypeInstruction(Instruction):
    def execute(self):
        variable = self.arguments[0]
        value = self.arguments[1].get_value()

        Memory().update_variable(variable.get_frame(), variable.get_name(), type(value).__name__)


class LabelInstruction(Instruction):
    def execute(self):
        pass


class JumpInstruction(Instruction):
    def execute(self):
        label = self.arguments[0].get_value()
        Memory().set_program_counter(label)


class JumpIfEqInstruction(Instruction):
    def execute(self):
        label = self.arguments[0].get_value()
        value1 = self.arguments[1].get_value()
        value2 = self.arguments[2].get_value()

        if value1 == value2:
            Memory().set_program_counter(label)


class JumpIfNeqInstruction(Instruction):
    def execute(self):
        label = self.arguments[0].get_value()
        value1 = self.arguments[1].get_value()
        value2 = self.arguments[2].get_value()

        if value1 != value2:
            Memory().set_program_counter(label)


class ExitInstruction(Instruction):
    def execute(self):
        code = self.arguments[0].get_value()
        exit(code)


class DPrintInstruction(Instruction):
    def execute(self):
        print(self.arguments[0].get_value(), file=sys.stderr, end=" ")


class BreakInstruction(Instruction):
    def execute(self):
        breakpoint()


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
    @staticmethod
    def get_frame_method(self, frame_name: str):
        if frame_name == "GF":
            return self.get_global_frame
        elif frame_name == "LF":
            return self.get_local_frame
        elif frame_name == "TF":
            return self.get_temporary_frame
        else:
            raise Exception("Unknown frame name ({})".format(frame_name))

    def __init__(self):
        self._global_frame = {}
        self._local_frame = {}
        self._temporary_frame = {}
        self._stack = []

    def get_global_frame(self) -> Dict:
        return self._global_frame

    def get_local_frame(self) -> Dict:
        return self._local_frame

    def get_temporary_frame(self) -> Dict:
        return self._temporary_frame

    def get_stack(self) -> List:
        return self._stack

    def get_frame(self, frame_name: str) -> Dict:
        return self.get_frame_method(self, frame_name)()

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
    "MOVE": MoveInstruction,
    "CREATEFRAME": CreateFrameInstruction,
    "PUSHFRAME": PushFrameInstruction,
    "POPFRAME": PopFrameInstruction,
    "DEFVAR": DefVarInstruction,
    "CALL": CallInstruction,
    "RETURN": ReturnInstruction,
    "ADD": AddInstruction,
    "SUB": SubInstruction,
    "MUL": MulInstruction,
    "IDIV": IDivInstruction,
    "LT": LTInstruction,
    "GT": GTInstruction,
    "EQ": EQInstruction,
    "AND": AndInstruction,
    "OR": OrInstruction,
    "NOT": NotInstruction,
    "INT2CHAR": Int2CharInstruction,
    "STRI2INT": Stri2IntInstruction,
    "READ": ReadInstruction,
    "WRITE": WriteInstruction,
    "CONCAT": ConcatInstruction,
    "STRLEN": StrLenInstruction,
    "GETCHAR": GetCharInstruction,
    "SETCHAR": SetCharInstruction,
    "TYPE": TypeInstruction,
    "LABEL": LabelInstruction,
    "JUMP": JumpInstruction,
    "JUMPIFEQ": JumpIfEqInstruction,
    "JUMPIFNEQ": JumpIfNeqInstruction,
    "EXIT": ExitInstruction,
    "DPRINT": DPrintInstruction,
    "BREAK": BreakInstruction,
}

ARGUMENT_TYPE_MAP = {
    "int": IntegerArgument,
    "bool": BooleanArgument,
    "string": StringArgument,
    "nil": NilArgument,
    "label": LabelArgument,
    "type": TypeArgument,
    "var": VariableArgument,
}


def main():
    root = ElementTree.parse("examples/arithmetics.xml")

    for instruction_tag in root.findall("instruction"):
        opcode = instruction_tag.get("opcode")
        instruction_class = INSTRUCTION_MAP[opcode]

        arguments = []
        for argument_tag in instruction_tag.findall("./*"):
            argument_type = argument_tag.get("type")
            argument_value = argument_tag.text
            argument_class = ARGUMENT_TYPE_MAP[argument_type]
            argument = argument_class(argument_value)
            arguments.append(argument)

        instruction = instruction_class(arguments)
        instruction.execute()


if __name__ == '__main__':
    main()
