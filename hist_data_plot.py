import argparse
import requests
import string
import Tkinter
import datetime
import random
import itertools
import logging


class Ticker():
	def __init__(self, name):
		self.name=name
		self.historical_data = {}

	def downloadHistorialData(self, ds,ms,ys,df, mf,yf):
		url = "http://chart.finance.yahoo.com/table.csv?s=" + self.name +"&a=" + str(ms-1) + "&b=" + str(ds) + "&c="+str(ys) + \
		"&d=" + str(mf-1) + "&e=" + str(df) + "&f="+str(yf) + "&g=d&ignore=.csv"
		
		data_response = requests.get(url)
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
		return roi_values[-1] 

		
	def reloadHistoryData(self, data):
		dateData = string.split(data,'\n')

		startAdjClose = 0
		isFirstDay = 1

		for currentDateData in reversed(dateData[1:]):
			dataFiels = string.split(currentDateData,",")
			if len(dataFiels) < 6:
				continue
			#Date,Open,High,Low,Close,Volume,Adj Close
			cur_date = datetime.datetime.strptime(dataFiels[0],"%Y-%m-%d").date()
			cur_open = dataFiels[1]
			cur_high = dataFiels[2]
			cur_low = dataFiels[3]
			cur_close = dataFiels[4]
			cur_vol = dataFiels[5]
			cur_adj_close = dataFiels[6]
			if isFirstDay == 1:
				startAdjClose = float(cur_adj_close)
				isFirstDay = 0
			cur_roi = (float(cur_adj_close) - startAdjClose)/startAdjClose
			dateDict = {cur_date:{"open":dataFiels[1],"high":dataFiels[2],"low":dataFiels[3],"close":dataFiels[4],"vol":dataFiels[5],"adj_close":dataFiels[6],"roi":cur_roi} }
			self.historical_data.update(dateDict)
		
			

	def printme(self):
		print "Ticker: %s \n" % self.name
		print "Available history data: \n"
		for dateData in self.historical_data:
			print "date %s  %s " % (dateData, self.historical_data[dateData])

	def getDataSize(self):
		return len(self.historical_data)

	def getName(self):
		return self.name

class PlotDrawer():
	def __init__(self,startDate, finishDate,maxValue,width = 1400.0, height = 800):
		self.width = width
		self.height = height
		date_count = finishDate - startDate
		self.xAxisStep = self.width /(date_count.days + 50)
		self.yScalePosNumber = maxValue + 2
		self.yAxisStep = self.height/self.yScalePosNumber
		self.startDate = startDate
		self.finishDate = finishDate

		root = Tkinter.Tk()	
		canv = Tkinter.Canvas(root,width = width,height = height,bg="white")
		self.canv = canv
		self.root = root
		self.colors = ["red", "blue","green", "yellow", "brown", "orange","cyan","purple","azure","pink",\
							 "coral","violet","maroon","navy","tan","gold","peru","spring green"]
		
	def drawXScale(self):
		self.canv.create_line(0,self.height-30,self.width,self.height-30,width=2,arrow=Tkinter.LAST) 
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
		self.canv.create_line(10,self.height-30,10,10,width=2,arrow=Tkinter.LAST)
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
			fill="blue", font=("Helvectica", "10"),anchor=Tkinter.W)


def getMaxFromTickers(tickers):
	allValues = []
	for ticker in tickers:
		allValues.append(ticker.getMaxROI())
	allValues.sort()
	return allValues[-1]

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
	parser.add_argument("--day_start","-ds",type=int, default=1, help="start period date")
	parser.add_argument("--month_start","-ms",type=int, default=1, help="start period month")
	parser.add_argument("--year_start","-ys",type=int, default=2014, help="start period year")
	parser.add_argument("--all_tickers","-at",type=int, default=0, help="show roi for the all 3-4 length ticker names")
#	parser.add_argument("--day_finish","-df",type=int, default=1, help="finish period date")
#	parser.add_argument("--month_finish","-mf",type=int, default=7, help="finish period month")
#	parser.add_argument("--year_finish","-yf",type=int, default=2016, help="finish period year")
#	parser.add_argument("--period_pace","-p",type=str, default="week", help="time periods on graph")
	args = parser.parse_args()

	startDate = datetime.date(args.year_start,args.month_start,args.day_start)
	finishDate = datetime.date.today()

	logger = logging.getLogger()
	logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

	tickerNames = ['IUSB', 'IYK','BND', 'SHY', 'TLT','IAGG','AGG','DIA']
	if args.all_tickers == 1:
		tickerNames = getAllPossibleTickerNames()
		tickers = []
	for ticker_name in tickerNames:
		try:
			currentTicker = Ticker(name=ticker_name)
			currentTicker.downloadHistorialData(startDate.day,startDate.month,startDate.year,finishDate.day,finishDate.month,finishDate.year)
			tickers.append(currentTicker)
			if len(tickers) > 10:
				break
		except Exception, e:
			pass
		
	maxValue = round(getMaxFromTickers(tickers)*100) + 1
	plot = PlotDrawer(startDate,finishDate, maxValue)
	plot.drawGraph(tickers)


if __name__ == "__main__":
    main()

