import os
import sys

import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from scripts.forecast import prepare_features


def test_prepare_features_builds_expected_shape():
    series = pd.Series([1, 2, 3, 4, 5, 6], dtype=float)
    X, y = prepare_features(series, lookback=3)
    assert X.shape == (3, 3)
    assert y.shape == (3,)
    assert list(y) == [4.0, 5.0, 6.0]
