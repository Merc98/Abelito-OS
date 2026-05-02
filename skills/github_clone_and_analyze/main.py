from __future__ import annotations
from connectors.github_client import clone_repo
from suites.developer.deep_analyzer import DeepAnalyzer
from suites.developer.restructurer import propose_refactors

class GitHubCloneAnalyzeSkill:
    def execute_action(self, action: str, params: dict):
        if action != 'run':
            raise ValueError('unsupported action')
        repo_url=params['repo_url']
        cloned=clone_repo(repo_url)
        if cloned['status'] not in {'ok','exists'}:
            return {"status":"error","clone":cloned}
        analysis=DeepAnalyzer().analyze_path(cloned['path'])
        proposals=propose_refactors(analysis)
        return {"status":"ok","repo":cloned['path'],"analysis":analysis,"proposals":proposals}

def setup():
    return GitHubCloneAnalyzeSkill()
