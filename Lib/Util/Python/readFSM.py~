"""
ReadFSM class reads text of lua files and generates a list of states and a list of states with their transitions, using the 'get_states' and 'get_transitions' methods, respectively.

Modified by adding NaoGoalie BodyFSM states, and getBGHfsm function changed to getBodyFSM, which returns a list containing NaoPlayer BodyFSM states and NaoGoalie BodyFSM states.
"""

import os

#Get user's ID
usr = str(os.getenv('USER'))

#NOTE!!! Works with code in Human-Controlled-Naos directory
game = open("/home/"+usr+"/Human-Controlled-Naos/Player/GameFSM/RoboCup/GameFSM.lua", "r").readlines()
body_player = open("/home/"+usr+"/Human-Controlled-Naos/Player/BodyFSM/NaoPlayer/BodyFSM.lua", "r").readlines()
body_goalie = open("/home/"+usr+"/Human-Controlled-Naos/Player/BodyFSM/NaoGoalie/BodyFSM.lua", "r").readlines()
head = open("/home/"+usr+"/Human-Controlled-Naos/Player/HeadFSM/NaoPlayer/HeadFSM.lua", "r").readlines()

class ReadFSM:

	def __init__(self, text):
	    self.text = text

	def get_states(self):

	    new_state = "sm = fsm.new"
	    add_state = "sm:add_state"
	    
	    # append lines
	    output = []
	    for line in self.text:
	    	if new_state in line or add_state in line:
	    	    output.append(line)
	    
	    output2 = []
	    for i in output:
	    	start = i.index("(") + 1
	    	end = i.index(")")
	    	output2.append(i[start:end])
	    	
	    return output2
    

	def get_transitions(self):

	    tran = "sm:set_transition"

	    # appends lines
	    output = []
	    for line in self.text:
		if tran in line:
		    output.append(line)

	    # selects transition string
	    output2 = []
	    for i in output:
		start = i.index("(") + 1
		end = i.index(")")
		output2.append(i[start:end])

	    # manipulates final string
	    # different files use different types of quotes
	    output3 = []
	    for i in output2:
		i = i.replace(', "', ':')
		i = i.replace('", ', ':')
		i = i.replace(", '", ":")
		i = i.replace("', ", ":")
		output3.append(i)

	    return output3
	

def getBGHfsm():
	g = ReadFSM(game)
	bp = ReadFSM(body_player)
	bg = ReadFSM(body_goalie)
	h = ReadFSM(head)

	# these are the lists of states
	game_states = g.get_states()

	bodyPlayer_states = bp.get_states()
	bodyGoalie_states = bg.get_states()

	head_states = h.get_states()
	head_trans = h.get_transitions()

	fsm_player = [game_states, bodyPlayer_states, head_states]
	fsm_goalie = [game_states, bodyGoalie_states, head_states]

	fsm_states = [fsm_player,fsm_goalie]
	return fsm_states
        
