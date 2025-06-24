import subprocess
import os

running_processes = {}

def start_script(script_path):
    ext = os.path.splitext(script_path)[1]
    if ext == '.sh':
        proc = subprocess.Popen(['bash', script_path])
    elif ext == '.py':
        proc = subprocess.Popen(['python3', script_path])
    else:
        return None
    running_processes[os.path.basename(script_path)] = proc
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
