"""NLP extraction for predicate/object from natural language queries.

Extracts semantic structure from user requests like:
  "fire off a quick note to Sarah" -> predicate: "send", object: "message"
"""

import os
import re
from dataclasses import dataclass

from openai import OpenAI

# Common predicate mappings (fallback for non-LLM extraction)
PREDICATE_MAP: dict[str, str] = {
    # send variants
    "fire off": "send",
    "shoot": "send",
    "drop": "send",
    "ping": "send",
    "DM": "send",
    # read variants
    "check out": "read",
    "look at": "read",
    "pull up": "read",
    "grab": "read",
    # delete variants
    "nuke": "delete",
    "trash": "delete",
    "get rid of": "delete",
    "remove": "delete",
    # update variants
    "tweak": "update",
    "fix": "update",
    "modify": "update",
    "edit": "update",
}

# Common object mappings
OBJECT_MAP: dict[str, str] = {
    "note": "message",
    "DM": "message",
    "text": "message",
    "ping": "message",
    "doc": "document",
    "paper": "document",
    "writeup": "document",
    "pic": "image",
    "photo": "image",
    "screenshot": "image",
    "sheet": "spreadsheet",
    "data": "spreadsheet",
}


@dataclass
class Extraction:
    """Extracted semantic components from a user query."""

    raw_query: str
    predicate: str
    predicate_raw: str
    object: str
    object_raw: str
    recipient: str | None = None
    topic: str | None = None
    confidence: float = 0.0

    @property
    def action_text(self) -> str:
        """Combined action text for embedding."""
        return f"{self.predicate} {self.object}"


def extract_simple(query: str) -> Extraction:
    """Simple regex-based extraction (no LLM).

    Works for straightforward queries but may miss nuance.
    """
    query_lower = query.lower()

    # Try to match known predicates
    predicate = "unknown"
    predicate_raw = ""
    for phrase, canonical in PREDICATE_MAP.items():
        if phrase in query_lower:
            predicate = canonical
            predicate_raw = phrase
            break

    # Common verb extraction as fallback
    if predicate == "unknown":
        verbs = ["send", "get", "create", "delete", "update", "search", "list", "share", "upload"]
        for verb in verbs:
            if verb in query_lower:
                predicate = verb
                predicate_raw = verb
                break

    # Try to match known objects
    obj = "item"
    obj_raw = ""
    for phrase, canonical in OBJECT_MAP.items():
        if phrase in query_lower:
            obj = canonical
            obj_raw = phrase
            break

    # Common noun extraction as fallback
    if obj == "item":
        nouns = [
            "message",
            "email",
            "file",
            "document",
            "event",
            "meeting",
            "issue",
            "page",
            "channel",
        ]
        for noun in nouns:
            if noun in query_lower:
                obj = noun
                obj_raw = noun
                break

    # Extract recipient (after "to")
    recipient = None
    to_match = re.search(r"\bto\s+(\w+)", query_lower)
    if to_match:
        recipient = to_match.group(1)

    return Extraction(
        raw_query=query,
        predicate=predicate,
        predicate_raw=predicate_raw or predicate,
        object=obj,
        object_raw=obj_raw or obj,
        recipient=recipient,
        confidence=0.7 if predicate != "unknown" and obj != "item" else 0.4,
    )


def extract_with_llm(query: str) -> Extraction:
    """LLM-based extraction for better semantic understanding."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return extract_simple(query)

    client = OpenAI(api_key=api_key)

    prompt = f"""Extract the semantic components from this user request.

Request: "{query}"

Respond in this exact format:
predicate: <the action verb, normalized (e.g., "send", "create", "delete", "search")>
object: <what the action is on, normalized (e.g., "message", "file", "event")>
recipient: <who it's for, if mentioned, otherwise "none">
topic: <what it's about, if mentioned, otherwise "none">
confidence: <0.0 to 1.0 based on how clear the intent is>

Example:
Request: "fire off a quick note to Sarah about the meeting"
predicate: send
object: message
recipient: Sarah
topic: the meeting
confidence: 0.95"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=150,
    )

    text = response.choices[0].message.content or ""

    # Parse response
    def get_field(name: str) -> str:
        match = re.search(rf"{name}:\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
        return match.group(1).strip() if match else ""

    predicate = get_field("predicate") or "unknown"
    obj = get_field("object") or "item"
    recipient = get_field("recipient")
    topic = get_field("topic")
    conf_str = get_field("confidence")

    try:
        confidence = float(conf_str)
    except (ValueError, TypeError):
        confidence = 0.8

    return Extraction(
        raw_query=query,
        predicate=predicate,
        predicate_raw=predicate,
        object=obj,
        object_raw=obj,
        recipient=None if recipient == "none" else recipient,
        topic=None if topic == "none" else topic,
        confidence=confidence,
    )


def extract(query: str, use_llm: bool = True) -> Extraction:
    """Extract semantic components from a user query.

    Args:
        query: The natural language query
        use_llm: Whether to use LLM for extraction (more accurate but slower)
    """
    if use_llm:
        return extract_with_llm(query)
    return extract_simple(query)
