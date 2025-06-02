## TCC-Gabriel2025

This project is a simulation developed for my TCC (Trabalho de Conclusão de Curso - Course Conclusion Work) in Automation Engineering at the Federal University of Rio Grande, supervised by Professor Rodrigo da Silva Guerra. It involves multiple players (humans and LLMs) controlling objects in a shared environment, with the secret objective that the user himself must discover. The project utilizes Pygame for visualization, Pymunk for physics simulation, and network communication for multi-player interaction.

This README provides a basic overview of the project. For more detailed information, please refer to the code and comments within the project files.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/TCC-Gabriel2025.git
    cd TCC-Gabriel2025
    ```

2.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Dependencies

The project relies on the following libraries:

*   Pygame: For game visualization and user input.
*   Pymunk: For physics simulation.
*   PyYAML: For reading configuration files.

You can install these dependencies using pip:

```bash
pip install pygame pymunk pyyaml
```

### How to Run

1.  **Start the server:**
    ```bash
    python mainServer.py
    ```

2.  **Start the game client(s) in separate terminals:**
    ```bash
    python mainGame.py
    ```
Make sure the server is running before starting the game clients.

3. **DEBUG Option, open 4 clients in the same terminal:**
    ```bash
    chmod +x test.sh
    ./test.sh
    ```

### Code Explanation

*   **`config.yaml`:** Contains the game configuration, such as screen dimensions, server IP and port, and game parameters.
*   **`mainServer.py`:** The server application that manages the game state and communication between clients.
*   **`mainGame.py`:** The client application that handles user input, renders the game, and communicates with the server.
*   **`screen.py`:** The code that uses pygame to display the window to the user
*   **`objects/`:** Contains the definitions for the game objects (generic and T-shaped).
*   **`player/`:** Contains the definition for the human player and the LLM player.
*   **`utils/`:** Contains utility modules for configuration, network communication, and calculations.

### Project Structure

```
TCC-Gabriel2025/
├── config/
│   ├── config.yaml
│   └── color.yaml
├── objects/
│   ├── generic.py
│   └── TShape.py
├── player/
│   └── human.py
│   └── linguisticModel.py
├── utils/
│   ├── config.py
│   ├── network.py
│   └── objective.py
├── mainGame.py
└── mainServer.py
└── screen.py
```

### Common Errors

*   **ConnectionRefusedError:**
    *   **Cause:** The server is not running or is not accessible.
    *   **Solution:** Ensure the server is running and check the server IP and port configuration in `config.yaml`.

*   **ModuleNotFoundError:**
    *   **Cause:** A required library is not installed.
    *   **Solution:** Make sure you have installed all the dependencies listed in the "Dependencies" section.

*   **JSONDecodeError:**
    *   **Cause:** There is an issue with the data being sent or received over the network.
    *   **Solution:** Check the network connection and ensure that the server and clients are running correctly.

### Authorship
* Author: Gabriel Rocha de Souza
* Orientation: Rodrigo da Silva Guerra
* Co-Orientation: Marcelo Rita Pias
* Institution: Universidade Federal de Rio Grande (FURG)
* Course: Automation Engineering
* Year: 2025