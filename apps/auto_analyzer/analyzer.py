"""Auto-Analyzer: Self-analysis and improvement engine for Abelito OS."""
from __future__ import annotations

import asyncio
import os
import re
import ast
from pathlib import Path
from typing import Any, Literal
from dataclasses import dataclass, field

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger()


@dataclass
class CodeIssue:
    """Represents a code quality or security issue."""
    file_path: str
    line_number: int
    issue_type: Literal["security", "performance", "maintainability", "bug"]
    severity: Literal["low", "medium", "high", "critical"]
    description: str
    suggestion: str
    auto_fixable: bool = False
    proposed_fix: str | None = None


@dataclass
class ImprovementPlan:
    """Plan for self-improvement."""
    issues: list[CodeIssue] = field(default_factory=list)
    priority_actions: list[str] = field(default_factory=list)
    estimated_impact: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "issues": [
                {
                    "file": i.file_path,
                    "line": i.line_number,
                    "type": i.issue_type,
                    "severity": i.severity,
                    "description": i.description,
                    "suggestion": i.suggestion,
                    "auto_fixable": i.auto_fixable,
                }
                for i in self.issues
            ],
            "priority_actions": self.priority_actions,
            "estimated_impact": self.estimated_impact,
        }


class AutoAnalyzer:
    """Self-analysis engine that scans codebase for improvements."""
    
    def __init__(self, base_path: str = "/workspace"):
        self.base_path = Path(base_path)
        self.issues: list[CodeIssue] = []
        
    def scan_all(self) -> ImprovementPlan:
        """Scan entire codebase for issues."""
        logger.info("Starting full codebase scan")
        self.issues = []
        
        # Scan Python files
        for py_file in self.base_path.rglob("*.py"):
            if "venv" not in str(py_file) and "__pycache__" not in str(py_file):
                self._scan_python_file(py_file)
        
        # Check for common security issues
        self._check_security_issues()
        
        # Check architecture patterns
        self._check_architecture()
        
        # Prioritize issues
        plan = self._create_improvement_plan()
        logger.info(f"Scan complete: found {len(plan.issues)} issues")
        return plan
    
    def _scan_python_file(self, file_path: Path) -> None:
        """Analyze a Python file for issues."""
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")
            
            # Check for hardcoded credentials
            for i, line in enumerate(lines, 1):
                if re.search(r'(password|secret|api_key|token)\s*=\s*["\'][^"\']+["\']', line, re.IGNORECASE):
                    if "os.getenv" not in line and "os.environ" not in line:
                        self.issues.append(CodeIssue(
                            file_path=str(file_path),
                            line_number=i,
                            issue_type="security",
                            severity="critical",
                            description="Hardcoded credential detected",
                            suggestion="Use environment variables instead",
                            auto_fixable=False,
                        ))
                
                # Check for TODO/FIXME comments older than needed
                if re.search(r'#\s*(TODO|FIXME|XXX|HACK)', line):
                    self.issues.append(CodeIssue(
                        file_path=str(file_path),
                        line_number=i,
                        issue_type="maintainability",
                        severity="low",
                        description=f"Unresolved comment marker: {line.strip()}",
                        suggestion="Address or remove this marker",
                        auto_fixable=False,
                    ))
            
            # AST-based analysis
            try:
                tree = ast.parse(content)
                self._ast_analyze(tree, str(file_path), content)
            except SyntaxError:
                self.issues.append(CodeIssue(
                    file_path=str(file_path),
                    line_number=0,
                    issue_type="bug",
                    severity="high",
                    description="Syntax error in file",
                    suggestion="Fix syntax errors before proceeding",
                    auto_fixable=False,
                ))
                
        except Exception as e:
            logger.error(f"Error scanning {file_path}: {e}")
    
    def _ast_analyze(self, tree: ast.AST, file_path: str, content: str) -> None:
        """AST-based code analysis."""
        # Check for bare except clauses
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    self.issues.append(CodeIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        issue_type="maintainability",
                        severity="medium",
                        description="Bare except clause catches all exceptions",
                        suggestion="Specify exception types explicitly",
                        auto_fixable=True,
                        proposed_fix="except Exception as e:",
                    ))
            
            # Check for eval/exec usage
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ("eval", "exec", "compile"):
                        self.issues.append(CodeIssue(
                            file_path=file_path,
                            line_number=node.lineno,
                            issue_type="security",
                            severity="critical",
                            description=f"Dangerous function {node.func.id}() detected",
                            suggestion="Avoid eval/exec; use safer alternatives",
                            auto_fixable=False,
                        ))
    
    def _check_security_issues(self) -> None:
        """Check for common security vulnerabilities."""
        # Check requirements.txt for known vulnerable packages
        req_file = self.base_path / "requirements.txt"
        if req_file.exists():
            content = req_file.read_text()
            # Simple check - in production would use safety/bandit
            if "flask" in content.lower() and "csrf" not in content.lower():
                pass  # Would add specific checks here
    
    def _check_architecture(self) -> None:
        """Check architectural patterns and anti-patterns."""
        # Check for singleton anti-pattern
        for py_file in self.base_path.rglob("*.py"):
            content = py_file.read_text()
            if "class" in content and ".__new__" in content:
                self.issues.append(CodeIssue(
                    file_path=str(py_file),
                    line_number=0,
                    issue_type="maintainability",
                    severity="medium",
                    description="Singleton pattern detected - consider dependency injection",
                    suggestion="Use dependency injection for better testability",
                    auto_fixable=False,
                ))
    
    def _create_improvement_plan(self) -> ImprovementPlan:
        """Create prioritized improvement plan."""
        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_issues = sorted(self.issues, key=lambda x: severity_order[x.severity])
        
        # Generate priority actions
        priority_actions = []
        critical_count = sum(1 for i in self.issues if i.severity == "critical")
        high_count = sum(1 for i in self.issues if i.severity == "high")
        
        if critical_count > 0:
            priority_actions.append(f"Address {critical_count} critical security issues immediately")
        if high_count > 0:
            priority_actions.append(f"Fix {high_count} high-severity bugs")
        
        # Estimate impact
        impact = "Low"
        if critical_count > 0 or high_count > 5:
            impact = "High"
        elif len(self.issues) > 10:
            impact = "Medium"
        
        return ImprovementPlan(
            issues=sorted_issues,
            priority_actions=priority_actions,
            estimated_impact=impact,
        )
    
    async def apply_auto_fixes(self, plan: ImprovementPlan) -> int:
        """Apply automatic fixes where possible."""
        fixed_count = 0
        for issue in plan.issues:
            if issue.auto_fixable and issue.proposed_fix:
                try:
                    file_path = Path(issue.file_path)
                    content = file_path.read_text()
                    lines = content.split("\n")
                    
                    # Apply fix (simplified - real implementation would be more sophisticated)
                    if 0 <= issue.line_number - 1 < len(lines):
                        lines[issue.line_number - 1] = issue.proposed_fix
                        file_path.write_text("\n".join(lines))
                        fixed_count += 1
                        logger.info(f"Auto-fixed {issue.file_path}:{issue.line_number}")
                except Exception as e:
                    logger.error(f"Failed to auto-fix {issue.file_path}: {e}")
        
        return fixed_count


async def main():
    """Run auto-analysis."""
    analyzer = AutoAnalyzer()
    plan = analyzer.scan_all()
    
    print("\n=== ABELITO OS AUTO-ANALYSIS REPORT ===\n")
    print(f"Issues found: {len(plan.issues)}")
    print(f"Estimated impact: {plan.estimated_impact}")
    print("\nPriority Actions:")
    for action in plan.priority_actions:
        print(f"  • {action}")
    
    print("\nTop Issues:")
    for i, issue in enumerate(plan.issues[:10], 1):
        print(f"{i}. [{issue.severity.upper()}] {issue.issue_type}: {issue.description}")
        print(f"   File: {issue.file_path}:{issue.line_number}")
        print(f"   Suggestion: {issue.suggestion}\n")
    
    # Apply auto-fixes
    fixed = await analyzer.apply_auto_fixes(plan)
    if fixed > 0:
        print(f"\n✓ Applied {fixed} automatic fixes")


if __name__ == "__main__":
    asyncio.run(main())
