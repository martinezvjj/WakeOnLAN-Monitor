# 🖥️ WakeOnLAN Monitor

Aplicación web para monitorear el estado (online/offline) de computadores en una red local y encenderlos remotamente mediante **Wake-on-LAN**.

---

## ¿Qué hace?

- Muestra en tiempo real el estado de cada equipo registrado (🟢 Online / 🔴 Offline)
- Detecta correctamente equipos apagados, incluso cuando el router responde en su nombre
- Permite encender equipos remotamente con un clic usando Wake-on-LAN (WoL)
- Recarga la lista de equipos sin reiniciar el servidor
- Se actualiza automáticamente cada 10 segundos

---

## Requisitos

- Python 3.8 o superior
- Red local con soporte Wake-on-LAN en los equipos destino
- Los equipos deben tener WoL habilitado en la BIOS/UEFI

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/martinezvjj/WakeOnLAN-Monitor.git
cd WakeOnLAN-Monitor
```

### 2. Crear entorno virtual (recomendado)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install flask wakeonlan
```

#### Bibliotecas utilizadas

| Biblioteca | Versión mínima | Descripción |
|------------|---------------|-------------|
| `flask` | 2.0+ | Framework web para servir la interfaz y la API REST |
| `wakeonlan` | 2.0+ | Envío de magic packets para Wake-on-LAN |
| `subprocess` | (built-in) | Ejecución de comandos ping del sistema operativo |
| `threading` | (built-in) | Monitor de pings en hilo separado sin bloquear el servidor |
| `os` | (built-in) | Detección del sistema operativo para ajustar comandos |

---

## Configuración de equipos

Edita el archivo `computers.txt` para registrar los equipos a monitorear.

### Formato

```
ubicacion,nombre,ip_o_hostname,mac
```

### Ejemplo

```
# Comentarios se ignoran (líneas que empiezan con #)
Nivel Central,PC-Recepcion,192.168.1.10,AA:BB:CC:DD:EE:FF
Nivel Central,NB-Gerencia,192.168.1.20,11:22:33:44:55:66
Sala Reuniones,PC-Proyector,PROYECTOR.empresa.local,77:88:99:AA:BB:CC
```

### Reglas
- La **MAC debe tener exactamente 6 octetos** separados por `:` o `-`
- Se puede usar **IP directa** o **hostname** (ej: `EQUIPO.dominio.local`)
- Si la MAC es inválida, el equipo igual se monitorea pero el botón WoL no funcionará
- Las líneas que comienzan con `#` son comentarios y se ignoran

---

## Ejecución

```bash
python server.py
```

Luego abre el navegador en:

```
http://localhost:5001
```

O desde otro equipo en la red:

```
http://IP_DEL_SERVIDOR:5001
```

---

## Endpoints API

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/` | Interfaz web principal |
| `GET` | `/computers` | Lista de equipos con su estado en JSON |
| `POST` | `/reload` | Recarga `computers.txt` sin reiniciar el servidor |
| `POST` | `/wake` | Envía magic packet WoL a una MAC address |

### Ejemplo `/wake`

```bash
curl -X POST http://localhost:5001/wake \
     -H "Content-Type: application/json" \
     -d '{"mac": "AA:BB:CC:DD:EE:FF"}'
```

---

## Estructura del proyecto

```
WakeOnLAN-Monitor/
├── server.py          # Servidor Flask, lógica de ping y WoL
├── index.html         # Interfaz web (servida por Flask)
├── computers.txt      # Lista de equipos a monitorear
└── README.md          # Este archivo
```

---

## Notas técnicas

- El monitor de pings corre en un **hilo separado** con un lock para prevenir errores por ejecución simultánea.
- El ping verifica `TTL=` en la salida y descarta respuestas ICMP del router ("host inaccesible"), evitando falsos positivos cuando un equipo está apagado pero el router responde en su nombre.
- Compatible con Windows (detecta mensajes en español e inglés) y Linux/macOS.

---

## Licencia

MIT — libre para uso personal y comercial.