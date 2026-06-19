"""Tests for the structured AgentAction parser.

The ReAct agent used to parse LLM output with a fragile regex
``r"Action:\\s*(\\w+)\\((.+?)\\)"``. Real LLM outputs drift, so the
parser now expects a JSON object (optionally inside a markdown code
fence) and validates it against a Pydantic ``AgentAction`` model.

These tests exercise the parser in isolation (no LLM, no network) and
also confirm the new class is importable from ``ai.agent``.
"""

import json

import pytest


# ─────────────────────────────────────────────────────────────────────
# Importability — required by the audit task
# ─────────────────────────────────────────────────────────────────────


def test_agent_action_class_is_importable():
    """AgentAction must be importable from ai.agent."""
    from ai.agent import AgentAction

    assert AgentAction is not None
    fields = AgentAction.model_fields
    assert set(fields.keys()) == {"thought", "tool", "argument"}
    # tool field must be constrained to the four registered tools.
    tool_field = fields["tool"]
    allowed = set(getattr(tool_field, "args", []) or [])
    # Pydantic v2 Literal → metadata json_schema.enum
    enum_vals = set((tool_field.metadata or [{}])[0].get("__metadata__", {}).get("values", []) if False else [])
    # Safer: pull the Literal from the annotation directly.
    from typing import get_args, get_origin
    ann = AgentAction.model_fields["tool"].annotation
    # Pydantic v2 wraps Literal as a `Literal` object — use get_args.
    literal_vals = set()
    if hasattr(ann, "__args__"):
        literal_vals = set(get_args(ann))
    assert literal_vals == {
        "check_url",
        "check_upi_receipt",
        "search_database_cases",
        "check_kyc_document",
    }


# ─────────────────────────────────────────────────────────────────────
# _parse_agent_action — direct / fence / failure paths
# ─────────────────────────────────────────────────────────────────────


def test_parse_agent_action_direct_json():
    from ai.agent import _parse_agent_action

    payload = {
        "thought": "I should check this URL first.",
        "tool": "check_url",
        "argument": "http://malicious-login-chase.com",
    }
    raw = json.dumps(payload)
    action = _parse_agent_action(raw)
    assert action is not None
    assert action.thought == payload["thought"]
    assert action.tool == "check_url"
    assert action.argument == payload["argument"]


def test_parse_agent_action_code_fence_recovery():
    """On first-attempt failure, recover from ```json ... ``` fence."""
    from ai.agent import _parse_agent_action

    raw = (
        "Sure, here you go:\n"
        "```json\n"
        "{\n"
        '  "thought": "Check the UTR length.",\n'
        '  "tool": "check_upi_receipt",\n'
        '  "argument": "123456789012"\n'
        "}\n"
        "```\n"
    )
    action = _parse_agent_action(raw)
    assert action is not None
    assert action.tool == "check_upi_receipt"
    assert action.argument == "123456789012"


def test_parse_agent_action_rejects_unknown_tool():
    """A tool name not in the Literal must fail validation, not 500."""
    from ai.agent import _parse_agent_action

    raw = json.dumps({
        "thought": "do something risky",
        "tool": "rm_rf",
        "argument": "/",
    })
    assert _parse_agent_action(raw) is None


def test_parse_agent_action_rejects_legacy_regex_format():
    """The legacy 'Action: tool_name(arg)' format must NOT parse — it
    never produced valid JSON in the first place, and silently accepting
    it would mask LLM drift."""
    from ai.agent import _parse_agent_action

    legacy = (
        "Thought: I should check the URL.\n"
        "Action: check_url(http://malicious-login-chase.com)"
    )
    assert _parse_agent_action(legacy) is None


def test_parse_agent_action_empty_and_garbage():
    """Empty input and pure prose must return None, not raise."""
    from ai.agent import _parse_agent_action

    assert _parse_agent_action("") is None
    assert _parse_agent_action("Just thinking out loud, no JSON here.") is None
    assert _parse_agent_action("```json\n{not valid json at all\n```") is None


# ─────────────────────────────────────────────────────────────────────
# Agent loop — ensure parser failure does NOT raise (no 500)
# ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_agent_does_not_500_on_unparseable_output():
    """If every step produces unparseable prose, the agent must
    gracefully time out with a structured report, not raise."""
    from ai.agent import FraudInvestigatorAgent

    prose_response = {
        "choices": [{"message": {"content": "I think therefore I am."}}]
    }

    class _FakeGroq:
        async def __call__(self, *args, **kwargs):  # noqa: D401
            return prose_response

    # Patch the symbol the agent imported, so the agent's call resolves
    # to our fake regardless of how the live client is wired.
    import ai.agent as agent_mod

    original = agent_mod.ask_groq
    agent_mod.ask_groq = _FakeGroq()
    try:
        agent = FraudInvestigatorAgent(max_steps=2)
        result = await agent.run("investigate this")
    finally:
        agent_mod.ask_groq = original

    assert isinstance(result, dict)
    assert "final_report" in result
    # The timeout message is the structured fallback — not an exception.
    assert "Investigation timeout" in result["final_report"] or "Investigation" in result["final_report"]
    assert result["steps_taken"] == 2