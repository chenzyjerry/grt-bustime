#!/bin/bash
# Setup script for GRT Bus Time on Raspberry Pi

echo "Setting up GRT Bus Time..."

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

echo ""
echo "Setup complete!"
echo ""
echo "To run the script:"
echo "  source venv/bin/activate"
echo "  python3 bus_arrival_times.py"
echo ""
echo "To run continuously:"
echo " Install tmux if not already installed: sudo apt install tmux"
echo " Start a new tmux session: tmux"
echo " Run the script inside tmux: python3 bus_arrival_times.py"
echo " Detach from tmux session: Ctrl+B then D"
echo " To stop the script, reattach to tmux and press Ctrl+C"
echo " Reattach to tmux session: tmux attach"
