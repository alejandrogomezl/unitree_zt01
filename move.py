import asyncio
import logging
import json
import sys
import pygame
from go2_webrtc_driver.webrtc_driver import Go2WebRTCConnection, WebRTCConnectionMethod
from go2_webrtc_driver.constants import RTC_TOPIC, SPORT_CMD

logging.basicConfig(level=logging.INFO)

JOYSTICK_DEADZONE = 0.0
MAX_SPEED = 1.0

def process_joystick_input(axis_value):
   if abs(axis_value) < JOYSTICK_DEADZONE:
       return 0.0
   return round(axis_value * MAX_SPEED, 2)

async def send_movement(conn, x, y, z):
   for i in range(2):
       print(f"🕹 Moviendo: x={x}, y={y}, z={z} (envío {i+1}/2)")
       await conn.datachannel.pub_sub.publish_request_new(
           RTC_TOPIC["SPORT_MOD"],
           {
               "api_id": SPORT_CMD["Move"],
               "parameter": {"x": x, "y": y, "z": z * 2.5}
           }
       )
       await asyncio.sleep(0.1)

async def main():
   pygame.init()
   pygame.joystick.init()
   if pygame.joystick.get_count() == 0:
       print("❌ No se detectó ningún mando.")
       return

   joystick = pygame.joystick.Joystick(0)
   joystick.init()
   print(f"🎮 Mando detectado: {joystick.get_name()}")

   conn = Go2WebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip="192.168.166.9")
   await conn.connect()
   print("✅ Conectado al robot")

   response = await conn.datachannel.pub_sub.publish_request_new(
       RTC_TOPIC["MOTION_SWITCHER"], {"api_id": 1001}
   )
   mode = json.loads(response["data"]["data"])["name"]
   if mode != "normal":
       print("🔄 Cambiando a modo 'normal'...")
       await conn.datachannel.pub_sub.publish_request_new(
           RTC_TOPIC["MOTION_SWITCHER"],
           {"api_id": 1002, "parameter": {"name": "normal"}}
       )
       await asyncio.sleep(4)

   print("👋 Enviando saludo")
   await conn.datachannel.pub_sub.publish_request_new(
       RTC_TOPIC["SPORT_MOD"],
       {"api_id": SPORT_CMD["Hello"]}
   )

   print("🕹️ Controla el robot con el joystick (Ctrl+C para salir)")

   prev_buttons = [False] * joystick.get_numbuttons()

   try:
       while True:
           pygame.event.pump()

           # Movimiento
           x = -process_joystick_input(joystick.get_axis(1))
           y = -process_joystick_input(joystick.get_axis(0))
           z = process_joystick_input(joystick.get_axis(3))

           if x != 0 or y != 0 or z != 0:
               await send_movement(conn, x, y, z)

           # A: saludar (índice 0)
           if joystick.get_button(0) and not prev_buttons[0]:
               print("👋 Botón A pulsado: saludo")
               await conn.datachannel.pub_sub.publish_request_new(
                   RTC_TOPIC["SPORT_MOD"],
                   {"api_id": SPORT_CMD["Hello"]}
               )

           # X: sentarse (índice 2)
           if joystick.get_button(2) and not prev_buttons[2]:
               print("🪑 Botón X pulsado: sentarse")
               await conn.datachannel.pub_sub.publish_request_new(
                   RTC_TOPIC["SPORT_MOD"],
                   {"api_id": SPORT_CMD["Sit"]}
               )

           # Y: levantarse (índice 3)
           if joystick.get_button(3) and not prev_buttons[3]:
               print("🦵 Botón Y pulsado: levantarse")
               await conn.datachannel.pub_sub.publish_request_new(
                   RTC_TOPIC["SPORT_MOD"],
                   {"api_id": SPORT_CMD["StandUp"]}
               )

           # Guardar estado de los botones
           for i in range(len(prev_buttons)):
               prev_buttons[i] = joystick.get_button(i)

           await asyncio.sleep(0.1)
   except KeyboardInterrupt:
       print("\n⛔ Finalizado por el usuario")

if __name__ == "__main__":
   try:
       asyncio.run(main())
   except Exception as e:
       logging.error(f"❌ Error: {e}")
       sys.exit(1)

