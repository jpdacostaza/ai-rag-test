#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Start the memory API server
exec python main.py
