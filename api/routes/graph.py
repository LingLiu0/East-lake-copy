"""
Graph Routes - Knowledge graph endpoints
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi.security import APIKeyHeader

from api.models import GraphResponse, GraphNode, GraphEdge
from api.services import get_github_service
from api.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/graph", tags=["graph"])

# Rate limiter
limiter = Limiter(key_func=get_remote_address)
api_key_header = APIKeyHeader(name=settings.api_key_header, auto_error=False)


async def verify_api_key(api_key: Annotated[str | None, Depends(api_key_header)]):
    """Verify API key"""
    if settings.admin_api_key and api_key != settings.admin_api_key:
        if settings.debug or not settings.admin_api_key:
            return True
        raise HTTPException(status_code=403, detail="Invalid API key")
    return True


@router.get("/", response_model=GraphResponse)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def get_graph(
    _auth: Annotated[bool, Depends(verify_api_key)],
):
    """
    Get the complete knowledge graph

    Returns all nodes (documents) and edges (links) from the knowledge base.
    """
    try:
        github_service = get_github_service()
        graph_data = github_service.get_knowledge_graph()

        nodes = [
            GraphNode(
                id=node["id"],
                label=node["label"],
                type=node.get("type", "document"),
                category=node.get("category"),
            )
            for node in graph_data.get("nodes", [])
        ]

        edges = [
            GraphEdge(
                source=edge["source"],
                target=edge["target"],
                label=edge.get("label"),
            )
            for edge in graph_data.get("edges", [])
        ]

        return GraphResponse(nodes=nodes, edges=edges)

    except Exception as e:
        logger.error(f"Failed to get graph: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get graph: {str(e)}")


@router.get("/node/{node_id}")
async def get_node(
    node_id: str,
    depth: int = Query(default=1, ge=1, le=3),
    _auth: Annotated[bool, Depends(verify_api_key)],
):
    """
    Get a specific node and its connections

    - **node_id**: The node ID/path to query
    - **depth**: How many levels of connections to return (1-3)
    """
    try:
        github_service = get_github_service()
        graph_data = github_service.get_knowledge_graph()

        # Find the node
        target_node = None
        for node in graph_data.get("nodes", []):
            if node["id"] == node_id or node["label"] == node_id:
                target_node = node
                break

        if not target_node:
            raise HTTPException(status_code=404, detail=f"Node not found: {node_id}")

        # Find direct connections
        connected_edges = [
            edge for edge in graph_data.get("edges", [])
            if edge["source"] == node_id or edge["target"] == node_id
        ]

        # Build result
        connected_nodes = []
        for edge in connected_edges:
            node_id = edge["target"] if edge["source"] == node_id else edge["source"]
            for node in graph_data.get("nodes", []):
                if node["id"] == node_id:
                    connected_nodes.append(node)
                    break

        return {
            "node": target_node,
            "connections": connected_nodes[:depth * 10],  # Limit results
            "total_connections": len(connected_edges),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get node: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get node: {str(e)}")


@router.get("/mermaid")
async def get_graph_mermaid(
    _auth: Annotated[bool, Depends(verify_api_key)],
):
    """
    Get knowledge graph in Mermaid diagram format

    Useful for embedding in markdown documents.
    """
    try:
        github_service = get_github_service()
        graph_data = github_service.get_knowledge_graph()

        # Generate Mermaid code
        mermaid_lines = ["graph TD"]

        # Add nodes
        for node in graph_data.get("nodes", [])[:50]:  # Limit to 50 for performance
            node_id = node["id"].replace("-", "_").replace("/", "_").replace(".", "_")
            label = node["label"][:30]  # Truncate long labels
            mermaid_lines.append(f'    {node_id}["{label}"]')

        # Add edges
        for edge in graph_data.get("edges", [])[:100]:  # Limit to 100
            source = edge["source"].replace("-", "_").replace("/", "_").replace(".", "_")
            target = edge["target"].replace("-", "_").replace("/", "_").replace(".", "_")
            mermaid_lines.append(f"    {source} --> {target}")

        return {
            "diagram": "\n".join(mermaid_lines),
            "node_count": len(graph_data.get("nodes", [])),
            "edge_count": len(graph_data.get("edges", [])),
        }

    except Exception as e:
        logger.error(f"Failed to generate mermaid: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate mermaid: {str(e)}")