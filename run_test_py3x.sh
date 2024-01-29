cd /Users/stephen.hilton/Dev/SxT-Python-SDK

# -- py3.10.13
python3.10 -m venv venv_310
. ./venv_310/bin/activate
pip install --upgrade pip
pip3 install -r requirements.txt
pip3 install pytest
cd tests
echo RUNNING PYTHON 3.10 TESTING
pytest --verbose
deactivate
cd ..

# -- py3.11
python3.11 -m venv venv_311
. ./venv_311/bin/activate
pip install --upgrade pip
pip3 install -r requirements.txt
pip3 install pytest
cd tests
echo RUNNING PYTHON 3.11 TESTING
pytest --verbose
deactivate
cd ..
