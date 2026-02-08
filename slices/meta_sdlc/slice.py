"""
Meta SDLC CI/CD Framework for RefactorBot V2

Self-improvement framework that enables each slice to:
1. Analyze its own code and performance
2. Generate improvement plans
3. Apply code patches
4. Run tests and validation
"""

import ast
import hashlib
import json
import logging
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..slice_base import AtomicSlice

logger = logging.getLogger(__name__)


class ImprovementType(Enum):
    """Types of improvements a slice can make."""
    PERFORMANCE = "performance"
    SECURITY = "security"
    CODE_QUALITY = "code_quality"
    DOCUMENTATION = "documentation"
    TEST_COVERAGE = "test_coverage"
    BUG_FIX = "bug_fix"
    REFACTORING = "refactoring"
    FEATURE = "feature"


class AnalysisLevel(Enum):
    """Depth of code analysis."""
    SURFACE = "surface"
    DEEP = "deep"
    COMPREHENSIVE = "comprehensive"


@dataclass
class CodeIssue:
    """Represents a code issue found during analysis."""
    issue_id: str
    file_path: str
    line_number: int
    issue_type: str
    severity: str  # low, medium, high, critical
    description: str
    suggestion: str
    auto_fixable: bool = False
    fix_code: Optional[str] = None


@dataclass
class ImprovementPlan:
    """A plan for improving a slice."""
    plan_id: str
    slice_name: str
    created_at: datetime
    improvements: List["SliceImprovement"]
    estimated_impact: str
    risk_level: str
    requires_restart: bool = False


@dataclass
class SliceImprovement:
    """A single improvement in a plan."""
    improvement_id: str
    type: ImprovementType
    title: str
    description: str
    changes: List["CodeChange"]
    estimated_time: int  # minutes
    prerequisites: List[str] = field(default_factory=list)


@dataclass
class CodeChange:
    """A change to be made to the code."""
    file_path: str
    change_type: str  # add, modify, delete, replace
    line_start: int
    line_end: int
    original_code: str
    new_code: str
    reason: str


@dataclass
class AnalysisResult:
    """Result of code analysis."""
    analysis_id: str
    slice_name: str
    analyzed_at: datetime
    analysis_level: AnalysisLevel
    issues_found: List[CodeIssue]
    metrics: Dict[str, Any]
    recommendations: List[str]
    health_score: float  # 0.0 to 100.0


@dataclass
class TestResult:
    """Result of running tests."""
    test_run_id: str
    executed_at: datetime
    total_tests: int
    passed: int
    failed: int
    errors: int
    coverage: float
    duration: float
    output: str


class MetaSDLCEngine:
    """
    Meta SDLC Engine for self-improving slices.
    
    Each slice has its own MetaSDLCEngine instance that provides:
    - Code analysis and issue detection
    - Improvement plan generation
    - Automatic code patching
    - Test execution and validation
    - CI/CD pipeline management
    """
    
    def __init__(self, slice_instance: "AtomicSlice"):
        self.slice = slice_instance
        self.slice_id = slice_instance.slice_id
        self.slice_name = slice_instance.slice_name
        self.slice_path = Path(slice_instance.config_path).parent if hasattr(slice_instance, 'config_path') else Path(".")
        
        # Analysis cache
        self._last_analysis: Optional[AnalysisResult] = None
        self._improvement_history: List[ImprovementPlan] = []
        
        # Settings
        self.auto_fix_enabled = False
        self.analysis_depth = AnalysisLevel.DEEP
        self.max_improvements_per_plan = 10
        
    async def run_full_analysis(self, level: AnalysisLevel = None) -> AnalysisResult:
        """Run comprehensive code analysis."""
        level = level or self.analysis_depth
        
        logger.info(f"Starting {level.value} analysis for slice {self.slice_name}")
        
        issues = []
        metrics = {}
        recommendations = []
        
        # Static code analysis
        if level in [AnalysisLevel.DEEP, AnalysisLevel.COMPREHENSIVE]:
            static_issues = await self._static_code_analysis()
            issues.extend(static_issues)
        
        # Performance analysis
        perf_metrics = await self._performance_analysis()
        metrics.update(perf_metrics)
        
        # Security analysis
        if level == AnalysisLevel.COMPREHENSIVE:
            security_issues = await self._security_analysis()
            issues.extend(security_issues)
        
        # Calculate metrics
        metrics.update(await self._calculate_code_metrics())
        
        # Generate recommendations
        recommendations = self._generate_recommendations(issues, metrics)
        
        # Calculate health score
        health_score = self._calculate_health_score(issues, metrics)
        
        result = AnalysisResult(
            analysis_id=self._generate_id(),
            slice_name=self.slice_name,
            analyzed_at=datetime.utcnow(),
            analysis_level=level,
            issues_found=issues,
            metrics=metrics,
            recommendations=recommendations,
            health_score=health_score
        )
        
        self._last_analysis = result
        logger.info(f"Analysis complete for {self.slice_name}: {len(issues)} issues, health={health_score:.1f}")
        
        return result
    
    async def _static_code_analysis(self) -> List[CodeIssue]:
        """Perform static code analysis."""
        issues = []
        
        python_files = list(self.slice_path.rglob("*.py"))
        
        for py_file in python_files:
            try:
                file_issues = await self._analyze_python_file(py_file)
                issues.extend(file_issues)
            except Exception as e:
                logger.warning(f"Could not analyze {py_file}: {e}")
        
        # Check for common issues
        issues.extend(self._check_common_issues())
        
        return issues
    
    async def _analyze_python_file(self, file_path: Path) -> List[CodeIssue]:
        """Analyze a Python file for issues."""
        issues = []
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                tree = ast.parse(content)
        except SyntaxError as e:
            issues.append(CodeIssue(
                issue_id=self._generate_id(),
                file_path=str(file_path),
                line_number=e.lineno or 1,
                issue_type="syntax_error",
                severity="critical",
                description=f"Syntax error: {e.msg}",
                suggestion="Fix the syntax error",
                auto_fixable=False
            ))
            return issues
        
        # Analyze AST
        for node in ast.walk(tree):
            # Check for bare except
            if isinstance(node, ast.Try):
                for handler in node.handlers:
                    if handler.name is None:
                        issues.append(CodeIssue(
                            issue_id=self._generate_id(),
                            file_path=str(file_path),
                            line_number=handler.lineno,
                            issue_type="broad_exception",
                            severity="high",
                            description="Bare except clause catches all exceptions",
                            suggestion="Use 'except SpecificException:' instead",
                            auto_fixable=False
                        ))
            
            # Check for print statements
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == "print":
                    issues.append(CodeIssue(
                        issue_id=self._generate_id(),
                        file_path=str(file_path),
                        line_number=node.lineno,
                        issue_type="print_statement",
                        severity="low",
                        description="Print statement found - use logging instead",
                        suggestion="Replace with proper logging calls",
                        auto_fixable=True,
                        fix_code="logger.info(...)"
                    ))
            
            # Check for hardcoded passwords
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if any(secret in target.id.lower() for secret in ["password", "secret", "api_key"]):
                            if isinstance(node.value, ast.Str):
                                issues.append(CodeIssue(
                                    issue_id=self._generate_id(),
                                    file_path=str(file_path),
                                    line_number=node.lineno,
                                    issue_type="hardcoded_secret",
                                    severity="critical",
                                    description="Potential hardcoded secret detected",
                                    suggestion="Use environment variables or configuration",
                                    auto_fixable=False
                                ))
        
        # Check file length
        lines = content.split("\n")
        if len(lines) > 500:
            issues.append(CodeIssue(
                issue_id=self._generate_id(),
                file_path=str(file_path),
                line_number=len(lines),
                issue_type="file_too_long",
                severity="medium",
                description=f"File has {len(lines)} lines - consider splitting",
                suggestion="Split into smaller modules",
                auto_fixable=False
            ))
        
        return issues
    
    def _check_common_issues(self) -> List[CodeIssue]:
        """Check for common issues across the slice."""
        issues = []
        
        # Check for missing __init__.py
        init_files = list(self.slice_path.rglob("__init__.py"))
        if not init_files:
            issues.append(CodeIssue(
                issue_id=self._generate_id(),
                file_path=str(self.slice_path),
                line_number=1,
                issue_type="missing_init",
                severity="medium",
                description="No __init__.py files found",
                suggestion="Add __init__.py files to packages",
                auto_fixable=True,
                fix_code="# Package initialization"
            ))
        
        # Check for TODO comments
        # This would be implemented with regex search
        
        return issues
    
    async def _performance_analysis(self) -> Dict[str, Any]:
        """Analyze performance characteristics."""
        return {
            "avg_file_size": 0,  # Would calculate from file analysis
            "complexity_score": 0,
            "import_depth": 0,
            "suggested_improvements": []
        }
    
    async def _security_analysis(self) -> List[CodeIssue]:
        """Perform security analysis."""
        issues = []
        
        # Check for SQL injection vulnerabilities
        sql_patterns = [
            (r"execute\s*\([^)]*%", "Potential SQL injection"),
            (r"f[\"'].*SELECT[^\"']*\{", "Potential SQL injection with f-string"),
        ]
        
        # Check for path traversal
        path_patterns = [
            (r"open\s*\([^)]*\%", "Potential path traversal"),
            (r"os\.path\.join\s*\([^)]*\.\.", "Potential path traversal"),
        ]
        
        # Would implement actual scanning here
        
        return issues
    
    async def _calculate_code_metrics(self) -> Dict[str, Any]:
        """Calculate code metrics."""
        python_files = list(self.slice_path.rglob("*.py"))
        
        total_lines = 0
        code_lines = 0
        comment_lines = 0
        blank_lines = 0
        
        for py_file in python_files:
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    total_lines += len(lines)
                    for line in lines:
                        stripped = line.strip()
                        if not stripped:
                            blank_lines += 1
                        elif stripped.startswith("#"):
                            comment_lines += 1
                        else:
                            code_lines += 1
            except Exception:
                pass
        
        return {
            "total_files": len(python_files),
            "total_lines": total_lines,
            "code_lines": code_lines,
            "comment_lines": comment_lines,
            "blank_lines": blank_lines,
            "comment_ratio": (comment_lines / code_lines * 100) if code_lines > 0 else 0
        }
    
    def _generate_recommendations(
        self,
        issues: List[CodeIssue],
        metrics: Dict[str, Any]
    ) -> List[str]:
        """Generate improvement recommendations."""
        recommendations = []
        
        # Group issues by type
        by_type = {}
        for issue in issues:
            if issue.issue_type not in by_type:
                by_type[issue.issue_type] = []
            by_type[issue.issue_type].append(issue)
        
        # Generate recommendations based on issues
        if "hardcoded_secret" in by_type:
            recommendations.append("Move secrets to environment variables or secure configuration")
        
        if "broad_exception" in by_type:
            recommendations.append("Replace broad except clauses with specific exception handling")
        
        if "print_statement" in by_type:
            recommendations.append("Replace print statements with proper logging")
        
        if metrics.get("comment_ratio", 100) < 10:
            recommendations.append("Increase code documentation - add docstrings and comments")
        
        if len(issues) > 20:
            recommendations.append("Consider refactoring to reduce code complexity")
        
        return recommendations
    
    def _calculate_health_score(
        self,
        issues: List[CodeIssue],
        metrics: Dict[str, Any]
    ) -> float:
        """Calculate overall health score (0-100)."""
        score = 100.0
        
        # Deduct for issues by severity
        severity_weights = {
            "critical": 15,
            "high": 10,
            "medium": 5,
            "low": 1
        }
        
        for issue in issues:
            score -= severity_weights.get(issue.severity, 5)
        
        # Bonus for documentation
        if metrics.get("comment_ratio", 0) > 20:
            score += 5
        
        # Cap score
        return max(0.0, min(100.0, score))
    
    async def generate_improvement_plan(
        self,
        analysis: AnalysisResult = None
    ) -> ImprovementPlan:
        """Generate an improvement plan based on analysis."""
        analysis = analysis or await self.run_full_analysis()
        
        improvements = []
        
        # Group issues by type and create improvements
        issue_groups = {}
        for issue in analysis.issues_found:
            if issue.issue_type not in issue_groups:
                issue_groups[issue.issue_type] = []
            issue_groups[issue.issue_type].append(issue)
        
        # Create improvements for each group
        for issue_type, group_issues in issue_groups.items():
            if len(improvements) >= self.max_improvements_per_plan:
                break
            
            improvement = self._create_improvement_from_issues(issue_type, group_issues)
            if improvement:
                improvements.append(improvement)
        
        # Calculate risk level
        high_risk = sum(1 for i in improvements if i.type in [
            ImprovementType.REFACTORING,
            ImprovementType.BUG_FIX
        ])
        risk_level = "high" if high_risk > 3 else "medium" if high_risk > 0 else "low"
        
        plan = ImprovementPlan(
            plan_id=self._generate_id(),
            slice_name=self.slice_name,
            created_at=datetime.utcnow(),
            improvements=improvements,
            estimated_impact="High" if len(improvements) > 5 else "Medium",
            risk_level=risk_level,
            requires_restart=risk_level == "high"
        )
        
        self._improvement_history.append(plan)
        return plan
    
    def _create_improvement_from_issues(
        self,
        issue_type: str,
        issues: List[CodeIssue]
    ) -> Optional[SliceImprovement]:
        """Create an improvement from a group of issues."""
        # Determine improvement type
        type_mapping = {
            "hardcoded_secret": ImprovementType.SECURITY,
            "broad_exception": ImprovementType.CODE_QUALITY,
            "print_statement": ImprovementType.CODE_QUALITY,
            "syntax_error": ImprovementType.BUG_FIX,
            "file_too_long": ImprovementType.REFACTORING,
            "missing_init": ImprovementType.CODE_QUALITY,
        }
        
        improvement_type = type_mapping.get(issue_type, ImprovementType.CODE_QUALITY)
        
        # Create changes
        changes = []
        auto_fixable = all(i.auto_fixable for i in issues)
        
        for issue in issues:
            if issue.auto_fixable and issue.fix_code:
                changes.append(CodeChange(
                    file_path=issue.file_path,
                    change_type="modify",
                    line_start=issue.line_number,
                    line_end=issue.line_number,
                    original_code=f"# Line {issue.line_number}: {issue.description}",
                    new_code=issue.fix_code,
                    reason=issue.suggestion
                ))
        
        if not changes:
            return None
        
        return SliceImprovement(
            improvement_id=self._generate_id(),
            type=improvement_type,
            title=f"Fix {len(issues)} {issue_type} issues",
            description=f"Address {len(issues)} {issue_type} issues found in analysis",
            changes=changes,
            estimated_time=len(changes) * 5,  # 5 minutes per change
            prerequisites=["backup_code"] if auto_fixable else []
        )
    
    async def apply_improvement_plan(self, plan: ImprovementPlan) -> bool:
        """Apply an improvement plan to the slice."""
        logger.info(f"Applying improvement plan {plan.plan_id} to {self.slice_name}")
        
        # Backup current state
        backup_path = await self._create_backup()
        logger.info(f"Created backup at {backup_path}")
        
        success = True
        
        # Apply each improvement
        for improvement in plan.improvements:
            for change in improvement.changes:
                result = await self._apply_change(change)
                if not result:
                    success = False
                    logger.error(f"Failed to apply change: {change.file_path}")
        
        if success:
            # Run tests to validate
            test_result = await self.run_tests()
            if test_result.failed > 0:
                logger.warning(f"Tests failed after applying improvements: {test_result.failed}")
                # Could rollback here if needed
        else:
            # Rollback
            await self._rollback(backup_path)
        
        return success
    
    async def _apply_change(self, change: CodeChange) -> bool:
        """Apply a single code change."""
        try:
            path = Path(change.file_path)
            
            if not path.exists():
                return False
            
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            # Apply the change
            if change.change_type == "replace":
                lines[change.line_start - 1:change.line_end] = [change.new_code + "\n"]
            elif change.change_type == "add":
                lines.insert(change.line_start - 1, change.new_code + "\n")
            elif change.change_type == "delete":
                lines[change.line_start - 1:change.line_end] = []
            
            with open(path, "w", encoding="utf-8") as f:
                f.writelines(lines)
            
            logger.info(f"Applied change to {path}")
            return True
            
        except Exception as e:
            logger.error(f"Error applying change: {e}")
            return False
    
    async def _create_backup(self) -> Path:
        """Create a backup of the current slice state."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.slice_path / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        backup_path = backup_dir / f"backup_{timestamp}"
        
        # Create tarball of slice
        import shutil
        shutil.make_archive(str(backup_path), "zip", self.slice_path)
        
        return backup_path
    
    async def _rollback(self, backup_path: Path):
        """Rollback to a previous backup."""
        try:
            import shutil
            # Extract backup to temp, then copy over
            temp_dir = backup_path.parent / "temp_rollback"
            shutil.unpack_archive(str(backup_path) + ".zip", str(temp_dir), "zip")
            
            # Copy files back
            for item in temp_dir.iterdir():
                dest = self.slice_path / item.name
                if dest.exists():
                    if dest.is_dir():
                        shutil.rmtree(dest)
                    else:
                        dest.unlink()
                shutil.copytree(item, dest) if item.is_dir() else shutil.copy(item, dest)
            
            # Cleanup
            shutil.rmtree(temp_dir)
            
            logger.info(f"Rolled back to {backup_path}")
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
    
    async def run_tests(self, test_type: str = "unit") -> TestResult:
        """Run slice tests."""
        logger.info(f"Running {test_type} tests for {self.slice_name}")
        
        test_run_id = self._generate_id()
        start_time = time.time()
        
        # Run pytest
        try:
            result = subprocess.run(
                [
                    sys.executable, "-m", "pytest",
                    str(self.slice_path / "tests"),
                    "-v", "--tb=short",
                    "--cov", str(self.slice_path),
                    "--cov-report=json"
                ],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            output = result.stdout + result.stderr
            
            # Parse results (simplified)
            passed = result.returncode == 0
            total = 1
            failed = 0 if passed else 1
            
            # Parse coverage from JSON report
            coverage = 0.0
            coverage_file = self.slice_path / "coverage.json"
            if coverage_file.exists():
                with open(coverage_file) as f:
                    data = json.load(f)
                    coverage = data.get("totals", {}).get("percent_covered", 0)
            
            duration = time.time() - start_time
            
            return TestResult(
                test_run_id=test_run_id,
                executed_at=datetime.utcnow(),
                total_tests=total,
                passed=total - failed,
                failed=failed,
                errors=0,
                coverage=coverage,
                duration=duration,
                output=output
            )
            
        except subprocess.TimeoutExpired:
            return TestResult(
                test_run_id=test_run_id,
                executed_at=datetime.utcnow(),
                total_tests=0,
                passed=0,
                failed=0,
                errors=1,
                coverage=0,
                duration=time.time() - start_time,
                output="Test execution timed out"
            )
        
        except Exception as e:
            return TestResult(
                test_run_id=test_run_id,
                executed_at=datetime.utcnow(),
                total_tests=0,
                passed=0,
                failed=0,
                errors=1,
                coverage=0,
                duration=time.time() - start_time,
                output=str(e)
            )
    
    async def create_cicd_pipeline(self) -> Dict[str, Any]:
        """Create CI/CD pipeline configuration for the slice."""
        pipeline = {
            "name": f"{self.slice_name}-pipeline",
            "trigger": {
                "branches": ["main", "develop"],
                "paths": [f"slices/{self.slice_name}/**"]
            },
            "stages": [
                {
                    "name": "lint",
                    "run": "flake8 slices/{} --max-line-length=100".format(self.slice_name),
                    "fail_fast": True
                },
                {
                    "name": "test",
                    "run": "pytest slices/{}/tests -v --cov".format(self.slice_name),
                    "fail_fast": False
                },
                {
                    "name": "analyze",
                    "run": "python -c 'from slices.{}.slice import {}; m=MetaSDLCEngine({}()); m.run_full_analysis()'".format(
                        self.slice_name, self.slice_name.title().replace("_", ""), self.slice_name
                    )
                },
                {
                    "name": "security",
                    "run": "bandit -r slices/{}".format(self.slice_name)
                },
                {
                    "name": "build",
                    "run": "docker build -t {}-slice:latest .".format(self.slice_name)
                }
            ]
        }
        
        return pipeline
    
    def _generate_id(self) -> str:
        """Generate a unique ID."""
        return hashlib.md5(
            f"{self.slice_name}{time.time()}".encode()
        ).hexdigest()[:12]
