#!/bin/bash

#give permission for everything in the express-app directory
sudo chmod -R 777 /home/ec2-user/Finaltest1

#navigate into our working directory where we have all our github files
cd /home/ec2-user/Finaltest1


#start our node app in the background
python3 app.py > app.out.log 2> app.err.log < /dev/null &