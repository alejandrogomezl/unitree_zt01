from flask import Flask, render_template, redirect, url_for
import os

from script_manager import start_script, stop_script, is_running, get_pid

SCRIPT_DIR = os.path.join(os.path.dirname(__file__), 'scripts')
app = Flask(__name__)

@app.route('/')
def index():
    scripts = [f for f in os.listdir(SCRIPT_DIR) if f.endswith(('.sh', '.py'))]
    status = {s: {'running': is_running(s), 'pid': get_pid(s)} for s in scripts}
    return render_template('index.html', scripts=scripts, status=status)

@app.route('/run/<script>')
def run_script(script):
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
