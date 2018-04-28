import urllib2
import xml.etree.ElementTree as ET

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
            text = response.read().decode('iso-8859-1')
            print text
            root = ET.fromstring(text.encode('utf8'))
            return root
        return None