"""Core data models for issues and reports."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Severity level of an issue."""

    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class Issue(BaseModel):
    """A single issue found during analysis.

    Attributes:
        rule_id: Unique identifier for the rule (e.g., ALIGN_PTR_CAST)
        severity: How severe this issue is
        file: Path to the file where the issue was found
        line: Line number (1-indexed)
        column: Optional column number (1-indexed)
        message: Human-readable description of the issue
        suggestion: How to fix the issue
        verification: Optional method to verify the fix
        code_snippet: Optional relevant code snippet
    """

    rule_id: str = Field(..., description="Rule identifier, e.g., ALIGN_PTR_CAST")
    severity: Severity = Field(..., description="Severity level")
    file: str = Field(..., description="File path")
    line: int = Field(..., ge=1, description="Line number (1-indexed)")
    column: Optional[int] = Field(None, ge=1, description="Column number (1-indexed)")
    message: str = Field(..., description="Issue description")
    suggestion: str = Field(..., description="How to fix the issue")
    verification: Optional[str] = Field(None, description="How to verify the fix")
    code_snippet: Optional[str] = Field(None, description="Relevant code snippet")

    def __str__(self) -> str:
        """String representation for display."""
        location = f"{self.file}:{self.line}"
        if self.column:
            location += f":{self.column}"
        return f"[{self.severity.value}] {location} {self.rule_id}: {self.message}"


class Report(BaseModel):
    """Complete analysis report.

    Attributes:
        project_path: Root path of the analyzed project
        files_scanned: Number of files analyzed
        risk_score: Overall risk score (0-100, higher is better)
        issues: List of all issues found
        summary: Human-readable summary
        recommendations: List of actionable recommendations
        generated_at: When the report was generated
    """

    project_path: str = Field(..., description="Project root path")
    files_scanned: int = Field(..., ge=0, description="Number of files analyzed")
    risk_score: int = Field(..., ge=0, le=100, description="Risk score (0-100)")
    issues: List[Issue] = Field(default_factory=list, description="List of issues found")
    summary: str = Field(..., description="Human-readable summary")
    recommendations: List[str] = Field(
        default_factory=list, description="Actionable recommendations"
    )
    generated_at: datetime = Field(
        default_factory=datetime.now, description="Report generation timestamp"
    )

    @property
    def error_count(self) -> int:
        """Number of ERROR-level issues."""
        return sum(1 for issue in self.issues if issue.severity == Severity.ERROR)

    @property
    def warning_count(self) -> int:
        """Number of WARNING-level issues."""
        return sum(1 for issue in self.issues if issue.severity == Severity.WARNING)

    @property
    def info_count(self) -> int:
        """Number of INFO-level issues."""
        return sum(1 for issue in self.issues if issue.severity == Severity.INFO)

    @property
    def status(self) -> str:
        """Human-readable status based on risk score."""
        if self.risk_score >= 80:
            return "RECOMMENDED"
        elif self.risk_score >= 50:
            return "NEEDS FIXES"
        else:
            return "NOT RECOMMENDED"

    @classmethod
    def from_analysis_results(
        cls,
        project_path: str,
        files_scanned: int,
        issues: List[Issue],
        build_success: bool = True,
    ) -> "Report":
        """Create a report from analysis results.

        Args:
            project_path: Project root path
            files_scanned: Number of files analyzed
            issues: List of issues found
            build_success: Whether cross-compilation succeeded

        Returns:
            A complete Report instance
        """
        # Calculate risk score
        score = 100
        score -= sum(20 for issue in issues if issue.severity == Severity.ERROR)
        score -= sum(8 for issue in issues if issue.severity == Severity.WARNING)
        if not build_success:
            score -= 30
        score = max(0, score)  # Ensure non-negative

        # Generate summary
        error_count = sum(1 for i in issues if i.severity == Severity.ERROR)
        warning_count = sum(1 for i in issues if i.severity == Severity.WARNING)
        info_count = sum(1 for i in issues if i.severity == Severity.INFO)

        summary = (
            f"Found {error_count} ERRORs, {warning_count} WARNINGs, "
            f"{info_count} INFOs across {files_scanned} files."
        )

        # Generate recommendations
        recommendations = []

        if score < 50:
            recommendations.append(
                "DO NOT migrate until all critical ERRORs are fixed."
            )
        elif score < 80:
            recommendations.append(
                "Fix all ERRORs before attempting migration."
            )

        if error_count > 0:
            recommendations.append(
                f"Priority: Fix {error_count} ERROR issues first."
            )

        if warning_count > 10:
            recommendations.append(
                f"Review {warning_count} warnings for potential improvements."
            )

        if not build_success:
            recommendations.append(
                "Cross-compilation failed. Review build errors."
            )

        if score >= 80:
            recommendations.append(
                "Project appears ready for RISC-V migration."
            )

        return cls(
            project_path=project_path,
            files_scanned=files_scanned,
            risk_score=score,
            issues=issues,
            summary=summary,
            recommendations=recommendations,
        )
