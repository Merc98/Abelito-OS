from skills.__loader__ import SkillRegistry
from pathlib import Path


def test_suites_discovered_and_loadable():
    reg = SkillRegistry(Path('skills'))
    reg.discover()
    names = {s['name'] for s in reg.list_available()}
    assert {'osint_suite','pentest_suite','dev_code_suite','sandbox_restructure_suite'}.issubset(names)
    assert reg.load_skill('dev_code_suite') is not None


def test_permission_guard_osint():
    reg = SkillRegistry(Path('skills'))
    reg.discover()
    osint = reg.load_skill('osint_suite')
    try:
        osint.execute_action('dns_lookup', {'domain': 'example.com'})
    except PermissionError:
        assert True
    else:
        assert False
