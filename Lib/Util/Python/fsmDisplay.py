"""
Cara Takemoto
Caitlyn Clabaugh
Meagan Neal
Melanie Shafer
Kathryn Rath

Soccer tool!! 


"""
import math
import numpy as np
import scipy as sp
import Image as im
import shm
import tkMessageBox, tkFont, tkSimpleDialog, tkFileDialog, sys, os, ImageTk
from Tkinter import *
import readFSM

class fsmDisplay:

	def __init__(self, fsmInput, naoTeam, naoID):
		
		self.naoTeam = naoTeam
		self.naoID = naoID
		
		#Goalie has a different fsm
		if int(self.naoID) is 1:
			self.role = 'Goalie'
			fsmInput = fsmInput[1]
			self.states = [None] * 3
			for fsm in range(len(fsmInput)):
				self.states[fsm] = fsmInput[fsm]
		elif int(self.naoID) > 1:
			#Other player #s start from 1 in webots
			webots_num = int(self.naoID) - 1
			self.role = 'Player'+str(webots_num)
			fsmInput = fsmInput[0]
			self.states = [None] * 3
			for fsm in range(len(fsmInput)):
				self.states[fsm] = fsmInput[fsm]
	
		self.root = Tk()
		self.root.title("Team "+self.naoTeam+self.role)

		self.background = Canvas(self.root, width=500, height=300) 
		self.background.grid(row=0, column=0)

		#set first current states from shared memory
		self.currentState = [None] * 3
		self.currentIndex = [None] * 3
		
		#Create game fsm shared memory access
		usr = str(os.getenv("USER"))
		gcmName = "gcmFsm" + str(self.naoTeam) + str(self.naoID) + usr
		self.gcmFSM = shm.ShmWrapper(gcmName)

		#get current body state
		self.currentState[0] = self.shm2string(self.gcmFSM.get_game_state())
		self.currentState[1] = self.shm2string(self.gcmFSM.get_body_state())
		self.currentState[2] = self.shm2string(self.gcmFSM.get_head_state())

		#Create buttons on window
		self.draw_fsm()
	
		#create event that is constantly renewed to get new data
		self.root.after(0, self.update)

		self.root.mainloop()

	def update(self):

		#highlight current state
		self.highlight_current_state()
		
		#update buttons' statuses
		#self.button_status()
	
		#create event that is constantly renewed to get new data
		self.root.after(200, self.update)

		
	def draw_fsm(self):
		#create attribute to hold buttons
		self.stateB = [None] * len(self.states)
		#Go through the fsm machines and their states and figure out
		#where to display them
		col_num = 0
		for fsm in range(len(self.states)):
			row_num = 0
			self.stateB[fsm] = [0] * len(self.states[fsm])
			for state in range(len(self.states[fsm])):
				self.stateB[fsm][state] = Button(self.background, text=str(self.states[fsm][state]), width=20, background="white", disabledforeground='grey')
				self.stateB[fsm][state].grid(row=row_num, column=col_num)
				#bind button to a click event and pass in fsm and state info
				self.stateB[fsm][state].bind('<Button-1>', self.makeEventHandler(fsm, state))
				#All states not in body, and cetain states should be disabled
				if fsm != 1 or self.states[fsm][state] == 'bodyStart' or self.states[fsm][state] == 'bodyReady' or self.states[fsm][state] == 'bodyIdle' or self.states[fsm][state] == 'bodyStop' or self.states[fsm][state] == 'bodyAnnass':
					#configure button's state
					self.stateB[fsm][state].config(state=DISABLED)
				row_num += 1
			col_num += 1
	
	#Mouse event helper function
	#event, fsm, and state can be passed into change State		  
	def makeEventHandler(self, fsm, state):
		def stateEvent(event):
			if self.stateB[fsm][state]['state'] != 'disabled':
				self.changeState(fsm, state, event)
		return stateEvent

	def changeState(self, fsm, state, event):
		#Convert state str to int array as needed for shared memory
		newState = self.shm2array(self.states[fsm][state])

		#Change the memory segment
		if fsm is 1:
			self.gcmFSM.set_body_next_state(newState)
		else:
			print "Attempt to get state from undefined FSM"

	def highlight_current_state(self):
		#Find current states and highlight them
		for fsm in range(len(self.states)):
			#game state
			if fsm is 0:
				stateName = self.shm2string(self.gcmFSM.get_game_state())
			#body state
			elif fsm is 1:
				stateName = self.shm2string(self.gcmFSM.get_body_state())
			#head state
			elif fsm is 2:
				stateName = self.shm2string(self.gcmFSM.get_head_state())
			else:
				print "Attempt to get state from undefined FSM"

			#If first time being called, set first state
			if self.currentIndex[fsm] == None and self.currentState[fsm] in self.states[fsm]:
				self.currentIndex[fsm] = self.states[fsm].index(self.currentState[fsm])

			#highlight appropriate states
			if stateName in self.states[fsm]:
				#get button index of current state
				stateIndex = self.states[fsm].index(stateName)
				#unhighlight old current state
				self.stateB[fsm][self.currentIndex[fsm]].config(background="white")
				#highlight new current state as red
				self.stateB[fsm][stateIndex].config(background="red")

				#set new current states
				self.currentState[fsm] = stateName
				self.currentIndex[fsm] = stateIndex

			else:
				print "ERROR: UNKNOWN STATE"   
	
	def shm2string(self, shm):
		#for every element of shm array, convert to char
		#concatenate to full string
		return "".join([chr(int(i)) for i in shm])

	def shm2array(self, shm):
		#make string into array of floats
		#state names recognized in shared memory this way
		array = []
		for c in shm:
			i = ord(c)
			array.append(i)
		print array
		return array


test = fsmDisplay(readFSM.getBGHfsm(), sys.argv[1], sys.argv[2])

