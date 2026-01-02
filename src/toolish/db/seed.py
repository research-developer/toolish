"""Seed database with sample tools for testing."""

import argparse

from toolish.catalog import load_catalog
from toolish.db.chroma import ToolDatabase
from toolish.models.tool import Tool, ToolParams, ToolRoute, ToolSemantics

# 18 sample tools across various services
SAMPLE_TOOLS: list[Tool] = [
    # === SLACK (3 tools) ===
    Tool(
        id="slack-send-message",
        service="slack.com",
        route=ToolRoute(method="POST", path="/message"),
        semantics=ToolSemantics(
            canonical="send message via Slack",
            predicates=["send", "post", "message", "notify", "ping", "DM", "fire off", "shoot"],
            objects=["message", "note", "notification", "text", "DM", "ping"],
            contexts=["team communication", "workplace messaging", "instant messaging"],
            negative_examples=["send email", "schedule message", "send file"],
        ),
        params={
            "channel": ToolParams(type="string", required=True, description="Channel or user"),
            "body": ToolParams(type="string", required=True, description="Message content"),
        },
    ),
    Tool(
        id="slack-upload-file",
        service="slack.com",
        route=ToolRoute(method="POST", path="/file"),
        semantics=ToolSemantics(
            canonical="upload file to Slack",
            predicates=["upload", "share", "send", "post", "attach"],
            objects=["file", "document", "attachment", "image", "screenshot"],
            contexts=["file sharing", "team collaboration"],
        ),
        params={
            "channel": ToolParams(type="string", required=True, description="Target channel"),
            "file": ToolParams(type="file", required=True, description="File to upload"),
        },
    ),
    Tool(
        id="slack-list-channels",
        service="slack.com",
        route=ToolRoute(method="GET", path="/channels"),
        semantics=ToolSemantics(
            canonical="list Slack channels",
            predicates=["list", "show", "get", "find", "search"],
            objects=["channels", "rooms", "conversations"],
            contexts=["channel discovery", "workspace navigation"],
        ),
    ),
    # === EMAIL/GMAIL (3 tools) ===
    Tool(
        id="gmail-send-email",
        service="gmail.com",
        route=ToolRoute(method="POST", path="/send"),
        semantics=ToolSemantics(
            canonical="send email via Gmail",
            predicates=["send", "email", "mail", "compose", "write", "fire off"],
            objects=["email", "mail", "message", "letter"],
            contexts=["email communication", "professional correspondence"],
            negative_examples=["send Slack message", "send text"],
        ),
        params={
            "to": ToolParams(type="string", required=True, description="Recipient email"),
            "subject": ToolParams(type="string", required=True, description="Email subject"),
            "body": ToolParams(type="string", required=True, description="Email body"),
        },
    ),
    Tool(
        id="gmail-search-inbox",
        service="gmail.com",
        route=ToolRoute(method="GET", path="/search"),
        semantics=ToolSemantics(
            canonical="search Gmail inbox",
            predicates=["search", "find", "look for", "check", "query"],
            objects=["emails", "mail", "inbox", "messages"],
            contexts=["email search", "finding messages"],
        ),
        params={
            "query": ToolParams(type="string", required=True, description="Search query"),
        },
    ),
    Tool(
        id="gmail-archive",
        service="gmail.com",
        route=ToolRoute(method="POST", path="/archive"),
        semantics=ToolSemantics(
            canonical="archive Gmail messages",
            predicates=["archive", "move", "file", "store", "hide"],
            objects=["email", "message", "mail", "thread"],
            contexts=["inbox management", "email organization"],
        ),
    ),
    # === GOOGLE DRIVE (3 tools) ===
    Tool(
        id="gdrive-upload",
        service="drive.google.com",
        route=ToolRoute(method="POST", path="/upload"),
        semantics=ToolSemantics(
            canonical="upload file to Google Drive",
            predicates=["upload", "save", "store", "backup", "put"],
            objects=["file", "document", "spreadsheet", "data"],
            contexts=["cloud storage", "file backup"],
        ),
    ),
    Tool(
        id="gdrive-share",
        service="drive.google.com",
        route=ToolRoute(method="POST", path="/share"),
        semantics=ToolSemantics(
            canonical="share Google Drive file",
            predicates=["share", "send", "give access", "collaborate"],
            objects=["file", "document", "folder", "spreadsheet"],
            contexts=["file sharing", "collaboration"],
        ),
    ),
    Tool(
        id="gdrive-search",
        service="drive.google.com",
        route=ToolRoute(method="GET", path="/search"),
        semantics=ToolSemantics(
            canonical="search Google Drive",
            predicates=["search", "find", "look for", "locate", "grab"],
            objects=["file", "document", "spreadsheet", "folder", "data"],
            contexts=["file discovery", "document search"],
        ),
    ),
    # === GOOGLE CALENDAR (3 tools) ===
    Tool(
        id="gcal-create-event",
        service="calendar.google.com",
        route=ToolRoute(method="POST", path="/event"),
        semantics=ToolSemantics(
            canonical="create calendar event",
            predicates=["create", "schedule", "add", "book", "set up"],
            objects=["event", "meeting", "appointment", "call", "sync"],
            contexts=["scheduling", "time management", "meetings"],
        ),
        params={
            "title": ToolParams(type="string", required=True, description="Event title"),
            "start": ToolParams(type="datetime", required=True, description="Start time"),
            "end": ToolParams(type="datetime", required=True, description="End time"),
        },
    ),
    Tool(
        id="gcal-list-events",
        service="calendar.google.com",
        route=ToolRoute(method="GET", path="/events"),
        semantics=ToolSemantics(
            canonical="list calendar events",
            predicates=["list", "show", "get", "check", "view", "what's on"],
            objects=["events", "meetings", "schedule", "calendar", "agenda"],
            contexts=["schedule review", "availability check"],
        ),
    ),
    Tool(
        id="gcal-invite",
        service="calendar.google.com",
        route=ToolRoute(method="POST", path="/invite"),
        semantics=ToolSemantics(
            canonical="invite to calendar event",
            predicates=["invite", "add", "include", "send invite"],
            objects=["attendee", "guest", "person", "participant"],
            contexts=["meeting coordination", "event planning"],
        ),
    ),
    # === GITHUB (3 tools) ===
    Tool(
        id="github-create-issue",
        service="github.com",
        route=ToolRoute(method="POST", path="/issue"),
        semantics=ToolSemantics(
            canonical="create GitHub issue",
            predicates=["create", "open", "file", "report", "submit"],
            objects=["issue", "bug", "ticket", "problem", "feature request"],
            contexts=["bug tracking", "project management", "development"],
        ),
    ),
    Tool(
        id="github-list-prs",
        service="github.com",
        route=ToolRoute(method="GET", path="/pulls"),
        semantics=ToolSemantics(
            canonical="list pull requests",
            predicates=["list", "show", "get", "check", "review"],
            objects=["PRs", "pull requests", "merge requests", "code reviews"],
            contexts=["code review", "development workflow"],
        ),
    ),
    Tool(
        id="github-merge",
        service="github.com",
        route=ToolRoute(method="POST", path="/merge"),
        semantics=ToolSemantics(
            canonical="merge pull request",
            predicates=["merge", "approve", "land", "ship", "integrate"],
            objects=["PR", "pull request", "branch", "code"],
            contexts=["code integration", "release management"],
        ),
    ),
    # === NOTION (2 tools) ===
    Tool(
        id="notion-create-page",
        service="notion.so",
        route=ToolRoute(method="POST", path="/page"),
        semantics=ToolSemantics(
            canonical="create Notion page",
            predicates=["create", "add", "write", "make", "start"],
            objects=["page", "document", "note", "doc", "wiki"],
            contexts=["documentation", "note-taking", "knowledge base"],
        ),
    ),
    Tool(
        id="notion-search",
        service="notion.so",
        route=ToolRoute(method="GET", path="/search"),
        semantics=ToolSemantics(
            canonical="search Notion",
            predicates=["search", "find", "look up", "query"],
            objects=["page", "document", "note", "content"],
            contexts=["knowledge discovery", "documentation search"],
        ),
    ),
    # === MICROSOFT TEAMS (1 tool) ===
    Tool(
        id="teams-send-message",
        service="teams.microsoft.com",
        route=ToolRoute(method="POST", path="/message"),
        semantics=ToolSemantics(
            canonical="send message via Teams",
            predicates=["send", "post", "message", "notify", "ping"],
            objects=["message", "chat", "notification"],
            contexts=["team communication", "enterprise messaging"],
            negative_examples=["send Slack message"],
        ),
    ),
]


def seed_database(
    db: ToolDatabase | None = None,
    clear_first: bool = True,
    from_catalog: bool = False,
    category: str | None = None,
) -> int:
    """Seed the database with sample tools.

    Args:
        db: Database instance (creates new if None)
        clear_first: Whether to clear existing data
        from_catalog: Load tools from YAML catalog instead of hardcoded samples
        category: If from_catalog, optionally filter by category (ai, productivity, devtools)

    Returns the number of tools seeded.
    """
    if db is None:
        db = ToolDatabase()

    if clear_first:
        print("Clearing existing data...")
        db.clear()

    if from_catalog:
        # Load tools from YAML catalog
        if category:
            print(f"Loading tools from catalog/{category}/...")
            tools = load_catalog(category=category)
        else:
            print("Loading tools from catalog/...")
            tools = load_catalog()
    else:
        # Use hardcoded sample tools
        tools = SAMPLE_TOOLS

    print(f"Seeding {len(tools)} tools...")
    for tool in tools:
        print(f"  - {tool.id}: {tool.semantics.canonical}")
        db.register_tool(tool)

    print("Done!")
    return len(tools)


def seed_from_catalog(
    db: ToolDatabase | None = None,
    clear_first: bool = True,
    category: str | None = None,
) -> int:
    """Convenience function to seed from catalog."""
    return seed_database(db=db, clear_first=clear_first, from_catalog=True, category=category)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed toolish database")
    parser.add_argument(
        "--from-catalog",
        action="store_true",
        help="Load tools from YAML catalog instead of hardcoded samples",
    )
    parser.add_argument(
        "--category",
        choices=["ai", "productivity", "devtools"],
        help="Only load tools from a specific catalog category",
    )
    parser.add_argument(
        "--no-clear",
        action="store_true",
        help="Don't clear existing data before seeding",
    )
    args = parser.parse_args()

    seed_database(
        from_catalog=args.from_catalog,
        category=args.category,
        clear_first=not args.no_clear,
    )
