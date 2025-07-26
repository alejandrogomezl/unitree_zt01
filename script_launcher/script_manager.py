import subprocess
import os
import json

running_process = None
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
STATE_FILE = os.path.join(os.path.dirname(__file__), "state.json")
os.makedirs(LOG_DIR, exist_ok=True)

def save_state(script_name, pid):
    with open(STATE_FILE, "w") as f:
        json.dump({"script": script_name, "pid": pid}, f)

def clear_state():
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return None

def start_script(script_path):
    global running_process
    if running_process:  # Si ya hay uno corriendo, no hacer nada
        return None

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

    running_process = proc
    save_state(script_name, proc.pid)
    return proc.pid

def stop_script():
    global running_process
    state = load_state()
    if running_process:
        running_process.terminate()
        running_process.wait()
        running_process = None
        clear_state()
        return True
    elif state:  # Si el proceso no está en memoria pero hay state
        try:
            os.kill(state["pid"], 9)
        except:
            pass
        clear_state()
        return True
    return False

def get_active_script():
    state = load_state()
    return state["script"] if state else None

def get_pid():
    state = load_state()
    return state["pid"] if state else None

def is_running():
    return bool(load_state())

def get_log(script_name):
    log_path = os.path.join(LOG_DIR, f"{script_name}.log")
    if os.path.exists(log_path):
        with open(log_path, "r") as f:
            return f.read()
    return "No log available yet."
