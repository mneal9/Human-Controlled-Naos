module(..., package.seeall);

require('Body')
require('Kinematics')
require('Config');
require('vector')
require('mcm')
require('unix')

active = true;
--stopRequest = false;
stopRequest = 2;

-- Walk Parameters
tStep = Config.walk.tStep;
tZmp = Config.walk.tZmp;
bodyHeight = Config.walk.bodyHeight;
stepHeight = Config.walk.stepHeight;
footY = Config.walk.footY;
supportX = Config.walk.supportX;
supportY = Config.walk.supportY;
hipRollCompensation = Config.walk.hipRollCompensation;
tSensorDelay = Config.walk.tSensorDelay or 0.035;
maxX = Config.walk.maxX or {-.06, .08};
maxY = Config.walk.maxY or {-.04, .04};
maxZ = Config.walk.maxZ or {-.4, .4};

maxVelX = Config.walk.maxVelX or {-.02, .03};
maxVelY = Config.walk.maxVelY or {-.015, .015};
maxVelZ = Config.walk.maxVelZ or {-.15, .15};

--Check to make sure robot does not stop at innapropriate times--
--stopping = false;

--Variables to help make robot stand still after falling, standing--
still = false;
delay = 0;


t0 = 0;maxX = Config.walk.maxX or {-.06, .08};

iStep0 = -1;

-- For generalized support for multiple robots
qLArm=Config.walk.qLArm;
qRArm=Config.walk.qRArm;

--Single support phases
ph1Single = Config.walk.phSingle[1];
ph2Single = Config.walk.phSingle[2];

--ZMP shift phases
ph1Zmp = ph1Single;
ph2Zmp = ph2Single;

uTorso = vector.new({supportX, 0, 0});
uLeft = vector.new({0, footY, 0});
uRight = vector.new({0, -footY, 0});

pLLeg = vector.new({0, footY, 0, 0,0,0});
pRLeg = vector.new({0, -footY, 0, 0,0,0});
pTorso = vector.new({supportX, 0, bodyHeight, 0,0,0});

velCurrent = vector.new({0, 0, 0});
velCommand = vector.new({0, 0, 0});

uTorsoShift = vector.new({0, 0, 0});
aShiftFilterX = 1 - math.exp(-.010/0.2);
aShiftFilterY = 1 - math.exp(-.010/0.4);

torsoSensorGainX=Config.walk.torsoSensorGainX;
torsoSensorGainY=Config.walk.torsoSensorGainY;

torsoSensorGainY=0.5;

--ZMP exponential coefficients:
aXP = 0;
aXN = 0;
aYP = 0;
aYN = 0;

--Gyro stabilization variables

ankleShift = vector.new({0, 0});
kneeShift = 0;
hipShift = vector.new({0,0});
armShift = vector.new({0, 0});

--Gyro stabilization parameters

ankleImuParamX = Config.walk.ankleImuParamX;
ankleImuParamY = Config.walk.ankleImuParamY;
kneeImuParamX = Config.walk.kneeImuParamX;
hipImuParamY = Config.walk.hipImuParamY;

--active = true;
iStep0 = -1;
iStep = 0;
t0 = Body.get_time();
delay2=0;
delaycount=0;
lastRoll=0;

initdone=false;
initial_step=0;

function zmp_solve(zs, z1, z2, x1, x2)
  --[[
    Solves ZMP equation:
    x(t) = z(t) + aP*exp(t/tZmp) + aN*exp(-t/tZmp) - tZmp*mi*sinh((t-Ti)/tZmp)
    where the ZMP point is piecewise linear:
    z(0) = z1, z(T1 < t < T2) = zs, z(tStep) = z2
  --]]
  local T1 = tStep*ph1Zmp;
  local T2 = tStep*ph2Zmp;
  local m1 = (zs-z1)/T1;
  local m2 = -(zs-z2)/(tStep-T2);

  local c1 = x1-z1+tZmp*m1*math.sinh(-T1/tZmp);
  local c2 = x2-z2+tZmp*m2*math.sinh((tStep-T2)/tZmp);
  local expTStep = math.exp(tStep/tZmp);
  local aP = (c2 - c1/expTStep)/(expTStep-1/expTStep);
  local aN = (c1*expTStep - c2)/(expTStep-1/expTStep);
  return aP, aN;
end

function zmp_com(ph)
  local com = vector.new({0, 0, 0});
  expT = math.exp(tStep*ph/tZmp);
  com[1] = uSupport[1] + aXP*expT + aXN/expT;
  com[2] = uSupport[2] + aYP*expT + aYN/expT;
  if (ph < ph1Zmp) then
    com[1] = com[1] + m1X*tStep*(ph-ph1Zmp)
              -tZmp*m1X*math.sinh(tStep*(ph-ph1Zmp)/tZmp);
    com[2] = com[2] + m1Y*tStep*(ph-ph1Zmp)
              -tZmp*m1Y*math.sinh(tStep*(ph-ph1Zmp)/tZmp);
  elseif (ph > ph2Zmp) then
    com[1] = com[1] + m2X*tStep*(ph-ph2Zmp)
              -tZmp*m2X*math.sinh(tStep*(ph-ph2Zmp)/tZmp);
    com[2] = com[2] + m2Y*tStep*(ph-ph2Zmp)
              -tZmp*m2Y*math.sinh(tStep*(ph-ph2Zmp)/tZmp);
  end

  com[3] = .5*(uLeft[3] + uRight[3]);
  return com;
end

function foot_phase(ph)
  -- Computes relative x,z motion of foot during single support phase
  -- phSingle = 0: x=0, z=0, phSingle = 1: x=1,z=0
  phSingle = math.min(math.max(ph-ph1Single, 0)/(ph2Single-ph1Single),1);
  local phSingleSkew = phSingle^0.8 - 0.17*phSingle*(1-phSingle);
  local xf = .5*(1-math.cos(math.pi*phSingleSkew));
  local zf = .5*(1-math.cos(2*math.pi*phSingleSkew));
  return xf, zf;
end

function entry()
  print ("walk entry")
  local dpLeft = Kinematics.lleg_torso(Body.get_lleg_position());
  local dpRight = Kinematics.rleg_torso(Body.get_rleg_position());
  uLeft = pose_global({dpLeft[1], dpLeft[2], dpLeft[6]}, uTorso);
  uRight = pose_global({dpRight[1], dpRight[2], dpRight[6]}, uTorso);
 
  --SJ: there is some discontinuity after kicking
  uLeft = pose_global(vector.new({-supportX, footY, 0}),uTorso);
  uRight = pose_global(vector.new({-supportX, -footY, 0}),uTorso);

  uLeft1 = uLeft;
  uLeft2 = uLeft;
  uRight1 = uRight;
  uRight2 = uRight;
  uTorso1 = uTorso;
  uTorso2 = uTorso;
  uSupport = uTorso;

  pLLeg = vector.new{uLeft[1], uLeft[2], 0, 0, 0, uLeft[3]};
  pRLeg = vector.new{uRight[1], uRight[2], 0, 0, 0, uRight[3]};
  pTorso = vector.new{uTorso[1], uTorso[2], bodyHeight, 0, 0, uTorso[3]};
   
  qLegs = Kinematics.inverse_legs(pLLeg, pRLeg, pTorso, 0);
  -- This assumes RLeg follows LLeg in servo order:
  Body.set_lleg_command(qLegs);
  -- Arms
  Body.set_larm_command(qLArm);
  Body.set_larm_hardness(.2);
  Body.set_rarm_command(qRArm);
  Body.set_rarm_hardness(.2);
end

function update()
  if (not active) then return end

  ------------------------------
  --Update for test_kick.--
  ------------------------------
  tStep = Config.walk.tStep;

  ph1Single = Config.walk.phSingle[1];
  ph2Single = Config.walk.phSingle[2];
  ph1Zmp = ph1Single;
  ph2Zmp = ph2Single;

  stepHeight = Config.walk.stepHeight;
  bodyHeight = Config.walk.bodyHeight;
  footY = Config.walk.footY;
  supportX = Config.walk.supportX;
  supportY = Config.walk.supportY;

  imuOn = Config.walk.imuOn or false;
  ankleImuParamX = Config.walk.ankleImuParamX;
  ankleImuParamY = Config.walk.ankleImuParamY;
  kneeImuParamX = Config.walk.kneeImuParamX;
  hipImuParamY = Config.walk.hipImuParamY;

  jointFeedbackOn = Config.walk.jointFeedbackOn or false;
  torsoSensorGainX=Config.walk.torsoSensorGainX or .5;
  torsoSensorGainY=Config.walk.torsoSensorGainY or .5;
  if not jointFeedbackOn then
    torsoSensorGainX = 0;
    torsoSensorGainY = 0;
  end

  maxX = Config.walk.maxX or {-.06, .08};
  maxY = Config.walk.maxY or {-.04, .04};
  maxZ = Config.walk.maxZ or {-.4, .4};

  fsrOn = Config.walk.fsrOn or false;
  --------------------------------------
  

  t = Body.get_time();
  iStep, ph = math.modf((t-t0)/tStep);
  --[[
  if fsrOn thend
     local fl=Body.get_sensor_fsrLeft();
     local fr=Body.get_sensor_fsrRight();
	
     local fls=fl[1]+fl[2]+fl[3]+fl[4];
     local frs=fr[1]+fr[2]+fr[3]+fr[4];
	   --print(fls,frs);
	--]]

     
     --local fsr_threshold= Config.walk.fsr_threshold or 0.3;

--[[
	--Check if the foot is mid-air during the single support phase
  if ph>0.47 and ph<0.53 and delay2==0 then 
    local supportLegTemp = iStep % 2; 
			if supportLegTemp==0 and frs>fsr_threshold then --left foot 
			  delaycount=delaycount+1;
			  print("Early landing",delaycount)
			elseif supportLegTemp==1 and fls>fsr_threshold then
			  delaycount=delaycount+1;
		 	   print("Early landing",delaycount)
			else
			  delaycount=0;
			end
		end
	
--]]


--[[
---This is the delay code Spencer was working on.  THIS block is the good stuff.--
	tDelayBalance= Config.walk.tDelayBalance or 1.0;
	gyroDiffThresh = 160;
  imuGyr = Body.get_sensor_imuGyr();  
  gyro_roll=-(imuGyr[1]-gyro0[1]);
  gyro_pitch=-(imuGyr[2]-gyro0[2]);
  --print(string.format('Roll: %.5f\t Pitch: %.5f', gyro_roll, gyro_pitch));
  currentRoll = gyro_roll;
  if math.abs(lastRoll - currentRoll) > gyroDiffThresh and stopping==true then
  	print "Delaying!!!";
  	delaycount=delaycount+1;
  end
  lastRoll=currentRoll;
  --]]
  
  --[[
  roll_threshold=350;
  pitch_threshold=1000;
  --IMU stabilization values. Stop when gyro detects beyond a certain range.--
  if math.abs(gyro_roll)> roll_threshold then delay2=1.0;end
  if math.abs(gyro_pitch)> pitch_threshold then delay2=1.0;end
--]]


--[[
--delay block, if delay is ever reinstated.  This is what you should re-enable.--
  if delaycount>0 and delay2==0 and stopping==true then 
	delay2=tDelayBalance;
	delaycount=0;
  end
  
  if stopping==false then
  	stopping=true;
  end
  
  --]]

  --Stop when stop request is received--
  if (iStep > iStep0) and(stopRequest==2) then
      stopRequest = 0;
      active = false;
      return "stop";
  end

--[[
  --Don't delay anything if the walk hasn't been initialized once
  if initdone==false then delay2=0; end
  if fsrOn then
      --Wait a bit if the foot landed prematurely
		if (iStep > iStep0) and delay2>0 then
	 	   t0=t0+ ph*tStep;
	 	   delay2=math.max(0,delay2-ph*tStep)
			 ph=1.0;
			 iStep=iStep0;
		end
  end
--]]

  if (iStep > iStep0) then
    --initdone=true; --Walk has been initialized at least once.
    if still==false then
	    update_velocity();
	  elseif delay <= 0 then 
			delay=Config.walk.delay or 2;
			velCurrent[1]=0;
			velCurrent[2]=0;
			velCurrent[3]=0;			
		end
		
		if delay > 0 then
			delay=delay-1;
			if delay<=0 then
				still=false;
			end
		end
		
    -- New step
    iStep0 = iStep;
    supportLeg = iStep % 2; -- 0 for left support, 1 for right support

    uLeft1 = uLeft2;
    uRight1 = uRight2;
    uTorso1 = uTorso2;

--Code to enable stopping with feet together.  Currently disabled.--

    if (stopRequest==1) then  --Final step
      stopRequest=2;
      velCurrent=vector.new({0,0,0});
    end
--[[
      if supportLeg == 0 then
        -- Left support
        uRight2 = pose_global({0,-2*footY,0}, uLeft1);
      else
        -- Right support
        uLeft2 = pose_global({0,2*footY,0}, uRight1);
      end
-]]
   -- else --Normal working
    if supportLeg == 0 then
      -- Left support
      uRight2 = step_right_destination(velCurrent, uLeft1, uRight1);
    else
      -- Right support
      uLeft2 = step_left_destination(velCurrent, uLeft1, uRight1);
    end

    if supportLeg == 0 then
        uSupport = pose_global({supportX, supportY, 0}, uLeft);

        Body.set_lleg_hardness(.7*vector.ones(6));
        Body.set_rleg_hardness(.5*vector.ones(6));
    else
        -- Right support
        uSupport = pose_global({supportX, -supportY, 0}, uRight);

        Body.set_lleg_hardness(.5*vector.ones(6));
        Body.set_rleg_hardness(.7*vector.ones(6));
    end

    uTorso2 = step_torso(uLeft2, uRight2);

    --Compute ZMP coefficients
    m1X = (uSupport[1]-uTorso1[1])/(tStep*ph1Zmp);
    m2X = (uTorso2[1]-uSupport[1])/(tStep*(1-ph2Zmp));
    m1Y = (uSupport[2]-uTorso1[2])/(tStep*ph1Zmp);
    m2Y = (uTorso2[2]-uSupport[2])/(tStep*(1-ph2Zmp));
    aXP, aXN = zmp_solve(uSupport[1], uTorso1[1], uTorso2[1],
                          uTorso1[1], uTorso2[1]);
    aYP, aYN = zmp_solve(uSupport[2], uTorso1[2], uTorso2[2],
                          uTorso1[2], uTorso2[2]);
  end

  xFoot, zFoot = foot_phase(ph);
  
  if initial_step>0 then
     zFoot=0;
  end

  qLHipRollCompensation = 0;
  qRHipRollCompensation = 0;

  toeTipCompensation=0.0;
  --Lifting toetip
  if velCurrent[1]>0.04 then
    toeTipCompensation= -5*math.pi/180 *
          math.min(1, phSingle/.1, (1-phSingle)/.1);
  elseif velCurrent[1]<-0.01 then
    toeTipCompensation= 2*math.pi/180 *
          math.min(1, phSingle/.1, (1-phSingle)/.1);
  end

  if supportLeg == 0 then
    -- Left support
    uRight = se2_interpolate(xFoot, uRight1, uRight2);

    pLLeg[3] = 0;
    pRLeg[3] = stepHeight*zFoot;

    if (phSingle > 0) and (phSingle < 1) then
      qLHipRollCompensation = hipRollCompensation*
                              math.min(1, phSingle/.1, (1-phSingle)/.1);
    end

    pTorsoSensor = Kinematics.torso_lleg(Body.get_lleg_position());
    pTorsoSensor[2] = pTorsoSensor[2] + .085*pTorsoSensor[4];
    uTorsoSensor = pose_global({pTorsoSensor[1], pTorsoSensor[2], pTorsoSensor[6]},
                                uLeft);
  else
    -- Right support
    uLeft = se2_interpolate(xFoot, uLeft1, uLeft2);

    pLLeg[3] = stepHeight*zFoot;
    pRLeg[3] = 0;
    
    if (phSingle > 0) and (phSingle < 1) then
      qRHipRollCompensation = -hipRollCompensation*
                              math.min(1, phSingle/.1, (1-phSingle)/.1);
    end

    pTorsoSensor = Kinematics.torso_rleg(Body.get_rleg_position());
    pTorsoSensor[2] = pTorsoSensor[2] + .085*pTorsoSensor[4];
    uTorsoSensor = pose_global({pTorsoSensor[1], pTorsoSensor[2], pTorsoSensor[6]},
                                uRight);
  end

  uTheoretic = uTorsoShift + zmp_com(ph - tSensorDelay/tStep);
  uError = uTorsoSensor - uTheoretic;
  uTorsoShift[1] = uTorsoShift[1] +
                    aShiftFilterX*(torsoSensorGainX*uError[1] - uTorsoShift[1]);
  uTorsoShift[2] = uTorsoShift[2] +
                    aShiftFilterY*(torsoSensorGainY*uError[2] - uTorsoShift[2]);

  --Exponential low-pass filter torso angle measurements

  uTorso = zmp_com(ph);

  pLLeg[1], pLLeg[2], pLLeg[6] = uLeft[1], uLeft[2], uLeft[3];
  pRLeg[1], pRLeg[2], pRLeg[6] = uRight[1], uRight[2], uRight[3];

-- pTorso[1], pTorso[2], pTorso[6] = uTorso[1], uTorso[2], uTorso[3];

--[[
   uTorsoCommand=pose_global({uTorsoShift[1],uTorsoShift[2],0},uTorso);
   pTorso[1], pTorso[2], pTorso[6] = 
	uTorsoCommand[1], uTorsoCommand[2],
	uTorsoCommand[3];
--]]

  pTorso[1], pTorso[2], pTorso[6] = 
	uTorso[1]+uTorsoShift[1], uTorso[2]+uTorsoShift[2], uTorso[3];

  qLegs = Kinematics.inverse_legs(pLLeg, pRLeg, pTorso, supportLeg);
  
  qLegs[2] = qLegs[2] + qLHipRollCompensation;
  qLegs[8] = qLegs[8] + qRHipRollCompensation;

  --Stabilization using gyro feedback

  --Ankle stabilization using gyro feedback
  imuGyr = Body.get_sensor_imuGyr();
  gyro0 = Body.get_sensor_imuGyr0();

  -- Mapping between OP gyro to nao gyro
  gyro_roll = -(imuGyr[1]-gyro0[1]);
  gyro_pitch = -(imuGyr[2]-gyro0[2]);

	if imuOn then
		ankleShiftX=procFunc(gyro_pitch*ankleImuParamX[2],ankleImuParamX[3],
			ankleImuParamX[4]);
		ankleShiftY=procFunc(gyro_roll*ankleImuParamY[2],ankleImuParamY[3],ankleImuParamY[4]);
		kneeShiftX=procFunc(gyro_pitch*kneeImuParamX[2],kneeImuParamX[3],kneeImuParamX[4]);
		hipShiftY=procFunc(gyro_roll*hipImuParamY[2],hipImuParamY[3],hipImuParamY[4]);

		ankleShift[1]=ankleShift[1]+ankleImuParamX[1]*(ankleShiftX-ankleShift[1]);
		ankleShift[2]=ankleShift[2]+ankleImuParamY[1]*(ankleShiftY-ankleShift[2]);
		kneeShift=kneeShift+kneeImuParamX[1]*(kneeShiftX-kneeShift);
		hipShift[2]=hipShift[2]+hipImuParamY[1]*(hipShiftY-hipShift[2]);
	end

  if supportLeg == 0 then  -- Left support
    --Hip roll stabilization
    qLegs[2] = qLegs[2] + hipShift[2];

    --Knee pitch stabilization
    qLegs[4] = qLegs[4] + kneeShift;

    --Ankle pitch stabilization
    qLegs[5] = qLegs[5]  + ankleShift[1];

    --Ankle roll stabilization
    qLegs[6] = qLegs[6] + ankleShift[2];

    --Lifting toetip
    qLegs[11] = qLegs[11]  + toeTipCompensation;

  else

    --Hip roll stabilization
    qLegs[8] = qLegs[8]  + hipShift[2];

    --Knee pitch stabilization
    qLegs[10] = qLegs[10] + kneeShift;

    --Ankle pitch stabilization
    qLegs[11] = qLegs[11]  + ankleShift[1];

    --Ankle roll stabilization
    qLegs[12] = qLegs[12] + ankleShift[2];

    --Lifting toetip
    qLegs[5] = qLegs[5]  + toeTipCompensation;


  end

  local spread=(uLeft[3]-uRight[3])/2;

  --Additional ankle bias (should calibrated for each Nao)
--  qLegs[5] = qLegs[5]  + Config.walk.anklePitchComp[1];
--  qLegs[11] = qLegs[11]  + Config.walk.anklePitchComp[2];


  qLegs[5] = qLegs[5]  + 
	Config.walk.anklePitchComp[1]*math.cos(spread);
  qLegs[11] = qLegs[11]  + 
	Config.walk.anklePitchComp[2]*math.cos(spread);


  Body.set_lleg_command(qLegs);


end

function exit()
end

function mod_angle(a)
  -- Reduce angle to [-pi, pi)
  a = a % (2*math.pi);
  if (a >= math.pi) then
    a = a - 2*math.pi;
  end
  return a;
end

function pose_global(pRelative, pose)
  local ca = math.cos(pose[3]);
  local sa = math.sin(pose[3]);
  return vector.new{pose[1] + ca*pRelative[1] - sa*pRelative[2],
                    pose[2] + sa*pRelative[1] + ca*pRelative[2],
                    pose[3] + pRelative[3]};
end

function pose_relative(pGlobal, pose)
  local ca = math.cos(pose[3]);
  local sa = math.sin(pose[3]);
  local px = pGlobal[1]-pose[1];
  local py = pGlobal[2]-pose[2];
  local pa = pGlobal[3]-pose[3];
  return vector.new{ca*px + sa*py, -sa*px + ca*py, mod_angle(pa)};
end

--Helps smooth out the motions using a weighted average--
function se2_interpolate(t, u1, u2)
  return vector.new{u1[1]+t*(u2[1]-u1[1]),
                    u1[2]+t*(u2[2]-u1[2]),
                    u1[3]+t*mod_angle(u2[3]-u1[3])};
end

function step_left_destination(vel, uLeft, uRight)
  local u0 = se2_interpolate(.5, uLeft, uRight);
  -- Determine nominal midpoint position 1.5 steps in future
  local u1 = pose_global(vel, u0);
  local u2 = pose_global(.5*vel, u1);
  local uLeftPredict = pose_global({0, footY, 0}, u2);
  local uLeftRight = pose_relative(uLeftPredict, uRight);
  -- Do not pidgeon toe, cross feet:
  uLeftRight[1] = math.min(math.max(uLeftRight[1], -0.10), 0.10);
  uLeftRight[2] = math.min(math.max(uLeftRight[2], 0.09), 0.20);
  uLeftRight[3] = math.min(math.max(uLeftRight[3], -0*math.pi/180), 40*math.pi/180);
  return pose_global(uLeftRight, uRight);
end

function step_right_destination(vel, uLeft, uRight)
  local u0 = se2_interpolate(.5, uLeft, uRight);
  -- Determine nominal midpoint position 1.5 steps in future
  local u1 = pose_global(vel, u0);
  local u2 = pose_global(.5*vel, u1);
  local uRightPredict = pose_global({0, -footY, 0}, u2);
  local uRightLeft = pose_relative(uRightPredict, uLeft);
  -- Do not pidgeon toe, cross feet:
  uRightLeft[1] = math.min(math.max(uRightLeft[1], -0.10), 0.10);
  uRightLeft[2] = math.min(math.max(uRightLeft[2], -0.20), -0.09);
  uRightLeft[3] = math.min(math.max(uRightLeft[3], -40*math.pi/180), 0*math.pi/180);
  return pose_global(uRightLeft, uLeft);
end

function step_torso(uLeft, uRight)
  local u0 = se2_interpolate(.5, uLeft, uRight);
  local uLeftSupport = pose_global({supportX, supportY, 0}, uLeft);
  local uRightSupport = pose_global({supportX, -supportY, 0}, uRight);
  return se2_interpolate(.5, uLeftSupport, uRightSupport);
end

function set_velocity(vx, vy, vz)
  vz=math.min(math.max(vz,maxZ[1]),maxZ[2]);
  
--  local angleFactor=math.min(1.0, 1.5-math.abs(vz/maxZ[1]));
  local angleFactor=1;
  local stepMag=math.sqrt(vx^2+vy^2);
  local magFactor=math.min(0.06,stepMag)/(stepMag+0.000001);


  velCommand[1]=vx*magFactor*angleFactor;
  velCommand[2]=vy*magFactor*angleFactor;
  velCommand[3]=vz;

  --print("Velocity :",unpack(velCommand))
end

function update_velocity()

  local velDiff={};
  velDiff[1]= math.min(math.max(velCommand[1]-velCurrent[1],maxVelX[1]),
	maxVelX[2]);
  velDiff[2]= math.min(math.max(velCommand[2]-velCurrent[2],maxVelY[1]),
	maxVelY[2]);
  velDiff[3]= math.min(math.max(velCommand[3]-velCurrent[3],maxVelZ[1]),
	maxVelZ[2]);

  velCurrent[1] = math.min(math.max(velCurrent[1]+velDiff[1],
 	maxX[1]), maxX[2]);
  velCurrent[2] = math.min(math.max(velCurrent[2]+velDiff[2],
 	maxY[1]), maxY[2]);
  velCurrent[3] = math.min(math.max(velCurrent[3]+velDiff[3],
	 maxZ[1]), maxZ[2]);

  if initial_step>0 then
     velCurrent=vector.new({0,0,0})
     initial_step=initial_step-1;
  end

end


function get_velocity()
  return velCurrent;
end

function start()
--  stopRequest = false;
  stopRequest = 0;
  if (not active) then
    active = true;
    iStep0 = -1;
    t0 = Body.get_time();
    initdone=false;
    delaycount=0;
    initial_step=1;
  end
end

function stop()
  stopRequest = math.max(1,stopRequest);
--  stopRequest = 2;
end

function stopAlign()
  stop()
end

function get_odometry(u0)
  if (not u0) then
    u0 = vector.new({0, 0, 0});
  end
  local uFoot = se2_interpolate(.5, uLeft, uRight);
  return pose_relative(uFoot, u0), uFoot;
end

function get_body_offset()
  local uFoot = se2_interpolate(.5, uLeft, uRight);
  return pose_relative(uTorso, uFoot);
end

function procFunc(a,deadband,maxvalue)
  if a>0 then 
	b=math.min( math.max(0,math.abs(a)-deadband), maxvalue);
  else 
	b=-math.min( math.max(0,math.abs(a)-deadband), maxvalue);
  end
  return b;
end

entry();

