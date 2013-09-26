#!/usr/local/bin/bash

echo "IT'S ALIVE"

python medulla.py >> hippocampus/log/sys.log &
python doctor.py
