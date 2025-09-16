from datetime import datetime, timedelta
from networkx import MultiDiGraph
from job_nimbus import JobStatus
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class JobGraphEmbedding:
    """Represents the "status flow" of jobs as a set of
    edges in a graph."""

    def __init__(self, status_partition: list[frozenset[JobStatus]], remove_cycles: bool = False):
        self.status_to_node = {}
        self.start_node_id = len(status_partition)
        for node_id, status_group in enumerate(status_partition):
            for status in status_group:
                self.status_to_node[status] = node_id
        self.graph = MultiDiGraph()
        self.graph.add_nodes_from(range(len(status_partition)), num_jobs=0)
        # add a node for the start status
        self.graph.add_node(self.start_node_id, num_jobs=0)
        self.remove_cycles = remove_cycles

    def add_status_history(self, status_history: list[(datetime, JobStatus)]) -> int:
        filtered_status_history = filter_status_history(status_history, self.status_to_node, self.remove_cycles)

        for i in range(len(filtered_status_history)):
            if i == 0:
                from_date = filtered_status_history[0][0]
                from_node_id = self.start_node_id
            else:
                from_date, from_node_id = filtered_status_history[i-1]

            # add value to the node
            self.graph.nodes[from_node_id]['num_jobs'] += 1

            # add an edge for this status
            to_date, to_node_id = filtered_status_history[i]
            self.graph.add_edge(from_node_id, to_node_id, duration=to_date - from_date)
        return len(filtered_status_history)

    def to_sankey(self):
        source_indices = []
        target_indices = []
        values = []
        avg_durations = []
        for i in self.graph.nodes:
            for j in self.graph.nodes:
                edges = self.graph.get_edge_data(i, j)
                if edges is not None and len(edges) > 0:
                    source_indices.append(i)
                    target_indices.append(j)
                    values.append(len(edges))

                    total_duration = timedelta(0)
                    for _, edge_attr in edges.items():
                        total_duration += edge_attr['duration']
                    avg_duration = (total_duration / len(edges)).days
                    avg_durations.append(avg_duration)
        return source_indices, target_indices, values, avg_durations

def filter_status_history(status_history: list[(datetime, JobStatus)], status_to_node_id: dict[JobStatus, int], remove_cycles: bool = False) -> list[tuple[datetime, int]]:
    try:
        filtered_status_history = []
        node_encounters = set()
        last_node_id = None
        for date, status in status_history:
            if (node_id := status_to_node_id.get(status)) is not None and node_id != last_node_id:
                if remove_cycles and node_id in node_encounters:
                    # we've seen this node before, so remove the cycle
                    # logger.info(f"Removing cycle: {filtered_status_history=} {node_encounters=} {status=} {date=} {node_id=}")
                    while filtered_status_history[-1][1] != node_id:
                        _, popped_node_id = filtered_status_history.pop()
                        node_encounters.discard(popped_node_id)
                else:
                    # we've never seen this node before
                    node_encounters.add(node_id)
                    filtered_status_history.append((date, node_id))
                last_node_id = node_id

        # assert no cycles
        if remove_cycles:
            node_encounters = set()
            for date, node_id in filtered_status_history:
                if node_id in node_encounters:
                    logger.error(f"Cycle detected: {status_history=} {filtered_status_history=}")
                node_encounters.add(node_id)
        return filtered_status_history
    except Exception as e:
        logger.error(f"Error filtering status history: {status_history}")
        raise e
