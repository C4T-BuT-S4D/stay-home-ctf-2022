import time

import onnxruntime


def predict(model_path: str, scalar):
    sess = onnxruntime.InferenceSession(model_path)
    inputs = sess.get_inputs()
    outputs = sess.get_outputs()
    if len(inputs) != 1:
        raise ValueError("model should have only one input")
    if len(outputs) < 1 or len(outputs) > 2:
        raise ValueError("model should have 1 or 2 outputs (class and probability)")
    input_name = inputs[0].name
    output_names = [x.name for x in outputs]
    result = sess.run(output_names, {input_name: [
        scalar
    ]
    })

    prediction = result[0].tolist()[0]
    prediction_prob = None
    if len(outputs) > 1 and len(result[1]) > 0 and prediction in result[1][0]:
        prediction_prob = result[1][0][prediction]
    return prediction, prediction_prob
