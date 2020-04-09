import urllib
import xml.etree.ElementTree as ET
import json


class CurrentStationStatus:
    def __init__(self, name):
        self.name = name
        self.minutes = {}
    def add_line(self, line, dest, minutes):
        if not line in self.minutes:
            self.minutes[line] = [{"dest": dest, "minutes": minutes},] 
        else:
            self.minutes[line].append({"dest": dest, "minutes": minutes})
            self.minutes[line] = sorted(self.minutes[line], key=lambda item:int(item["minutes"]))


class ApiHandler:
    URL = "http://apps.titsa.com/apps/apps_sae_llegadas_parada.asp?idParada="
    URL2 = "&idApp=" 
    URL_TRANVIA = "http://tranviaonline.metrotenerife.com/api/infoStops/infoPanel"

    def __init__(self, idApp):
        self.idApp = idApp

    def new_request(self, id):
        url_final = ApiHandler.URL + str(id) + ApiHandler.URL2 + self.idApp
        
        response = urllib.request.urlopen(url_final)

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

    
    '''
    def station_name(self, id):
        url_final = ApiHandler.URL + str(id) + ApiHandler.URL2 + self.idApp
        
        response = urllib.request.urlopen(url_final)

        if response.getcode() == 200:
            text = response.read().decode('utf8')
            root = ET.fromstring(text.encode('utf8'))
            return root[0].find("denominacion").text
        return None
    '''

    def tranvia_stations(self):
        response = urllib.request.urlopen(ApiHandler.URL_TRANVIA)

        if response.getcode() == 200:
            text = response.read().decode('utf8')
            json_object = json.loads(text)

            stations = {}
            for entry in json_object:
                stations[entry[u"stopDescription"].lower().capitalize()] = entry[u"stop"]
            return stations

        return None

    def tranvia_request(self, stop):
        response = urllib.request.urlopen(ApiHandler.URL_TRANVIA)
        print(stop)
        if response.getcode() == 200:
            text = response.read().decode('utf8')
            json_object = json.loads(text)

            status = None
            for entry in json_object:
                if stop == entry[u"stop"]:
                    if status is None:
                        status = CurrentStationStatus(entry[u"stopDescription"])
                    status.add_line("L"+str(entry[u"route"]), entry[u"destinationStopDescription"], str(entry[u"remainingMinutes"]))

            return status