#!/bin/sh

git submodule init
git submodule update
cd src/highlight
git pull origin master

cp -r src/app src/soccer src/studio src/video ..
