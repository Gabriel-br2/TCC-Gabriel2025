from LLM.source.LLM_base import Base_Agent


class Agent_Thinker(Base_Agent):
    def __init__(self, llm_source="local"):
        self.tag = "current_turn_data"
        super().__init__(
            agent_name="THINKER",
            llm_source=llm_source,
            model="deepseek/deepseek-r1-0528-qwen3-8b:free",
        )

    def _set_initial_context(self):
        self.context = """
            You are an Agent participating in a collective environment.
            Context:
            - You are in a collaborative game with 3 other agents (Humans or LLMs).
            - Goal: Find a hidden specific configuration (pose: x, y, rz) for the objects.
            - Communication: Strictly non-verbal (movement only).

            Your Cognitive Architecture (Mandatory Process):
            1. Social Learning:
            - Attention: Focus on specific movements of other players.
            - Retention: Formulate a hypothesis/rule based on the group's history.
            - Motivation: Decide if you are exploring (seeking info) or exploiting (showing info).

            2. Theory of Mind (ToM):
            - Infer the beliefs and intents of other players. Do they know the goal? Are they confused?.

            Analyze the provided game state data and generate a JSON plan as in the pattern.
            """

    def _get_return_json_pattern(self) -> dict:
        root = dict()

        root["attention_focus"] = (
            "Describe which piece movement caught your attention in the last rounds and why.",
        )

        root["theory_of_mind_inference"] = (
            "Your inference about the other players' mental states.",
        )

        root["retention_hypothesis"] = (
            "The current rule or pattern you have encoded in memory about the hidden goal.",
        )

        # root["motivation_drive"] = (
        #    "Why are you acting? Options: 'imitation' (copying others), 'demonstration' (teaching others), or 'exploration' (testing hypothesis).",
        # )

        root["intended_outcome"] = (
            "A high-level description of what you want to achieve physically to fulfill your motivation."
        )

        return root

    def think(self, current_turn_data: dict):
        self.generate_payload(msg=current_turn_data, msg_tag=self.tag)
        response = self.request()  # "screendata/last.jpg")

        return response


# --------------------------------------------------------------------------------------------


class Agent_Player(Base_Agent):
    def __init__(self, llm_source="local"):
        self.tag = "Thinker interpretation from actual turn"
        super().__init__(
            agent_name="PLAYER",
            llm_source=llm_source,
            model="deepseek/deepseek-r1-0528-qwen3-8b:free",
        )

    def _set_initial_context(self):
        self.context = (
            self.context
        ) = """
            You are the player agent.
            Your task is to execute the game movement based on the cognitive plan provided by the agent Thinker.

            The game mechanics have strict constraints:
            1. MOVEMENT: You can move the object in X and Y axes (dx, dy).
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
        root["dx"] = (
            "REQUIRED ONLY IF action is 'move'. Represents the delta change in X pixels.",
        )
        root["dy"] = (
            "REQUIRED ONLY IF action is 'move'. Represents the delta change in Y pixels.",
        )
        return root

    def play(self, thinker_analysis: dict):
        self.generate_payload(msg=thinker_analysis, msg_tag=self.tag)
        response = self.request()
        return response
