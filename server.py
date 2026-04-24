from flask import Flask, jsonify, request, send_file
import os
import subprocess
import threading
import time
from wakeonlan import send_magic_packet

app = Flask(__name__)

DATA_FILE = 'computers.txt'
PING_INTERVAL = 10  # segundos

computers = []  # Lista global de equipos
computers_lock = threading.Lock()  # Lock para evitar race conditions


def load_computers():
    global computers
    new_list = []
    if os.path.exists(DATA_FILE):
        print(f"[INFO] Leyendo archivo: {DATA_FILE}")
        with open(DATA_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    print(f"[DEBUG] Ignorando línea comentada o vacía: {line}")
                    continue
                parts = line.split(',')
                print(f"[DEBUG] Leyendo línea: {line}")
                if len(parts) >= 3:
                    ubicacion, nombre, ip = parts[:3]
                    mac = parts[3].strip() if len(parts) > 3 else None

                    # Validar que la MAC tenga exactamente 6 octetos
                    if mac:
                        octetos = mac.replace('-', ':').split(':')
                        if len(octetos) != 6:
                            print(f"[WARN] MAC inválida para {nombre} ({mac}), se ignorará para WoL")
                            mac = None

                    print(f"[INFO] Agregando equipo - Ubicación: {ubicacion}, Nombre: {nombre}, IP: {ip}, MAC: {mac}")
                    new_list.append({
                        'ubicacion': ubicacion,
                        'nombre': nombre,
                        'ip': ip,
                        'mac': mac,
                        'status': False
                    })
                else:
                    print(f"[WARN] Línea ignorada por formato incorrecto: {line}")
    else:
        print(f"[ERROR] Archivo {DATA_FILE} no encontrado")

    with computers_lock:
        computers = new_list

    print(f"[INFO] {len(new_list)} equipos cargados.")


def ping_host(ip):
    try:
        if os.name == 'nt':
            cmd = ['ping', '-n', '1', '-w', '1000', ip]  # timeout 1000ms en Windows
        else:
            cmd = ['ping', '-c', '1', '-W', '2', ip]     # timeout 2s en Linux

        completed = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        output = completed.stdout.lower()
        print(f"[DEBUG] ping {ip} | código: {completed.returncode} | salida: {output.strip()}")

        # Debe haber TTL= en la salida (indica respuesta real del host)
        if 'ttl=' not in output:
            return False

        # Descartar respuestas ICMP del router: el PC está apagado pero el
        # router responde "host inaccesible" con returncode 0 (falso positivo)
        palabras_negativas = [
            'inaccesible',   # Windows español
            'unreachable',   # Windows inglés / Linux
            'timed out',     # Windows inglés
            'tiempo agotado' # Windows español
        ]
        if any(p in output for p in palabras_negativas):
            return False

        return True

    except Exception as e:
        print(f"[ERROR] Error haciendo ping a {ip}: {e}")
        return False


def monitor_pings():
    print("[INFO] Iniciando monitor de pings")
    while True:
        # Tomar snapshot seguro de la lista
        with computers_lock:
            snapshot = list(computers)

        for c in snapshot:
            status = ping_host(c['ip'])
            if c['status'] != status:
                print(f"[INFO] Estado cambiado para {c['nombre']} (IP: {c['ip']}): {c['status']} -> {status}")
            c['status'] = status

        time.sleep(PING_INTERVAL)


@app.route('/')
def index():
    return send_file('index.html')


@app.route('/computers')
def get_computers():
    with computers_lock:
        data = list(computers)
    return jsonify(data)


@app.route('/reload', methods=['POST'])
def reload_computers():
    load_computers()
    with computers_lock:
        total = len(computers)
    return jsonify({'success': True, 'msg': f'{total} equipos recargados desde {DATA_FILE}'})


@app.route('/wake', methods=['POST'])
def wake():
    data = request.json
    mac = data.get('mac')
    if mac:
        mac_clean = mac.replace('-', ':').lower()
        # Validar formato antes de enviar
        octetos = mac_clean.split(':')
        if len(octetos) != 6:
            return jsonify({'success': False, 'msg': f'MAC inválida: {mac} (debe tener 6 octetos)'}), 400
        try:
            print(f"[INFO] Enviando Wake-on-LAN a MAC: {mac_clean}")
            send_magic_packet(mac_clean)
            return jsonify({'success': True, 'msg': f'Magic packet enviado a {mac_clean}'})
        except Exception as e:
            print(f"[ERROR] Falló Wake-on-LAN: {e}")
            return jsonify({'success': False, 'msg': str(e)})
    else:
        print("[WARN] MAC ausente en solicitud Wake-on-LAN")
        return jsonify({'success': False, 'msg': 'MAC address falta'}), 400


if __name__ == '__main__':
    load_computers()
    threading.Thread(target=monitor_pings, daemon=True).start()
    app.run(host='0.0.0.0', port=5001)