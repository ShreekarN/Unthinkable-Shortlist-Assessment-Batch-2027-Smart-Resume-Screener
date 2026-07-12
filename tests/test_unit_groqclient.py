import json

import pytest

from app import groqclient


def testCleanJsonRemovesMarkdownFence():
    raw = "```json\n{\"name\": \"Alex\"}\n```"
    cleaned = groqclient.cleanJson(raw)
    assert cleaned == "{\"name\": \"Alex\"}"


def testParseJsonValid():
    data = groqclient.parseJson('{"score": 8, "justification": "Good fit"}')
    assert data["score"] == 8


def testParseJsonInvalidRaises():
    with pytest.raises(json.JSONDecodeError):
        groqclient.parseJson("not json")


def testGetClientMissingKey(monkeypatch):
    monkeypatch.setattr(groqclient, "groqApiKey", "")
    with pytest.raises(ValueError, match="GROQAPIKEY"):
        groqclient.getClient()


def testCallGroqJsonRetriesOnce(monkeypatch):
    calls = {"count": 0}

    def fakeCallGroq(systemPrompt, userPrompt):
        calls["count"] += 1
        if calls["count"] == 1:
            return "bad json"
        return '{"score": 7, "justification": "ok", "strengths": [], "gaps": []}'

    monkeypatch.setattr(groqclient, "callGroq", fakeCallGroq)
    data = groqclient.callGroqJson("system", "user")
    assert data["score"] == 7
    assert calls["count"] == 2
