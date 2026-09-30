import random

import numpy as np
import pytest


@pytest.fixture(autouse=True)
def semilla_fija():
    """Fija la semilla de numpy y random antes de cada test.

    autouse=True hace que se aplique a todos los tests sin necesidad
    de importarla explícitamente.
    """
    np.random.seed(42)
    random.seed(42)
    yield