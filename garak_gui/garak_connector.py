import subprocess
import threading
import re
import queue

def _parse_plugin_list(output, plugin_type):
    """
    Parses the output of a `garak --list...` command.
    :param output: The stdout of the command as a string.
    :param plugin_type: The type of plugin (e.g., "probes").
    :return: A list of plugin names.
    """
    plugins = []
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    lines = output.splitlines()

    in_section = False
    header = f"{plugin_type}:"

    for line in lines:
        cleaned_line = ansi_escape.sub('', line)
        stripped_line = cleaned_line.strip()

        if stripped_line == header:
            in_section = True
            continue

        if in_section:
            # If we hit a new, unindented section, stop
            if not cleaned_line.startswith('  ') and stripped_line.endswith(':'):
                break
            # For generators, the format is just the name
            if plugin_type == "generators":
                if stripped_line:
                    plugins.append(stripped_line.split(" ")[0])
            # For other types, it's "plugin.name:"
            elif stripped_line.endswith(':'):
                plugin_name = stripped_line.rstrip(':')
                if plugin_name:
                    plugins.append(plugin_name)
    return plugins

def get_plugins(plugin_type):
    """
    Gets a list of available plugins of a given type.

    :param plugin_type: The type of plugin ("probes", "detectors", "buffs", "generators").
    :return: A tuple containing a list of plugin names and an error message (or None).
    """
    try:
        command = ["python", "-m", "garak", f"--list_{plugin_type}"]
        output = subprocess.check_output(command, text=True, stderr=subprocess.STDOUT)
        return _parse_plugin_list(output, plugin_type), None
    except FileNotFoundError:
        return [], "Error: 'python -m garak' not found. Is garak installed in this environment?"
    except subprocess.CalledProcessError as e:
        return [], f"Error getting {plugin_type}:\n{e.output}"

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
        return None
    except Exception as e:
        output_queue.put(f"An unexpected error occurred: {e}\n")
        output_queue.put(None)
        return None

    return process

def run_interactive_garak(output_queue, input_queue):
    """
    Runs garak in interactive mode and handles two-way communication.

    :param output_queue: A queue.Queue object to put output lines on.
    :param input_queue: A queue.Queue object to get input lines from.
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
            output_queue.put(None)

        def dequeue_input():
            while process.poll() is None:
                try:
                    line = input_queue.get(timeout=0.1)
                    if line is None: # Sentinel
                        process.stdin.close()
                        break
                    process.stdin.write(line + "\n")
                    process.stdin.flush()
                except queue.Empty:
                    continue
            if process.stdin:
                try:
                    process.stdin.close()
                except Exception:
                    pass

        output_thread = threading.Thread(target=enqueue_output)
        output_thread.daemon = True
        output_thread.start()

        input_thread = threading.Thread(target=dequeue_input)
        input_thread.daemon = True
        input_thread.start()


    except FileNotFoundError:
        output_queue.put("Error: 'python' command not found. Make sure Python is in your PATH.\n")
        output_queue.put(None)
        return None
    except Exception as e:
        output_queue.put(f"An unexpected error occurred: {e}\n")
        output_queue.put(None)
        return None

    return process
