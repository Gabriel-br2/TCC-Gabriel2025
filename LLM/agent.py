from LLM.source.LLM_base import Base_Agent


class Agent_Thinker(Base_Agent):
    def __init__(self, llm_source="local"):
        self.tag = "current_turn"
        super().__init__(agent_name="THINKER", llm_source=llm_source, model="llava")

    def _set_initial_context(self):
        self.context = """Analyze the provided image and generate a JSON with the following fields:
                        - last actions: a list of the consequences of the actions you took in the previous turns
                        - position: coordinates or bounding box of the relevant object in the image (x, y, width, height)
                        - interpretation: textual description of what you see in the image
                        - action_hint: an indication of how to achieve a specific goal related to the object in the image

                        return only the JSON, without further explanation."""

    def _get_return_json_pattern(self) -> dict:
        root = dict()
        root["last actions"] = (
            "A list of the consequences of the actions you take in the previous turns.",
        )
        root["position"] = (
            "Your detailed analysis of agent positions in the previous turn, including movement deltas.",
        )
        root["interpretation"] = (
            "Your detailed analysis of what happened in previous turns: actions, results, and learnings.",
        )
        root["action_hint"] = (
            "Your detailed analysis of what should happen in the next turns: suggested actions and expected results."
        )

    def think(self, current_turn_data: dict):
        self.generate_payload(msg=current_turn_data, msg_tag=self.tag)
        response = self.request("screendata/last.jpg")

        return response


# --------------------------------------------------------------------------------------------


class Agent_Player(Base_Agent):
    def __init__(self, llm_source="local"):
        self.tag = "Thinker"
        super().__init__(agent_name="PLAYER", llm_source=llm_source, model="qwen:14b")

    def _set_initial_context(self):
        self.context = """Your task is to analyze the user's Game interpretation and generate a SINGLE JSON object representing ONE action.
                          You must choose ONLY ONE of the two possible actions: 'move' or 'rotate'. Never return both.

                          1.  If the appropriate action is a movement, use this structure for exemple:
                              {'action': 'move', 'object_id': 0, 'dx': 10, 'dy': -5}

                          2.  If the appropriate action is a rotation, use this structure for exemple:
                              {'action': 'rotate', 'object_id': 0}

                          Analyze the interpretation below and return only the single JSON object for the correct action."""

    def _get_return_json_pattern(self) -> dict:
        root = dict()
        root["action"] = (
            "The action to be performed. The value must be EXACTLY 'move' or 'rotate'.",
        )
        root["object_id"] = (
            "The numeric (integer) ID of the game object to be affected.",
        )
        root["dx"] = (
            "USED ONLY IF the action is 'move'. Represents the delta change in the horizontal position in pixels then you can make big moves(X-axis).",
        )
        root["dy"] = (
            "USED ONLY IF the action is 'move'. Represents the delta change in the vertical position in pixels then you can make big moves(Y-axis)."
        )

    def play(self, thinker_analysis: dict):
        self.generate_payload(msg=thinker_analysis, msg_tag=self.tag)
        response = self.request()
        return response
