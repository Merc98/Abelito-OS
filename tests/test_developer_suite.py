from suites.developer.deep_analyzer import DeepAnalyzer
from suites.developer.restructurer import propose_refactors


def test_deep_analyzer_basic(tmp_path):
    f = tmp_path / 'x.py'
    f.write_text('import os\n\n# hi\ndef f(x):\n    if x:\n        return 1\n    return 0\n')
    out = DeepAnalyzer().analyze_path(str(f))
    assert out['files'] == 1
    assert out['functions'] == 1


def test_restructurer_proposals():
    actions = propose_refactors({'complexity': 40, 'unused_imports': 2, 'maintainability': 50})
    assert actions
