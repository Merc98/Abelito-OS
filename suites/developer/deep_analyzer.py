from __future__ import annotations
import ast
from pathlib import Path

class DeepAnalyzer:
    def analyze_path(self, path: str) -> dict:
        p = Path(path)
        files = [p] if p.is_file() else list(p.rglob('*.py'))
        metrics = {"files":0,"loc":0,"comments":0,"functions":0,"complexity":0,"unused_imports":0}
        for f in files:
            txt = f.read_text(errors='ignore')
            metrics['files'] += 1
            metrics['loc'] += len(txt.splitlines())
            metrics['comments'] += sum(1 for l in txt.splitlines() if l.strip().startswith('#'))
            tree = ast.parse(txt)
            funcs=[n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            metrics['functions'] += len(funcs)
            metrics['complexity'] += sum(1 for n in ast.walk(tree) if isinstance(n,(ast.If,ast.For,ast.While,ast.Try,ast.BoolOp)))
            imports=[n.names[0].name for n in ast.walk(tree) if isinstance(n,ast.Import)]
            names={n.id for n in ast.walk(tree) if isinstance(n,ast.Name)}
            metrics['unused_imports'] += sum(1 for i in imports if i.split('.')[0] not in names)
        maintainability=max(0,100-(metrics['complexity']+metrics['unused_imports']*2))
        return {**metrics, "maintainability": maintainability}
