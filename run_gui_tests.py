import os
import sys

# TEST 1
import py_compile
py_compile.compile('gui.py')
print('gui.py OK - TEST 1 PASSED')

# TEST 2
sys.argv = ['gui.py']
import gui
print('Flask app created OK')
print('Routes:', [str(r) for r in gui.app.url_map.iter_rules()])
print('TEST 2 PASSED')

# TEST 3
with open('gui_template.html', encoding='utf-8') as f:
    html = f.read()
assert '<canvas' in html, 'Missing canvas elements'
assert 'socket.io' in html, 'Missing socket.io'
assert 'sensor_update' in html, 'Missing sensor handler'
assert 'submit_answer' in html, 'Missing submit handler'
assert 'contradiction' in html.lower(), 'Missing contradiction UI'
assert len(html) > 5000, f'HTML too short: {len(html)} chars'
print(f'HTML file: {len(html)} chars')
print('TEST 3 PASSED')

# TEST 4
import threading, time, requests

def run_flask():
    gui.socketio.run(gui.app, host='127.0.0.1', port=5099, debug=False, use_reloader=False)

t = threading.Thread(target=run_flask, daemon=True)
t.start()
time.sleep(2)

r = requests.get('http://127.0.0.1:5099/')
assert r.status_code == 200, f'Got {r.status_code}'
assert 'POLYTRUTH' in r.text
print('Server responds OK')
print('TEST 4 PASSED')
