import random
import csv

import numpy as np
import catboost
import onnx
import onnx.numpy_helper as nphelp
from onnx.tools import update_model_dims


class DatasetBuilder:
    def __init__(self):
        self.X = []
        self.y = []

    def to_csv(self, file_name):
        keys = self.keys() + ["test_result"]
        with open(file_name, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=keys)
            writer.writeheader()
            for i, row in enumerate(self.X):
                row = row + [self.y[i]]
                dict_row = {x: y for x, y in zip(keys, row)}
                writer.writerow(dict_row)

    def build(self):
        return self.X, self.y

    def random_rows(self, n):
        for i in range(n):
            self.X.append(self.random_row())
            self.y.append(self.random_prediction())
        if len(set(self.y)) == 1:
            self.y[0] = 1 - self.y[0]
        return self

    def add_row(self, row, y):
        self.X.append(row)
        self.y.append(y)
        return self

    @classmethod
    def random_row(cls):
        return [cls.random_age(), cls.random_sex(), cls.random_rh(), cls.random_blood_type(),
                cls.random_sugar_level()]

    @staticmethod
    def keys():
        return ['age', 'sex', 'rh', 'blood_type', 'sugar_level']

    @classmethod
    def make_dict(cls, row):
        return {x[0]: x[1] for x in zip(cls.keys(), row)}

    @staticmethod
    def random_prediction():
        return random.randint(0, 1)

    @staticmethod
    def random_age():
        return random.randint(20, 65)

    @staticmethod
    def random_sex():
        return random.randint(0, 1)

    @staticmethod
    def random_rh():
        return random.choice([-1, 1])

    @staticmethod
    def random_blood_type():
        return random.randint(0, 4)

    @staticmethod
    def random_sugar_level():
        return round(random.random() * 20, 3)


class ModelHelper:
    def __init__(self):
        self.cb_model = None
        self.onnx_model = None

    def build_cb_model(self, X, y):
        cbc = catboost.CatBoostClassifier(iterations=20, allow_writing_files=False, silent=True)
        cbc.fit(X, y)
        self.cb_model = cbc
        return cbc

    def build_onnx_model(self, size=5, pos=3, thresh=20, graph_name='vaccine-model', company_name='c4tbuts4d'):
        # Create input.
        x = onnx.helper.make_tensor_value_info('X', onnx.TensorProto.FLOAT, ["N", 5])
        # Create output.
        res_out = onnx.helper.make_tensor_value_info('output', onnx.TensorProto.BOOL, ["N"])
        # Create const tensors.
        mask_array = np.zeros(size, dtype=int)
        mask_array[pos] = 1
        value_tensor = mask_array * thresh
        mask_tensor = onnx.helper.make_tensor('mask', onnx.TensorProto.BOOL, [size], mask_array)
        greater_tensor = onnx.helper.make_tensor('val', onnx.TensorProto.FLOAT, [size], value_tensor)
        shape_t = onnx.helper.make_tensor('out_shape', onnx.TensorProto.INT64, [1], np.array([-1]))

        graph = onnx.helper.make_graph(nodes=[
            onnx.helper.make_node(
                'Greater',
                inputs=[x.name, greater_tensor.name],
                outputs=['greater_out'],
            ),
            onnx.helper.make_node(
                'And',
                inputs=['greater_out', mask_tensor.name],
                outputs=['and_out'],
            ),
            onnx.helper.make_node(
                'Compress',
                inputs=['and_out', mask_tensor.name],
                outputs=['compress_out'], axis=1, ),
            onnx.helper.make_node(
                'Reshape',
                inputs=['compress_out', 'out_shape'],
                outputs=[res_out.name]
            )
        ],
            name=graph_name,
            inputs=[x, ],
            outputs=[res_out, ],
            initializer=[greater_tensor, mask_tensor, shape_t]
        )

        model_def = onnx.helper.make_model(graph,
                                           producer_name=company_name)
        onnx.checker.check_model(model_def)
        self.onnx_model = model_def
        return self.onnx_model

    def save(self, out_path):
        if self.cb_model:
            # Save model to ONNX-ML format
            self.cb_model.save_model(
                out_path,
                format="onnx",
                export_parameters={
                }
            )
        if self.onnx_model:
            onnx.save(self.onnx_model, out_path)

# if __name__ == '__main__':
#     db = DatasetBuilder().random_rows(50)
#     db.to_csv('sample_ds.csv')
# one_row = db.random_row()
# db.add_row(one_row, 1)
# X, y = db.build()
# mh = ModelHelper()
# cbm = mh.build_cb_model(X, y)
# mh.build_onnx_model()
# print(cbm.predict([one_row, ]))
# mh.save("/tmp/catboost_m.onnx")
# mh.
