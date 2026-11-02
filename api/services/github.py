"""
GitHub Service - Fetch and manage documents from GitHub repository
"""
import logging
import os
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import requests
from github import Github

from api.config import settings

logger = logging.getLogger(__name__)


class GitHubService:
    """Service for interacting with GitHub repository"""

    def __init__(self):
        self.owner = settings.github_owner
        self.repo = settings.github_repo
        self._client = None

    @property
    def client(self) -> Github:
        """Get GitHub client"""
        if self._client is None:
            token = settings.github_token or os.getenv("GITHUB_TOKEN")
            self._client = Github(token) if token else Github()
        return self._client

    def get_repository(self):
        """Get repository object"""
        return self.client.get_repo(f"{self.owner}/{self.repo}")

    def get_document_content(self, path: str) -> str | None:
        """
        Get document content by path

        Args:
            path: Relative path to the document in the repo

        Returns:
            Document content as string, or None if not found
        """
        try:
            repo = self.get_repository()
            contents = repo.get_contents(path)
            if hasattr(contents, "decoded_content"):
                return contents.decoded_content.decode("utf-8")
            return None
        except Exception as e:
            logger.warning(f"Failed to get content for {path}: {e}")
            return None

    def get_all_documents(self, extensions: list[str] = [".md"]) -> list[dict[str, Any]]:
        """
        Get all documents from the repository

        Args:
            extensions: List of file extensions to include

        Returns:
            List of document dicts with content, path, title
        """
        documents = []
        try:
            repo = self.get_repository()
            contents = repo.get_contents("")

            while contents:
                file_content = contents.pop(0)

                if file_content.type == "dir":
                    # Skip certain directories
                    if file_content.name.startswith(".") or file_content.name in [".git", "node_modules"]:
                        continue
                    try:
                        contents.extend(repo.get_contents(file_content.path))
                    except Exception as e:
                        logger.warning(f"Failed to get contents of {file_content.path}: {e}")
                else:
                    # Check extension
                    if any(file_content.name.endswith(ext) for ext in extensions):
                        try:
                            content = file_content.decoded_content.decode("utf-8")
                            documents.append({
                                "path": file_content.path,
                                "title": file_content.name.replace(".md", ""),
                                "content": content,
                            })
                        except Exception as e:
                            logger.warning(f"Failed to decode {file_content.path}: {e}")

        except Exception as e:
            logger.error(f"Failed to get documents: {e}")

        return documents

    def get_knowledge_graph(self) -> dict[str, Any]:
        """
        Extract knowledge graph from documents

        Returns:
            Dict with nodes and edges
        """
        documents = self.get_all_documents()
        nodes = []
        edges = []

        # Create nodes from documents
        for doc in documents:
            path = doc["path"]
            title = doc["title"]

            # Determine category from path
            category = "doc"
            if "/" in path:
                category = path.split("/")[0]

            nodes.append({
                "id": path,
                "label": title,
                "type": "document",
                "category": category,
            })

            # Extract links from content
            content = doc["content"]
            import re
            links = re.findall(r'\[\[([^\]]+)\]\]', content)
            for link in links:
                edges.append({
                    "source": path,
                    "target": f"{link}.md",
                    "label": "links to",
                })

        return {"nodes": nodes, "edges": edges}

    def get_statistics(self) -> dict[str, Any]:
        """
        Get knowledge base statistics

        Returns:
            Dict with statistics
        """
        documents = self.get_all_documents()

        # Count by category
        categories: dict[str, int] = {}
        tags: dict[str, int] = {}

        for doc in documents:
            path = doc["path"]
            if "/" in path:
                category = path.split("/")[0]
                categories[category] = categories.get(category, 0) + 1
            else:
                categories["root"] = categories.get("root", 0) + 1

            # Extract tags from front matter
            content = doc["content"]
            if "tags:" in content:
                import re
                tag_matches = re.findall(r'tags:\s*\[([^\]]+)\]', content)
                for match in tag_matches:
                    for tag in match.split(","):
                        tag = tag.strip().strip('"\'')
                        if tag:
                            tags[tag] = tags.get(tag, 0) + 1

        # Count links
        total_links = 0
        for doc in documents:
            import re
            links = re.findall(r'\[\[([^\]]+)\]\]', doc["content"])
            total_links += len(links)

        return {
            "total_documents": len(documents),
            "total_concepts": categories.get("concepts", 0),
            "total_links": total_links,
            "categories": categories,
            "tags": dict(sorted(tags.items(), key=lambda x: x[1], reverse=True)[:20]),
        }


# Singleton instance
github_service = GitHubService()


def get_github_service() -> GitHubService:
    """Get GitHub service instance"""
    return github_service