"""CLI REPL for testing semantic tool discovery."""

import sys

from toolish.db.chroma import ToolDatabase
from toolish.db.seed import seed_database
from toolish.models.tool import ToolStatus
from toolish.search.resolver import Resolver

# Status icons
STATUS_ICONS = {
    ToolStatus.CONNECTED: "\u2705",  # green checkmark
    ToolStatus.KEYCHAIN: "\U0001F510",  # lock with key
    ToolStatus.AVAILABLE: "\U0001F517",  # link
    ToolStatus.UNAVAILABLE: "\u274C",  # red X
}

STATUS_LABELS = {
    ToolStatus.CONNECTED: "CONNECTED",
    ToolStatus.KEYCHAIN: "KEYCHAIN",
    ToolStatus.AVAILABLE: "AVAILABLE",
    ToolStatus.UNAVAILABLE: "UNAVAILABLE",
}


def print_banner() -> None:
    """Print welcome banner."""
    print("\n" + "=" * 60)
    print("  TOOLISH - Semantic Tool Discovery")
    print("=" * 60)
    print("\nCommands:")
    print("  <query>     Search for tools (e.g., 'fire off a note')")
    print("  /seed       Re-seed the database")
    print("  /list       List all registered tools")
    print("  /quick      Toggle LLM extraction (faster but less accurate)")
    print("  /help       Show this help")
    print("  /quit       Exit")
    print("-" * 60 + "\n")


def run_repl() -> None:
    """Run the interactive REPL."""
    print_banner()

    db = ToolDatabase()
    resolver = Resolver(db)
    use_llm = True

    # Check if seeded
    tools = db.get_all_tools()
    if not tools:
        print("Database is empty. Run /seed first or seeding now...")
        try:
            seed_database(db)
        except Exception as e:
            print(f"Error seeding: {e}")
            print("Make sure OPENAI_API_KEY is set in .env file")
            return

    while True:
        try:
            query = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not query:
            continue

        # Handle commands
        if query.startswith("/"):
            cmd = query.lower()

            if cmd in ("/quit", "/exit", "/q"):
                print("Goodbye!")
                break

            elif cmd == "/help":
                print_banner()

            elif cmd == "/seed":
                print("Seeding database...")
                try:
                    count = seed_database(db)
                    print(f"Seeded {count} tools.")
                except Exception as e:
                    print(f"Error: {e}")

            elif cmd == "/list":
                tools = db.get_all_tools()
                print(f"\nRegistered tools ({len(tools)}):")
                for t in tools:
                    print(f"  - {t['id']}: {t['canonical']}")

            elif cmd == "/quick":
                use_llm = not use_llm
                mode = "LLM" if use_llm else "simple regex"
                print(f"Extraction mode: {mode}")

            else:
                print(f"Unknown command: {query}")
                print("Type /help for available commands")

            continue

        # Resolve query
        print(f"\nSearching... (mode: {'LLM' if use_llm else 'simple'})")

        try:
            result = resolver.resolve(query, use_llm=use_llm)
        except Exception as e:
            print(f"Error: {e}")
            continue

        # Show extraction
        ext = result.extraction
        print(f"\nExtraction:")
        print(f"  predicate: {ext.predicate} (raw: '{ext.predicate_raw}')")
        print(f"  object: {ext.object} (raw: '{ext.object_raw}')")
        if ext.recipient:
            print(f"  recipient: {ext.recipient}")
        print(f"  confidence: {ext.confidence:.2f}")

        # Show results
        print(f"\nResults ({result.confidence} confidence):")
        print("-" * 50)

        if not result.matches:
            print("  No matching tools found.")
            print("  Try a different query or /seed to populate data.")
        else:
            for i, match in enumerate(result.matches[:5], 1):
                icon = STATUS_ICONS[match.status]
                label = STATUS_LABELS[match.status]
                tool = match.tool

                print(f"{i}. {icon} [{label:9}] {tool.service}")
                print(f"   {tool.route.method} {tool.route.path}")
                print(f"   {tool.semantics.canonical}")
                print(f"   Score: {match.final_score:.3f} (semantic: {match.semantic_score:.3f})")
                print()


def main() -> None:
    """Entry point."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "seed":
            print("Seeding database...")
            seed_database()
            return

    run_repl()


if __name__ == "__main__":
    main()
