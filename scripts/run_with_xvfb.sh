#!/bin/bash
# Helper script to run openai_agent_tool.py with xvfb-run

# Check if xvfb is installed
if ! command -v xvfb-run &> /dev/null; then
    echo "Error: xvfb-run is not installed. Please install it with:"
    echo "  sudo apt-get install xvfb  # On Ubuntu/Debian"
    echo "  sudo yum install xorg-x11-server-Xvfb  # On CentOS/RHEL"
    exit 1
fi

# Run the script with xvfb-run
echo "Running openai_agent_tool.py with virtual display..."
xvfb-run -a python "$(dirname "$0")/openai_agent_tool.py" "$@"