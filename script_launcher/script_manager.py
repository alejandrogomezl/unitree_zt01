import subprocess
import os

running_processes = {}
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

def start_script(script_path):
    ext = os.path.splitext(script_path)[1]
    script_name = os.path.basename(script_path)

    log_path = os.path.join(LOG_DIR, f"{script_name}.log")
    log_file = open(log_path, "w")

    if ext == '.sh':
        proc = subprocess.Popen(['bash', script_path], stdout=log_file, stderr=subprocess.STDOUT)
    elif ext == '.py':
        proc = subprocess.Popen(['python3', script_path], stdout=log_file, stderr=subprocess.STDOUT)
    else:
        return None

    running_processes[script_name] = proc
    return proc.pid

def stop_script(script_name):
    proc = running_processes.get(script_name)
    if proc:
        proc.terminate()
        proc.wait()
        del running_processes[script_name]
        return True
    return False

def is_running(script_name):
    proc = running_processes.get(script_name)
    return proc and proc.poll() is None

def get_pid(script_name):
    proc = running_processes.get(script_name)
    return proc.pid if proc else None

def get_log(script_name):
    log_path = os.path.join(LOG_DIR, f"{script_name}.log")
    if os.path.exists(log_path):
        with open(log_path, "r") as f:
            return f.read()
    return "No log available yet."
