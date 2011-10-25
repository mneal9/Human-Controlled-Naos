'''
Meagan Neal

GUI to watch the motion finite state machine for a single robot specified by the system args (specifically, teamID and playerID).  

'''
import pyshm
import shm
import tkMessageBox, tkFont, tkSimpleDialog, tkFileDialog, sys, os
from Tkinter import *

class motionVisualizer:
	def __init__(self, naoTeam, naoID):

		self.root = Tk()
		
		self.naoTeam = naoTeam
		self.naoID = naoID

		if int(naoID) is 1:
			self.role = "Goalie"
		else:
			num = int(naoID)-1			
			self.role = str(num)

#Set size/color of canvas for GUI 
		self.width = 800
		self.height = 500
		self.canvas = Canvas(self.root, bg ='white', width=self.width, height=self.height)

#Placement for bubbles
		self.kick_coords = 590, 325, 690, 425
		self.kick_text_coords = 640, 375
		
		self.walk_coords = 430, 325, 530, 425
		self.walk_text_coords = 480, 375
		
		self.stance_coords = 270, 325, 370, 425
		self.stance_text_coords = 320, 375
		
		self.sit_coords = 110, 200, 210, 300
		self.sit_text_coords = 160, 250
		
		self.relax_coords = 270, 75, 370, 175
		self.relax_text_coords = 320, 125
		
		self.stand_up_coords = 430, 75, 530, 175
		self.stand_up_text_coords = 480, 125
		
		self.falling_coords = 590, 75, 690, 175
		self.falling_text_coords = 640, 125

#Placement for arrows
		self.sit2stance = 210, 300, 270, 325
		self.sit2relax = 200, 210, 270, 175
		self.relax2stance = 370, 175, 370, 325
		self.stance2walk = 370, 325,430, 325
		self.kick2walk = 590, 325, 530, 325
		self.standup2stance = 430, 175, 270, 425
		self.walk2falling = 530, 325, 590, 175
		self.falling2standup = 590, 175, 530, 175
		
#Draw a circle at specified location and text/font/size 
		self.kick = self.canvas.create_oval(self.kick_coords,fill='#6599FF',outline='#6599FF')
		self.kick_text = self.canvas.create_text(self.kick_text_coords, text = 'kick',font=("Helvectica", "20"))

		self.walk = self.canvas.create_oval(self.walk_coords,fill='#6599FF',outline='#6599FF')
		self.walk_text = self.canvas.create_text(self.walk_text_coords, text = 'walk',font=("Helvectica", "20"))

		self.stance = self.canvas.create_oval(self.stance_coords,fill='#6599FF',outline='#6599FF')
		self.stance_text = self.canvas.create_text(self.stance_text_coords, text = 'stance',font=("Helvectica", "20"))

		self.sit = self.canvas.create_oval(self.sit_coords,fill='#6599FF',outline='#6599FF')
		self.sit_text = self.canvas.create_text(self.sit_text_coords, text = 'sit',font=("Helvectica", "20"))

		self.relax = self.canvas.create_oval(self.relax_coords,fill='#6599FF',outline='#6599FF')
		self.relax_text = self.canvas.create_text(self.relax_text_coords, text = 'relax',font=("Helvectica", "20"))

		self.stand_up = self.canvas.create_oval(self.stand_up_coords,fill='#6599FF',outline='#6599FF')
		self.stand_up_text = self.canvas.create_text(self.stand_up_text_coords, text = 'stand up',font=("Helvectica", "20"),width=100)

		self.falling = self.canvas.create_oval(self.falling_coords,fill='#6599FF',outline='#6599FF')
		self.falling_text = self.canvas.create_text(self.falling_text_coords, text = 'falling',font=("Helvectica", "20"))

#Draw arrow at specified location
		'''self.sit2stance_arrow = self.canvas.create_line(self.sit2stance, arrow=LAST)
		self.stance2sit_arrow = self.canvas.create_line(self.sit2stance, arrow=FIRST)

		self.sit2relax_arrow = self.canvas.create_line(self.sit2relax, arrow=LAST)
		self.relax2sit_arrow = self.canvas.create_line(self.sit2relax, arrow=FIRST)

		self.relax2stance_arrow = self.canvas.create_line(self.relax2stance, arrow=LAST)

		self.stance2walk_arrow = self.canvas.create_line(self.stance2walk, arrow=LAST)
		self.walk2stance_arrow = self.canvas.create_line(self.stance2walk, arrow=FIRST)

		self.kick2walk_arrow = self.canvas.create_line(self.kick2walk, arrow=LAST)
		self.walk2kick_arrow = self.canvas.create_line(self.kick2walk, arrow=FIRST)

		self.stance2standup_arrow = self.canvas.create_line(self.stance2standup, arrow=FIRST)

		self.walk2falling_arrow = self.canvas.create_line(self.walk2falling, arrow=LAST)

		self.falling2standup_arrow = self.canvas.create_line(self.falling2standup, arrow=LAST)'''			

		self.canvas.pack()

		usr = str(os.getenv('USER'))
		self.gcmFsm_name = 'gcmFsm' + str(self.naoTeam)+str(self.naoID)+usr
		self.gcmFSM = shm.ShmWrapper(self.gcmFsm_name)

		self.root.title("Motion State for Nao "+str(self.role)+" on Team "+str(self.naoTeam))

		self.motionState = None
		self.stateBubble = None
		self.pastState = None
		self.stateArrow = None
		
		self.root.after(0, self.update)
	
		self.root.mainloop()                

#UPDATE...if state has changed, erase highlighting circle 
	def update(self):
                if self.stateBubble != None:
			self.pastState = self.motionState
                        self.canvas.delete(self.stateBubble)
						 				
		motion_state = "".join([chr(int(x)) for x in self.gcmFSM.get_motion_state()])

		#SET HIGHLIGHT TO CURRENT STATE
		#if current state is kick, highlight bubble
		if motion_state == "NaoKick":
			self.stateBubble = self.canvas.create_oval(self.kick_coords,fill=None,outline='#FF9900',width=5)
			self.motionState = "kick"
			if self.pastState == "walk":
				if self.stateArrow != None:
					self.canvas.delete(self.stateArrow)
				self.stateArrow = self.canvas.create_line(self.kick2walk, arrow=LAST)
			elif self.pastState is None:
				print("no past state yet")
		
		#if current state is sit, highlight bubble
		elif motion_state == "sit":
			self.stateBubble = self.canvas.create_oval(self.sit_coords,fill=None,outline='#FF9900',width=5)
			self.motionState = "sit"
			if self.pastState == "relax":
				if self.stateArrow != None:
					self.canvas.delete(self.stateArrow)
				self.stateArrow = self.canvas.create_line(self.sit2relax, arrow=FIRST)
			elif self.pastState == "stance":
				if self.stateArrow != None:
					self.canvas.delete(self.stateArrow)
				self.stateArrow = self.canvas.create_line(self.sit2stance, arrow=FIRST)
			elif self.pastState == None:
				print("no past state yet")

		#if current state is relax, highlight bubble
		elif motion_state == "relax":
			self.stateBubble = self.canvas.create_oval(self.relax_coords,fill=None,outline='#FF9900',width=5)
			self.motionState = "relax"
			if self.pastState == "sit":
				if self.stateArrow != None:
					self.canvas.delete(self.stateArrow)
				self.stateArrow = self.canvas.create_line(self.sit2relax, arrow=LAST)
			elif self.pastState == None:
				print("no past state yet")

		#if current state is fallling, highlight bubble
		elif motion_state == "falling":
			self.stateBubble = self.canvas.create_oval(self.falling_coords,fill=None,outline='#FF9900',width=5)
			self.motionState = "falling"
			if self.pastState == "walk":
				if self.stateArrow != None:
					self.canvas.delete(self.stateArrow)
				self.walk2falling_arrow = self.canvas.create_line(self.walk2falling, arrow=LAST)
			elif self.pastState == None:
				print("no past state yet")
		
		#if current state is walk, highlight bubble
		elif motion_state == "NaoWalk":
			self.stateBubble = self.canvas.create_oval(self.walk_coords,fill=None,outline='#FF9900',width=5)
			self.motionState = "walk"
			if self.pastState == "stance":
				if self.stateArrow != None:
					self.canvas.delete(self.stateArrow)
				self.stateArrow = self.canvas.create_line(self.stance2walk, arrow=LAST)
			elif self.pastState == None:
				print("no past state yet")


		#if current state is stance, highlight bubble
		elif motion_state == "stance":
			self.stateBubble = self.canvas.create_oval(self.stance_coords,fill=None,outline='#FF9900',width=5)
			self.motionState = "stance"
			if self.pastState == "sit":
				if self.stateArrow != None:
					self.canvas.delete(self.stateArrow)
				self.stateArrow = self.canvas.create_line(self.sit2stance, arrow=LAST)
			elif self.pastState == "relax":
				if self.stateArrow != None:
					self.canvas.delete(self.stateArrow)
				self.stateArrow = self.canvas.create_line(self.relax2stance, arrow=LAST)
			elif self.pastState == "standup":
				if self.stateArrow != None:
					self.canvas.delete(self.stateArrow)
				self.stateArrow = self.canvas.create_line(self.standup2stance, arrow=FIRST)
			elif self.pastState == None:
				print("no past state yet")

		#if current state is stand up, highlight bubble
		elif motion_state == "standup":
			self.stateBubble = self.canvas.create_oval(self.stand_up_coords,fill=None,outline='#FF9900',width=5)
			self.motionState = "standup"
			if self.pastState == "falling":
				if self.stateArrow != None:
					self.canvas.delete(self.stateArrow)
				self.falling2standup_arrow = self.canvas.create_line(self.falling2standup, arrow=LAST)
			elif self.pastState == None:
				print("no past state yet")

			
		#if current state does not exist, error
		else:
			print('got invalid motion state')
			
		#after 200mil sec UPDATE
                self.root.after(200, self.update)


win = motionVisualizer(sys.argv[1], sys.argv[2])			

