import json
import os
from pathlib import Path

from flask import Flask, Response, jsonify, redirect, render_template_string, request, url_for

app = Flask(__name__)
STATE_FILE = Path(os.environ.get('GORODOVOY_STATE_FILE', '/tmp/gorodovoy_state.json'))
ESTOP_FILE = Path(os.environ.get('GORODOVOY_ESTOP_FILE', '/tmp/gorodovoy_estop'))
IMAGE_FILE = STATE_FILE.with_suffix('.jpg')

PAGE = '''
<!doctype html><html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Gorodovoy Robot</title>
<style>
body{font-family:Arial,sans-serif;background:#101820;color:#eef;margin:0;padding:20px}
main{max-width:900px;margin:auto}img{width:100%;max-width:640px;background:#222;border-radius:10px}
.panel{background:#1d2a35;padding:16px;border-radius:10px;margin:12px 0}
button{padding:14px 20px;border:0;border-radius:8px;font-weight:bold;margin:5px}
.stop{background:#d33;color:white}.enable{background:#287d50;color:white}
small{color:#b8c6d1}
</style></head><body><main><h1>Gorodovoy Robot</h1>
<div class="panel"><img src="/video" alt="Видеопоток робота"></div>
<div class="panel"><div id="state">Загрузка состояния…</div></div>
<div class="panel">
<form method="post" action="/stop"><button class="stop">АВАРИЙНЫЙ STOP</button></form>
<form method="post" action="/enable"><button class="enable">Разрешить оператору</button></form>
<small>Разрешение оператора не отменяет программные блокировки и не заменяет физический E-STOP.</small>
</div></main>
<script>
async function refresh(){try{let r=await fetch('/api/status');let s=await r.json();
document.getElementById('state').innerHTML=
'Статус: <b>'+s.status+'</b><br>Цель: '+s.target_valid+
'<br>Зафиксирована: '+s.target_locked+
'<br>Расстояние: '+(s.distance_m===null?'нет данных':s.distance_m.toFixed(2)+' м')+
'<br>Ошибка центра: '+s.center_error_px+' px'+
'<br>Depth aligned: '+s.depth_aligned+
'<br>Разрешение оператора: '+s.operator_enabled;
}catch(e){document.getElementById('state').textContent='Нет связи с ROS-сервисом состояния';}}
setInterval(refresh,1000);refresh();
</script></body></html>
'''


def read_state():
    try:
        return json.loads(STATE_FILE.read_text(encoding='utf-8'))
    except Exception:
        return {
            'status': 'STOP', 'target_valid': False, 'target_locked': False,
            'emergency_stop': True, 'distance_m': None, 'center_error_px': 0,
            'depth_aligned': False, 'operator_enabled': False,
        }


@app.get('/')
def index():
    return render_template_string(PAGE)


@app.get('/api/status')
def status():
    return jsonify(read_state())


@app.get('/video')
def video():
    def generate():
        import time
        while True:
            try:
                data = IMAGE_FILE.read_bytes()
                if data:
                    yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + data + b'\r\n')
            except OSError:
                pass
            time.sleep(0.12)
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.post('/stop')
def stop():
    ESTOP_FILE.unlink(missing_ok=True)
    return redirect(url_for('index'))


@app.post('/enable')
def enable():
    # This is only an operator-enable flag; perception still enforces depth/target interlocks.
    ESTOP_FILE.parent.mkdir(parents=True, exist_ok=True)
    ESTOP_FILE.write_text('operator enabled\n', encoding='utf-8')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host=os.environ.get('HOST', '0.0.0.0'),
            port=int(os.environ.get('PORT', '5000')), threaded=True)
