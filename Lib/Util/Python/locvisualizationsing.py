#!/usr/bin/env python

"""
Cara Takemoto
Caitlyn Clabaugh
September 2011

Visualization for the localization of the Nao Robots.

Notes:
PhotoImage class can read GIF and PGM/PPM images from files

window = Window("./scalefield.gif", "./red_robo.gif", "blue_robo.gif", 1, 1)

root.title("...")
"""
import numpy as np
import scipy as sp
import Image as im
import shm
import tkMessageBox, tkFont, tkSimpleDialog, tkFileDialog, sys, os, ImageTk
from Tkinter import *

class LocalVisualization:
        def __init__(self, bg_file, red_nao_img, blue_nao_img, naoTeam, naoID):
                #which nao are we looking at?
                self.naoTeam = naoTeam
                self.naoID = naoID
                #Convert to correct Webots role/number
                if naoID is 1:
                        self.role = 'Goalie'
                else:
                        webots_num = int(naoID)-1
                        self.role = 'Player '+str(webots_num)

                #creats root, or master
                self.root = Tk()
                
		#Make scalable
		self.root.resizable()

                #Create Background
                self.bg = im.open(bg_file)
		self.DispBg = ImageTk.PhotoImage(self.bg)
        
                #Create red and blue nao images
                self.red_nao = PhotoImage(file=red_nao_img)
                self.blue_nao = PhotoImage(file=blue_nao_img)
                
                #save the width and height
                self.width, self.height = self.bg.size
                
                #Create canvas
                self.canvas = Canvas(self.root, width=self.width, height=self.height)
        
                #Add background to canvas
                self.bgID = self.canvas.create_image(0, 0, anchor=NW, image=self.DispBg)
                
                #shift view so that you can't click off image
                self.canvas.xview_moveto(0.0)
                self.canvas.yview_moveto(0.0)
		#pack canvas and make it expand with window
                self.canvas.pack(fill=BOTH, expand=True, anchor=NW)
                
                #text of coordinates.
                #Use StringVar so that variable automaticaly updates
                self.xycoortxt = StringVar()
                #labels where coor info will appear
                self.xycoor = Label(self.root, textvariable = self.xycoortxt)
                self.xycoor.pack(side=BOTTOM, anchor=SE, padx=2, pady=2)
                #text of robot coordinates
                #Use StringVar so that variable automaticaly updates
                self.robocoortxt = StringVar()
                #labels where coor info will appear
                self.robocoor = Label(self.root, textvariable = self.robocoortxt)
                self.robocoor.pack(side=BOTTOM, anchor=NE, padx=2, pady=2)
                
                ##Checkbuttons 
                #Show robot view
                self.showRobotView = StringVar()
                self.showRobotView.set("hidden")
                self.c1 = Checkbutton(self.root, text="Show Nao Camera", variable=self.showRobotView,
                                 onvalue="display", offvalue="hidden")

                self.c1.pack(side=BOTTOM, anchor=W, padx=4, pady=4)
                
                #Set title of the window
                self.root.title("Localization for Team "+str(self.naoTeam)+' '+str(self.role))
                
		#Create window to display robot view
		self.imgWin = Toplevel(master=self.root)

		#Make it so user cannot ex the toplevel window, but removes title and cannot move window
		#self.imgWin.overrideredirect(1)
		self.imgWin.protocol('WM_DELETE_WINDOW', self.noExit)

		#Keep hidden
		self.imgWin.withdraw()

                ##EVENTS
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
                #Set up not related to window set up
                
                #Get user's ID
                usr = str(os.getenv('USER'))
        
                #Make shared memory segment
                gtSegName = 'gcmTeam'+str(self.naoTeam)+str(self.naoID)+usr
                wrSegName = 'wcmRobot'+str(self.naoTeam)+str(self.naoID)+usr
                wbSegName = 'wcmBall' +str(self.naoTeam)+str(self.naoID)+usr
                viSegName = 'vcmImage' +str(self.naoTeam)+str(self.naoID)+usr
                self.gcmTeam = shm.ShmWrapper(gtSegName)
                self.wcmRobot = shm.ShmWrapper(wrSegName)
                self.wcmBall = shm.ShmWrapper(wbSegName)
                self.vcmImage = shm.ShmWrapper(viSegName)
                
                
                #initialize
                self.whichP = None
                self.robotPP = None
                self.ballPP = None
                self.headingVector = None
                
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
                #To convert from window coordinates to canvas coordinates, and from canvas to webots
		[x,y] = self.coorTranslate(self.canvas.canvasx(event.x), self.canvas.canvasy(event.y), "canvas2webots")

                self.xycoortxt.set( "x: "+str(x)+
                                   " y: "+str(y))
                self.whichP = self.canvas.create_oval(event.x, event.y,event.x+5, event.y+5, fill="blue")
                
        def update(self):
                #draw robot and ball predicted positions on field
                self.drawPositions()
        
                #show live image stream of what robot is seeing
                self.dispVideo()

                #reschedule update so it runs again
                self.root.after(200, self.update)
        
        def drawPositions(self):
                #remove previous positions from canvas
                if self.robotPP != None:
                        self.canvas.delete(self.robotPP)
                if self.ballPP != None:
                        self.canvas.delete(self.ballPP)
                if self.headingVector != None:
                        self.canvas.delete(self.headingVector)
        
                #Get team color from shared memory
                team_color = self.gcmTeam.get_color()
                if team_color > 0:
                        robo_img = self.red_nao
                        team_color = 'red'
                        other_team_color = 'blue'
                else:
                        robo_img = self.blue_nao
                        team_color = 'blue'
                        other_team_color = 'red'

                #Get predicted position of robot from shared memory
                positionR = self.wcmRobot.get_pose()
        
                #Get predicted position of ball from shared memory
                positionB = self.wcmBall.get_xy()
                #Turn into global coords
                positionBG = self.pose_global([positionB[0], positionB[1], 0], [positionR[0], positionR[1], positionR[2]])
        
                #DRAW IT!
                #robot...
                self.ppR = self.coorTranslate(positionR[0],positionR[1], "webots2canvas")
                #self.robotPP = self.canvas.create_oval(self.ppR[0]-5, self.ppR[1]-5, self.ppR[0]+5, self.ppR[1]+5, fill=team_color) #if you just want a simple dot as the robot icon
                self.robotPP = self.canvas.create_image(self.ppR[0], self.ppR[1], image = robo_img, anchor=SW) #if you want a robot as the robot icon
                #ball...
                self.ppB = self.coorTranslate(positionBG[0],positionBG[1], "webots2canvas")
                #self.ppB = self.coorTranslate(0,0, "webots2canvas") #test position = WORKS!!!
                self.ballPP = self.canvas.create_oval(self.ppB[0]-5, self.ppB[1]-5,self.ppB[0]+5, self.ppB[1]+5, fill='orange', outline='orange')
                #heading...
                heading_point = self.calcHeading(positionR, .5)
                self.headingVector = self.canvas.create_line(self.ppR[0], self.ppR[1], heading_point[0], heading_point[1], fill=team_color, arrow='last')
        
                #set text to display coordinates
                self.robocoortxt.set("Predicted Pos ("+str(positionR[0])+", "+str(positionR[1])+")")                
        
        def dispVideo(self):
                #Function to display robot images

                if self.showRobotView.get() == "hidden" and self.imgWin.state() == "normal":
                        #Hides the window displaying the robot image
                        self.imgWin.withdraw()
                elif self.showRobotView.get() == "display" and self.imgWin.state() == "withdrawn":
                        #Displays the image of the robot and creates window
                        self.imgWin.deiconify()
                        yuyv = self.vcmImage.get_yuyv()
                        rgbImg = self.yuyv2rgb(yuyv)
                        #display img somewhere (you could test with a different image)
                        #note rgb image size is (160,120)
                        
                        self.imgWin.title(str('T: ' + self.naoTeam)+' '+str(self.role))
                        self.topImg = ImageTk.PhotoImage(rgbImg)
                        #Create canvas
                        self.imgCanvas = Canvas(self.imgWin, width=160, height=120)
                        self.imgCanvas.pack()
                
                        #Add background to canvas
                        self.tImgID = self.imgCanvas.create_image(0, 0, anchor=NW, image=self.topImg)
                        self.imgCanvas.grid(row=0, column=0, columnspan=4)
                elif self.showRobotView.get() == "display" and self.imgWin.state() == "normal":
                        #Displays the image of the robot 
                        yuyv = self.vcmImage.get_yuyv()
                        rgbImg = self.yuyv2rgb(yuyv)
                        #display img somewhere (you could test with a different image)
                        #note rgb image size is (160,120)
                        self.topImg = ImageTk.PhotoImage(rgbImg)
			#Delete old image
			self.imgCanvas.delete(self.tImgID)
                        #update image to be new image
                        self.tImgID = self.imgCanvas.create_image(0, 0, anchor=NW, image=self.topImg)

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
                #img.save('img.png') #just saved to test out...
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
        
        def pose_global(self, pRelative, pose):
                #converts relative coords (pRelative) to global through robots pose 
                #taken from util.lua
        
                ca = np.cos(pose[2])
                sa = np.sin(pose[2])
                return [pose[0] + ca*pRelative[0] - sa*pRelative[1],
                        pose[1] + sa*pRelative[0] + ca*pRelative[1],
                        pose[2] + pRelative[2]]

	def coorTranslate(self, valuex, valuey, which):
		#translate coordinates between the two coordinate systems

		#Min and Max values for canvas and webots
		webotsxMax = 7.4/2
		webotsxMin = -7.4/2
		webotsyMax = 5.4/2
		webotsyMin = -5.4/2	
		canvasxMax = self.width
		canvasxMin = 0
		#min is actually a max
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


"""
        def coorTranslate(self, x, y, which):
                #convert coordinates in webots coor sys to canvas
                #canvas coor start in TL, range - x: 0 - self.width, y: 0 - self.height
                #webots 7.4 by 5.4
		if which == "webots2canvas":
		        #First scale to new coor sys, y is negative because the y values get greater
		        #as they move down the axis instead of lesser
		        newX = x * (self.width/7.4)
		        newY = y * -(self.height/5.4)
		        
		        #Translate origin
		        #vector from center origin to TL origin
		        transV = [self.width/2 - 0, self.height/2 - 0]
		        newX = newX + transV[0]
		        newY = newY + transV[1]
        
       		else:
		        #Min and Max values for canvas and webots
			webotsxMax = 7.4/2
			webotsxMin = -7.4/2
			webotsyMax = 5.4/2
			webotsyMin = -5.4/2	
			canvasxMax = self.width
			canvasxMin = 0
			canvasyMax = 0
			canvasyMin = -self.height

			# Figure out how 'wide' each range is
			webotsxSpan = webotsxMax - webotsxMin
			webotsySpan = webotsyMax - webotsyMin
			canvasxSpan = canvasxMax - canvasxMin
			canvasySpan = canvasyMax - canvasyMin

			# Convert the first range into a 0-1 range (float)
			xvalueScaled = float(x - canvasxMin) / float(canvasxSpan)
			yvalueScaled = float(-y - canvasyMin) / float(canvasySpan)
			# Convert the 0-1 range into a value in the 2nd range.
			newX = webotsxMin + (xvalueScaled * webotsxSpan)
			newY = webotsyMin + (yvalueScaled * webotsySpan)
                
                return [newX, newY]
"""


win = LocalVisualization("scalefield.gif", "red_robo.gif", "blue_robo.gif", sys.argv[1], sys.argv[2])

