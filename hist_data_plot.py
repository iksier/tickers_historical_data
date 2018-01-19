# coding: utf8

import argparse
import requests
import string
import tkinter
import datetime
import random
import itertools
import logging
import sys
import re
from io import StringIO
import io

class Ticker():
	def __init__(self, name):
	
		self.name=name
		self.historical_data = {}
		url = "https://finance.yahoo.com/quote/" +  name
		logger.debug("Check if %s quote exists by % s", name,url)
		data_response = requests.get(url)
		logger.debug("data received")
		if data_response.status_code != 200:
			logger.warning("No data for %s" % name)		
			raise "Failed to  create"
		logger.debug("code==200")
		logger.debug(data_response.encoding)
		html_text = u''
		html_text = html_text + data_response.text
		if html_text.find("<title>Requested symbol wasn") != -1:
			logger.warning("%s quote doesn't exisr" % name)	

	def downloadHistorialData(self, ds,ms,ys,df, mf,yf):
		logger.debug("try to load data for: %s", self.name)
		
		date_start = datetime.datetime(ys,ms,ds)
		logger.debug(date_start)
		date_finish = datetime.datetime(yf,mf,df)
		logger.debug(date_finish)
		date_start_timestamp = 0
		date_start_timestamp = date_start.timestamp()
		date_finish_timestamp = 0
		date_finish_timestamp = date_finish.timestamp()
		date_finish_timestamp_str = str("%d" % date_finish_timestamp)
		date_start_timestamp_str = str("%d" % date_start_timestamp)		
		res = requests.get('https://finance.yahoo.com/quote/' + self.name + '/history')
		yahoo_cookie = res.cookies['B']
		yahoo_crumb = None
		logger.debug(res)
		pattern = re.compile('.*"CrumbStore":\{"crumb":"(?P<crumb>[^"]+)"\}')
		for line in res.text.splitlines():
			m = pattern.match(line)
			if m is not None:
				yahoo_crumb = m.groupdict()['crumb']
		cookie_tuple = yahoo_cookie, yahoo_crumb
		logger.debug(cookie_tuple)
		url_kwargs = {'symbol': self.name, 'timestamp_end': date_finish_timestamp_str,'timestamp_start': date_start_timestamp_str, \
        	'crumb': cookie_tuple[1]}
		logger.debug(url_kwargs)
		url_price = 'https://query1.finance.yahoo.com/v7/finance/download/' \
			'{symbol}?period1={timestamp_start}&period2={timestamp_end}&interval=1d&events=history' \
			'&crumb={crumb}'.format(**url_kwargs)
		logger.debug("try get data by: %s", url_price)
		data_response = requests.get(url_price, cookies={'B': cookie_tuple[0]})
		attempt_num = 1
		while data_response.status_code != 200 and attempt_num < 4:
			time.sleep(3)	
			data_response = requests.get(url_price, cookies={'B': cookie_tuple[0]})
			attempt_num = attempt_num + 1

		if data_response.status_code != 200:
			logger.warning("No data for %s" % self.name)		
			raise "Failed to load"
		self.reloadHistoryData(data_response.text)

	def getROI(self,date):
		return self.historical_data[date]["roi"]

	def getMaxROI(self):
		data_values = self.historical_data.values()
		roi_values = [x["roi"] for x in data_values]
		roi_values.sort()
		logger.debug("%s maxRoi %d", self.name,roi_values[-1])
		return roi_values[-1] 

		
	def reloadHistoryData(self, data):
		logger.debug("start reloading data for " + self.name)
		logger.debug("data size %d", len(data))
		buf = io.StringIO(data)
		dateData = buf.readlines()	
		startAdjClose = 0
		isFirstDay = 1

		for currentDateData in dateData[1:]:
			dataFiels = currentDateData.split(",")
			
			if len(dataFiels) < 6:
				continue
			#Date,Open,High,Low,Close,Volume,Adj Close
			cur_date = datetime.datetime.strptime(dataFiels[0],"%Y-%m-%d").date()
			cur_open = dataFiels[1]
			cur_high = dataFiels[2]
			cur_low = dataFiels[3]
			cur_close = dataFiels[4]
			cur_vol = dataFiels[6]
			cur_adj_close = dataFiels[5]
			if isFirstDay == 1:
				startAdjClose = float(cur_adj_close)
				isFirstDay = 0
			cur_roi = (float(cur_adj_close) - startAdjClose)/startAdjClose
			dateDict = {cur_date:{"open":dataFiels[1],"high":dataFiels[2],"low":dataFiels[3],"close":dataFiels[4],"vol":dataFiels[5],"adj_close":dataFiels[6],"roi":cur_roi} }
			self.historical_data.update(dateDict)
		logger.debug("data successfully loaded")
		
			

	def printme(self):
		print ("Ticker: %s \n" % self.name)
		print ("Available history data: \n")
		for dateData in self.historical_data:
			print ("date %s  %s " % (dateData, self.historical_data[dateData]))

	def getDataSize(self):
		return len(self.historical_data)

	def getName(self):
		return self.name

class PlotDrawer():
	def __init__(self,startDate, finishDate,maxValue,width = 1000.0, height = 600):
		logger.debug("Init plot drawer fot start_date %s, finish date %s, maxValue %d" % (startDate, finishDate, maxValue))
		self.width = width
		self.height = height
		date_count = finishDate - startDate
		self.xAxisStep = self.width /(date_count.days + 50)
		self.yScalePosNumber = maxValue + 2
		self.yAxisStep = max(self.height/self.yScalePosNumber, 20)
		logger.debug("yScalePosNumber: %d, step: %d",self.yScalePosNumber,self.yAxisStep)
		self.startDate = startDate
		self.finishDate = finishDate

		root = tkinter.Tk()	
		canv = tkinter.Canvas(root,width = width,height = height,bg="white")
		self.canv = canv
		self.root = root
		self.colors = ["red", "blue","green", "yellow", "brown", "orange","cyan","purple","azure","pink",\
							 "coral","violet","maroon","navy","tan","gold","peru","spring green"]
		
	def drawXScale(self):
		self.canv.create_line(0,self.height-30,self.width,self.height-30,width=2,arrow=tkinter.LAST) 
		currentDate = self.startDate
		dateNumber = 0
		prevDateNumber = 0
		while currentDate < self.finishDate:
			if currentDate.weekday()==0 and dateNumber > prevDateNumber + 28:
				self.canv.create_text(dateNumber*self.xAxisStep+5,self.height-25, text = currentDate.strftime("%d.%m.%y"), fill="red", font=("Helvectica", "10"))
				prevDateNumber = dateNumber									
			dateNumber = dateNumber + 1
			currentDate = currentDate + datetime.timedelta(1)

	def drawYScale(self):
		self.canv.create_line(10,self.height-30,10,10,width=2,arrow=tkinter.LAST)
		currentScalePos = 1
		while currentScalePos < self.yScalePosNumber:
			self.canv.create_text(20,self.height-30 -currentScalePos*self.yAxisStep, text = str(currentScalePos)+"%" , fill="red", font=("Helvectica", "10"))
			currentScalePos = currentScalePos + 1
	
	def drawGraph(self,tickers):
		
		self.drawXScale()
		self.drawYScale()
		for ticker in tickers:
			self.drawTicker(ticker)
		self.canv.pack()	
		self.root.mainloop()

	def drawTicker(self,ticker):
		currentDate = self.startDate
		lineColor = random.choice(self.colors)
		prevPoint = {"x":0,"y":self.height-30}
		dateNumber = 0
		pointValue = 0.0
		while currentDate < self.finishDate: 
			try:
				pointValue = ticker.getROI(currentDate) * 100
				logger.debug(pointValue)
				self.canv.create_line(prevPoint["x"],prevPoint["y"],dateNumber*self.xAxisStep+5,self.height-30-pointValue*self.yAxisStep,\
					fill=lineColor,width=1)
				prevPoint["x"] = dateNumber*self.xAxisStep+5
				prevPoint["y"] = self.height-30-pointValue*self.yAxisStep
			except:
				pass
			dateNumber = dateNumber + 1
			currentDate = currentDate + datetime.timedelta(1)
		tickerLabelText = ticker.getName() + "(" + "%.2f" % pointValue + "%)"

		self.canv.create_text(dateNumber*self.xAxisStep+5,self.height-30-pointValue*self.yAxisStep, text = tickerLabelText, \
			fill="blue", font=("Helvectica", "10"),anchor=tkinter.W)

def printAllMaxROI(tickers):
	for ticker in tickers:
		print(ticker.name,"\t",ticker.getMaxROI())
def getMaxFromTickers(tickers):
	allValues = []
	for ticker in tickers:
		allValues.append(ticker.getMaxROI())
	allValues.sort()
	return allValues[-1]
def loadTickerNamesFromFile(ticker_file):
	logger.debug("start loadTickerNamesFromFile")
	tickerList = []
	with open(ticker_file, "r") as tick_file:
		cur_ticker_name = tick_file.readline()
		while cur_ticker_name:
			tickerList.append(cur_ticker_name[:-1])
			cur_ticker_name = tick_file.readline()		
	logger.debug(tickerList)
	return tickerList

def getAllPossibleTickerNames():
	allTickerNames = []
	alphabetList = list(string.ascii_uppercase)
	threeLettersCombinations = itertools.product(alphabetList,repeat=3)
	for ticker_name in threeLettersCombinations:
		allTickerNames.append(ticker_name)
	fourLettersCombinations = itertools.product(alphabetList,repeat=4)
	for ticker_name in threeLettersCombinations:
		allTickerNames.append(ticker_name)
	resultTickerName = []
	map(lambda x: resultTickerName.append(string.join(x).replace(' ','')), allTickerNames)
	return resultTickerName

def main():
	parser = argparse.ArgumentParser("Download historical data by tikker list from finance.yahoo.com and graph ROI plot")
	parser.add_argument("--day_start","-ds",type=int, default=11, help="start period date")
	parser.add_argument("--month_start","-ms",type=int, default=1, help="start period month")
	parser.add_argument("--year_start","-ys",type=int, default=2017, help="start period year")
	parser.add_argument("--all_tickers","-at",type=int, default=0, help="show roi for the all 3-4 length ticker names")
	parser.add_argument("--tickers_file_name","-tf", default="", help="file containing tickers list")
#	parser.add_argument("--day_finish","-df",type=int, default=1, help="finish period date")
#	parser.add_argument("--month_finish","-mf",type=int, default=7, help="finish period month")
#	parser.add_argument("--year_finish","-yf",type=int, default=2016, help="finish period year")
#	parser.add_argument("--period_pace","-p",type=str, default="week", help="time periods on graph")
	args = parser.parse_args()
 	
	startDate = datetime.date(args.year_start,args.month_start,args.day_start)
	finishDate = datetime.date.today()
	tickerNames = ['BND']
	tickers = []
	if args.all_tickers == 1:
		tickerNames = getAllPossibleTickerNames()
	if args.tickers_file_name != "":
		tickerNames = loadTickerNamesFromFile(args.tickers_file_name)
	for ticker_name in tickerNames:
		try:
			currentTicker = Ticker(name=ticker_name)
			currentTicker.downloadHistorialData(startDate.day,startDate.month,startDate.year,finishDate.day,finishDate.month,finishDate.year)
			tickers.append(currentTicker)
			logger.debug ("%s added. %d tickers in total",ticker_name,len(tickers))
		except:
			logger.error('Error: {}'.format(sys.exc_info()[0]))
			logger.error("Exception for %s ticker", ticker_name)
			pass
		
	maxValue = round(getMaxFromTickers(tickers)*100) + 1
	printAllMaxROI(tickers)
	plot = PlotDrawer(startDate,finishDate, maxValue)
	plot.drawGraph(tickers)


if __name__ == "__main__":
	logger = logging.getLogger()
	logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(funcName)s - %(message)s')
	logger.debug ("logger inited")
	main()
