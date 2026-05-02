from abel_core.orchestrator import BrainOrchestrator
from abel_core.graph_manager import GraphService


def test_orchestrator_process():
    o = BrainOrchestrator()
    out = o.process('run osint dns check')
    assert out['tasks'][0]['task'] == 'osint'


def test_graph_semantic_and_traverse():
    g = GraphService()
    g.add_node('a', 'python testing')
    g.add_node('b', 'osint dns whois')
    g.add_edge('a', 'b')
    assert 'b' in g.traverse('a', 1)
    assert g.search_semantic('dns whois', 1)[0] == 'b'
