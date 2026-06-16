import logging
from typing import Optional

import networkx as nx

from backend.db.connection import get_connection

logger = logging.getLogger(__name__)

APP_GRAPH: Optional[nx.DiGraph] = None


def build_graph(db_path: str = "data/cmdb.db") -> nx.DiGraph:
    """Load all active applications and edge tables into a networkx DiGraph."""
    conn = get_connection(db_path)
    G = nx.DiGraph()

    try:
        # Application nodes
        rows = conn.execute(
            "SELECT application_id, application_name, application_type, company, business_process "
            "FROM applications WHERE active_status = 1"
        ).fetchall()
        for row in rows:
            G.add_node(
                row["application_id"],
                node_type="application",
                name=row["application_name"],
                application_type=row["application_type"],
                company=row["company"],
                business_process=row["business_process"],
            )

        # Business process nodes
        for row in conn.execute("SELECT process_id, process_name FROM business_processes").fetchall():
            G.add_node(row["process_id"], node_type="process", name=row["process_name"])

        # Application type nodes
        for row in conn.execute("SELECT type_id, type_name FROM application_types").fetchall():
            G.add_node(row["type_id"], node_type="application_type", name=row["type_name"])

        # Architecture type nodes
        for row in conn.execute("SELECT arch_id, arch_name FROM architecture_types").fetchall():
            G.add_node(row["arch_id"], node_type="architecture_type", name=row["arch_name"])

        # Edges: app → process
        for row in conn.execute("SELECT application_id, process_id FROM app_supports_process").fetchall():
            G.add_edge(row["application_id"], row["process_id"], edge_type="supports_process")

        # Edges: app → application type
        for row in conn.execute("SELECT application_id, type_id FROM app_uses_type").fetchall():
            G.add_edge(row["application_id"], row["type_id"], edge_type="uses_type")

        # Edges: app → architecture type
        for row in conn.execute("SELECT application_id, arch_id FROM app_has_architecture").fetchall():
            G.add_edge(row["application_id"], row["arch_id"], edge_type="has_architecture")

    finally:
        conn.close()

    logger.info("Graph built: %d nodes, %d edges", G.number_of_nodes(), G.number_of_edges())
    return G


def reload_graph(db_path: str = "data/cmdb.db") -> None:
    global APP_GRAPH
    APP_GRAPH = build_graph(db_path)


def get_graph() -> nx.DiGraph:
    if APP_GRAPH is None:
        raise RuntimeError("Graph not loaded — call reload_graph() first")
    return APP_GRAPH
