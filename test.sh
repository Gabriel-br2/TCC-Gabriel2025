#!/bin/bash

# chmod +x test.sh
for i in {1..4}; do
    python3 mainGame.py &
done

wait
