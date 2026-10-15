from src.slash_commands.protocol import SlashCommand, CommandOption, SlashOptionValueType
class ParseCommand:
    """
        Validate and parse a user-provided slash command and prepare it for the running
        application. Performs syntax checks and normalizes inputs; can be used as a
        pre-runtime hook (similar to a pre-commit) to reject invalid commands early.
    """

    @classmethod
    def _validate_command(cls, command: str) -> bool:
        # Basic validation logic for command names
        if not command or not command.isidentifier():
            return False
        return True

    @classmethod
    def _get_argument_only(cls, input_str: str) -> str:
        """Extract arguments from a slash command string.
        e.g.
          --name John from the actual command [/greet --name John] returns "name"
          --tags 1,2,3 from the actual command [/read --files f1.txt,f2.txt,f3.txt] returns "files"
        :param input_str: The input string to parse, e.g. "/ greet--name John"
        :return: A of argument string.
        :raise ValueError: If the input string is not a valid slash command.
        """
        input_str = input_str.strip()  # Handle leading/trailing spaces
        parts = input_str.split('/')[1:]  # Skip the initial empty part before the first '/'
        if not parts:
            raise ValueError("No command found after '/'")
        command_part = parts[0].strip()
        if ' ' in command_part:
            command = command_part.split()[0]
        else:
            command = command_part
        if not cls._validate_command(command):
            raise ValueError(f"Invalid command name: '{command}'")
        return command



    @classmethod
    def _get_options_only(cls, input_str: str) -> tuple[str, list[str]] | None:
        """Extract options from a slash command string.
         e.g.
          --name John from the actual command [/greet --name John] returns "--name John"
          --tags 1,2,3 from the actual command [/read --files f1.txt,f2.txt,f3.txt] returns "--files f1.txt,f2.txt,f3.txt"

        :param input_str: The input string to parse "
        :return: A list of CommandOption objects.
        :raise ValueError: If the input string is not a valid slash command.
        """
        argument : str
        value : list[str]
        if not input_str.__contains__("--"):
            # when there is no option in the command
            return None
        parts = input_str.split('--')[1:]  # Skip the command part
        for part in parts:
            # because of options could be like --name John --tags 1,2,3
            sub_parts = part.strip().split()
            if len(sub_parts) >= 2:
                # option name is the first part, value is the rest
                argument = sub_parts[0]
                values = sub_parts[1:]
                return argument, values
            else:
                # that means the option is not followed by a value todo we could use default value here like True
                raise ValueError(f"Invalid option format: '{part.strip()}' after --")
        return None


    @classmethod
    def get_command(cls, input_str: str) -> SlashCommand:
        """Parse and validate a slash command string.

        :param input_str: The input string to parse, e.g. "/ greet--name John"
        :return: A SlashCommand object with parsed command and arguments.
        :raise ValueError: If the input string is not a valid slash command.
        """
        if not input_str.startswith("/"):
            raise ValueError("Command must start with '/'")

        argument = cls._get_argument_only(input_str)
        options_result = cls._get_options_only(input_str)
        
        if options_result is None:
            # No options provided
            options = []
        else:
            name, values = options_result
            options = [CommandOption(name=name, value=values, type=SlashOptionValueType.STRING if len(values) > 1 else SlashOptionValueType.CHARACTER)]
            
        return SlashCommand(command=argument, options=options, requirements=None, description=None, handler=None)

if __name__ == '__main__':
    cmd = ParseCommand.get_command('/agent --high tell me a joke')
    print(cmd)