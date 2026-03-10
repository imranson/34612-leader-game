# !pip install xlsxwriter

import zipfile
import os
import random
import gc
from IPython.display import Javascript
import pandas as pd

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

# require comp34612.zip
extract_path = "."
zip_filename = "comp34612.zip"

os.makedirs(extract_path, exist_ok=True)

with zipfile.ZipFile(zip_filename, "r") as zip_ref:
    zip_ref.extractall(extract_path)

from engine import Engine
from gui import GUI

# import packages here

class Leader:
    _subclass_registry = {}

    def __init__(self, name, engine):
        self.name = name
        self.engine = engine

    @classmethod
    def cleanup_old_subclasses(cls):
        """
        A function to remove old subclasses before defining new ones.
        """
        existing_subclasses = list(cls.__subclasses__())

        for subclass in existing_subclasses:
            subclass_name = subclass.__name__
            if subclass_name in cls._subclass_registry:
                del cls._subclass_registry[subclass_name]
                del subclass
        gc.collect()

    @classmethod
    def update_subclass_registry(cls):
        """
        A function to update registry after cleaning up old subclasses.
        """
        cls.cleanup_old_subclasses()
        cls._subclass_registry = {subclass.__name__: subclass for subclass in cls.__subclasses__()}

    def new_price(self, date):
        """
        A function for setting the new price of each day.
        :param date: date of the day to be updated
        :return: (float) price for the day
        """
        pass

    def get_price_from_date(self, date):
        """
        A function for getting the price set on a date.
        :param date: (int) date to get the price from
        :return: a tuple (leader_price, follower_price)
        """
        return self.engine.exposed_get_price(date)


    def start_simulation(self):
        """
        A function runs at the beginning of the simulation.
        """
        pass

    def end_simulation(self):
        """
        A function runs at the beginning of the simulation.
        """
        pass
    


class SimpleLeader(Leader):
    def __init__(self, name, engine):
        super().__init__(name, engine)

    def new_price(self, date: int):
        return 1.5 + random.random() * 0.1
    


group_num = 37
assert isinstance(group_num, int), f"Expected an integer for group_num, but got {type(group_num).__name__}"



# for marking purposes
# from marking import MarkingGUI
# marking_gui = MarkingGUI(engine, Leader, group_num)
# marking_gui.marking()

# from google.colab import files
# files.download('results.xlsx')