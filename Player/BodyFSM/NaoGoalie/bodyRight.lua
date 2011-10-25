module(..., package.seeall);

require('Body')
require('walk')
require('vector')
require('util')
require('Config')
require('wcm')
require('Speak')
require('gcm')


-- maximum walk velocity
maxStep = 0.06;

function entry()
  print(_NAME.." entry");


end

function update()
  local t = Body.get_time();

  walk.set_velocity(0,-maxStep,0);

--continues until shared memory's next body state is changed
  nextState = gcm.get_fsm_body_next_state();
  if (nextState ~= _NAME) then
    return "done";
  end

end

function exit()
  print(_NAME..' exit');
end

