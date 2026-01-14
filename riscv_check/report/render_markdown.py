"""Markdown report generation."""

from datetime import datetime
from pathlib import Path
from typing import List

from riscv_check.report.model import Report, Issue, Severity


class MarkdownRenderer:
    """Renderer for Markdown output."""

    def __init__(self):
        """Initialize the renderer."""
        pass

    def render(self, report: Report, output_path: Path):
        """Render report to Markdown file.

        Args:
            report: Report to render
            output_path: Path to output file
        """
        lines = [
            "# RISC-V Migration Risk Report",
            "",
            f"**Project**: `{report.project_path}`",
            f"**Generated**: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Risk Score**: {self._score_badge(report.risk_score)}",
            "",
            "---",
            "",
        ]

        # Summary
        lines.extend(self._render_summary(report))

        # Issues
        if report.issues:
            lines.extend(self._render_issues(report.issues))

        # Recommendations
        if report.recommendations:
            lines.extend(self._render_recommendations(report.recommendations))

        # Write to file
        output_path.write_text("\n".join(lines))

    def _score_badge(self, score: int) -> str:
        """Generate a score badge.

        Args:
            score: Risk score

        Returns:
            Markdown badge string
        """
        if score >= 80:
            color = "brightgreen"
            status = "PASS"
        elif score >= 50:
            color = "yellow"
            status = "WARN"
        else:
            color = "red"
            status = "FAIL"

        return (
            f"![{status}]"
            f"(https://img.shields.io/badge/{status}-{score}-{color})"
        )

    def _render_summary(self, report: Report) -> List[str]:
        """Render summary section.

        Args:
            report: Report to summarize

        Returns:
            List of markdown lines
        """
        return [
            "## Summary",
            "",
            f"- **Files scanned**: {report.files_scanned}",
            f"- **Risk score**: {report.risk_score}/100 ({report.status})",
            f"- **Issues found**:",
            f"  - 🔴 **ERROR**: {report.error_count}",
            f"  - 🟡 **WARNING**: {report.warning_count}",
            f"  - 🔵 **INFO**: {report.info_count}",
            "",
            f"{report.summary}",
            "",
            "---",
            "",
        ]

    def _render_issues(self, issues: List[Issue]) -> List[str]:
        """Render issues section.

        Args:
            issues: List of issues

        Returns:
            List of markdown lines
        """
        lines = [
            "## Detailed Findings",
            "",
        ]

        # Group by severity
        error_issues = [i for i in issues if i.severity == Severity.ERROR]
        warning_issues = [i for i in issues if i.severity == Severity.WARNING]
        info_issues = [i for i in issues if i.severity == Severity.INFO]

        # Render each group
        if error_issues:
            lines.extend(self._render_issue_group("Critical Issues (ERROR)", error_issues))

        if warning_issues:
            lines.extend(self._render_issue_group("Warnings (WARNING)", warning_issues))

        if info_issues:
            lines.extend(self._render_issue_group("Info (INFO)", info_issues))

        return lines

    def _render_issue_group(self, title: str, issues: List[Issue]) -> List[str]:
        """Render a group of issues.

        Args:
            title: Group title
            issues: List of issues

        Returns:
            List of markdown lines
        """
        lines = [
            f"### {title}",
            "",
        ]

        for i, issue in enumerate(issues, 1):
            location = f"{issue.file}:{issue.line}"
            if issue.column:
                location += f":{issue.column}"

            lines.append(
                f"#### {i}. {location} - `{issue.rule_id}`"
            )
            lines.append("")
            lines.append(f"**Severity**: {self._severity_emoji(issue.severity)} {issue.severity.value}")
            lines.append("")
            lines.append(f"**Description**: {issue.message}")
            lines.append("")

            if issue.code_snippet:
                lines.append("**Code**:")
                lines.append("")
                lines.append("```c")
                lines.append(issue.code_snippet)
                lines.append("```")
                lines.append("")

            if issue.suggestion:
                lines.append("**Suggestion**:")
                lines.append("")
                lines.append(issue.suggestion)
                lines.append("")

            if issue.verification:
                lines.append("**Verification**:")
                lines.append("")
                lines.append(f"```bash")
                lines.append(issue.verification)
                lines.append(f"```")
                lines.append("")

            lines.append("---")
            lines.append("")

        return lines

    def _render_recommendations(self, recommendations: List[str]) -> List[str]:
        """Render recommendations section.

        Args:
            recommendations: List of recommendations

        Returns:
            List of markdown lines
        """
        lines = [
            "## Recommendations",
            "",
        ]

        for rec in recommendations:
            lines.append(f"- {rec}")

        lines.append("")
        lines.append("---")
        lines.append("")

        return lines

    def _severity_emoji(self, severity: Severity) -> str:
        """Get emoji for severity level.

        Args:
            severity: Severity level

        Returns:
            Emoji string
        """
        return {
            Severity.ERROR: "🔴",
            Severity.WARNING: "🟡",
            Severity.INFO: "🔵",
        }[severity]
