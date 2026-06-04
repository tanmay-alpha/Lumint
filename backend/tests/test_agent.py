import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_agent_investigate_tool_usage():
    """Verify that the agent ReAct loop executes tools and reaches a final answer."""
    # We mock ask_groq to simulate the ReAct loop:
    # Call 1: Decide to check the URL using the check_url tool.
    # Call 2: Decide to search the database.
    # Call 3: Formulate the final answer.
    
    mock_responses = [
        # Response 1: Wants to check the URL
        {
            "choices": [
                {
                    "message": {
                        "content": "Thought: I should start by checking if the URL provided is a phishing URL.\nAction: check_url(http://malicious-login-chase.com)"
                    }
                }
            ]
        },
        # Response 2: Wants to check cases
        {
            "choices": [
                {
                    "message": {
                        "content": "Thought: The URL is suspicious with a risk score of 80. Now I should search for existing cases with 'chase' to see if there's related activity.\nAction: search_database_cases(chase)"
                    }
                }
            ]
        },
        # Response 3: Final Answer
        {
            "choices": [
                {
                    "message": {
                        "content": "Thought: I have gathered all necessary information. I will compile the final report.\nFinal Answer: Investigation complete. The URL http://malicious-login-chase.com represents a high-risk phishing threat targeting Chase Bank. Action is recommended to block the domain."
                    }
                }
            ]
        }
    ]
    
    with patch("ai.agent.ask_groq", side_effect=mock_responses) as mock_ask:
        r = client.post("/api/ai/investigate", json={"query": "Investigate http://malicious-login-chase.com"})
        assert r.status_code == 200
        data = r.json()
        assert "final_report" in data
        assert "http://malicious-login-chase.com" in data["final_report"]
        assert data["steps_taken"] == 3
        assert mock_ask.call_count == 3

def test_agent_investigate_fallback_on_error():
    """Verify that the agent handles failures gracefully."""
    with patch("ai.agent.ask_groq", side_effect=Exception("API limit reached")):
        r = client.post("/api/ai/investigate", json={"query": "Investigate suspicious-link.org"})
        # The agent should handle this internally or return 500 error gracefully. Let's see:
        # Our endpoint raises a 500 HTTPException on agent failure.
        assert r.status_code == 500
        assert "Agent investigation failed" in r.json()["detail"]
