module(..., package.seeall);

require('Body')
require('gcm')

function entry()
  print(_NAME..' entry');

end

function update()

--go to next state!

  nextState = gcm.get_fsm_body_next_state();

  if (nextState == 'bodyApproach') then
    print('must approach');
    return 'approach';
  end
  if (nextState == 'bodyKick') then
    print('must kick');
    return 'kick';
  end
  if (nextState == 'bodyOrbit') then
    print('must orbit');
    return 'orbit';
  end
  if (nextState == 'bodyGotoCenter') then
    print('must go to center');
    return 'center';
  end
  if (nextState == 'bodyGotoBall') then
    print('must go to ball');
    return 'ball';
  end
  if (nextState == 'bodyPosition') then
    print('must position');
    return 'position';
  end
  if (nextState == 'bodyOrbitLeft') then
    print('must orbit to the left');
    return 'orbitL';
  end
  if (nextState == 'bodyOrbitRight') then
    print('must orbit to the right');
    return 'orbitR';
  end
  if (nextState == 'bodyLeft') then
    print('must go left');
    return 'left';
  end
  if (nextState == 'bodyHalt') then
    print('stop');
    return 'stop';
  end

end

function exit()
  print(_NAME..' exit');
end
