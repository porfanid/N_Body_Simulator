from .base_simulation import BaseNBodySimulation, calculate_acceleration_helper
import numpy as np
from multiprocessing import Pool, cpu_count

class NBodySimulation(BaseNBodySimulation):
    """Class handling the N-body physics simulation with CPU support"""

    def __init__(self, num_bodies=10, dt=0.01, softening=0.1, boundary=400):
        self.xp = np
        super().__init__(num_bodies, dt, softening, boundary)

    def update(self):
        """Update the simulation by one time step"""
        self.accelerations[:] = 0

        with Pool(processes=cpu_count()) as pool:
            results = pool.map(calculate_acceleration_helper,
                               [(self.positions, self.masses, self.G, self.softening, i)
                                for i in range(self.num_bodies)])

        for i, acc in enumerate(results):
            self.accelerations[i] = acc

        self.velocities += self.accelerations * self.dt
        self.positions += self.velocities * self.dt

        for i in range(self.num_bodies):
            self.trails[i].append((self.positions[i, 0], self.positions[i, 1]))
            if len(self.trails[i]) > self.max_trail_length:
                self.trails[i].pop(0)

        self.calculate_energy()

    def calculate_acceleration(self, i):
        ax, ay = super().calculate_acceleration(i)
        return np.array([np.sum(ax), np.sum(ay)])

    def is_gpu(self):
        return False