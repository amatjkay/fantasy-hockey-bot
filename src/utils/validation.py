from typing import Dict
import jsonschema

PLAYER_STATS_SCHEMA = {
    "type": "object",
    "properties": {
        "players": {
            "type": "object",
            "patternProperties": {
                "^[0-9]{4}-[0-9]{2}-[0-9]{2}$": {
                    "type": "object",
                    "properties": {
                        "grade": {"type": "string"},
                        "weekly_appearances": {"type": "integer"},
                        "appearances": {"type": "object"}
                    },
                    "required": ["grade", "weekly_appearances", "appearances"]
                }
            }
        }
    },
    "required": ["players"]
}

def validate_player_stats(data: Dict) -> bool:
    try:
        jsonschema.validate(data, PLAYER_STATS_SCHEMA)
        return True
    except jsonschema.exceptions.ValidationError:
        return False 