# Service Discovery

[NLP-Driven Resolution](NLP-Driven%20Resolution%20f6ffe573289e4b23b8b1193aa9827b2d.md)

> Resolves natural language requests to WebSpec routes via semantic understanding. Extracts predicates and objects from phrases like "fire off a quick note," normalizes them to canonical forms, generates embeddings, and ranks matches by semantic similarity, authorization status, user preference, and context hints. Configurable confirmation modes from always-confirm to auto-execute.
> 

[Embedding Schema](Embedding%20Schema%2006459c7c8cf6460897183c574664d3e0.md)

> Defines how tools register for semantic discovery using vector embeddings. Tools specify canonical descriptions, predicate synonyms (e.g., "fire off," "shoot," "drop" → send), and object types. Multi-vector search across canonical, predicate, and object indices enables meaning-based matching. Includes similarity thresholds, caching strategy, and negative example "repulsion."
> 

[The Three-Way Join](The%20Three-Way%20Join%2022db5688c9354c23af90d9b52792b517.md)

> Core discovery algorithm that joins user intent against three data sources: connected services (OAuth tokens), the tool registry (all available tools with embeddings), and keychain hints (domains user has credentials for). Weighted scoring combines semantic similarity with connection status (Connected > Keychain > Available) plus recency and preference boosts.
>