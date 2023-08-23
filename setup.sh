sudo apt-get install python3-venv -y
python3 -m venv jetson_env --system-site-packages
source jetson_env/bin/activate

export OPENBLAS_CORETYPE=ARMV8 ## YOu might need 
### Install python dependencies
pip3 install --upgrade pip
pip3 install -r requirements.txt

# --no-deps
#pip3 install --no-deps imutils
#

