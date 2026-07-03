# 🤖 Social Learning Experiment between Humans and Artificial Agents

## 📝 Project Description

This project investigates whether artificial agents can effectively participate in processes of discovery and collective learning. The system is based on a collaborative multiplayer game developed in Python using Pygame, where human players and large language models (LLMs) interact without verbal communication, relying solely on observation of each other's actions. The central goal is to evaluate if and how LLMs can integrate into social learning cycles, similar to human cultural transmission processes.

---

## ⚙️ System Behavior

The system is a networked multiplayer game with a client-server architecture. Four participants — human players and/or LLMs — simultaneously interact in a shared virtual environment. Each player is represented by a distinct, colored shape. The game mechanics encourage players to move and rotate their pieces to collectively discover and reach an unknown goal, indicated only by a percentage-based feedback system that increases as the group approaches the correct solution.

Key dynamics:

- No verbal communication is allowed; only behavioral observation.
- The system tracks and replaces participants across multiple generational cycles, analyzing knowledge transmission.
- Feedback is based on Intersection over Union (IoU) calculations of overlapping shapes.

---

## 🗂️ Code Structure

```

TCC-Gabriel2025/
├── main_game.py              # Client entry point (delegates to game.client)
├── main_server.py            # Server entry point (delegates to game.server)
├── config/                   # YAML configuration
├── game/
│   ├── shared/               # Config, protocol, shapes, collision, objective
│   ├── server/               # WebSocket server, cycle generator, monitor, logging
│   ├── client/               # Pygame UI, network client, player input
│   ├── llm/                  # LLM agents and backends (prompt engineering)
│   └── analysis/             # Post-session plotting
└── scripts/                  # Local multi-player test helpers

````

---

## 📦 Installation

First, clone the repository:

```bash
git clone https://github.com/yourusername/TCC-Gabriel2025.git
cd TCC-Gabriel2025
````

Then, create a virtual environment (optional but recommended):

```bash
python -m venv venv
source venv/bin/activate   # On Linux/Mac
venv\Scripts\activate      # On Windows
```

Install the required Python packages:

```bash
pip install -r requirements.txt
```

### Running the System

1. Start the **server**:

```bash
python3 server.py
```

2. Start one or more **game clients** (in different terminals or machines):

```bash
python3 client.py
```

### Running Automatically

For code debugging purposes, you can automatically launch the server and game clients with a single command.

1. First, make the script executable (Linux/macOS):

```bash
chmod +x scripts/run_test_human.sh

```

2. Then, to run the system:

**On Linux/macOS:**

```bash
./run_test_human.sh

```

**On Windows:**

```powershell
./run_test_human.ps1

```

---

## ⚙️ Configuration Structure

The system is configured via **YAML files** located in the `config/` directory:

- `config.yaml`: Contains game parameters such as:
  - Piece size.
  - Feedback sensitivity.
  - Server connection details.

Adjusting these files allows easy experimentation with game dynamics, user interface aesthetics, and network configurations.

---

## 📝 Notes

- Ensure Python 3.x and Pygame are properly installed (`pip install -r requirements.txt`).
- To start the system:
  - Run `main_server.py` on the host machine.
  - Launch `main_game.py` on each client machine.

**Important**: The system is designed for controlled experiments with human subjects and artificial agents. Ethical protocols must be followed.

---

## ❗ Common Errors

| Error              | Cause                   | Solution                                                 |
| ------------------ | ----------------------- | -------------------------------------------------------- |
| Connection refused | Server not running      | Ensure `main_server.py` is running before clients connect |
| Display issues     | Pygame not installed    | Run `pip install pygame`                                 |
| YAML parsing error | Incorrect config syntax | Validate YAML files using online validators              |
| Game crash on move | Invalid object state    | Ensure proper initialization of game objects             |

---

## 📌 Version

**Current Version:** `2.0`

**Version History:**

* **v1.0** — Initial system with collision-based control via mouse manipulation of pieces.
* **v2.0** — Refactored to a multiplayer collaborative game focusing on social learning, with client-server architecture and generational knowledge transmission.

---

## 👥 Team

* **Gabriel Rocha de Souza** — Development, research, and documentation.
* **Matheus P. Silveira** — Development, code refactoring, implementation and professionalization. 
* **Prof. Dr. Rodrigo da Silva Guerra** — Academic advisor.

Affiliated with:
**Federal University of Rio Grande (FURG)** — Center for Computational Sciences (C3), Automation Engineering.

---

## 🎓 Academic Context

This project is developed as part of Gabriel R. Souza **Bachelor's Thesis** in **Automation Engineering** at the **Federal University of Rio Grande (FURG)**.

The experimental procedures involving human participants have been **officially approved by the Research Ethics Committee (Comitê de Ética em Pesquisa - CEP)** at FURG, ensuring compliance with all applicable ethical standards.

The results and findings from this project will be:

1. **Presented as the official Bachelor's Thesis** for the completion of the Automation Engineering degree.
2. **Subsequently converted into a scientific article** for broader dissemination and contribution to the academic community in the field of Artificial Intelligence, Human-Machine Interaction, and Social Learning Systems.

---

**Ethical Consideration:**
The participation of human subjects strictly adheres to ethical guidelines, ensuring participant consent, data privacy, and scientific integrity.

---

> **"Machines learning from humans. Humans learning from machines. Together, evolving and innovating."**
