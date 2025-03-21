from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QPushButton, QHBoxLayout, QDoubleSpinBox, QLabel, QSpinBox, QVBoxLayout, QWidget, \
    QMainWindow, QComboBox


class MainWindow(QMainWindow):
    """Main window class for the N-body simulator application"""

    def __init__(self, simulation_widget):
        super().__init__()

        self.setWindowTitle("N-Body Simulator")
        self.resize(800, 600)

        # Create the simulation widget
        self.simulation_widget = simulation_widget

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
        if self.simulation_widget.simulation.is_gpu():
            self.body_spinner.setRange(2, 10000)
        else:
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