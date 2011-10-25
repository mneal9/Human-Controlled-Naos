module(..., package.seeall);

require('Body')
require('Config')
require('Speak')

function entry()
  print(_NAME..' entry');

end

function update()
  
  Speak.talk('annassa ka ta ka low ka lay yah yah yah neh kay brin marr brin marr brin marr!')

  return 'done';
end

function exit()
  print(_NAME..' exit');
end
