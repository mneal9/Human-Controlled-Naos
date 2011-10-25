module(..., package.seeall);

require('Body')
require('walk')
require('vector')
require('Config')
require('wcm')

t0 = 0;

timeout = 3.0;

maxStep = 0.06;

rOrbit = 0.27;

rFar = 0.45;

thAlign = 10*math.pi/180;

tLost = 3.0;

direction = 1;

dribbleThres = 0.75;


function entry()
  print(_NAME.." entry");

  t0 = Body.get_time();
  attackBearing = wcm.get_attack_bearing();
  if (attackBearing > 0) then
    direction = 1;
  else
    direction = -1;
  end
end

function update()
  local t = Body.get_time();

  attackBearing, daPost = wcm.get_attack_bearing();

  ball = wcm.get_ball();

  ballR = math.sqrt(ball.x^2 + ball.y^2);
  ballA = math.atan2(ball.y, ball.x+0.10);
  dr = ballR - rOrbit;
  aStep = ballA - direction*(90*math.pi/180 - dr/0.40);
  vx = maxStep*math.cos(aStep);
  
  --Does setting vx to 0 improve performance of orbit?--
  vx = 0;
  
  vy = maxStep*math.sin(aStep);
  va = 0.75*ballA;

  walk.set_velocity(vx, vy, va);

  if (t - ball.t > tLost) then
    return 'ballLost';
  end

 --continues until shared memory's next body state is changed
  nextState = gcm.get_fsm_body_next_state();
  if (nextState ~= _NAME) then
    --BALL FAR
    if (ballR > rFar) then
      return 'done';
    end
    --ALL GOOD
    if (math.abs(attackBearing) < thAlign) then
      return 'done';
    end
    return 'done';
  end

end

function exit()
  print(_NAME..' exit');
end

