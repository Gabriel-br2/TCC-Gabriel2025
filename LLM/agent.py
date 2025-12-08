from LLM.source.LLM_base import Base_Agent

colors = ["blue", "pink", "yellow", "cyan"]


class Agent_Thinker(Base_Agent):
    def __init__(self, iam, llm_source="local", memory_path=None):
        self.tag = "current turn"
        self.iam = iam

        super().__init__(
            agent_name="THINKER",
            llm_source=llm_source,
            model="openai/gpt-4.1-nano",
            memory_path=memory_path,
        )

    def _set_initial_context(self):
        self.context = f"""
            Context:
            - You are in a collaborative environment with 3 other agents.
            - Goal: Find a hidden objective, only placing your objects (x, y, rz).
            - Your Control: You are agent {colors[self.iam]}, You control all objects of this color. The other agents control the other colors.
            - Score: A global score (0-100%) indicates how close ALL AGENTS are to the hidden objective. Higher is better.
            - Collaboration: You MUST COLLABORATE with other agents to maximize the global score.

            INPUT:
            - Image (Current State): The provided image shows the current game state. It displays all objects for all players and the current score.
            - Object ID: The image contains each of your {colors[self.iam]} objects labeled with a unique ID (e.g., 1, 2...). You must use this ID to specify which object you want to move.
            - Memory (Historical Data): You will receive a memory (history) containing position and score data from previous rounds. Use this information to inform your strategy.
            - If the memory is empty, it means this is the first turn.
            - If the memory has 'objective reached' for any turn, it means the hidden objective was found in that turn.
                - thins positions must be used to refine your strategy. specifically, analyze how the positions of all objects (yours and others) are correlated.


            - You will receive the actual information about the game with a JSON object with the following data:
                * "actual score"`: The current global score (0-100%).
                * "actual position"`: A nested JSON object with the positions of all objects for all other players, and your objects in the format:
                    'p_[color]':
                            'obj_[id] = ["type": shape, "pos": [x, y], "rot": rz]

            where:
            - 'Shape': indicates a token for the look alike geometric form of the object (e.g., 'I', 'L', 'T', etc.).
            - 'x' and 'y': represent the object's coordinates on the 2D plane (in pixels).
            - 'rz': indicates the rotation angle of the object around the z-axis (in degrees).

            GAME_RULES AND CONSTRAINTS:
            1. Movement Constraints:
               - You can only place your objects in between 0 to 500 in X and 0 to 500 in Y.
               - The objects can rotate only +90 degrees (clockwise).
               - You cannot change objects controlled by other agents.
            2. Score Dynamics:
               - The global score reflects the collective progress of ALL agents towards the hidden objective, you must collaborate to maximize it.
               - The other players objects positions are very important to determine your objects position .

            OUTPUT, Your Cognitive Architecture (Mandatory Process):
            1. Social Learning:
            - Attention: Focus on specific movements of other players.
            - Retention: Formulate a hypothesis/rule based on the group's history.
            - Motivation: Reward driven by the Global Score (0-100%):
                a) Positive reward when d(Score)/dt > 0 (Score increases), the action was good. Negative reward when Score drops, the action was bad.
                b) Causal Attribution: You MUST attribute the change in score to the correct agent. If other agent move
                and the result score increased significantly, you must conclude that the gain was primarily **caused by a successful positioning/movement by one or more collaborating agents.
                c) Exploitation vs Exploration: If the score is rising, you should refine your position. If the score is stagnant or dropping, you should change your strategy.
                d) Statistically, there's a high chance that the other players already know the objective.

            2. Theory of Mind (ToM):
            - Infer the intent of other players: Are they optimizing correctly, Exploring the score?

            Analyze the provided game state data and generate a JSON plan as in the pattern.
            """

    def _get_return_json_pattern(self) -> dict:
        root = dict()

        root["image_interpretation"] = (
            "describe the key observations from the current game state image, focusing on the positions and orientations and intersection of all objects, especially those of other agents in reletion to yours.",
        )

        root["attention_focus"] = (
            "Identify which specific movement (by others) caused the most significant change in the score during the last steps."
        )

        root["theory_of_mind_inference"] = (
            "Infer the intent of other players: Are they optimizing correctly, Exploring the score?"
        )

        root["retention_hypothesis"] = (
            "Your current best estimate of the target configuration (x, y, rz) based on previous high-score moments."
        )

        root["motivation_drive"] = (
            "Analyze the score gradient (dScore/dt). Decide whether to go to position due to rising score or change strategy due to stagnation."
        )

        root["intended_outcome"] = (
            "Describe the precise physical adjustment (e.g., 'Rotate', 'Stop moving') you intend to perform to validate your hypothesis."
        )
        return root

    def think(self, current_turn_data: dict):
        self.generate_payload(msg=current_turn_data, msg_tag=self.tag)
        response = self.request("screendata/last.jpg")

        return response


# --------------------------------------------------------------------------------------------


class Agent_Player(Base_Agent):
    def __init__(self, iam, llm_source="local", memory_path=None):
        self.tag = "Thinker interpretation from actual turn"
        super().__init__(
            agent_name="PLAYER",
            llm_source=llm_source,
            model="openai/gpt-4.1-nano",
            memory_path=memory_path,
        )

    def _set_initial_context(self):
        self.context = (
            self.context
        ) = f"""
            Your task is to execute the game movement based on the cognitive plan provided by the agent Thinker.

            The game mechanics have strict constraints:
            1. MOVEMENT: You can put a object in position X and Y.
            - Low values result in invisible movement.

            2. ROTATION: You can ONLY rotate the object by exactly +90 degrees (clockwise).
            - You CANNOT choose arbitrary angles (like 45 or 30).
            - A single 'rotate' action equals +90 degrees.

            You must choose ONE action ('move' or 'rotate') that best aligns with the 'intended_outcome' requested by the Thinker.

            Analyze the game plan and generate a JSON command exactly as in the pattern.
            """

    def _get_return_json_pattern(self) -> dict:
        root = dict()

        root["reasoning"] = (
            "Briefly explain why this specific move or rotation helps achieve the Thinker's goal.",
        )
        root["object_id"] = ("A single integer ID of the piece you are manipulating.",)
        root["action"] = (
            "The physical action type. Must be EXACTLY 'move' or 'rotate'.",
        )
        root["x"] = (
            "REQUIRED ONLY IF action is 'move'. Represents the X pixels position to change.",
        )
        root["y"] = (
            "REQUIRED ONLY IF action is 'move'. Represents the Y pixels position to change.",
        )
        return root

    def play(self, thinker_analysis: dict):
        self.generate_payload(msg=thinker_analysis, msg_tag=self.tag)
        response = self.request()
        return response


# --------------------------------------------------------------------------------------------


class Agent_summary(Base_Agent):
    def __init__(self, iam, llm_source="local"):
        self.tag = "Resume"
        super().__init__(
            agent_name="RESUME",
            llm_source=llm_source,
            model="openai/gpt-4.1-nano",
            memory=False,
        )

    def _set_initial_context(self):
        self.context = (
            self.context
        ) = """YOU ARE A STRATEGIC SUMMARIZER AGENT. You will Receive a JSON object representing turns in an AI agent's decision-making process.
            Your goal is to transform this raw turn data into a clear, concise, and high-level executive summary.

            INPUT DATA CONTEXT
            You will receive a JSON object representing previous turn's "memory". The keys have specific meanings:

            * "previous positions"`: The state of the environment *before* the agent's action.
            * "previous score"`: The evaluation score of the "previous positions".
            * "interpretation from agent thinker"`: The agent's *thought process* and logical analysis. **This is the most important field for finding the rationale.**
            * "movements from agent player"`: The specific action or decision the agent made based on its interpretation. **This is the key decision/conclusion.**
            * "result positions"`: The state of the environment *after* the agent's action.
            * "result score"`: The evaluation score of the "result positions".

            SUMMARY GUIDELINES
            1.  **Focus on Decision and Rationale:** The summary MUST clearly state the **action taken** (from `"movements from agent player"`) and the **primary reason** for it (synthesized from `"interpretation from agent thinker"`).
            2.  **Quantify the Outcome:** Use `"previous score"` and `"result score"` to assess the impact of the move (e.g., "Score improved from 50% to 65%"). If `"result score"` is null, state that the outcome is pending.
            3.  **Be High-Level:** Do not report the raw data from `"previous positions"` or `"result positions"`. Summarize the *meaning* of the move, not the move's data.
            4.  **Language:** English.
            5.  **Tone:** Professional, direct, and objective.

            You must return ONLY a valid JSON object with the exact structure below. Do not add markdown (```json) or any text before or after the JSON object.
            """

    def _get_return_json_pattern(self) -> dict:
        root = dict()

        root["key_rationale"] = (
            "A one-sentence summary of the reason or logical justification for the decision (from 'interpretation').",
        )

        root["decision_summary"] = (
            "A one-sentence summary of the action taken (from 'movements').",
        )

        root["outcome_assessment"] = (
            "A brief statement on the result, comparing 'previous score' and 'result score'. (e.g., 'Score improved from X to Y because of ...')",
        )
        return root

    def summary(self, memory: dict):
        print(
            "========================================= summary called ========================================="
        )
        self.generate_payload(msg=memory, msg_tag=self.tag)
        response = self.request()
        return response
