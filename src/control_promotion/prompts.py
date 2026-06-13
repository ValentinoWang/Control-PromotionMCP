from __future__ import annotations


PROMPTS = {
    "review-control-candidate": {
        "description": "Review a proposed rule, guard, skill, or remediation and decide its control level.",
        "arguments": [
            {"name": "candidate", "description": "Candidate text to review.", "required": True},
            {"name": "evidence_paths", "description": "Optional comma-separated evidence paths.", "required": False},
        ],
        "template": (
            "Review this control candidate using the control-promotion MCP tools. "
            "Call inspect_project, evaluate_control_candidate, and render_smell_gate_report.\n\n"
            "Candidate:\n{candidate}\n\nEvidence paths: {evidence_paths}"
        ),
    },
    "promote-experience": {
        "description": "Turn an incident, repeated fix, or experience into a control asset decision.",
        "arguments": [
            {"name": "experience", "description": "Raw experience or incident narrative.", "required": True},
        ],
        "template": (
            "Classify this experience into a failure class, route it to the right control destination, "
            "and list proof obligations before promotion.\n\n{experience}"
        ),
    },
    "retire-guard": {
        "description": "Assess whether an old guard can be retired after stronger prevention exists.",
        "arguments": [
            {"name": "guard", "description": "Guard or control to assess.", "required": True},
            {"name": "replacement", "description": "Stronger replacement control.", "required": False},
        ],
        "template": (
            "Assess whether this guard can be retired. Check overlap, replacement strength, "
            "required proof, and verification commands.\n\nGuard: {guard}\nReplacement: {replacement}"
        ),
    },
}


def render_prompt(name: str, arguments: dict[str, str]) -> str:
    prompt = PROMPTS[name]
    values = {argument["name"]: arguments.get(argument["name"], "") for argument in prompt["arguments"]}
    return prompt["template"].format(**values)
