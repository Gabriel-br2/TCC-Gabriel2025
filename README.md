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

TCC-Gabriel2025-main/
├── mainGame.py               # Game client main file
├── mainServer.py             # Server main file
├── screen.py                 # Rendering utilities
├── teste.py                  # Test scripts
├── config/                   # Configuration files
│   ├── color.yaml            # Player color settings
│   └── config.yaml           # Game parameters
├── objects/                  # Game objects
│   ├── generic.py
│   ├── teewee.py
│   └── \_shape/
│       └── *shape*.py
├── players/                  # Players logic
│   └── human.py
│   └── linguisticModel.py    
├── utils/                    # Utility modules
│   ├── colision.py
│   ├── config.py
│   ├── network.py
│   └── objective.py
└── old/                      # Legacy code (version 1.0)

````

---

## 🛠️ Hardware Interface

There are **no dedicated hardware components** in this project. All interactions occur within the software environment, making the system fully platform-independent, requiring only:

- A personal computer with internet access.
- Python 3.x and required dependencies.

## 📦 Dependencies and Installation

### ✅ Required Dependencies

- Python 3.8+  
- Pygame  
- PyYAML  

All dependencies are listed in the `requirements.txt` file.

### ✅ Installing Dependencies

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

Finally, install the required Python packages:

```bash
pip install -r requirements.txt
```

### ✅ Running the System

1. Start the **server**:

```bash
python mainServer.py
```

2. Start one or more **game clients** (in different terminals or machines):

```bash
python mainGame.py
```

Ensure all participants are connected to the same network or configured for remote access.

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
  - Run `mainServer.py` on the host machine.
  - Launch `mainGame.py` on each client machine.

**Important**: The system is designed for controlled experiments with human subjects and artificial agents. Ethical protocols must be followed.

---

## ❗ Common Errors

| Error              | Cause                   | Solution                                                 |
| ------------------ | ----------------------- | -------------------------------------------------------- |
| Connection refused | Server not running      | Ensure `mainServer.py` is running before clients connect |
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
* **Prof. Dr. Rodrigo da Silva Guerra** — Academic advisor.
* **Prof. Dr. Marcelo Rita Pias** — Academic co-advisor.

Affiliated with:
**Federal University of Rio Grande (FURG)** — Center for Computational Sciences (C3), Automation Engineering.

---

## 🎓 Academic Context

This project is developed as part of the **Bachelor's Thesis (TCC)** in **Automation Engineering** at the **Federal University of Rio Grande (FURG)**.

The experimental procedures involving human participants have been **officially approved by the Research Ethics Committee (Comitê de Ética em Pesquisa - CEP)** at FURG, ensuring compliance with all applicable ethical standards.

The results and findings from this project will be:

1. **Presented as the official Bachelor's Thesis (TCC)** for the completion of the Automation Engineering degree.
2. **Subsequently converted into a scientific article** for broader dissemination and contribution to the academic community in the field of Artificial Intelligence, Human-Machine Interaction, and Social Learning Systems.

---

**Ethical Consideration:**
The participation of human subjects strictly adheres to ethical guidelines, ensuring participant consent, data privacy, and scientific integrity.

---

> **"Machines learning from humans. Humans learning from machines. Together, evolving and innovating."**
