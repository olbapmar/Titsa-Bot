# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
import ConfigParser
from api_handler import ApiHandler

def process_xml(xml_titsa):

    if len(list(xml_titsa)) >= 1:
        text = "🚏" +  xml_titsa[0].find("denominacion").text + "🚏\n\n"
        for linea in xml_titsa:
            text += "🚍*" + linea.find("linea").text + "*(" + linea.find("destinoLinea").text + \
                    "): " + linea.find("minutosParaLlegar").text + " minutos \n"
        
        return text, 1
    else:
        text = "⚠ Parada no encontrada o sin guaguas por venir ⚠"
        return text, 0


def main():
    config = ConfigParser.ConfigParser()
    config.read('bot_config.ini')
    
    bot_token = config.get("TELEGRAM", "token")
    titsa_idApp = config.get("TITSA", "idApp")

    apiHandler = ApiHandler(titsa_idApp)

if __name__ == "__main__":
    main()