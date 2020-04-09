import heapq
import threading
import urllib.request
from io import BytesIO
from zipfile import ZipFile
import csv
from dataclasses import dataclass

@dataclass
class StopInfo:
    name: str
    id: str
    lon: float
    lat: float

    def distance(self, lat, lon) -> float:
        return ((self.lat -lat)**2 + (self.lon - lon)**2)

class OpenTransitThread:
    def __init__(self, url, interval):
        self.url = url #"http://www.titsa.com/Google_transit.zip"
        self.interval = interval

    def start(self):
        self.__getTransitFile()

    def __getTransitFile(self):
        response = urllib.request.urlopen(self.url)
        
        if response.getcode() == 200:
            zipfile = ZipFile(BytesIO(response.read()))
            StopsHandler.updateStops(zipfile.open("stops.txt"))
        
        self.thread = threading.Timer(self.interval, self.__getTransitFile)
        self.thread.start()

    def stop(self):
        if self.thread is not None:
            self.thread.cancel()

class StopsHandler:
    stops = {}
    mutex = threading.Lock()

    @staticmethod
    def updateStops(stopsInfo):
        stops = {}
        csv_reader = csv.DictReader(stopsInfo.read().decode("utf-8-sig").splitlines())
        for stop in csv_reader:
            stops[int(stop["stop_id"])] = StopInfo(stop["stop_name"], stop["stop_id"], float(stop["stop_lon"]), float(stop["stop_lat"]))

        with StopsHandler.mutex:
            StopsHandler.stops = stops

    @staticmethod
    def nearestStops(k, lat, lon):
        if len(StopsHandler.stops) == 0:
            return None
        with StopsHandler.mutex:
            auxList = []
            for stop in StopsHandler.stops.values():
                auxList.append((stop.distance(lat,lon), stop))

            return [aux[1] for aux in heapq.nsmallest(k, auxList, key=lambda item: item[0])]

    @staticmethod
    def stationName(id):
        return StopsHandler.stops[int(id)].name

    @staticmethod
    def stopLocation(id):
        stop = StopsHandler.stops[int(id)]
        return stop.lat, stop.lon