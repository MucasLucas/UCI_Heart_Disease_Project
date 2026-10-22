"""Read-only identity and specification checks for the accepted project artifact."""
import json
import math
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from day03_preprocessing import FEATURES

EXPECTED_MODEL_SHA256 = "948f8939076cdc1e001a74d7bb414b28c88e21b7de32b0a2172fdc4a805ce1ae"
FROZEN_THRESHOLD = 0.3528716233973672

def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def wilson(successes, total):
    """Descriptive Wilson 95% limits; undefined when the denominator is zero."""
    if total == 0:
        return float("nan"), float("nan")
    z = 1.959963984540054
    p = successes / total
    denominator = 1 + z*z/total
    center = (p + z*z/(2*total)) / denominator
    radius = z * math.sqrt(p*(1-p)/total + z*z/(4*total*total)) / denominator
    lower = 0.0 if successes == 0 else max(0.0, center-radius)
    upper = 1.0 if successes == total else min(1.0, center+radius)
    return lower, upper

def validate_bundle(bundle, freeze):
    if list(bundle["features"]) != FEATURES or freeze["features"] != FEATURES:
        raise ValueError("Frozen feature list changed.")
    if bundle["threshold"] != FROZEN_THRESHOLD or freeze["threshold"] != FROZEN_THRESHOLD:
        raise ValueError("Frozen threshold changed.")
    if bundle["specification"] != freeze["selected"]:
        raise ValueError("Bundle and accepted specification differ.")
    model = bundle["model"]
    if not isinstance(model, Pipeline) or not isinstance(model.named_steps.get("classifier"), RandomForestClassifier):
        raise ValueError("Expected the frozen uncalibrated forest pipeline.")
    if freeze["selected"]["candidate"] != "c06" or freeze["selected"]["calibration"] != "none":
        raise ValueError("Unexpected accepted model; this procedure targets c06.")
    classifier = model.named_steps["classifier"]
    for key, expected in freeze["model_parameters"].items():
        if classifier.get_params().get(key) != expected:
            raise ValueError(f"Frozen model parameter changed: {key}")
    if not np.array_equal(classifier.classes_, [0, 1]):
        raise ValueError("Unexpected class order.")
    return model
