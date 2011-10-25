module(..., package.seeall);

require('Body')
require('walk')
require('vector')
require('Config')
require('wcm')
require('gcm')

maxStep = 0.06;

rClose = 0.30;

tLost = 3.0;


function entry()
  print(_NAME.." entry");

end

function update()
  
  ball = wcm.get_ball();
  pose = wcm.get_pose();
  ballGlobal = util.pose_global({ball.x, ball.y, 0}, {pose.x, pose.y, pose.a});
  tBall = Body.get_time() - ball.t;

  id = gcm.get_team_player_id();
  role = gcm.get_team_role();
  if id == 1 then
    -- goalie
    centerPosition = vector.new(wcm.get_goal_defend());
    centerPosition[1] = centerPosition[1] - util.sign(centerPosition[1]) * .5;
    -- face center
    centerPosition[3] = math.atan2(centerPosition[2], 0 - centerPosition[1]);

    -- use stricter thresholds
    thAlign = 10*math.pi/180;
    rClose = .1;
  else
    if (role == 2) then
      -- defend
      centerPosition = vector.new(wcm.get_goal_defend())/2.0;
    elseif (role == 3) then
      -- support
      centerPosition = vector.zeros(3);
    else
      -- attack
      centerPosition = vector.new(wcm.get_goal_attack())/2.0;
    end
  end

  centerRelative = util.pose_relative(centerPosition, {pose.x, pose.y, pose.a});
  rCenterRelative = math.sqrt(centerRelative[1]^2 + centerRelative[2]^2);

  vx = maxStep * centerRelative[1]/rCenterRelative;
  vy = maxStep * centerRelative[2]/rCenterRelative;
  if id == 1 then
    va = .2 * centerRelative[3];
  else
    va = .2 * math.atan2(centerRelative[2], centerRelative[1]);
  end
  walk.set_velocity(vx, vy, va);

  ballR = math.sqrt(ball.x^2 + ball.y^2);

--continues until shared memory's next body state is changed
  nextState = gcm.get_fsm_body_next_state();
  if (nextState ~= _NAME) then
    return 'done';
  end

end

function exit()
  print(_NAME..' exit');
end

