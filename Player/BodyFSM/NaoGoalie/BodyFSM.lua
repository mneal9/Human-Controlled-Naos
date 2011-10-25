module(..., package.seeall);

require('Body')
require('fsm')
require('gcm')

require('bodyIdle')
require('bodyStart')
require('bodyStop')
require('bodyReady')
require('bodyApproach')
require('bodyKick')
require('bodyOrbit')
require('bodyGotoCenter')
require('bodyPosition')
require('bodyControl')
require('bodyGotoBall')
require('bodyHalt')
require('bodyOrbitLeft')
require('bodyOrbitRight')
require('bodyRight')
require('bodyLeft')
require('bodyAnnass')

sm = fsm.new(bodyIdle); -- dont mess
sm:add_state(bodyStart); -- dont mess
sm:add_state(bodyStop); -- dont mess
sm:add_state(bodyReady); -- dont mess
sm:add_state(bodyAnnass);
sm:add_state(bodyControl); -- control state
sm:add_state(bodyApproach);
sm:add_state(bodyKick);
sm:add_state(bodyOrbit);
sm:add_state(bodyGotoCenter);
sm:add_state(bodyPosition);
sm:add_state(bodyGotoBall);
sm:add_state(bodyHalt);
sm:add_state(bodyOrbitLeft);
sm:add_state(bodyOrbitRight);
sm:add_state(bodyRight);
sm:add_state(bodyLeft);

sm:set_transition(bodyStart, 'done', bodyAnnass); -- ANNASS
sm:set_transition(bodyAnnass, 'done', bodyPosition); -- dont mess

-- transitions from control state to all other states
sm:set_transition(bodyControl, 'approach', bodyApproach);
sm:set_transition(bodyControl, 'kick', bodyKick);
sm:set_transition(bodyControl, 'orbit', bodyOrbit);
sm:set_transition(bodyControl, 'center', bodyGotoCenter);
sm:set_transition(bodyControl, 'position', bodyPosition);
sm:set_transition(bodyControl, 'ball', bodyGotoBall);
sm:set_transition(bodyControl, 'stop', bodyHalt);
sm:set_transition(bodyControl, 'orbitL', bodyOrbitLeft);
sm:set_transition(bodyControl, 'orbitR', bodyOrbitRight);
sm:set_transition(bodyControl, 'right', bodyRight);
sm:set_transition(bodyControl, 'left', bodyLeft);

-- transitions to control state
sm:set_transition(bodyPosition, 'done', bodyControl);
sm:set_transition(bodyApproach, 'done', bodyControl);
sm:set_transition(bodyKick, 'done', bodyControl);
sm:set_transition(bodyOrbit, 'done', bodyControl);
sm:set_transition(bodyApproach, 'done', bodyControl);
sm:set_transition(bodyGotoCenter, 'done', bodyControl);
sm:set_transition(bodyGotoBall, 'done', bodyControl);
sm:set_transition(bodyHalt, 'done', bodyControl);
sm:set_transition(bodyOrbitLeft, 'done', bodyControl);
sm:set_transition(bodyOrbitRight, 'done', bodyControl);
sm:set_transition(bodyRight, 'done', bodyControl);
sm:set_transition(bodyLeft, 'done', bodyControl);

-- if ball is lost (we might not be able to tell)
sm:set_transition(bodyGotoBall, 'ballLost', bodyPosition);
sm:set_transition(bodyOrbit, 'ballLost', bodyPosition);
sm:set_transition(bodyPosition, 'ballLost', bodyGotoBall);
sm:set_transition(bodyApproach, 'ballLost', bodyPosition);
sm:set_transition(bodyOrbitLeft, 'ballLost', bodyPosition);
sm:set_transition(bodyOrbitRight, 'ballLost', bodyPosition);

-- going straight to kick
sm:set_transition(bodyApproach, 'kick', bodyKick);

-- does this do anything??
sm:set_transition(bodyPosition, 'fall', bodyPosition);
sm:set_transition(bodyApproach, 'fall', bodyPosition);
sm:set_transition(bodyKick, 'fall', bodyPosition);
sm:set_transition(bodyRight, 'fall', bodyPosition);
sm:set_transition(bodyLeft, 'fall', bodyPosition);

-- set state debug handle to shared memory settor
sm:set_state_debug_handle(gcm.set_fsm_body_state, gcm.set_fsm_body_next_state);


function entry()
  sm:entry()
end

function update()
  sm:update();
end

function exit()
  sm:exit();
end
