import urllib2
import xml.etree.ElementTree as ET

class CurrentStationStatus:
    def __init__(self, name):
        self.name = name
        self.minutes = {}
    def add_line(self, line, dest, minutes):
        self.minutes[line] = {"dest": dest, "minutes": minutes}


class ApiHandler:
    URL = "http://apps.titsa.com/apps/apps_sae_llegadas_parada.asp?idParada="
    URL2 = "&idApp=" 

    def __init__(self, idApp):
        self.idApp = idApp

    def new_request(self, id):
        url_final = ApiHandler.URL + str(id) + ApiHandler.URL2 + self.idApp
        
        req = urllib2.Request(url_final)
        response = urllib2.urlopen(req)

        if response.getcode() == 200:
            text = response.read().decode('utf8')
            root = ET.fromstring(text.encode('utf8'))
            if len(root) >= 1:
                status = CurrentStationStatus(root[0].find("denominacion").text)
                for linea in root:
                    status.add_line(linea.find("linea").text, linea.find("destinoLinea").text, linea.find("minutosParaLlegar").text)
                
                return status
            else:
                return None

        return None

    

    def station_name(self, id):
        url_final = ApiHandler.URL + str(id) + ApiHandler.URL2 + self.idApp
        
        req = urllib2.Request(url_final)
        response = urllib2.urlopen(req)

        if response.getcode() == 200:
            text = response.read().decode('utf8')
            root = ET.fromstring(text.encode('utf8'))
            return root[0].find("denominacion").text
        return None