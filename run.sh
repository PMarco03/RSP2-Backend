#!/bin/bash
cd /home/scripts

python3 -m venv venv
. venv/bin/activate

pip install flask flask-cors
python start.py