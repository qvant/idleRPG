#!/bin/bash
cd /home/rpg_user/distr
rm -rf /home/rpg_user/distr/idleRPG
git clone https://github.com/qvant/idleRPG.git
rm -rf /home/rpg_user/distr/idleRPG/.gitignore
rm -rf /home/rpg_user/distr/idleRPG/.git
rm -rf /home/rpg_user/distr/idleRPG/.github
cp -a idleRPG/. /usr/app/idleRPG/
