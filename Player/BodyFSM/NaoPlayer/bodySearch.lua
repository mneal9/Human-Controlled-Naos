module(..., package.seeall);

require('Body')
require('walk')
require('vector')
require('Config')
require('wcm')
require('gcm')
require('Speak')


-- turn velocity
vSpin = 0.3;

direction = 1;

function entry()
  print(_NAME.." entry");

  -- set turn direction to last known ball position
  ball = wcm.get_ball();
  if (ball.y > 0) then
    direction = 1;
  else
    direction = -1;
  end

end

function update()

  local t = Body.get_time();

  ball = wcm.get_ball();

  -- search/spin until the ball is found
  walk.set_velocity(0, 0, direction*vSpin);

  if (t - ball.t < 0.1) then
    print 'Ball found'
  end

--continues until shared memory's next body state is changed
  nextState = gcm.get_fsm_body_next_state();
  if (nextState ~= _NAME) then
    if (t - ball.t > 0.1) then
      Speak.talk('Ball still lost')
    end
    return 'done'
  end

end

function exit()
  print(_NAME..' exit');
end
