import urllib.request
import re
import pandas as pd
import datetime


class Stock:
    def __init__(self, url):
        self.url = url
        self.json = self.get_json()
        self.name = self.get_name()
        self.id = None
        self.data = self.get_data()

    def get_json(self):
        req = urllib.request.Request(self.url)
        with urllib.request.urlopen(req) as response:
            responsedata = response.read()
            json = responsedata.decode()
        return json

    def get_name(self):
        regex = r'"name":"([^"]+)"'
        result = re.search(regex, self.json)
        name = result.group(1)
        return name

    def get_data(self):
        regex = r'"klines":\[(.+)\]'
        result = re.search(regex, self.json)
        regex = r'"([^"]*)"'
        templist = re.findall(regex, result.group(1))
        templist = list(map(lambda item: item.split(','), templist))
        stockdata = list()
        for item in templist:
            tempitem = [datetime.datetime.strptime(item[0], "%Y-%m-%d").date()]
            for i in range(1, len(item)):
                tempitem.append(float(item[i]))
            stockdata.append(tempitem)
        return stockdata