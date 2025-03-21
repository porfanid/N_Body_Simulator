from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath
from PySide6.QtWidgets import QWidget
from numpy import sqrt


class SimulationWidget(QWidget):
    """Widget for visualizing the N-body simulation"""

    def __init__(self, simulation, parent=None):
        super().__init__(parent)
        #self.setMinimumSize(600, 600)

        # Set up the simulation
        self.simulation = simulation
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
            radius = max(2, sqrt(mass) * 1.5)
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