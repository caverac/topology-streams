"""GPU availability detection for topostreams_cuda kernels."""

import importlib

available = False

try:
    importlib.import_module("topostreams_cuda")
    available = True
except (ImportError, OSError):
    pass
