#!/bin/bash

cd /home/RSP2-Backend

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

. venv/bin/activate

pip install -q flask flask-cors gunicorn

gunicorn -w 2 -b 0.0.0.0:5000 start:app