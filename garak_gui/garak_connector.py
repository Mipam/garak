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

    # The list command for generators is different, it's just the name
    prefix = f"{plugin_type}:"
    if plugin_type == "generators":
        prefix = ""

    for line in output.splitlines():
        line = ansi_escape.sub('', line).strip()

        if plugin_type != "generators" and not line.startswith(prefix):
            continue

        if plugin_type == "generators":
             # generators list is just the names, one per line, after a header
             if ":" in line or "garak" in line.lower() or not line:
                 continue
             plugin_name = line.strip()
        else:
            # Take the part after the prefix, split by space, take the first element
            plugin_name = line[len(prefix):].strip().split(" ")[0]

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
