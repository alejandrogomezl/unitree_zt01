import asyncio
import logging
import json
import sys
import pygame
import time
from go2_webrtc_driver.webrtc_driver import Go2WebRTCConnection, WebRTCConnectionMethod
from go2_webrtc_driver.constants import RTC_TOPIC, SPORT_CMD

# Configuración de logs
logging.basicConfig(level=logging.INFO)

# Parámetros
JOYSTICK_DEADZONE = 0.1
MAX_SPEED = 1.0
ROTATION_MULTIPLIER = 2.5
COMMAND_COOLDOWN = 0.2  # en segundos

# Utilidades
def process_axis(value):
    """Normaliza el valor del joystick con zona muerta"""
    return 0.0 if abs(value) < JOYSTICK_DEADZONE else round(value * MAX_SPEED, 2)

async def send_movement(conn, x, y, z):
    """Envía el comando de movimiento al robot"""
    logging.debug(f"Moviendo: x={x}, y={y}, z={z}")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"],
        {
            "api_id": SPORT_CMD["Move"],
            "parameter": {"x": x, "y": y, "z": z * ROTATION_MULTIPLIER}
        }
    )

async def main():
    # Inicializar pygame y joystick
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("❌ No se detectó ningún mando.")
        return

    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"🎮 Mando detectado: {joystick.get_name()}")

    # Conexión con el robot
    conn = Go2WebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip="192.168.4.15")
    await conn.connect()
    print("✅ Conectado al robot")

    # Comprobar y establecer modo
    response = await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["MOTION_SWITCHER"], {"api_id": 1001}
    )
    current_mode = json.loads(response["data"]["data"])["name"]
    if current_mode != "normal":
        print("🔄 Cambiando a modo 'normal'...")
        await conn.datachannel.pub_sub.publish_request_new(
            RTC_TOPIC["MOTION_SWITCHER"],
            {"api_id": 1002, "parameter": {"name": "normal"}}
        )
        await asyncio.sleep(4)

    # Saludo inicial
    print("👋 Enviando saludo inicial...")
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"],
        {"api_id": SPORT_CMD["Hello"]}
    )

    print("🕹️ Control activo. Usa el joystick para mover el robot. Ctrl+C para salir.")
    prev_buttons = [False] * joystick.get_numbuttons()
    last_command_time = time.time()

    try:
        while True:
            pygame.event.pump()

            # Joystick: ejes
            x = -process_axis(joystick.get_axis(1))  # vertical izquierdo
            y = -process_axis(joystick.get_axis(0))  # horizontal izquierdo
            z = process_axis(joystick.get_axis(3))   # horizontal derecho

            # Si ha pasado el cooldown, enviamos
            now = time.time()
            if (x, y, z) != (0, 0, 0) and (now - last_command_time) > COMMAND_COOLDOWN:
                await send_movement(conn, x, y, z)
                last_command_time = now

            # Botones
            buttons = {
                0: ("A", SPORT_CMD["Hello"], "👋 Saludo"),
                1: ("B", SPORT_CMD["StandUp"], "🦵 Levantar"),
                2: ("X", SPORT_CMD["Sit"], "🪑 Sentarse"),
                3: ("Y", SPORT_CMD["StandUp"], "🦵 Levantar"),
                7: ("Start", SPORT_CMD["Damp"], "⛔ Parar")
            }

            for idx, (name, cmd, desc) in buttons.items():
                if joystick.get_button(idx) and not prev_buttons[idx]:
                    print(f"{desc} ({name})")
                    await conn.datachannel.pub_sub.publish_request_new(
                        RTC_TOPIC["SPORT_MOD"], {"api_id": cmd}
                    )

            # Actualizar estado previo de botones
            prev_buttons = [joystick.get_button(i) for i in range(joystick.get_numbuttons())]
            await asyncio.sleep(0.05)
    except KeyboardInterrupt:
        print("\n⛔ Finalizado por el usuario")
    finally:
        pygame.quit()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logging.error(f"❌ Error: {e}")
        sys.exit(1)
