
"""Defines the abstract base protocol for slash-command handler registration and execution,
plus lightweight data classes representing commands and their options.
"""
from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from enum import Enum

class SlashOptionValueType(Enum):
    """
    e.g.
            1. single string :-  --name John this is very good
            (SO THE OPTIONS GOT THE ONE VALUE [John this is very good] AT ONCE)
            OUTPUT: CommandOption(name='name', type=<SlashOptionValueType.STRING: 'string'>, value=['John this is very good'], description=None, required=False, default=None)

            2. CHARACTER :- --tags a,b,c,d,e
            (SO THE OPTIONS GOT THE MULTIPLE VALUES ['a', 'b', 'c', 'd', 'e'] AT ONCE)
            OUTPUT: CommandOption(name='tags', type=<SlashOptionValueType.STRING: 'string'>, value=['a', 'b', 'c', 'd', 'e'], description=None, required=False, default=None)
    """
    STRING = "string"
    CHARACTER = "character"  # single character

@dataclass
class CommandOption:
    # for now there is no option in commands this for any future use/interface compatibility
    name: str
    type : SlashOptionValueType | None = SlashOptionValueType.CHARACTER
    value: list[Any] | None = None
    description: str | None = None
    required: bool = False
    default: Any | None = None

    def __post_init__(self):
        if self.type == SlashOptionValueType.STRING and self.value:
            # Join all parts into a single string for STRING type
            self.value = [' '.join(self.value)]
        elif self.type == SlashOptionValueType.CHARACTER and self.value:
            # Split the first value by commas for CHARACTER type
            self.value = [val.strip() for val in self.value[0].split(',') if val.strip()]


@dataclass
class SlashCommand:
    # command name (without the '/') e.g. "help"
    command: str
    options: list[CommandOption] | None
    requirements: list[Requirements] | None  # e.g. permissions or roles
    description: str | None
    handler: Callable[[SlashCommand, CommandOption | None], CommandResult] | None = None  # the function to execute the command

@dataclass
class CommandResult:
    # this could be changed to typed dict later for more structure
    success: bool
    message: str
    data: Any | None = None # this could be changed to typed dict later for more structure
    additional_warnings: list[str] | None = None # like handled errors but not critical
    error: dict[str, str] | None = None # error message if any # this could be changed to typed dict later for more structure

class Requirements:
    # for now there is no requirement in commands this for any future use/interface compatibility
    # this could have the data like user profile info settings permissions etc
    pass
