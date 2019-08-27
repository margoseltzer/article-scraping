import csv
import os
import numpy as np
import pandas as pd


path = os.path.dirname(os.path.realpath(__file__))
dirpath = os.path.dirname(path)
fakenews_path = os.path.dirname(dirpath)
fake_csv_path = fakenews_path + 'fivek_fake.csv'
real_csv_path = fakenews_path + 'fivek_real.csv'

with open(dirpath + 'obj_dict.csv', mode='r') as f: 
    reader = csv.reader(f)
    print(reader[0])