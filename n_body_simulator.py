import sys
import numpy as np
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSlider
from PySide6.QtWidgets import QPushButton, QLabel, QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox
from PySide6.QtCore import Qt, QTimer, Signal, Slot, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath


class NBodySimulation:
    """Class handling the N-body physics simulation"""

    def __init__(self, num_bodies=10, dt=0.01, softening=0.1, boundary=200):
        self.G = 6.67  # Gravitational constant (scaled for simulation)
        self.dt = dt  # Time step
        self.softening = softening  # Softening parameter to avoid numerical instability
        self.boundary = boundary  # Boundary of the simulation space

        self.reset(num_bodies)

    def reset(self, num_bodies=None):
        """Reset the simulation with the given number of bodies"""
        if num_bodies is not None:
            self.num_bodies = num_bodies

        # Initialize random positions and velocities
        self.positions = np.random.uniform(-self.boundary / 2, self.boundary / 2, (self.num_bodies, 2))
        self.velocities = np.random.uniform(-0.5, 0.5, (self.num_bodies, 2))

        # Initialize random masses (some larger than others)
        base_masses = np.random.uniform(0.5, 2.0, self.num_bodies)
        # Make a few bodies more massive
        for i in range(min(3, self.num_bodies)):
            idx = np.random.randint(0, self.num_bodies)
            base_masses[idx] = np.random.uniform(10, 20)

        self.masses = base_masses

        # Initialize colors based on mass
        self.colors = []
        for mass in self.masses:
            if mass > 5:
                # Larger masses are redder
                r = min(255, int(200 + mass * 2.5))
                g = max(0, int(255 - mass * 10))
                b = max(0, int(100 - mass * 5))
            else:
                # Smaller masses are bluer
                r = int(100 + mass * 20)
                g = int(100 + mass * 20)
                b = min(255, int(150 + mass * 20))
            self.colors.append(QColor(r, g, b))

        # Trails for bodies
        self.trails = [[] for _ in range(self.num_bodies)]
        self.max_trail_length = 50

        # Acceleration array
        self.accelerations = np.zeros((self.num_bodies, 2))

        # Energy tracking
        self.kinetic_energy = 0
        self.potential_energy = 0

    def update(self):
        """Update the simulation by one time step"""
        # Calculate accelerations
        self.accelerations[:] = 0

        # Vectorized distance calculation
        for i in range(self.num_bodies):
            # Get distances to all other bodies
            dx = self.positions[:, 0] - self.positions[i, 0]
            dy = self.positions[:, 1] - self.positions[i, 1]

            # Distance squared with softening
            inv_r3 = (dx ** 2 + dy ** 2 + self.softening ** 2) ** (-1.5)

            # Zero out self-interaction
            inv_r3[i] = 0

            # Calculate acceleration components (F = G * m1 * m2 / r^2)
            ax = self.G * dx * inv_r3 * self.masses
            ay = self.G * dy * inv_r3 * self.masses

            # Sum all accelerations
            self.accelerations[i, 0] += np.sum(ax)
            self.accelerations[i, 1] += np.sum(ay)

        # Update velocities (v += a * dt)
        self.velocities += self.accelerations * self.dt

        # Update positions (p += v * dt)
        self.positions += self.velocities * self.dt

        # Update trails
        for i in range(self.num_bodies):
            self.trails[i].append((self.positions[i, 0], self.positions[i, 1]))
            if len(self.trails[i]) > self.max_trail_length:
                self.trails[i].pop(0)

        # Calculate energies
        self.calculate_energy()

    def calculate_energy(self):
        """Calculate the kinetic and potential energy of the system"""
        # Kinetic energy: sum of (1/2) * m * v^2
        v_squared = np.sum(self.velocities ** 2, axis=1)
        self.kinetic_energy = 0.5 * np.sum(self.masses * v_squared)

        # Potential energy: sum of -G * m1 * m2 / r
        self.potential_energy = 0
        for i in range(self.num_bodies):
            for j in range(i + 1, self.num_bodies):
                dx = self.positions[i, 0] - self.positions[j, 0]
                dy = self.positions[i, 1] - self.positions[j, 1]
                r = np.sqrt(dx ** 2 + dy ** 2 + self.softening ** 2)
                self.potential_energy -= self.G * self.masses[i] * self.masses[j] / r

    def apply_boundary_conditions(self, condition="bounce"):
        """Apply boundary conditions to keep bodies in simulation space"""
        if condition == "bounce":
            # Check x boundaries
            beyond_right = self.positions[:, 0] > self.boundary / 2
            beyond_left = self.positions[:, 0] < -self.boundary / 2

            # Reflect positions and velocities
            self.positions[beyond_right, 0] = self.boundary - self.positions[beyond_right, 0]
            self.velocities[beyond_right, 0] *= -0.9  # Damping factor

            self.positions[beyond_left, 0] = -self.boundary - self.positions[beyond_left, 0]
            self.velocities[beyond_left, 0] *= -0.9

            # Check y boundaries
            beyond_top = self.positions[:, 1] > self.boundary / 2
            beyond_bottom = self.positions[:, 1] < -self.boundary / 2

            # Reflect positions and velocities
            self.positions[beyond_top, 1] = self.boundary - self.positions[beyond_top, 1]
            self.velocities[beyond_top, 1] *= -0.9

            self.positions[beyond_bottom, 1] = -self.boundary - self.positions[beyond_bottom, 1]
            self.velocities[beyond_bottom, 1] *= -0.9

        elif condition == "periodic":
            # Wrap around (torus-like boundary)
            self.positions[:, 0] = ((self.positions[:, 0] + self.boundary / 2) % self.boundary) - self.boundary / 2
            self.positions[:, 1] = ((self.positions[:, 1] + self.boundary / 2) % self.boundary) - self.boundary / 2

        elif condition == "open":
            # Allow bodies to leave, but replace those that get too far
            too_far = np.sqrt(np.sum(self.positions ** 2, axis=1)) > self.boundary * 2

            for i in np.where(too_far)[0]:
                # New random position near the edge
                angle = np.random.uniform(0, 2 * np.pi)
                radius = self.boundary / 2 * 0.9
                self.positions[i, 0] = np.cos(angle) * radius
                self.positions[i, 1] = np.sin(angle) * radius

                # Velocity toward center
                self.velocities[i, 0] = -np.cos(angle) * np.random.uniform(0.1, 0.5)
                self.velocities[i, 1] = -np.sin(angle) * np.random.uniform(0.1, 0.5)

                # Clear trail
                self.trails[i] = []


class SimulationWidget(QWidget):
    """Widget for visualizing the N-body simulation"""

    def __init__(self, parent=None):
        super().__init__(parent)
        #self.setMinimumSize(600, 600)

        # Set up the simulation
        self.simulation = NBodySimulation(num_bodies=10)
        self.boundary = self.simulation.boundary

        # Drawing settings
        self.scale_factor = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.show_trails = True
        self.show_vectors = False
        self.paused = False

        # Mouse tracking for panning
        self.setMouseTracking(True)
        self.last_mouse_pos = None
        self.dragging = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Fill background
        painter.fillRect(self.rect(), QColor(0, 0, 0))

        # Draw coordinate grid
        self.draw_grid(painter)

        # Center and scale the coordinate system
        width, height = self.width(), self.height()
        scale = min(width, height) / (self.boundary * self.scale_factor)

        center_x = width / 2 + self.offset_x
        center_y = height / 2 + self.offset_y

        # Draw the trails first (if enabled)
        if self.show_trails:
            for i, trail in enumerate(self.simulation.trails):
                if len(trail) < 2:
                    continue

                # Create a path for the trail
                path = QPainterPath()
                first_point = True

                for j, (x, y) in enumerate(trail):
                    # Convert simulation coordinates to screen coordinates
                    screen_x = center_x + x * scale
                    screen_y = center_y - y * scale  # Y is inverted in screen coordinates

                    if first_point:
                        path.moveTo(screen_x, screen_y)
                        first_point = False
                    else:
                        path.lineTo(screen_x, screen_y)

                # Set pen with fading opacity based on the color of the body
                color = self.simulation.colors[i]
                alpha_pen = QPen(QColor(color.red(), color.green(), color.blue(), 50))
                alpha_pen.setWidth(1)
                painter.setPen(alpha_pen)
                painter.drawPath(path)

        # Draw the bodies
        for i in range(self.simulation.num_bodies):
            # Get body data
            pos = self.simulation.positions[i]
            vel = self.simulation.velocities[i]
            mass = self.simulation.masses[i]
            color = self.simulation.colors[i]

            # Convert simulation coordinates to screen coordinates
            screen_x = center_x + pos[0] * scale
            screen_y = center_y - pos[1] * scale  # Y is inverted in screen coordinates

            # Draw the body as a circle (size based on mass)
            radius = max(2, np.sqrt(mass) * 1.5)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QPointF(screen_x, screen_y), radius, radius)

            # Draw velocity vectors (if enabled)
            if self.show_vectors:
                # Scale the velocity for display
                vec_scale = 5.0
                end_x = screen_x + vel[0] * vec_scale
                end_y = screen_y - vel[1] * vec_scale

                # Draw the vector
                painter.setPen(QPen(Qt.white, 1))
                painter.drawLine(screen_x, screen_y, end_x, end_y)

        # Draw energy information
        text_color = QColor(255, 255, 255)
        painter.setPen(text_color)
        painter.drawText(10, 20, f"KE: {self.simulation.kinetic_energy:.2f}")
        painter.drawText(10, 40, f"PE: {self.simulation.potential_energy:.2f}")
        total_energy = self.simulation.kinetic_energy + self.simulation.potential_energy
        painter.drawText(10, 60, f"TE: {total_energy:.2f}")

        # If paused, draw a pause indicator
        if self.paused:
            painter.drawText(width - 60, 20, "PAUSED")

    def draw_grid(self, painter):
        """Draw a coordinate grid to help visualize the space"""
        width, height = self.width(), self.height()
        scale = min(width, height) / (self.boundary * self.scale_factor)

        center_x = width / 2 + self.offset_x
        center_y = height / 2 + self.offset_y

        # Set up grid pen
        grid_pen = QPen(QColor(50, 50, 50))
        grid_pen.setWidth(1)
        painter.setPen(grid_pen)

        # Draw grid lines
        grid_spacing = 20 * scale  # Space between grid lines in pixels

        # Calculate the number of lines needed
        num_lines_x = int(width / grid_spacing) + 2
        num_lines_y = int(height / grid_spacing) + 2

        # Calculate where the (0,0) grid line is
        zero_x_offset = center_x % grid_spacing
        zero_y_offset = center_y % grid_spacing

        # Draw vertical grid lines
        for i in range(num_lines_x):
            x = i * grid_spacing - (zero_x_offset % grid_spacing)
            painter.drawLine(x, 0, x, height)

        # Draw horizontal grid lines
        for i in range(num_lines_y):
            y = i * grid_spacing - (zero_y_offset % grid_spacing)
            painter.drawLine(0, y, width, y)

        # Draw the axes with a slightly brighter color
        axes_pen = QPen(QColor(100, 100, 100))
        axes_pen.setWidth(2)
        painter.setPen(axes_pen)

        # X-axis
        painter.drawLine(0, center_y, width, center_y)

        # Y-axis
        painter.drawLine(center_x, 0, center_x, height)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.last_mouse_pos = event.position()
            self.dragging = True

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False

    def mouseMoveEvent(self, event):
        if self.dragging and self.last_mouse_pos is not None:
            # Calculate the difference
            delta = event.position() - self.last_mouse_pos

            # Update the offset
            self.offset_x += delta.x()
            self.offset_y += delta.y()

            # Save the current position
            self.last_mouse_pos = event.position()

            # Request a repaint
            self.update()

    def wheelEvent(self, event):
        # Zoom in or out with mouse wheel
        zoom_factor = 1.1

        if event.angleDelta().y() > 0:
            # Zoom in
            self.scale_factor /= zoom_factor
        else:
            # Zoom out
            self.scale_factor *= zoom_factor

        # Constrain zoom scale
        self.scale_factor = max(0.1, min(10.0, self.scale_factor))

        # Request a repaint
        self.update()

    def update_simulation(self):
        """Update the simulation if not paused"""
        if not self.paused:
            # Run multiple updates per frame for smoother/faster simulation
            for _ in range(1):
                self.simulation.update()
                self.simulation.apply_boundary_conditions()

        # Request a repaint
        self.update()

    def toggle_pause(self):
        """Toggle the simulation pause state"""
        self.paused = not self.paused

    def toggle_trails(self):
        """Toggle the display of trails"""
        self.show_trails = not self.show_trails

    def toggle_vectors(self):
        """Toggle the display of velocity vectors"""
        self.show_vectors = not self.show_vectors

    def reset_view(self):
        """Reset the view to the default"""
        self.offset_x = 0
        self.offset_y = 0
        self.scale_factor = 1.0
        self.update()

    def reset_simulation(self):
        """Reset the simulation with current settings"""
        self.simulation.reset()
        self.update()


class MainWindow(QMainWindow):
    """Main window class for the N-body simulator application"""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("N-Body Simulator")
        self.resize(800, 600)

        # Create the simulation widget
        self.simulation_widget = SimulationWidget()

        # Create the control panel
        self.create_control_panel()

        # Set up the main layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.addWidget(self.simulation_widget, 1)
        main_layout.addWidget(self.control_panel)

        self.setCentralWidget(main_widget)

        # Create a timer for animation
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.simulation_widget.update_simulation)
        self.timer.start(16)  # Approximately 60 FPS

    def create_control_panel(self):
        """Create the control panel with sliders and buttons"""
        self.control_panel = QWidget()
        layout = QVBoxLayout(self.control_panel)

        # Top row of controls
        top_row = QHBoxLayout()

        # Number of bodies spinner
        body_layout = QHBoxLayout()
        body_layout.addWidget(QLabel("Bodies:"))
        self.body_spinner = QSpinBox()
        self.body_spinner.setRange(2, 100)
        self.body_spinner.setValue(10)
        self.body_spinner.valueChanged.connect(self.update_body_count)
        body_layout.addWidget(self.body_spinner)
        top_row.addLayout(body_layout)

        # Time step control
        dt_layout = QHBoxLayout()
        dt_layout.addWidget(QLabel("dt:"))
        self.dt_spinner = QDoubleSpinBox()
        self.dt_spinner.setRange(0.001, 0.1)
        self.dt_spinner.setSingleStep(0.001)
        self.dt_spinner.setValue(0.01)
        self.dt_spinner.setDecimals(3)
        self.dt_spinner.valueChanged.connect(self.update_dt)
        dt_layout.addWidget(self.dt_spinner)
        top_row.addLayout(dt_layout)

        # Gravity constant
        gravity_layout = QHBoxLayout()
        gravity_layout.addWidget(QLabel("G:"))
        self.gravity_spinner = QDoubleSpinBox()
        self.gravity_spinner.setRange(0.1, 20.0)
        self.gravity_spinner.setSingleStep(0.1)
        self.gravity_spinner.setValue(6.67)
        self.gravity_spinner.valueChanged.connect(self.update_gravity)
        gravity_layout.addWidget(self.gravity_spinner)
        top_row.addLayout(gravity_layout)

        # Softening parameter
        soft_layout = QHBoxLayout()
        soft_layout.addWidget(QLabel("Soft:"))
        self.soft_spinner = QDoubleSpinBox()
        self.soft_spinner.setRange(0.01, 1.0)
        self.soft_spinner.setSingleStep(0.01)
        self.soft_spinner.setValue(0.1)
        self.soft_spinner.setDecimals(2)
        self.soft_spinner.valueChanged.connect(self.update_softening)
        soft_layout.addWidget(self.soft_spinner)
        top_row.addLayout(soft_layout)

        layout.addLayout(top_row)

        # Second row - boundary condition selector
        boundary_layout = QHBoxLayout()
        boundary_layout.addWidget(QLabel("Boundary:"))
        self.boundary_combo = QComboBox()
        self.boundary_combo.addItems(["bounce", "periodic", "open"])
        self.boundary_combo.currentTextChanged.connect(self.update_boundary_condition)
        boundary_layout.addWidget(self.boundary_combo)

        # Trail length
        trail_layout = QHBoxLayout()
        trail_layout.addWidget(QLabel("Trail:"))
        self.trail_spinner = QSpinBox()
        self.trail_spinner.setRange(0, 200)
        self.trail_spinner.setValue(50)
        self.trail_spinner.valueChanged.connect(self.update_trail_length)
        trail_layout.addWidget(self.trail_spinner)

        boundary_layout.addLayout(trail_layout)
        layout.addLayout(boundary_layout)

        # Bottom row of buttons
        button_layout = QHBoxLayout()

        # Play/Pause button
        self.pause_button = QPushButton("Pause")
        self.pause_button.setCheckable(True)
        self.pause_button.clicked.connect(self.toggle_pause)
        button_layout.addWidget(self.pause_button)

        # Reset button
        reset_button = QPushButton("Reset")
        reset_button.clicked.connect(self.reset_simulation)
        button_layout.addWidget(reset_button)

        # View controls
        view_reset_button = QPushButton("Reset View")
        view_reset_button.clicked.connect(self.simulation_widget.reset_view)
        button_layout.addWidget(view_reset_button)

        # Toggle trails button
        self.trails_button = QPushButton("Trails")
        self.trails_button.setCheckable(True)
        self.trails_button.setChecked(True)
        self.trails_button.clicked.connect(self.toggle_trails)
        button_layout.addWidget(self.trails_button)

        # Toggle vectors button
        self.vectors_button = QPushButton("Vectors")
        self.vectors_button.setCheckable(True)
        self.vectors_button.clicked.connect(self.toggle_vectors)
        button_layout.addWidget(self.vectors_button)

        layout.addLayout(button_layout)

    def update_body_count(self, value):
        """Update the number of bodies in the simulation"""
        self.simulation_widget.simulation.reset(num_bodies=value)

    def update_dt(self, value):
        """Update the time step of the simulation"""
        self.simulation_widget.simulation.dt = value

    def update_gravity(self, value):
        """Update the gravitational constant"""
        self.simulation_widget.simulation.G = value

    def update_softening(self, value):
        """Update the softening parameter"""
        self.simulation_widget.simulation.softening = value

    def update_trail_length(self, value):
        """Update the maximum trail length"""
        self.simulation_widget.simulation.max_trail_length = value

        # Trim existing trails if they're longer than the new max
        for i in range(self.simulation_widget.simulation.num_bodies):
            while len(self.simulation_widget.simulation.trails[i]) > value:
                self.simulation_widget.simulation.trails[i].pop(0)

    def update_boundary_condition(self, condition):
        """Update the boundary condition method"""
        self.boundary_condition = condition

    def toggle_pause(self):
        """Toggle the simulation pause state"""
        self.simulation_widget.toggle_pause()
        self.pause_button.setText("Play" if self.simulation_widget.paused else "Pause")

    def toggle_trails(self):
        """Toggle the display of trails"""
        self.simulation_widget.toggle_trails()

    def toggle_vectors(self):
        """Toggle the display of velocity vectors"""
        self.simulation_widget.toggle_vectors()

    def reset_simulation(self):
        """Reset the simulation with current settings"""
        self.simulation_widget.reset_simulation()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())