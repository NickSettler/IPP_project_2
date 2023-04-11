from __future__ import annotations
import sys
import re
import argparse
from typing import List, Dict
from xml.etree import ElementTree
from abc import abstractmethod, ABC

# Interpreter error codes
INVALID_XML_ERROR_CODE = 31
WRONG_XML_STRUCTURE_ERROR_CODE = 32
SEMANTIC_ERROR_CODE = 52
WRONG_OPERAND_TYPE_ERROR_CODE = 53
UNDEFINED_VARIABLE_ERROR_CODE = 54
NON_EXISTING_FRAME_ERROR_CODE = 55
MISSING_VALUE_ERROR_CODE = 56
WRONG_OPERAND_VALUE_ERROR_CODE = 57
STRING_OPERATION_ERROR_CODE = 58

# Value check flags
VALUE_TYPE_INT_CHECK = 0x1
VALUE_TYPE_BOOL_CHECK = 0x2
VALUE_TYPE_STRING_CHECK = 0x4
VALUE_TYPE_NIL_CHECK = 0x8
VALUE_TYPE_NOT_NIL_CHECK = 0x10
VALUE_TYPE_SAME_CHECK = 0x20

# Variable check flags
VARIABLE_DEFINED_CHECK = 0x1
VARIABLE_NULL_CHECK = 0x2
VARIABLE_CORRECT_FRAME_CHECK = 0x4


class Helpers:
    """
    Helper class for static methods
    """

    @staticmethod
    def replace_special_chars(input_str):
        """
        Replace special characters in format \\ddd with their ASCII representation
        :param input_str: Input string
        :return: String with replaced characters
        """
        pattern = r"\\(\d{3})"

        def replace(match):
            return chr(int(match.group(1)))

        return re.sub(pattern, replace, input_str)

    @staticmethod
    def process_output(arg) -> str:
        """
        Process output for WRITE instruction
        :param arg: Argument to process
        :return: Processed argument
        """
        if type(arg) is bool:
            return "true" if arg else "false"
        elif type(arg) is None:
            return ""
        elif type(arg) is str:
            return Helpers.replace_special_chars(arg)
        else:
            return str(arg)

    @staticmethod
    def variable_args_check(args: List[Argument],
                            check1=VARIABLE_CORRECT_FRAME_CHECK,
                            check2=VARIABLE_NULL_CHECK | VARIABLE_CORRECT_FRAME_CHECK,
                            check3=VARIABLE_NULL_CHECK | VARIABLE_CORRECT_FRAME_CHECK) -> bool:
        """
        Check if variable arguments are valid
        :param args: List of arguments
        :param check1: Check for first argument
        :param check2: Check for second argument
        :param check3: Check for third argument
        :return: True if arguments are valid
        """
        if type(args[0]) is VariableArgument:
            variable_check(args[0], check1)

        if len(args) > 1 and type(args[1]) is VariableArgument:
            variable_check(args[1], check2)

        if len(args) > 2 and type(args[2]) is VariableArgument:
            variable_check(args[2], check3)

        return True

    @staticmethod
    def math_args_check(args: List[Argument]) -> bool:
        """
        Check if arguments for math instructions are valid
        :param args: List of arguments
        :return: True if arguments are valid
        """
        Helpers.variable_args_check(args)

        value1 = args[1].get_value()
        value2 = args[2].get_value()

        check = VALUE_TYPE_INT_CHECK | VALUE_TYPE_NOT_NIL_CHECK
        value_check(value1, check)
        value_check(value2, check)

        return True

    @staticmethod
    def relational_args_check(args: List[Argument]) -> bool:
        """
        Check if arguments for relational instructions are valid
        :param args: List of arguments
        :return: True if arguments are valid
        """
        Helpers.variable_args_check(args)

        value1 = args[1].get_value()
        value2 = args[2].get_value()

        check = VALUE_TYPE_NIL_CHECK | VALUE_TYPE_SAME_CHECK

        values_check(value1, value2, check)

        return True

    @staticmethod
    def logical_args_check(args: List[Argument], is_not=False) -> bool:
        """
        Check if arguments for logical instructions are valid
        :param args: List of arguments
        :param is_not: True if instruction is NOT
        :return: True if arguments are valid
        """
        Helpers.variable_args_check(args)

        value1 = args[1].get_value()

        check = VALUE_TYPE_BOOL_CHECK | VALUE_TYPE_NOT_NIL_CHECK
        value_check(value1, check)

        if not is_not:
            value2 = args[2].get_value()
            value_check(value2, check)

        return True


# Arguments section
# -----------------
# Arguments are used to pass data to instructions
# Each argument has a type and a value
# Variable argument has a frame and a name
# Label argument has an order
# Argument is an abstract class and its subclasses are used to represent different types of arguments

class Argument(ABC):
    value: str
    name: str
    frame: str

    def __init__(self, value: str | None, frame: str = "", name: str = ""):
        self.value = value
        self.frame = frame
        self.name = name

    def get_type(self):
        return self.__class__.__name__

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
    def __init__(self, value: str):
        super().__init__(value)
        self.order = None

    def get_value(self) -> str:
        return self.value

    def get_order(self) -> int:
        return self.order


class TypeArgument(Argument):
    def get_value(self) -> str:
        return self.value


class VariableArgument(Argument):
    def __init__(self, value: str):
        frame, name = value.split("@", 1)
        super().__init__(None, frame, name)

    def get_value(self) -> str:
        memory = Memory().get_frame(self.frame)

        if memory is None:
            sys.stderr.write("Error: Non-existing frame\n")
            sys.exit(NON_EXISTING_FRAME_ERROR_CODE)

        if self.name not in memory:
            sys.stderr.write("Error: Variable not defined\n")
            sys.exit(UNDEFINED_VARIABLE_ERROR_CODE)
        else:
            return memory[self.name] if memory[self.name] is not None else ""


def value_check(value: any, check: int) -> bool:
    """
    Check if value is valid according to check flags
    :param value: Value to check
    :param check: Check flags
    :return: True if value is valid
    """
    if check & VALUE_TYPE_INT_CHECK:
        if type(value) is not int:
            sys.stderr.write("Error: Invalid operand type\n")
            sys.exit(WRONG_OPERAND_TYPE_ERROR_CODE)
    if check & VALUE_TYPE_BOOL_CHECK:
        if type(value) is not bool:
            sys.stderr.write("Error: Invalid operand type\n")
            sys.exit(WRONG_OPERAND_TYPE_ERROR_CODE)
    if check & VALUE_TYPE_STRING_CHECK:
        if type(value) is not str:
            sys.stderr.write("Error: Invalid operand type\n")
            sys.exit(WRONG_OPERAND_TYPE_ERROR_CODE)
    if check & VALUE_TYPE_NIL_CHECK:
        if value is None:
            sys.stderr.write("Error: Invalid operand type\n")
            sys.exit(WRONG_OPERAND_TYPE_ERROR_CODE)

    if check & VALUE_TYPE_NOT_NIL_CHECK:
        if value is None:
            sys.stderr.write("Error: Missing operand value\n")
            sys.exit(MISSING_VALUE_ERROR_CODE)

    return True


def values_check(value1, value2, check: int) -> bool:
    """
    Makes checks on two values
    :param value1: first value to check
    :param value2: second value to check
    :param check: check flags
    :return: True if values are valid according to check flags else False
    """
    if check & VALUE_TYPE_SAME_CHECK:
        if type(value1) is not type(value2):
            sys.stderr.write("Error: Invalid operand type\n")
            sys.exit(WRONG_OPERAND_TYPE_ERROR_CODE)

    return value_check(value1, check) and value_check(value2, check)


def variable_check(variable: VariableArgument, check: int) -> bool:
    """
    Makes checks on variable
    :param variable: variable to check
    :param check: check flags
    :return: True if variable is valid according to check flags else False
    """
    if check & VARIABLE_DEFINED_CHECK:
        memory = Memory().get_frame(variable.frame)

        if variable.name not in memory:
            sys.stderr.write("Error: Variable not defined\n")
            sys.exit(UNDEFINED_VARIABLE_ERROR_CODE)

    if check & VARIABLE_NULL_CHECK:
        if variable.get_value() == '':
            sys.stderr.write("Error: Missing operand value\n")
            sys.exit(MISSING_VALUE_ERROR_CODE)

    if check & VARIABLE_CORRECT_FRAME_CHECK:
        if Memory().get_frame(variable.get_frame()) is None:
            sys.stderr.write("Error: Invalid frame\n")
            sys.exit(NON_EXISTING_FRAME_ERROR_CODE)

    return True


# Instructions section
# --------------------
# Each instruction is a class that inherits from Instruction class
# and implements execute method (Command pattern)
# Each instruction has a list of arguments that are passed to it
# during initialization
# Instructions are mapped to their names in INSTRUCTIONS_MAP dictionary

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
        Helpers.variable_args_check(self.arguments)

        variable = self.arguments[0]
        value = self.arguments[1].get_value()

        Memory().update_variable(variable.get_frame(), variable.get_name(), value)


class CreateFrameInstruction(Instruction):
    def execute(self):
        Memory().set_temporary_frame({})


class PushFrameInstruction(Instruction):
    def execute(self):
        if Memory().get_temporary_frame() is None:
            sys.stderr.write("Error: Non-existing frame\n")
            sys.exit(NON_EXISTING_FRAME_ERROR_CODE)

        Memory().push_frame_stack(Memory().get_temporary_frame())
        Memory().set_temporary_frame(None)


class PopFrameInstruction(Instruction):
    def execute(self):
        if Memory().get_frame_stack_size() == 0:
            sys.stderr.write("Error: Empty frame stack\n")
            sys.exit(NON_EXISTING_FRAME_ERROR_CODE)

        Memory().set_temporary_frame(Memory().pop_frame_stack())


class DefVarInstruction(Instruction):
    def execute(self):
        Helpers.variable_args_check(self.arguments)

        variable = self.arguments[0]
        Memory().create_variable(variable.get_frame(), variable.get_name())


class CallInstruction(Instruction):
    def execute(self):
        label = self.arguments[0].get_value()

        order = Memory().get_label(label)
        if order is None:
            sys.stderr.write("Error: Non-existing label\n")
            sys.exit(SEMANTIC_ERROR_CODE)

        Memory().push_call_stack(Memory().get_program_counter())
        Memory().set_program_counter(order)


class ReturnInstruction(Instruction):
    def execute(self):
        if Memory().get_call_stack_size() == 0:
            sys.stderr.write("Error: Empty call stack\n")
            sys.exit(MISSING_VALUE_ERROR_CODE)

        prev_order = Memory().pop_call_stack()

        Memory().set_program_counter(prev_order)


class PushSInstruction(Instruction):
    def execute(self):
        Helpers.variable_args_check(self.arguments, VARIABLE_CORRECT_FRAME_CHECK | VARIABLE_NULL_CHECK)

        value = self.arguments[0].get_value()
        Memory().get_stack().append(value)


class PopSInstruction(Instruction):
    def execute(self):
        Helpers.variable_args_check(self.arguments)

        variable = self.arguments[0]

        stack = Memory().get_stack()

        if len(stack) == 0:
            sys.stderr.write("Error: Empty stack\n")
            sys.exit(MISSING_VALUE_ERROR_CODE)

        value = stack.pop()
        Memory().update_variable(variable.get_frame(), variable.get_name(), value)


class AddInstruction(Instruction):
    def execute(self):
        Helpers.math_args_check(self.arguments)

        variable = self.arguments[0]
        value1 = self.arguments[1].get_value()
        value2 = self.arguments[2].get_value()

        Memory().update_variable(variable.get_frame(), variable.get_name(), value1 + value2)


class SubInstruction(Instruction):
    def execute(self):
        Helpers.math_args_check(self.arguments)

        variable = self.arguments[0]
        value1 = self.arguments[1].get_value()
        value2 = self.arguments[2].get_value()

        Memory().update_variable(variable.get_frame(), variable.get_name(), value1 - value2)


class MulInstruction(Instruction):
    def execute(self):
        Helpers.math_args_check(self.arguments)

        variable = self.arguments[0]
        value1 = self.arguments[1].get_value()
        value2 = self.arguments[2].get_value()

        Memory().update_variable(variable.get_frame(), variable.get_name(), value1 * value2)


class IDivInstruction(Instruction):
    def execute(self):
        Helpers.math_args_check(self.arguments)

        variable = self.arguments[0]
        value1 = self.arguments[1].get_value()
        value2 = self.arguments[2].get_value()

        try:
            Memory().update_variable(variable.get_frame(), variable.get_name(), value1 // value2)
        except ZeroDivisionError:
            sys.stderr.write("Error: Division by zero\n")
            sys.exit(WRONG_OPERAND_VALUE_ERROR_CODE)


class LTInstruction(Instruction):
    def execute(self):
        Helpers.relational_args_check(self.arguments)

        variable = self.arguments[0]
        value1 = self.arguments[1].get_value()
        value2 = self.arguments[2].get_value()

        Memory().update_variable(variable.get_frame(), variable.get_name(), value1 < value2)


class GTInstruction(Instruction):
    def execute(self):
        Helpers.relational_args_check(self.arguments)

        variable = self.arguments[0]
        value1 = self.arguments[1].get_value()
        value2 = self.arguments[2].get_value()

        Memory().update_variable(variable.get_frame(), variable.get_name(), value1 > value2)


class EQInstruction(Instruction):
    def execute(self):
        Helpers.relational_args_check(self.arguments)

        variable = self.arguments[0]
        value1 = self.arguments[1].get_value()
        value2 = self.arguments[2].get_value()

        Memory().update_variable(variable.get_frame(), variable.get_name(), value1 == value2)


class AndInstruction(Instruction):
    def execute(self):
        Helpers.logical_args_check(self.arguments)

        variable = self.arguments[0]
        value1 = self.arguments[1].get_value()
        value2 = self.arguments[2].get_value()

        Memory().update_variable(variable.get_frame(), variable.get_name(), value1 and value2)


class OrInstruction(Instruction):
    def execute(self):
        Helpers.logical_args_check(self.arguments)

        variable = self.arguments[0]
        value1 = self.arguments[1].get_value()
        value2 = self.arguments[2].get_value()

        Memory().update_variable(variable.get_frame(), variable.get_name(), value1 or value2)


class NotInstruction(Instruction):
    def execute(self):
        Helpers.logical_args_check(self.arguments, True)

        variable = self.arguments[0]
        value = self.arguments[1].get_value()

        Memory().update_variable(variable.get_frame(), variable.get_name(), not value)


class Int2CharInstruction(Instruction):
    def execute(self):
        Helpers.variable_args_check(self.arguments)

        variable = self.arguments[0]
        value = self.arguments[1].get_value()

        try:
            new_value = chr(value)
            Memory().update_variable(variable.get_frame(), variable.get_name(), new_value)
        except ValueError:
            sys.stderr.write("ValueError: chr() arg not in range(0x110000)")
            sys.exit(STRING_OPERATION_ERROR_CODE)
        except TypeError:
            sys.stderr.write("TypeError: an integer is required")
            sys.exit(WRONG_OPERAND_TYPE_ERROR_CODE)


class Stri2IntInstruction(Instruction):
    def execute(self):
        Helpers.variable_args_check(self.arguments)

        variable = self.arguments[0]
        string = self.arguments[1].get_value()
        index = self.arguments[2].get_value()

        value_check(string, VALUE_TYPE_STRING_CHECK)
        value_check(index, VALUE_TYPE_INT_CHECK)

        if index >= len(string) or index < 0:
            sys.stderr.write("Error: Index out of range\n")
            sys.exit(STRING_OPERATION_ERROR_CODE)

        Memory().update_variable(variable.get_frame(), variable.get_name(), ord(string[index]))


class ReadInstruction(Instruction):
    def execute(self):
        Helpers.variable_args_check(self.arguments)

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
            print(Helpers.process_output(argument.get_value()), end="")


class ConcatInstruction(Instruction):
    def execute(self):
        Helpers.variable_args_check(self.arguments)

        variable = self.arguments[0]
        string1 = self.arguments[1].get_value()
        string2 = self.arguments[2].get_value()

        check = VALUE_TYPE_STRING_CHECK
        values_check(string1, string2, check)

        Memory().update_variable(variable.get_frame(), variable.get_name(), string1 + string2)


class StrLenInstruction(Instruction):
    def execute(self):
        Helpers.variable_args_check(self.arguments)

        variable = self.arguments[0]
        string = self.arguments[1].get_value()

        if type(string) is not str:
            sys.stderr.write("Argument is not a string")
            sys.exit(WRONG_OPERAND_TYPE_ERROR_CODE)

        Memory().update_variable(variable.get_frame(), variable.get_name(), len(string))


class GetCharInstruction(Instruction):
    def execute(self):
        Helpers.variable_args_check(self.arguments)

        variable = self.arguments[0]
        string = self.arguments[1].get_value()
        index = self.arguments[2].get_value()

        value_check(string, VALUE_TYPE_STRING_CHECK)
        value_check(index, VALUE_TYPE_INT_CHECK)
        values_check(string, index, VALUE_TYPE_NIL_CHECK)

        if index < 0 or index >= len(string):
            sys.stderr.write("IndexError: string index out of range")
            sys.exit(STRING_OPERATION_ERROR_CODE)

        Memory().update_variable(variable.get_frame(), variable.get_name(), string[index])


class SetCharInstruction(Instruction):
    def execute(self):
        Helpers.variable_args_check(self.arguments)

        variable = self.arguments[0]
        index = self.arguments[1].get_value()
        replace_string = self.arguments[2].get_value()

        if variable.get_value() == '':
            sys.stderr.write("Empty value")
            sys.exit(WRONG_OPERAND_TYPE_ERROR_CODE)

        if type(variable.get_value()) != str or type(index) != int or type(replace_string) != str:
            sys.stderr.write("Wrong type of operand")
            sys.exit(WRONG_OPERAND_TYPE_ERROR_CODE)

        if index < 0 or index >= len(variable.get_value()):
            sys.stderr.write("IndexError: string index out of range")
            sys.exit(STRING_OPERATION_ERROR_CODE)

        if len(replace_string) < 1:
            sys.stderr.write("ValueError: string length must be 1")
            sys.exit(STRING_OPERATION_ERROR_CODE)

        string = variable.get_value()

        string = string[:index] + replace_string[0] + string[index + 1:]
        Memory().update_variable(variable.get_frame(), variable.get_name(), string)


class TypeInstruction(Instruction):
    def execute(self):
        Helpers.variable_args_check(self.arguments)

        variable = self.arguments[0]
        value = self.arguments[1].get_value()

        type_str = type(value).__name__
        if type_str == "bool":
            type_str = "bool"
        elif type_str == "int":
            type_str = "int"
        elif type_str == "str":
            type_str = "string"
        elif type_str == "NoneType":
            type_str = "nil"

        Memory().update_variable(variable.get_frame(), variable.get_name(), type_str)


class LabelInstruction(Instruction):
    def execute(self):
        name = self.arguments[0].get_value()

        Memory().create_label(name, Memory().get_program_counter())


class JumpInstruction(Instruction):
    def execute(self):
        Helpers.variable_args_check(self.arguments)

        label = self.arguments[0].get_value()
        Memory().set_program_counter(Memory().get_label(label))


class JumpIfEqInstruction(Instruction):
    def execute(self):
        Helpers.variable_args_check(self.arguments)

        label = self.arguments[0].get_value()
        value1 = self.arguments[1].get_value()
        value2 = self.arguments[2].get_value()

        values_check(value1, value2, VALUE_TYPE_SAME_CHECK)

        if value1 == value2:
            Memory().set_program_counter(Memory().get_label(label))


class JumpIfNeqInstruction(Instruction):
    def execute(self):
        Helpers.variable_args_check(self.arguments)

        label = self.arguments[0].get_value()
        value1 = self.arguments[1].get_value()
        value2 = self.arguments[2].get_value()

        values_check(value1, value2, VALUE_TYPE_SAME_CHECK)

        if value1 != value2:
            Memory().set_program_counter(Memory().get_label(label))


class ExitInstruction(Instruction):
    def execute(self):
        Helpers.variable_args_check(self.arguments, VARIABLE_CORRECT_FRAME_CHECK | VARIABLE_NULL_CHECK)

        code = self.arguments[0].get_value()

        value_check(code, VALUE_TYPE_INT_CHECK)

        if code < 0 or code > 49:
            sys.stderr.write("Exit code must be in range <0,49>")
            sys.exit(WRONG_OPERAND_VALUE_ERROR_CODE)

        exit(code)


class DPrintInstruction(Instruction):
    def execute(self):
        Helpers.variable_args_check(self.arguments)

        print(self.arguments[0].get_value(), file=sys.stderr, end="")


class BreakInstruction(Instruction):
    def execute(self):
        # TODO: implement
        pass


# Memory section
# --------------
# Memory is singleton. It is implemented by metaclass MemoryMeta
# which ensures that only one instance of Memory is created
# Memory is used for storing variables, frames, labels and program counter

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
        self._stack = []
        self._call_stack = []
        self._frame_stack = []
        self._global_frame = {}
        self._local_frame = None
        self._temporary_frame = None
        self._program_counter = 0
        self._labels = {}

    def increment_program_counter(self):
        self._program_counter += 1

    def decrement_program_counter(self):
        self._program_counter -= 1

    def set_program_counter(self, value):
        self._program_counter = value

    def get_program_counter(self):
        return self._program_counter

    def get_global_frame(self) -> Dict:
        return self._global_frame

    def set_local_frame(self, frame: Dict):
        self._local_frame = frame

    def get_local_frame(self) -> Dict:
        return self._local_frame

    def set_temporary_frame(self, frame: Dict):
        self._temporary_frame = frame

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
            sys.stderr.write("Variable already defined")
            sys.exit(SEMANTIC_ERROR_CODE)

        frame[variable_name] = None

    def read_variable(self, frame_name: str, variable_name: str) -> VariableArgument:
        frame = self.get_frame(frame_name)

        if variable_name not in frame:
            sys.stderr.write("Variable not defined")
            sys.exit(UNDEFINED_VARIABLE_ERROR_CODE)

        return frame[variable_name]

    def update_variable(self, frame_name: str, variable_name: str, value) -> None:
        frame = self.get_frame(frame_name)

        if variable_name not in frame:
            sys.stderr.write("Variable not defined")
            sys.exit(UNDEFINED_VARIABLE_ERROR_CODE)

        frame[variable_name] = value

    def create_label(self, label_name: str, label_order: int) -> None:
        if label_name in self._labels:
            sys.stderr.write("Label already defined")
            sys.exit(SEMANTIC_ERROR_CODE)

        self._labels[label_name] = label_order

    def get_label(self, label_name: str) -> int:
        if label_name not in self._labels:
            sys.stderr.write("Label not defined")
            sys.exit(SEMANTIC_ERROR_CODE)

        return self._labels[label_name]

    def reset(self):
        self._global_frame = {}
        self._local_frame = {}
        self._temporary_frame = {}
        self._stack = []
        self._program_counter = 0
        self._labels = {}
        self._call_stack = []

    def push_call_stack(self, value):
        self._call_stack.append(value)

    def pop_call_stack(self):
        return self._call_stack.pop()

    def push_frame_stack(self, value):
        self._frame_stack.append(value)
        self._local_frame = self._frame_stack[-1]

    def get_call_stack_size(self):
        return len(self._call_stack)

    def pop_frame_stack(self):
        value = self._frame_stack.pop()

        if len(self._frame_stack) == 0:
            self._local_frame = None
        else:
            self._local_frame = self._frame_stack[-1]

        return value

    def get_frame_stack_size(self):
        return len(self._frame_stack)


# Dictionary to map instruction name to instruction class
INSTRUCTION_MAP = {
    "MOVE": MoveInstruction,
    "CREATEFRAME": CreateFrameInstruction,
    "PUSHFRAME": PushFrameInstruction,
    "POPFRAME": PopFrameInstruction,
    "DEFVAR": DefVarInstruction,
    "CALL": CallInstruction,
    "RETURN": ReturnInstruction,
    "PUSHS": PushSInstruction,
    "POPS": PopSInstruction,
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

# Dictionary to map argument type to argument class
ARGUMENT_TYPE_MAP = {
    "int": IntegerArgument,
    "bool": BooleanArgument,
    "string": StringArgument,
    "nil": NilArgument,
    "label": LabelArgument,
    "type": TypeArgument,
    "var": VariableArgument,
}


def checkXML(root: ElementTree):
    """
    Checks if XML is valid
    :param root:
    :return:
    """
    children = root.findall("./*")

    try:
        order_counter = int(children[0].get("order"))
    except:
        sys.stderr.write("Missing order attribute")
        sys.exit(WRONG_XML_STRUCTURE_ERROR_CODE)

    for child in children:
        if child.tag != "instruction":
            sys.stderr.write("Unknown tag ({})".format(child.tag))
            sys.exit(WRONG_XML_STRUCTURE_ERROR_CODE)

        try:
            order = int(child.get("order"))
        except:
            sys.stderr.write("Wrong order")
            sys.exit(WRONG_XML_STRUCTURE_ERROR_CODE)

        if order < 0 or order > len(children) or order < order_counter:
            sys.stderr.write("Wrong order")
            sys.exit(WRONG_XML_STRUCTURE_ERROR_CODE)

        order_counter = order


def processXML(root: ElementTree):
    """
    Processes XML file and executes instructions
    :param root: root of XML file
    :return: None
    """
    children = root.findall("./*")

    pc = Memory().get_program_counter()

    while pc < len(children):
        instruction_tag = children[pc]

        Memory().increment_program_counter()

        if instruction_tag.tag != "instruction":
            raise Exception("Unknown tag ({})".format(instruction_tag.tag))

        opcode = instruction_tag.get("opcode")

        if opcode not in INSTRUCTION_MAP.keys():
            raise Exception("Unknown opcode ({})".format(opcode))

        instruction_class = INSTRUCTION_MAP[opcode]

        arguments = []
        for argument_tag in instruction_tag.findall("./*"):
            if not argument_tag.tag.startswith("arg"):
                raise Exception("Unknown tag ({})".format(argument_tag.tag))

            argument_type = argument_tag.get("type")

            if argument_type not in ARGUMENT_TYPE_MAP.keys():
                raise Exception("Unknown argument type ({})".format(argument_type))

            argument_value = argument_tag.text if argument_tag.text else ""
            argument_class = ARGUMENT_TYPE_MAP[argument_type]
            argument = argument_class(argument_value)
            arguments.append(argument)

        instruction = instruction_class(arguments)
        instruction.execute()
        pc = Memory().get_program_counter()


SOURCE_FILE = False
INPUT_FILE = False


def process_args():
    """
    Processes interpreter arguments
    :return: None
    """
    parser = argparse.ArgumentParser(
        prog='interpret.py',
        description='IPPCode23 interpreter',
        epilog='Author: Nikita Moiseev (xmoise01)',
    )

    parser.add_argument('-s', '--source', help='Source file', required=False)
    parser.add_argument('-i', '--input', help='Input file', required=False)

    args = parser.parse_args()

    global SOURCE_FILE
    global INPUT_FILE

    SOURCE_FILE = args.source
    INPUT_FILE = args.input


def main():
    process_args()

    source_str = ""

    try:
        if SOURCE_FILE is not None:
            with open(SOURCE_FILE, "r") as source_file:
                source_str = source_file.read()
        else:
            for line in sys.stdin:
                source_str += line
    except FileNotFoundError:
        print("Source file not found")
        sys.exit(1)

    try:
        if INPUT_FILE:
            sys.stdin = open(INPUT_FILE, "r")
    except FileNotFoundError:
        print("Input file not found")
        sys.exit(1)

    try:
        root = ElementTree.fromstring(source_str)
    except ElementTree.ParseError:
        sys.stderr.write("Invalid XML")
        sys.exit(INVALID_XML_ERROR_CODE)

    checkXML(root)
    processXML(root)


if __name__ == '__main__':
    main()
