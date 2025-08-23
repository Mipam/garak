import subprocess
import threading

def run_garak_command(args, output_queue):
    """
    Runs a garak command in a separate thread and puts the output on a queue.

    :param args: A list of command-line arguments for garak.
    :param output_queue: A queue.Queue object to put output lines on.
    """
    command = ["python", "-m", "garak"] + args
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )

        for line in iter(process.stdout.readline, ''):
            output_queue.put(line)

        process.stdout.close()
        process.wait()

    except FileNotFoundError:
        output_queue.put("Error: 'python' command not found. Make sure Python is in your PATH.\n")
    except Exception as e:
        output_queue.put(f"An unexpected error occurred: {e}\n")
    finally:
        output_queue.put(None) # Sentinel value to indicate completion
