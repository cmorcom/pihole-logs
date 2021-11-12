import os
import sys
import argparse
from datetime import datetime
import statistics
from tkinter import Tk
from tkinter.filedialog import askopenfilename
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def promptForFile():
	Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
	filename = askopenfilename(filetypes=[("Comma-Separated Values", ".csv"), ("All Files","*")])
	print("Selected file:", filename)
	return filename

def readSpeed(s):
	num, unit = s.split(' ')
	num = float(num)
	if unit.startswith('G'):
		num *= 10**9
	if unit.startswith('M'):
		num *= 10**6
	if unit.startswith('K'):
		num *= 10**3
	num /= (10**6) #normalize to Mb/s
	return num

def getStatistics(title, data):
	hi = max(data)
	lo = min(data)
	mean = statistics.fmean(data)
	median = statistics.median(data)
	stdev = statistics.stdev(data)
	variance = statistics.variance(data)
	return f'{title}\nMax: {hi:.3f}\nMin: {lo:.3f}\nMean: {mean:.3f}\nMedian: {median:.3f}\nVariance: {variance:.3f}\nStd. Dev: {stdev:.3f}'

if __name__ == '__main__':
	# Parse commandline args
	parser = argparse.ArgumentParser(description='Process CSV from Pihole Grafana Dashboard.')
	parser.add_argument("-t", "--threshold", type=int, required=False, help="Minumum download speed threshold for data points.")
	parser.add_argument("-f", "--file", type=str, required=False, help="path of file to parse.")
	args = parser.parse_args()
	#parse threshold from args
	minval = 0
	if args.threshold is not None:
		print(f"Minumum Threshold for download speed = {args.threshold} Mbps.")
		minval = args.threshold
	#parse filename from args
	if args.file is not None and os.path.exists(args.file): filename = args.file
	else: filename = promptForFile()

	# Init storage vars
	linenum=0 # count line numbers in file
	X, download, upload = [], [], []
	with open(filename, 'r') as f:
		for row in f:
			try:
				time, down, up = row.strip('\n').split(',')
				#print(time, down, up)
				## get the speeds in Megabits per second
				if down == "": continue
				down = readSpeed(down)
				if down < minval: continue
				if up == "": up = '0 b/s'
				up = readSpeed(up)
				time = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
				#print(time, down, up)
				X.append(time)
				download.append(down)
				upload.append(up)
				linenum+=1
			except Exception as e:
				#Ignore lines that cause exceptions				
				print(e)
				print(f"Error: {linenum}: {row}")

	print(f"Read {linenum} lines from \"{filename}\"")
	
	####### PLOTTING GRAPH ######
	fig, ax = plt.subplots()
	# set x-axis 
	plt.xlabel("Timestamp")
	plt.xticks(rotation=75)
	ax.xaxis.set_major_locator(matplotlib.dates.DayLocator(interval=1))
	ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%d %b %y'))
	# set y-axis
	plt.ylabel("Speed (Megabits per second)")
	ax.set_ylim([0, 210])
	# show major gridlines
	plt.grid(color='lightgray', linestyle='-', linewidth=1)
	# plot dataset (shaded)
	ax.fill_between(X, download, color='green', linewidth=0.8, facecolor='darkseagreen', alpha=0.5, label='Download')
	ax.fill_between(X, upload, color='darkorange', linewidth=0.8, facecolor='orange', alpha=0.5, label='Upload')
	
	# show legend and other parameters
	plt.title(f"SpeedTest Logs from {X[0].strftime('%d %b %Y')} to {X[-1].strftime('%d %b %Y')}")
	props = dict(boxstyle='round', facecolor='wheat', alpha=0.75)
	ax.legend(loc='lower left')
	ax.text(1.01, 1.0, getStatistics("Download Statistics:", download), transform=ax.transAxes, fontsize=12, verticalalignment='top', bbox=props)
	ax.text(1.01, 0.5, getStatistics("Upload Statistics:", upload), transform=ax.transAxes, fontsize=12, verticalalignment='top', bbox=props)

	plt.show()