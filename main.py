import sys
from PySide6.QtWidgets import QApplication

from gui import MainWindow, SimulationWidget
from n_body_simulator import NBodySimulation


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow(SimulationWidget(NBodySimulation(num_bodies=10)))
    window.show()
    sys.exit(app.exec())