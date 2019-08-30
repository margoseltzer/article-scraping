import csv
import os

path = os.path.dirname(os.path.realpath(__file__))
dirpath = os.path.dirname(path)
labeled_path = dirpath + '/data/datasets/labeled_articles.csv'
print(labeled_path)

fakenews_path = os.path.dirname(dirpath)
fake_csv_path = fakenews_path + '/fivek_fake.csv'
real_csv_path = fakenews_path + '/fivek_real.csv'
whole_set_patj = fakenews_path + '/news_cleaned_2018_02_13.csv'

reader = csv.reader(open(fake_csv_path, mode='r'))
f_data = list(reader)
print(f_data[2][5])

reader = csv.reader(open(real_csv_path, mode='r'))
r_data = list(reader)
print(r_data[2][5])


with open(labeled_path, mode='a') as csv_f:
    w = csv.writer(csv_f)
    for r in f_data:
        w.writerow([r[5], 0])
    
    for r in r_data:
        w.writerow([r[5], 1])

