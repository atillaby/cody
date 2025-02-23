#!/bin/bash

echo "Starting API server..."
source venv/bin/activate
export PYTHONPATH=/workspaces/cody
export $(grep -v '^#' .env | xargs)
python run.py
