module(..., package.seeall);

require('Body')
require('Motion')
require('gcm')

function entry()
  print(_NAME..' entry');

  Motion.sm:set_state('stance');
end

function update()

--continues until shared memory's next body state is changed
  nextState = gcm.get_fsm_body_next_state();
  if (nextState ~= _NAME) then
    return 'done';
  end

end

function exit()
  print(_NAME..' exit');
end
