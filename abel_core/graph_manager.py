from __future__ import annotations
import math
from collections import Counter, defaultdict

class GraphService:
    def __init__(self):
        self.nodes = {}
        self.edges = defaultdict(set)

    def add_node(self, node_id: str, text: str, **attrs):
        self.nodes[node_id] = {"text": text, **attrs}

    def add_edge(self, src: str, dst: str, relation: str = "related"):
        self.edges[src].add(dst)

    def traverse(self, start: str, depth: int = 1) -> list[str]:
        visited = {start}
        frontier = {start}
        for _ in range(depth):
            nxt = set()
            for n in frontier:
                nxt.update(self.edges.get(n, set()))
            nxt -= visited
            visited |= nxt
            frontier = nxt
        return [n for n in visited if n != start]

    def _vec(self, t: str):
        return Counter(t.lower().split())

    def search_semantic(self, query: str, top_k: int = 3):
        q = self._vec(query)
        scores=[]
        for n,d in self.nodes.items():
            v=self._vec(d.get('text',''))
            dot=sum(q[k]*v.get(k,0) for k in q)
            nq=math.sqrt(sum(x*x for x in q.values())) or 1
            nv=math.sqrt(sum(x*x for x in v.values())) or 1
            scores.append((dot/(nq*nv),n))
        scores.sort(reverse=True)
        return [n for s,n in scores[:top_k] if s>0]
