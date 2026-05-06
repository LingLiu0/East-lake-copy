#!/usr/bin/env python3
"""
Embeddings CLI - Command line tool for managing document embeddings
Supports incremental updates to avoid re-indexing all documents
"""
import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

from api.services import get_github_service, get_vector_store

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def get_github_repo_path():
    """Get the GitHub repo path for fetching documents"""
    return os.getenv("EASTLAKE_GITHUB_REPO", "huangtao900103/East-lake")


def fetch_documents(github_service=None):
    """Fetch documents from GitHub or local"""
    if github_service is None:
        from api.services import get_github_service
        github_service = get_github_service()

    logger.info(f"Fetching documents from GitHub...")
    documents = github_service.get_all_documents()
    return documents


def index_documents(incremental: bool = False, force: bool = False):
    """Index all documents from GitHub"""
    documents = fetch_documents()

    if not documents:
        logger.warning("No documents found")
        return

    logger.info(f"Found {len(documents)} documents")

    vector_store = get_vector_store()

    # Check existing index
    existing_count = len(vector_store.metadata) if vector_store.metadata else 0
    logger.info(f"Existing index: {existing_count} documents")

    if incremental and existing_count > 0 and not force:
        # Incremental update - only add new/modified documents
        existing_paths = {doc["path"] for doc in vector_store.metadata}
        new_documents = [doc for doc in documents if doc["path"] not in existing_paths]

        if new_documents:
            logger.info(f"Adding {len(new_documents)} new documents...")
            vector_store.add_documents(new_documents)
            logger.info(f"Incremental index complete! Total: {len(vector_store.metadata)}")
        else:
            logger.info("No new documents to add")

    else:
        # Full rebuild
        logger.info("Rebuilding complete index...")
        vector_store.clear()
        vector_store.add_documents(documents)
        logger.info(f"Full index complete! Total: {len(documents)}")


def update_index(file_path: str = None):
    """Update index for specific file(s)"""
    vector_store = get_vector_store()
    github_service = get_github_service()

    if file_path:
        # Update single file
        content = github_service.get_document_content(file_path)
        if content:
            # Remove old version
            vector_store.metadata = [
                doc for doc in vector_store.metadata
                if doc["path"] != file_path
            ]

            # Add new version
            title = Path(file_path).stem
            vector_store.add_documents([{
                "path": file_path,
                "title": title,
                "content": content
            }])

            # Save
            from api.services.vector_store import vector_store as vs
            vs._save()

            logger.info(f"Updated index for: {file_path}")
        else:
            logger.warning(f"Could not fetch: {file_path}")
    else:
        # Rebuild entire index
        index_documents(incremental=False, force=True)


def search_documents(query: str, top_k: int = 5):
    """Search documents"""
    vector_store = get_vector_store()
    results = vector_store.search(query, top_k)

    if not results:
        logger.info("No results found")
        return

    logger.info(f"Found {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.get('title', result.get('path', 'Unknown'))}")
        print(f"   Path: {result.get('path', 'N/A')}")
        print(f"   Score: {result.get('score', 0):.3f}")
        preview = result.get('content', '')[:200]
        if preview:
            print(f"   Preview: {preview}...")


def search_with_highlights(query: str, top_k: int = 5):
    """Search with highlighted snippets"""
    vector_store = get_vector_store()
    results = vector_store.search(query, top_k)

    if not results:
        print("No results found")
        return

    print(f"\n=== Search Results for: '{query}' ===\n")

    for i, result in enumerate(results, 1):
        title = result.get('title', result.get('path', 'Unknown'))
        path = result.get('path', 'N/A')
        score = result.get('score', 0)
        content = result.get('content', '')

        # Highlight matching text
        import re
        query_lower = query.lower()
        content_lower = content.lower()

        # Find the position of the match
        pos = content_lower.find(query_lower)
        if pos >= 0:
            # Get surrounding context
            start = max(0, pos - 50)
            end = min(len(content), pos + len(query) + 50)
            snippet = content[start:end]
            snippet = f"...{snippet}..."
            # Add markers around match
            snippet = snippet.replace(query, f"**{query}**")
        else:
            snippet = content[:150] + "..."

        print(f"{i}. {title}")
        print(f"   📄 {path}")
        print(f"   ⭐ Score: {score:.3f}")
        print(f"   📝 {snippet}")
        print()


def show_stats():
    """Show statistics"""
    github_service = get_github_service()
    vector_store = get_vector_store()

    stats = github_service.get_statistics()
    indexed = len(vector_store.metadata) if vector_store.metadata else 0

    print("\n" + "=" * 50)
    print("  📊 East-lake Knowledge Base Statistics")
    print("=" * 50)

    print(f"\n  📚 Total Documents (GitHub): {stats.get('total_documents', 0)}")
    print(f"  🔍 Indexed Documents: {indexed}")
    print(f"  🔗 Total Links: {stats.get('total_links', 0)}")
    print(f"  💡 Concepts: {stats.get('total_concepts', 0)}")

    print("\n  📂 Categories:")
    for category, count in stats.get("categories", {}).items():
        print(f"     • {category}: {count}")

    print("\n  🏷️ Top Tags:")
    for tag, count in list(stats.get("tags", {}).items())[:10]:
        print(f"     • {tag}: {count}")

    print("\n" + "=" * 50)


def rebuild_index():
    """Completely rebuild the index"""
    logger.info("Starting full index rebuild...")
    index_documents(incremental=False, force=True)


def clean_index():
    """Clear the index"""
    vector_store = get_vector_store()
    vector_store.clear()
    logger.info("Index cleared")


def main():
    parser = argparse.ArgumentParser(
        description="East-lake Embeddings CLI - Manage document embeddings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s index                    # Index all documents
  %(prog)s index --incremental      # Only add new documents
  %(prog)s search "RAG technology"  # Search with highlights
  %(prog)s stats                    # Show statistics
  %(prog)s rebuild                  # Rebuild entire index
  %(prog)s clean                    # Clear index
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Index command
    index_parser = subparsers.add_parser("index", help="Index all documents")
    index_parser.add_argument("--incremental", "-i", action="store_true",
                              help="Only add new documents (faster)")
    index_parser.add_argument("--force", "-f", action="store_true",
                              help="Force full rebuild")

    # Update command
    update_parser = subparsers.add_parser("update", help="Update specific file")
    update_parser.add_argument("file", help="File path to update")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search documents")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--top-k", type=int, default=5,
                               help="Number of results (default: 5)")
    search_parser.add_argument("--no-highlight", action="store_true",
                               help="Don't show highlighted snippets")

    # Stats command
    subparsers.add_parser("stats", help="Show statistics")

    # Rebuild command
    subparsers.add_parser("rebuild", help="Rebuild entire index")

    # Clean command
    subparsers.add_parser("clean", help="Clear the index")

    args = parser.parse_args()

    if args.command == "index":
        index_documents(incremental=args.incremental, force=args.force)
    elif args.command == "update":
        update_index(args.file)
    elif args.command == "search":
        if args.no_highlight:
            search_documents(args.query, args.top_k)
        else:
            search_with_highlights(args.query, args.top_k)
    elif args.command == "stats":
        show_stats()
    elif args.command == "rebuild":
        rebuild_index()
    elif args.command == "clean":
        confirm = input("This will clear the entire index. Continue? (y/N): ")
        if confirm.lower() == 'y':
            clean_index()
        else:
            logger.info("Cancelled")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()