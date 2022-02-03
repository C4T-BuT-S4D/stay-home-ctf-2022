import sys

import catboost
import pandas

if len(sys.argv) < 3:
    print("usage: python3 train_and_save.py <input.csv> <out.onnx>")
    sys.exit(1)

PATH_TO_DATASET = sys.argv[1]
OUT_PATH = sys.argv[2]

df = pandas.read_csv(PATH_TO_DATASET)

X = df.drop(columns=['result'])
y = df['result']

cbc = catboost.CatBoostClassifier()
cbc.fit(X, y)

cbc.save_model(OUT_PATH, format="onnx", export_parameters={})

