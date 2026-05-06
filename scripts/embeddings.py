#!/usr/bin/env python3
"""
Embeddings CLI - Command line tool for managing document embeddings
"""
import argparse
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

from api.services import get_github_service, get_vector_store

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def index_documents():
    """Index all documents from GitHub"""
    logger.info("Fetching documents from GitHub...")
    github_service = get_github_service()
    documents = github_service.get_all_documents()

    if not documents:
        logger.warning("No documents found")
        return

    logger.info(f"Found {len(documents)} documents")

    logger.info("Indexing documents...")
    vector_store = get_vector_store()
    vector_store.clear()  # Clear existing index

    # Add in batches
    batch_size = 50
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        vector_store.add_documents(batch)
        logger.info(f"Indexed {min(i + batch_size, len(documents))}/{len(documents)} documents")

    logger.info("Indexing complete!")


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
        print(f"   Preview: {result.get('content', '')[:200]}...")


def show_stats():
    """Show statistics"""
    github_service = get_github_service()
    stats = github_service.get_statistics()

    print("\n=== Knowledge Base Statistics ===")
    print(f"Total Documents: {stats.get('total_documents', 0)}")
    print(f"Total Concepts: {stats.get('total_concepts', 0)}")
    print(f"Total Links: {stats.get('total_links', 0)}")

    print("\n--- Categories ---")
    for category, count in stats.get("categories", {}).items():
        print(f"  {category}: {count}")

    print("\n--- Top Tags ---")
    for tag, count in list(stats.get("tags", {}).items())[:10]:
        print(f"  {tag}: {count}")


def main():
    parser = argparse.ArgumentParser(description="East-lake Embeddings CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Index command
    subparsers.add_parser("index", help="Index all documents")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search documents")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--top-k", type=int, default=5, help="Number of results")

    # Stats command
    subparsers.add_parser("stats", help="Show statistics")

    args = parser.parse_args()

    if args.command == "index":
        index_documents()
    elif args.command == "search":
        search_documents(args.query, args.top_k)
    elif args.command == "stats":
        show_stats()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()