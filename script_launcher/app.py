from flask import Flask, render_template, redirect, url_for
import os
from script_manager import (
    start_script, stop_script, is_running, get_pid, get_log,
    get_current_script
)

SCRIPT_DIR = os.path.join(os.path.dirname(__file__), 'scripts')
app = Flask(__name__)

@app.route('/')
def index():
    scripts = [f for f in os.listdir(SCRIPT_DIR) if f.endswith(('.sh', '.py'))]
    current_script = get_current_script()
    status = {}
    for s in scripts:
        status[s] = {'running': (s == current_script and is_running(s)), 'pid': get_pid(s)}
    log_output = get_log(current_script) if current_script else "No hay script en ejecución."
    return render_template('index.html', scripts=scripts, status=status, current_script=current_script, log_output=log_output)

@app.route('/run/<script>')
def run_script(script):
    current_script = get_current_script()
    if current_script is None:  # Solo ejecutar si no hay otro en marcha
        script_path = os.path.join(SCRIPT_DIR, script)
        if os.path.isfile(script_path):
            start_script(script_path)
    return redirect(url_for('index'))

@app.route('/stop/<script>')
def stop_script_route(script):
    stop_script(script)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
