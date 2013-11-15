#!/usr/local/bin/bash

echo "IT'S ALIVE"

python medulla.py >> hippocampus/log/sys.log 2>>hippocampus/log/error.log &
python doctor.py
