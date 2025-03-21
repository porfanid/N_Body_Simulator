try:
    import cupy as cp
    from .simulator_gpu import NBodySimulation
except ImportError:
    from .simulator_cpu import NBodySimulation