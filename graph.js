class Graph {
  constructor() {
    this.nodes = new Map();
    this.adjacencyList = new Map();
  }

  addNode(node) {
    this.nodes.set(node.id, node);
    if (!this.adjacencyList.has(node.id)) {
      this.adjacencyList.set(node.id, []);
    }
  }

  addEdge(edge) {
    // Add forward edge
    this.adjacencyList.get(edge.from).push({
      to: edge.to,
      weight: edge.distance,
      accessible: edge.accessible,
    });

    // Add backward edge for drawing/undirected graph logic
    this.adjacencyList.get(edge.to).push({
        to: edge.from,
        weight: edge.distance,
        accessible: edge.accessible,
    });
  }
}

// Global instance
var graph = new Graph();