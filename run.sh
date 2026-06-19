#!/bin/bash

cd /home/RSP2-Backend

python3 -m venv venv
. venv/bin/activate

pip install flask flask-cors

python start.py