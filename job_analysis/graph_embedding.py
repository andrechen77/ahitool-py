from datetime import datetime
from networkx import MultiDiGraph
from job_nimbus import JobStatus

class JobGraphEmbedding:
    """Represents the "status flow" of jobs as a set of
    edges in a graph."""

    def __init__(self, status_partition: set[set[JobStatus]]):
        self.status_to_node = {}
        for node_id, status_set in enumerate(status_partition):
            for status in status_set:
                self.status_to_node[status] = node_id
        self.graph = MultiDiGraph()
        self.graph.add_nodes_from(range(len(status_partition)))

    def add_status_history(self, status_history: list[(datetime, JobStatus)]):
        filtered_status_history = filter_status_history(status_history, self.statuses)

        for i in range(len(filtered_status_history) - 1):
            from_date, from_node_id = filtered_status_history[i]
            to_date, to_node_id = filtered_status_history[i+1]
            self.graph.add_edge(from_node_id, to_node_id, duration=to_date - from_date)

def filter_status_history(status_history: list[(datetime, JobStatus)], status_to_node_id: dict[JobStatus, int]) -> list[(datetime, int)]:
    filtered_status_history = []
    last_node_id = None
    last_date = None
    for date, status in status_history:
        if (node_id := status_to_node_id.get(status)) and node_id != last_node_id:
            filtered_status_history.append((date, node_id))
            last_node_id = node_id
            last_date = date
    return filtered_status_history
