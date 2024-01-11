from telnetlib import Telnet


def execute_snort_command(command):
    """
    Execute a Snort command in an interactive shell via Telnet.

    :param command: The command to be executed.
    :return: The response from the Telnet server.
    """
    try:
        with Telnet('127.0.0.1', 12345) as tn:

            tn.read_until(b'\n')

            tn.write(command.encode('ascii') + b'\n')

            response = tn.read_until(b'o")~', timeout=30).decode('ascii')

            return response

    except Exception as e:
        return f"Error: {e}"
