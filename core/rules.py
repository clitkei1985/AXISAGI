# core/rules.py

from typing import Dict

class RuleViolation(Exception):
    """Raised whenever a rule is violated or unknown."""
    pass

class Rules:
    """
    Global rule registry. Rules themselves cannot be modified at runtime from code;
    only enabled/disabled via Admin endpoints (which call set_rule).
    """
    _rules: Dict[str, bool] = {}

    @classmethod
    def load_rules(cls):
        """
        Initialize the rule set and default enabled‐state for each rule.
        These keys must match exactly what we use elsewhere.
        """
        cls._rules = {
            "NO_FEATURE_DELETION": True,
            "NO_CODE_SIMPLIFICATION": True,
            "NO_RULE_CIRCUMVENTION": True,
            "REQUIREMENTS_REFRESH_REGULARLY": True,
            "FILE_SPLIT_IF_OVER_200_LINES": True,
            "PROVIDE_DIRECTORY_STRUCTURE_FOR_NEW_FILES": True,
            "TAG_EACH_FILE_WITH_VERSION_NUMBER": True,
            "GOVERNED_BY_IMMUTABLE_REQUIREMENTS": True,
        }

    @classmethod
    def list(cls) -> Dict[str, bool]:
        """Return the full dictionary of rule_name → enabled_flag."""
        return dict(cls._rules)

    @classmethod
    def enforce(cls, rule: str):
        """
        If the rule is not in our set or is disabled, raise RuleViolation.
        Otherwise, do nothing (rule is satisfied).
        """
        if rule not in cls._rules:
            raise RuleViolation(f"Rule not recognized: {rule}")
        if not cls._rules[rule]:
            raise RuleViolation(f"Rule '{rule}' is currently disabled.")

    @classmethod
    def set_rule(cls, rule: str, enabled: bool):
        """
        Enable or disable a rule. Admin‐only operation.
        Raises RuleViolation if rule not in set.
        """
        if rule not in cls._rules:
            raise RuleViolation(f"Rule not recognized: {rule}")
        cls._rules[rule] = enabled

# Load defaults at import time
Rules.load_rules()
