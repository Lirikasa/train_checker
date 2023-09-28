import requests
import re
import base64
import json
import time
import threading
import os
from dotenv import load_dotenv

load_dotenv()

from playsound import playsound

import telebot

BOT_KEY = os.getenv('GCP_PROJECT_ID')
USER_ID = os.getenv('SERVICE_ACCOUNT_FILE')
CAPCHA_API_KEY = os.getenv('STORAGE_BUCKET_NAME')
CHAT_ID = os.getenv('CHAT_ID')

bot = telebot.TeleBot(BOT_KEY)

@bot.message_handler(content_types=["text"])
def bot_mesajes_texto(message):
    bot.send_message(CHAT_ID, message)


headers = {} 

def captchaDecoder():
    url = "https://webventas.sofse.gob.ar"

    response = requests.get(url)

    headers['Cookie'] = 'PHPSESSID=' + response.cookies['PHPSESSID']

    captcha = re.search("(https://webventas.sofse.gob.ar/vendor/captcha/captcha_busqueda.php\?.{13})", response.text)
   
    image = requests.request("GET", url=captcha[0], headers=headers).content

    image_base_64 = str(base64.b64encode(image))
    image_base_64 = image_base_64[1: len(image_base_64) - 1]

    payload = json.dumps({
        "userid": USER_ID,
        "apikey": CAPCHA_API_KEY,
        "data": image_base_64
    })

    captcha_resuelto = requests.request("POST", url="https://api.apitruecaptcha.org/one/gettext", data=payload).json()['result']

    return captcha_resuelto


def checkServicios(fecha, sentido):
    url = "https://webventas.sofse.gob.ar/ajax/servicio/obtener_servicios.php"

    status_payload={
        'fecha_seleccionada': fecha,
        'sentido': sentido,
    }

    def checkStatus(): 
        response = requests.request("POST", url, headers=headers, data=status_payload).json()

        try: 
            if response["status"] == -1 : 
                print('Conexion fallida')
                bot_mesajes_texto('Conexion fallida')
            elif response["sin_disponibilidad"] != 1 :
                playsound('./train.mp3')
                bot_mesajes_texto('Hay trenes')
                bot_mesajes_texto('Para el: ' + fecha)
            else:
                print('No hay trenes para el: ' + fecha)
                time.sleep(60)
                checkStatus()
        except: 
            bot_mesajes_texto('Me rompí :p')

    checkStatus()

def traerPasajes():
    url = "https://webventas.sofse.gob.ar/servicio.php"

    payload={'busqueda[tipo_viaje]': '2',
    'busqueda[origen]"': cod_origen,
    'busqueda[destino]': cod_destino,
    'busqueda[fecha_ida]': fecha_ida,
    'busqueda[fecha_vuelta]': fecha_vuelta,
    'busqueda[cantidad_pasajeros][adulto]': '1',
    'busqueda[cantidad_pasajeros][jubilado]"': '0',
    'busqueda[cantidad_pasajeros][menor]': '0',
    'busqueda[cantidad_pasajeros][bebe]': '0',
    'captcha': captchaDecoder()
    }

    requests.request("POST", url, headers=headers, data=payload)

cod_origen = input(">>> Ingrese codigo de origen: ")
cod_destino = input(">>> Ingrese codigo de destino: ")
fecha_ida = input(">>> Ingrese fecha de ida: ")
fecha_vuelta = input(">>> Ingrese fecha de vuelta: ")

traerPasajes()

ida = threading.Thread(target=checkServicios, args=(fecha_ida, '1'))

vuelta = threading.Thread(target=checkServicios, args=(fecha_vuelta, '2'))

ida.start()
vuelta.start()


