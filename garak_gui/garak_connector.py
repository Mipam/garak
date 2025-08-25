import subprocess
import threading
import re

def _parse_plugin_list(output, plugin_type):
    """
    Parses the output of a `garak --list...` command.

    :param output: The stdout of the command as a string.
    :param plugin_type: The type of plugin (e.g., "probes").
    :return: A list of plugin names.
    """
    plugins = []
    # Regex to remove ANSI escape codes
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

    lines = output.strip().splitlines()
    if not lines:
        return []

    # The first line is a header like "probes:" or "generators:", we can skip it.
    for line in lines[1:]:
        line = ansi_escape.sub('', line).strip()
        if not line:
            continue

        # For all plugin types, the name is the first word on the line.
        plugin_name = line.split(" ")[0]

        if plugin_name:
            plugins.append(plugin_name)
    return plugins

def get_plugins(plugin_type):
    """
    Gets a list of available plugins of a given type.

    :param plugin_type: The type of plugin ("probes", "detectors", "buffs", "generators").
    :return: A list of plugin names.
    """
    try:
        # Note: garak's command is --list_probes, but for generators it's --list-generators
        # Let's check the cli.py again.
        # Oh, it's `list_generators`. The help text in the docs was wrong. Good thing I checked.
        command = ["python", "-m", "garak", f"--list_{plugin_type}"]
        output = subprocess.check_output(command, text=True)
        return _parse_plugin_list(output, plugin_type)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error getting {plugin_type}: {e}")
        return []

def run_garak_command(args, output_queue):
    """
    Runs a garak command and streams its output to a queue.

    :param args: A list of command-line arguments for garak.
    :param output_queue: A queue.Queue object to put output lines on.
    :return: The subprocess.Popen object.
    """
    command = ["python", "-m", "garak"] + args
    process = None
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )

        def enqueue_output():
            for line in iter(process.stdout.readline, ''):
                output_queue.put(line)
            process.stdout.close()
            process.wait()
            output_queue.put(None) # Sentinel value

        thread = threading.Thread(target=enqueue_output)
        thread.daemon = True
        thread.start()

    except FileNotFoundError:
        output_queue.put("Error: 'python' command not found. Make sure Python is in your PATH.\n")
        output_queue.put(None)
    except Exception as e:
        output_queue.put(f"An unexpected error occurred: {e}\n")
        output_queue.put(None)

    return process

def start_interactive_process(output_queue):
    """
    Starts a garak interactive session and streams its output to a queue.

    :param output_queue: A queue.Queue object to put output lines on.
    :return: The subprocess.Popen object.
    """
    command = ["python", "-m", "garak", "--interactive"]
    process = None
    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )

        def enqueue_output():
            for line in iter(process.stdout.readline, ''):
                output_queue.put(line)
            process.stdout.close()
            process.wait()
            output_queue.put(None) # Sentinel value

        thread = threading.Thread(target=enqueue_output)
        thread.daemon = True
        thread.start()

    except FileNotFoundError:
        output_queue.put("Error: 'python' command not found. Make sure Python is in your PATH.\n")
        output_queue.put(None)
    except Exception as e:
        output_queue.put(f"An unexpected error occurred: {e}\n")
        output_queue.put(None)

    return process
