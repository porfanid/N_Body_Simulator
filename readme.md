# N-Body Simulator

This project is an N-body simulation that models the gravitational interactions between multiple bodies. The simulation can run on both CPU and GPU, leveraging the power of parallel processing for improved performance.

## Features

- **CPU and GPU Support**: Automatically switches between CPU and GPU based on availability.
- **Interactive GUI**: Control the simulation parameters and visualize the results in real-time.
- **Customizable Parameters**: Adjust the number of bodies, time step, gravitational constant, softening parameter, and more.
- **Trail and Vector Visualization**: Toggle the display of trails and velocity vectors for better understanding of the simulation dynamics.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/porfanid/n_body_simulator.git
    cd n_body_simulator
    ```

2. Create a virtual environment and activate it:
    ```sh
    python3 -m venv venv
    source venv/bin/activate
    ```

3. Install the required packages:
    - CPU version:
    ```sh
    pip install -r requirements.txt
    ```
    - GPU version:
    ```sh
    pip install -r requirements_gpu.txt
    ```

## Usage

1. Run the simulation:
    ```sh
    python main.py
    ```

2. The GUI will open, allowing you to control the simulation parameters and visualize the results.

## GUI Controls

- **Pause/Play**: Toggle the simulation between paused and running states.
- **Reset**: Reset the simulation with the current settings.
- **Reset View**: Reset the view to the default position.
- **Trails**: Toggle the display of trails behind the bodies.
- **Vectors**: Toggle the display of velocity vectors.

## Customization

You can customize the simulation parameters through the GUI or by modifying the code directly:

- **Number of Bodies**: Adjust the number of bodies in the simulation.
- **Time Step (dt)**: Change the time step for the simulation.
- **Gravitational Constant (G)**: Modify the gravitational constant.
- **Softening Parameter**: Adjust the softening parameter to avoid numerical instability.
- **Boundary**: Set the boundary of the simulation space.

## Code Structure

- `main.py`: Entry point of the application.
- `gui/`: Contains the GUI components.
- `n_body_simulator/`: Contains the simulation logic.
  - `base_simulation.py`: Base class for the simulation.
  - `simulator_cpu.py`: CPU-specific implementation.
  - `simulator_gpu.py`: GPU-specific implementation.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.