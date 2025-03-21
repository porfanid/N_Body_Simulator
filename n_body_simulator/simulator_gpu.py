from .base_simulation import BaseNBodySimulation, calculate_acceleration_helper

try:
    import cupy as cp
    xp = cp
except ImportError:
    import numpy as np
    xp = np

class NBodySimulation(BaseNBodySimulation):
    """Class handling the N-body physics simulation with GPU support"""

    def __init__(self, num_bodies=10, dt=0.01, softening=0.1, boundary=400):
        self.xp = xp
        super().__init__(num_bodies, dt, softening, boundary)

    def update(self):
        """Update the simulation by one time step"""
        self.accelerations[:] = 0

        for i in range(self.num_bodies):
            ax, ay = calculate_acceleration_helper((self.positions, self.masses, self.G, self.softening, i))
            self.accelerations[i, 0] += self.xp.sum(ax)
            self.accelerations[i, 1] += self.xp.sum(ay)

        self.velocities += self.accelerations * self.dt
        self.positions += self.velocities * self.dt

        for i in range(self.num_bodies):
            self.trails[i].append((self.positions[i, 0], self.positions[i, 1]))
            if len(self.trails[i]) > self.max_trail_length:
                self.trails[i].pop(0)

        self.calculate_energy()

    def is_gpu(self):
        return True