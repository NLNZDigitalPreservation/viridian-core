import os
import re
from argparse import ArgumentParser


def str2bool(value):
    true_values = {"true", "1", "yes", "y", "t", "on"}
    false_values = {"false", "0", "no", "n", "f", "off"}

    value = value.strip().lower()
    if value in true_values:
        return True
    elif value in false_values:
        return False
    else:
        raise ValueError(f"Invalid truth value: {value}")


class Parser(ArgumentParser):
    """An easy way to make flags also configurable from env variables"""

    def add_env_argument(self, *args, **kwargs):
        if len(args) != 1:
            raise ValueError("Provide exactly one flag name")

        flag_name = args[0]

        # Prioritize environment variables over the normal default
        environment_default = os.environ.get(_to_env_var_name(flag_name), None)
        if environment_default is not None:
            # If a type is specified such as 'int' or 'float' or 'str', convert
            # the environment variable using the callback
            type_callback = kwargs.get("type", None)
            if type_callback:
                environment_default = type_callback(environment_default)

            kwargs["default"] = environment_default

        # Mark the flag as not required if it's supplied as an env variable
        no_env_variable_set = _to_env_var_name(flag_name) not in os.environ
        marked_required = kwargs.get("required", False)
        kwargs["required"] = marked_required and no_env_variable_set

        super().add_argument(flag_name, **kwargs)

    def add_log_level(self):
        self.add_env_argument(
            "--log-level",
            default="INFO",
            help="The log level of logging",
        )
        self.add_env_argument(
            "--log-file",
            default="/data/viridian/persistent/fixity/logs/fixity-master.log",
            help="The file to write logs to (defaults to stdout if not set)",
        )

    @staticmethod
    def parse_duration(duration: str) -> int:
        """Parses a duration string in the format XdXhXm to seconds."""

        # Convert the journal max age to seconds
        match = re.match(r"^(\d+)d(\d+)h(\d+)m$", duration)
        if match is None:
            raise ValueError(
                "Invalid duration format, must be in the format XdXhXm. "
                f"Instead, {duration} was given."
            )
        duration_seconds = int(match[1]) * 86400  # Convert days to seconds
        duration_seconds += int(match[2]) * 3600  # Convert hours to seconds
        duration_seconds += int(match[3]) * 60  # Convert minutes to seconds

        return duration_seconds

    @staticmethod
    def str_to_bool(string: str) -> bool:
        return str2bool(string)


def _to_env_var_name(flag_name: str) -> str:
    """Converts a flag to an idiomatic environment variable name"""
    return flag_name.replace("--", "").replace("-", "_").upper()
