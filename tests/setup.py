# use the venv virtual environment:
# cd /Users/stephen.hilton/Dev/SxT-Python-SDK/tests 
# . ./venv/bin/activate
# ./tests/venv/bin/python
# pip3 install -r requirements.txt

from pathlib import Path
import sys
path_root = Path(Path(__file__).parents[1] / 'src').resolve()
sys.path.append(str(path_root))
