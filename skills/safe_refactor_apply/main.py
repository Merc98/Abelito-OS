from __future__ import annotations
from sandbox_backend.backend import SandboxBackend

class SafeRefactorApplySkill:
    def execute_action(self, action: str, params: dict):
        if action != 'validate_apply':
            raise ValueError('unsupported action')
        if not params.get('approved', False):
            return {"status":"blocked","reason":"HITL approval required"}
        result = SandboxBackend().run_tests_in_copy(params['repo_path'])
        if result.get('returncode') != 0:
            return {"status":"rejected","test_result":result}
        return {"status":"ready_to_apply","test_result":result}

def setup():
    return SafeRefactorApplySkill()
