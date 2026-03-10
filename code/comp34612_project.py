# !pip install xlsxwriter

import zipfile
import os
import random
import gc
from IPython.display import Javascript
import pandas as pd

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

extract_path = "."
zip_filename = "comp34612.zip"

os.makedirs(extract_path, exist_ok=True)

with zipfile.ZipFile(zip_filename, "r") as zip_ref:
    zip_ref.extractall(extract_path)