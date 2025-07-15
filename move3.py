import asyncio
import logging
from evdev import InputDevice, categorize, ecodes
from unitree_sdk2_python.high_level import SportClient
from unitree_sdk2_python.common import SportMode

logging.basicConfig(level=logging.INFO)

JOYSTICK_DEVICE = '/dev/input/event0'  # actualiza según tu sistema
JOY_DEADZONE = 0.1
MAX_SPEED = 1.0
ROT_MULT = 2.5

def norm(val):
    return 0.0 if abs(val) < JOY_DEADZONE else round(val * MAX_SPEED, 2)

async def main():
    dev = InputDevice(JOYSTICK_DEVICE)
    logging.info(f"Mando detectado: {dev.name}")

    sport = SportClient()
    await sport.connect()
    logging.info("✅ Conectado al robot por DDS")

    await sport.set_sport_mode(SportMode.Normal)
    logging.info("🔄 Modo 'normal' activado")

    prev = {"axes": (0,0,0), "buttons": {}}
    async for ev in dev.async_read_loop():
        if ev.type == ecodes.EV_ABS:
            ab = categorize(ev)
            # asigna índices correctos según tu mando
            ax = {1: -norm(ab.event.value/32767),
                  0: -norm(ab.event.value/32767),
                  3: norm(ab.event.value/32767)}
            x = ax.get(1, prev["axes"][0])
            y = ax.get(0, prev["axes"][1])
            z = ax.get(3, prev["axes"][2])
            if (x,y,z) != prev["axes"]:
                await sport.velocity_move(x, y, z * ROT_MULT)
                prev["axes"] = (x,y,z)

        elif ev.type == ecodes.EV_KEY and ev.value == 1:
            btn = ev.code
            mapping = {
                ecodes.BTN_SOUTH: ("Hello", sport.hello),
                ecodes.BTN_EAST: ("StandUp", sport.stand_up),
                ecodes.BTN_NORTH: ("Sit", sport.sit_down),
                ecodes.BTN_MODE: ("Damp", sport.damp)
            }
            if btn in mapping:
                name, action = mapping[btn]
                logging.info(f"🔘 Botón {name}")
                await action()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logging.error(f"❌ {e}")
        sys.exit(1)
