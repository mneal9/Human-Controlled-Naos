module(..., package.seeall);

require('Body')
require('fsm')
require('gcm')

require('bodyIdle')
require('bodyStart')
require('bodyStop')
require('bodyReady')
require('bodySearch')
require('bodyKick')
require('bodyGotoCenter')
require('bodyPosition')
require('bodyDribble')
require('bodyOrbit')
require('bodyApproach')

sm = fsm.new(bodyIdle); --no mess
sm:add_state(bodyStart); --no mess
sm:add_state(bodyStop); --no mess
sm:add_state(bodyReady); --no mess
sm:add_state(bodySearch);
sm:add_state(bodyApproach);
sm:add_state(bodyKick);
sm:add_state(bodyOrbit);
sm:add_state(bodyGotoCenter);
sm:add_state(bodyPosition);
sm:add_state(bodyDribble);

sm:set_transition(bodyStart, 'done', bodyPosition);

-- bodyPosition used when falling
sm:set_transition(bodyPosition, 'position2search', bodySearch);
sm:set_transition(bodyPosition, 'position2orbit', bodyOrbit);
sm:set_transition(bodyPosition, 'position2approach', bodyApproach);
sm:set_transition(bodyPosition, 'position2kick', bodyKick);
sm:set_transition(bodyPosition, 'position2center', bodyGotoCenter);
sm:set_transition(bodyPosition, 'position2dribble', bodyDribble);

sm:set_transition(bodySearch, 'search2position', bodyPosition);
sm:set_transition(bodySearch, 'search2orbit', bodyOrbit);
sm:set_transition(bodySearch, 'search2approach', bodyApproach);
sm:set_transition(bodySearch, 'search2kick', bodyKick);
sm:set_transition(bodySearch, 'search2center', bodyGotoCenter);
sm:set_transition(bodySearch, 'search2dribble', bodyDribble);

sm:set_transition(bodyApproach, 'approach2position', bodyPosition);
sm:set_transition(bodyApproach, 'approach2search', bodySearch);
sm:set_transition(bodyApproach, 'approach2orbit', bodyOrbit);
sm:set_transition(bodyApproach, 'approach2kick', bodyKick);
sm:set_transition(bodyApproach, 'approach2center', bodyGotoCenter);
sm:set_transition(bodyApproach, 'approach2dribble', bodyDribble);

sm:set_transition(bodyKick, 'kick2position', bodyPosition);
sm:set_transition(bodyKick, 'kick2search', bodySearch);
sm:set_transition(bodyKick, 'kick2orbit', bodyOrbit);
sm:set_transition(bodyKick, 'kick2approach', bodyApproach);
sm:set_transition(bodyKick, 'kick2center', bodyGotoCenter);
sm:set_transition(bodyKick, 'kick2dribble', bodyDribble);

sm:set_transition(bodyOrbit, 'orbit2position', bodyPosition);
sm:set_transition(bodyOrbit, 'orbit2search', bodySearch);
sm:set_transition(bodyOrbit, 'orbit2kick', bodyKick);
sm:set_transition(bodyOrbit, 'orbit2approach', bodyApproach);
sm:set_transition(bodyOrbit, 'orbit2center', bodyGotoCenter);
sm:set_transition(bodyOrbit, 'orbit2dribble', bodyDribble);

sm:set_transition(bodyGotoCenter, 'center2position', bodyPosition);
sm:set_transition(bodyGotoCenter, 'center2search', bodySearch);
sm:set_transition(bodyGotoCenter, 'center2orbit', bodyKick);
sm:set_transition(bodyGotoCenter, 'center2approach', bodyApproach);
sm:set_transition(bodyGotoCenter, 'center2orbit', bodyOrbit);
sm:set_transition(bodyGotoCenter, 'center2dribble', bodyDribble);

sm:set_transition(bodyDribble, 'dribble2position', bodyPosition);
sm:set_transition(bodyDribble, 'dribble2search', bodySearch);
sm:set_transition(bodyDribble, 'dribble2orbit', bodyKick);
sm:set_transition(bodyDribble, 'dribble2approach', bodyApproach);
sm:set_transition(bodyDribble, 'dribble2orbit', bodyOrbit);
sm:set_transition(bodyDribble, 'dribble2center', bodyGotoCenter);

-- set state debug handle to shared memory settor
--sm:set_state_debug_handle(gcm.set_fsm_body_state);

function entry()
  sm:entry()
end

function update()
  sm:update();
end

function exit()
  sm:exit();
end
