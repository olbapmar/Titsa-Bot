# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
import ConfigParser
from api_handler import ApiHandler
from telegram.ext import CommandHandler, MessageHandler, Updater, Filters
import telegram as telegram
import logging
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

apiHandler = None

def process_xml(xml_titsa):

    if len(list(xml_titsa)) >= 1:
        text = "🚏" +  xml_titsa[0].find("denominacion").text + "🚏\n\n"
        for linea in xml_titsa:
            text += "🚍*" + linea.find("linea").text + "*(" + linea.find("destinoLinea").text + \
                    "): "+ linea.find("minutosParaLlegar").text + " minutos \n"
        
        return text, 1
    else:
        text = "⚠ Parada no encontrada o sin guaguas por venir ⚠"
        return text, 0

def start(bot,update):
    bot.send_message(chat_id=update.message.chat_id, text="Hola! Gracias por usarme! \nEnvíame el código de una parada :)")

def responder_a_codigo(bot,update):
    if update.message.text.isdigit() and len(update.message.text) == 4:
        texto = process_xml(apiHandler.new_request(update.message.text))[0]
        bot.send_message(chat_id=update.message.chat_id, text=texto,parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        bot.send_message(chat_id=update.message.chat_id, text="Código inválido")

def main():
    config = ConfigParser.ConfigParser()
    config.read('bot_config.ini')
    
    bot_token = config.get("TELEGRAM", "token")

    titsa_idApp = config.get("TITSA", "idApp")
    global apiHandler 
    apiHandler = ApiHandler(titsa_idApp)

    updater = Updater(token=bot_token)
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    comandos = CommandHandler("start", start)
    mensajes = MessageHandler(Filters.text, responder_a_codigo)
    updater.dispatcher.add_handler(comandos)
    updater.dispatcher.add_handler(mensajes)

    updater.start_polling()


if __name__ == "__main__":
    main()