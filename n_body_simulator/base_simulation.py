from PySide6.QtGui import QColor

class BaseNBodySimulation:
    """Base class for handling the N-body physics simulation"""

    def __init__(self, num_bodies=10, dt=0.01, softening=0.1, boundary=400):
        self.G = 6.67  # Gravitational constant (scaled for simulation)
        self.dt = dt  # Time step
        self.softening = softening  # Softening parameter to avoid numerical instability
        self.boundary = boundary  # Boundary of the simulation space
        self.reset(num_bodies)

    def apply_boundary_conditions(self):
        """Apply boundary conditions to keep bodies within the simulation boundary"""
        for i in range(self.num_bodies):
            if self.positions[i, 0] < -self.boundary / 2 or self.positions[i, 0] > self.boundary / 2:
                self.velocities[i, 0] *= -1  # Reverse velocity in x direction
            if self.positions[i, 1] < -self.boundary / 2 or self.positions[i, 1] > self.boundary / 2:
                self.velocities[i, 1] *= -1  # Reverse velocity in y direction

    def reset(self, num_bodies=None):
        """Reset the simulation with the given number of bodies"""
        if num_bodies is not None:
            self.num_bodies = num_bodies

        self.positions = self.xp.random.uniform(-self.boundary / 2, self.boundary / 2, (self.num_bodies, 2))
        self.velocities = self.xp.random.uniform(-0.5, 0.5, (self.num_bodies, 2))

        base_masses = self.xp.random.uniform(0.5, 2.0, self.num_bodies)
        for i in range(min(3, self.num_bodies)):
            idx = self.xp.random.randint(0, self.num_bodies)
            base_masses[idx] = self.xp.random.uniform(10, 20)

        self.masses = base_masses

        self.colors = []
        for mass in self.masses:
            if mass > 5:
                r = min(255, int(200 + mass * 2.5))
                g = max(0, int(255 - mass * 10))
                b = max(0, int(100 - mass * 5))
            else:
                r = int(100 + mass * 20)
                g = int(100 + mass * 20)
                b = min(255, int(150 + mass * 20))
            self.colors.append(QColor(r, g, b))

        self.trails = [[] for _ in range(self.num_bodies)]
        self.max_trail_length = 50

        self.accelerations = self.xp.zeros((self.num_bodies, 2))

        self.kinetic_energy = 0
        self.potential_energy = 0

    def calculate_energy(self):
        v_squared = self.xp.sum(self.velocities ** 2, axis=1)
        self.kinetic_energy = 0.5 * self.xp.sum(self.masses * v_squared)

        self.potential_energy = 0
        for i in range(self.num_bodies):
            for j in range(i + 1, self.num_bodies):
                dx = self.positions[i, 0] - self.positions[j, 0]
                dy = self.positions[i, 1] - self.positions[j, 1]
                r = self.xp.sqrt(dx ** 2 + dy ** 2 + self.softening ** 2)
                self.potential_energy -= self.G * self.masses[i] * self.masses[j] / r


    def calculate_acceleration(self, i):
        dx = self.positions[:, 0] - self.positions[i, 0]
        dy = self.positions[:, 1] - self.positions[i, 1]

        inv_r3 = (dx ** 2 + dy ** 2 + self.softening ** 2) ** (-1.5)
        inv_r3[i] = 0

        ax = self.G * dx * inv_r3 * self.masses
        ay = self.G * dy * inv_r3 * self.masses
        return ax, ay