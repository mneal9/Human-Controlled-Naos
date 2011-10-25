#!/usr/bin/env python

"""
Cara Takemoto
Caitlyn Clabaugh
September 2011

Visualization for the localization of the Nao Robots.

Notes:
PhotoImage class can read GIF and PGM/PPM images from files

window = Window("./scalefield.gif")

root.title("...")
"""
import numpy as np
import scipy as sp
import Image as im
import pyshm
import shm
import tkMessageBox, tkFont, tkSimpleDialog, tkFileDialog, sys, os, ImageTk
from Tkinter import *

class LocalVisualization:
	def __init__(self, bg_file, red_nao_img, blue_nao_img):
		#creates root, or master
		self.root = Tk()
		
		#Create Background
		self.bg = im.open(bg_file)
		self.DispBg = ImageTk.PhotoImage(self.bg)

		#Create red and blue nao images
		self.red_nao = PhotoImage(file=red_nao_img)
		self.blue_nao = PhotoImage(file=blue_nao_img)
		
		#save the width and height
		self.width, self.height = self.bg.size
		
		#Set title of the window
		self.root.title("Localization for Webots")
		
		#Create canvas
		self.canvas = Canvas(self.root, width=self.width, height=self.height)
		
		#Add background to canvas
		self.bgID = self.canvas.create_image(0, 0, anchor=NW, image=self.DispBg)
		
		#shift view so that you can't click off image
		self.canvas.xview_moveto(0.0)
		self.canvas.yview_moveto(0.0)
		self.canvas.pack(fill=BOTH, expand=True, anchor=NW)
		
		#text of coordinates.
		#Use StringVar so that variable automaticaly updates
		self.xycoortxt = StringVar()
		#labels where coor info will appear
		self.xycoor = Label(self.root, textvariable = self.xycoortxt, font=("Helvetica", 14))
		self.xycoor.pack(side=BOTTOM, anchor=E, padx=4, pady=4)
		
		##Checkbuttons in separate window
		self.checkb = Toplevel(master=self.root)
		self.checkb.title("Robot Viewing Options")
		self.checkb.protocol('WM_DELETE_WINDOW', self.noExit)
		
		#Show robot, and robot view
		
		#16 variables, 8 robots and 2 check boxes each
		self.showRobotView = [None] * 8
		self.showRobotPos = [None] * 8
		self.robotPos = [None] * 8
		self.robotView = [None] * 8
		#Create window to display robot view
		self.imgWin = [None] * 8

		#Set up view variables
		nao = 0
		for team in range(2):
			for player in range(1,5):
				#*****Replace with player role
				if player is 1:
					message1 = "Show " + str(team) + "G's Position"
					message2 = "Show " + str(team) + "G's View"
				else:
					message1 = "Show " + str(team) + str(player-1) + "'s Position"
					message2 = "Show " + str(team) + str(player-1) + "'s View"
			
				self.showRobotView[nao] = StringVar()
				self.showRobotView[nao].set("hidden")
				self.showRobotPos[nao] = StringVar()
				self.showRobotPos[nao].set("display")
			
				self.robotPos[nao] = Checkbutton(self.checkb, text=message1, variable=self.showRobotPos[nao],
					onvalue="display", offvalue="hidden")
				self.robotView[nao] = Checkbutton(self.checkb, text=message2, variable=self.showRobotView[nao],
					onvalue="display", offvalue="hidden")
			
		
				self.robotPos[nao].pack(side=TOP, anchor=E)
				self.robotView[nao].pack(side=TOP, anchor=W)

				#create window for images
				self.imgWin[nao] = Toplevel(master=self.root)
				#Make it so user cannot ex the toplevel window
				self.imgWin[nao].protocol('WM_DELETE_WINDOW', self.noExit)


				#Keep hidden
				self.imgWin[nao].withdraw()
				nao += 1
			

		#Events
		#bind the left mouse click with the findCoor method
		self.canvas.bind("<Button-1>", self.findCoor)
		
		#If window is resized, update width
		#The widget changed size (or location, on some platforms).
		#The new size is provided in the width and height attributes of the event object passed to the callback.
		self.canvas.bind("<Configure>", self.updateWH)
	
		self.setup()
		
		#create event that is constantly renewed to get new data
		self.root.after(0, self.update)

		#Keeps running, handles all events
		self.root.mainloop()

	def noExit(self):
		print "Please use checkboxes!"

	def setup(self):
		#Set up not related to window setup

		#Get user's ID
		usr = str(os.getenv('USER'))
		
		#Make memory segment names
		self.segNames = []
		#make list to hold shared memory files
		self.gcmTeam = []
		self.wcmRobot = []
		self.vcmImage = []
		self.teamID = []
		self.playerID = []
		
		nao = 0
		for team in range(2):
			for player in range(1,5):
				self.segNames.append(str(team)+str(player)+usr)
				self.gcmTeam.append(shm.ShmWrapper('gcmTeam'+self.segNames[nao]))
				self.wcmRobot.append(shm.ShmWrapper('wcmRobot'+self.segNames[nao]))
				self.vcmImage.append(shm.ShmWrapper('vcmImage'+self.segNames[nao]))
				self.teamID.append(team)
				if player is 1:
					self.playerID.append("G")
				else:
					self.playerID.append(player-1)
				nao += 1
		
		#initialize
		self.whichP = None
		self.robotPP = [None]*8
		self.pp = [None]*8
		self.headingVector = [None]*8
		self.tImgID = [None] * 8
		self.imgCanvas = [None] * 8
		self.topImg = [None] * 8

	def updateWH(self, event):
		#Called when the main window is changed
		#If window changes size
		if self.width != event.width and self.height != event.height:

		        #save the width and height of canvas
		        self.width = event.width
		        self.height = event.height

			#resize image
			self.DispBg = ImageTk.PhotoImage(self.bg.resize((self.width, self.height)))
			#Remove old background
			self.canvas.delete(self.bgID)
			#set new one
			self.bgID = self.canvas.create_image(0, 0, anchor=NW, image=self.DispBg)

	def findCoor(self, event):
		#remove previous position from canvas
		if self.whichP != None:
			self.canvas.delete(self.whichP)
		#To convert from window coordinates to canvas coordinates
		[x,y] = self.self.coorTranslate(self.canvas.canvasx(event.x), self.canvas.canvasy(event.y), "canvas2webots")

                self.xycoortxt.set( "x: "+str(x)+
                                   " y: "+str(y))
		self.whichP = self.canvas.create_oval(event.x, event.y,event.x+5, event.y+5, fill="blue")
		
	def update(self):
		#draw robots' positions on field
		self.drawPositions()
		
		for nao in range(8):
			self.dispVideo(nao)

		#reschedule update so it runs again
		self.root.after(200, self.update)
		
	def drawPositions(self):
		#For each robot
		for nao in range(8):
			
			#remove previous position from canvas
			if self.robotPP[nao] != None:
				self.canvas.delete(self.robotPP[nao])
			if self.headingVector[nao] != None:
				self.canvas.delete(self.headingVector[nao])
			
			#If the position should be displayed
			if self.showRobotPos[nao].get() == "display":
				#Get team color from shared memory
				team_color = self.gcmTeam[nao].get_color()
				if team_color > 0:
					robo_img = self.red_nao
					team_color = 'red'
				else:
					robo_img = self.blue_nao
					team_color = 'blue'
					
				
				#Get predicted position of robot from shared memory
				position = self.wcmRobot[nao].get_pose()
	
				self.pp[nao] = self.coorTranslate(position[0],position[1], "webots2canvas")
				#self.robotPP[nao] = self.canvas.create_oval(self.pp[nao][0]-5, self.pp[nao][1]-5, self.pp[nao][0]+5, self.pp[nao][1]+5, fill=team_color, outline=team_color) #if you just want circles as the nao icon
				self.robotPP[nao] = self.canvas.create_image(self.pp[nao][0], self.pp[nao][1], image = robo_img, anchor=SW) #if you want little robots as nao icons
	
				#Get heading from shared memory and draw vector in that direction
				heading_point = self.calcHeading(position, .5)
				self.headingVector[nao] = self.canvas.create_line(self.pp[nao][0], self.pp[nao][1], heading_point[0], heading_point[1], fill=team_color, arrow='last')
				
        def dispVideo(self, nao):
                #Function to display robot images

                if self.showRobotView[nao].get() == "hidden" and self.imgWin[nao].state() == "normal":
                        #Hides the window displaying the robot image
                        self.imgWin[nao].withdraw()
                elif self.showRobotView[nao].get() == "display" and self.imgWin[nao].state() == "withdrawn":
                        #Displays the image of the robot and creates window
                        self.imgWin[nao].deiconify()
                        yuyv = self.vcmImage[nao].get_yuyv()
                        rgbImg = self.yuyv2rgb(yuyv)
                        #display img somewhere (you could test with a different image)
                        #note rgb image size is (160,120)
                        #REPLACE
                        self.imgWin[nao].title(str(self.teamID[nao])+' '+str(self.playerID[nao]))
                        self.topImg[nao] = ImageTk.PhotoImage(rgbImg)
                        #Create canvas
                        self.imgCanvas[nao] = Canvas(self.imgWin[nao], width=160, height=120)
                        self.imgCanvas[nao].pack()
                
                        #Add background to canvas
                        self.tImgID[nao] = self.imgCanvas[nao].create_image(0, 0, anchor=NW, image=self.topImg[nao])
                        self.imgCanvas[nao].grid(row=0, column=0, columnspan=4)
                elif self.showRobotView[nao].get() == "display" and self.imgWin[nao].state() == "normal":
                        #Displays the image of the robot 
                        yuyv = self.vcmImage[nao].get_yuyv()
                        rgbImg = self.yuyv2rgb(yuyv)
                        #display img somewhere (you could test with a different image)
                        #note rgb image size is (160,120)
                        self.topImg[nao] = ImageTk.PhotoImage(rgbImg)
			#Delete old image
			self.imgCanvas[nao].delete(self.tImgID)
                        #update image to be new image
                        self.tImgID[nao] = self.imgCanvas[nao].create_image(0, 0, anchor=NW, image=self.topImg[nao])

	
	#HELPERS
	def yuyv2rgb(self, yuyv):

		#converts from yuyv shared mem format to rgb image
		#from text_image.py
		# data is actually int32 (YUYV format) not float64
		yuyv.dtype = 'uint32'
		# convert to uint8 to seperate out YUYV
		yuyv.dtype = 'uint8'
		# reshape to Nx4
		yuyv_u8 = yuyv.reshape((120, 80, 4))

		#convert from yuyv to yuv to rgb
		rgb = []
		for i in range(len(yuyv_u8)):
			row = []
			for j in range(len(yuyv_u8[0])):
				y1 = yuyv_u8[i][j][0]
				u = yuyv_u8[i][j][1]
				y2 = yuyv_u8[i][j][2]
				v = yuyv_u8[i][j][3]
				rgb1 = self.yuv2rgb(y1, u, v)
				row.append(rgb1)
				rgb2 = self.yuv2rgb(y2, u, v)
				row.append(rgb2)
			rgb.append(row)
		#convert rgblist of tuples of (r,g,b) to array
		rgbArr = np.asarray(rgb)
		#convert array to image and save
		img = im.fromarray(np.uint8(rgbArr))
		# YOU CAN USE img TO DISPLAY ANYWHERE I THINK!
		img.save('img.png')
		return img

	def yuv2rgb(self, y, u, v):
		c = y - 16
		d = u - 128
		e = v - 128
		R = (298 * c) + (409 * e) + 128
		G = (298 * c) - (100 * d) - (208 * e) + 128
		B = (298 * c) + (516 * d) + 128
		R >>= 8
		G >>= 8
		B >>= 8
		return (self.clip(R), self.clip(G), self.clip(B))

	def clip(self,v):
		v = max(v, 0)
		v = min(v, 255)
		return v

	# THIS IS NOT QUITE RIGHT...
	def calcHeading(self, pose, length):
		#get (x,y) is orgin because relative to robot
		x0 = 0
		y0 = 0
		#get theta from robot pose
		theta = pose[2]
		hyp = length
		#find new coord on heading vector
		b = np.sin(theta)*hyp
		c = np.cos(theta)*hyp
		x1 = x0 + c
		y1 = y0 + b
		#convert to canvas coord
		new_coord = self.coorTranslate(x1, y1, "webots2canvas")
		return new_coord

	def coorTranslate(self, valuex, valuey, which):
		#translate coordinates between the two coordinate systems

		#Min and Max values for canvas and webots
		webotsxMax = 7.4/2
		webotsxMin = -7.4/2
		webotsyMax = 5.4/2
		webotsyMin = -5.4/2	
		canvasxMax = self.width
		canvasxMin = 0
		canvasyMax = 0
		canvasyMin = self.height

		# Figure out how 'wide' each range is
		webotsxSpan = webotsxMax - webotsxMin
		webotsySpan = webotsyMax - webotsyMin
		canvasxSpan = canvasxMax - canvasxMin
		canvasySpan = canvasyMax - canvasyMin

		if which == "canvas2webots":
			# Convert the first range into a 0-1 range (float)
			xvalueScaled = float(valuex - canvasxMin) / float(canvasxSpan)
			yvalueScaled = float(valuey - canvasyMin) / float(canvasySpan)
			# Convert the 0-1 range into a value in the 2nd range.
			finalx = webotsxMin + (xvalueScaled * webotsxSpan)
			finaly = webotsyMin + (yvalueScaled * webotsySpan)
		else:
			# Convert the first range into a 0-1 range (float)
			xvalueScaled = float(valuex - webotsxMin) / float(webotsxSpan)
			yvalueScaled = float(valuey - webotsyMin) / float(webotsySpan)
			# Convert the 0-1 range into a value in the 2nd range.
			finalx = canvasxMin + (xvalueScaled * canvasxSpan)
			finaly = canvasyMin + (yvalueScaled * canvasySpan)
		return [finalx, finaly]
		
win = LocalVisualization("scalefield.gif", "red_robo.gif", "blue_robo.gif")

