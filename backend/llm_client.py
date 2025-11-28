import json
from typing import Any, Dict

import requests

from .models import IssueRaw, IssueAnalysis


class LLMConfigError(Exception):
    pass


def _build_prompt(issue: IssueRaw) -> str:
    """Create a prompt string for the Ollama model."""

    # Clean comments first so we don't put any backslashes inside f-strings
    cleaned_comments: list[str] = []
    for c in issue.comments:
        safe = (c or "").replace("\n", " ")
        cleaned_comments.append(f"- {safe}")

    comments_block = "\n\n".join(cleaned_comments) or "No comments on this issue yet."

    prompt = f"""You are a senior engineer helping triage GitHub issues.

You will be given:
- Issue title
- Issue body
- Issue comments

Your task is to return a JSON object with the following schema:

{{
  "summary": "One-sentence summary of the main problem or request.",
  "type": "One of: bug, feature_request, documentation, question, other.",
  "priority_score": "A number from 1 (low) to 5 (critical), with a short justification.",
  "suggested_labels": ["2-4 short labels such as 'bug', 'frontend', 'auth'."],
  "potential_impact": "A short sentence describing impact on users if this is a bug, or 'N/A' otherwise."
}}

Rules:
- Respond with only JSON. No markdown, no extra commentary.
- The JSON must be valid and parseable by a strict JSON parser.
- Keep the text concise but informative.

Here is the GitHub issue:

Title:
{issue.title}

Body:
{issue.body}

Comments:
{comments_block}
"""

    # Strip indentation
    return "\n".join(line.strip() for line in prompt.splitlines())


def _parse_json_from_text(text: str) -> Dict[str, Any]:
    """Try to parse JSON robustly from the model output."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            snippet = text[start : end + 1]
            return json.loads(snippet)
        raise


def analyze_issue_with_llm(
    issue: IssueRaw,
    ollama_base_url: str = "http://127.0.0.1:11434",
    ollama_model: str = "llama3",
) -> IssueAnalysis:
    """Call a local Ollama model and turn the response into IssueAnalysis."""
    if not ollama_model:
        raise LLMConfigError("OLLAMA_MODEL is not set. Please set it to a model you pulled in Ollama.")

    prompt = _build_prompt(issue)

    url = f"{ollama_base_url.rstrip('/')}/api/chat"
    payload = {
        "model": ollama_model,
        "stream": False,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an experienced software engineer helping triage GitHub issues. "
                    "You only respond with valid JSON following the requested schema."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    }

    try:
        resp = requests.post(url, json=payload, timeout=120)
    except requests.RequestException as e:
        raise LLMConfigError(f"Could not connect to Ollama at {ollama_base_url}: {e}")

    if resp.status_code >= 400:
        raise LLMConfigError(f"Ollama API error: {resp.status_code} - {resp.text}")

    data = resp.json()

    # Non-streaming chat responses: {"message": {"content": "..."}}
    try:
        generated = data.get("message", {}).get("content", "")
    except AttributeError:
        generated = str(data)

    if not generated:
        raise LLMConfigError("Ollama returned an empty response.")

    parsed = _parse_json_from_text(generated)

    labels = parsed.get("suggested_labels", [])
    if not isinstance(labels, list):
        labels = [str(labels)]

    return IssueAnalysis(
        summary=str(parsed.get("summary", "")).strip(),
        type=str(parsed.get("type", "other")).strip(),
        priority_score=str(parsed.get("priority_score", "")).strip(),
        suggested_labels=[str(x).strip() for x in labels],
        potential_impact=str(parsed.get("potential_impact", "")).strip(),
    )
