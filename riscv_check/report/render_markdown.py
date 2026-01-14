"""Markdown report generation."""

from datetime import datetime
from pathlib import Path
from typing import List

from riscv_check.report.model import Report, Issue, Severity, EvidenceLevel
from riscv_check.report.render_maintainer import MaintainerRenderer


class MarkdownRenderer:
    """Renderer for Markdown output."""

    # Emojis to be removed in professional reports
    SEVERITY_EMOJIS = {
        Severity.ERROR: "🔴",
        Severity.WARNING: "🟡",
        Severity.INFO: "🔵",
    }

    # Text indicators (no emojis)
    SEVERITY_TEXT = {
        Severity.ERROR: "[ERROR]",
        Severity.WARNING: "[WARNING]",
        Severity.INFO: "[INFO]",
    }

    # Language templates
    TEMPLATES = {
        'en': {
            'title': "RISC-V Migration Risk Report",
            'summary': "Summary",
            'files_scanned': "Files scanned",
            'risk_score': "Risk score",
            'issues_found': "Issues found",
            'detailed_findings': "Detailed Findings",
            'severity': "Severity",
            'description': "Description",
            'code': "Code",
            'suggestion': "Suggestion",
            'verification': "Verification",
            'recommendations': "Recommendations",
        },
        'zh': {
            'title': "RISC-V 迁移风险评估报告",
            'summary': "摘要",
            'files_scanned': "扫描文件数",
            'risk_score': "风险评分",
            'issues_found': "发现问题",
            'detailed_findings': "详细发现",
            'severity': "严重程度",
            'description': "描述",
            'code': "代码",
            'suggestion': "建议",
            'verification': "验证",
            'recommendations': "建议",
        },
    }

    def __init__(self, style: str = 'concise', language: str = 'en'):
        """Initialize the renderer.

        Args:
            style: Report style ('verbose', 'concise', 'minimal')
            language: Report language ('en' or 'zh')
        """
        self.style = style
        self.language = language
        self.templates = self.TEMPLATES[language]

    def render(self, report: Report, output_path: Path):
        """Render report to Markdown file.

        Args:
            report: Report to render
            output_path: Path to output file
        """
        # Select render method based on style
        if self.style == 'verbose':
            lines = self._render_verbose(report)
        elif self.style == 'minimal':
            lines = self._render_minimal(report)
        elif self.style == 'maintainer':
            # Use MaintainerRenderer for maintainer style
            MaintainerRenderer().render(report.issues, output_path)
            return
        else:  # concise
            lines = self._render_concise(report)

        # Write to file
        output_path.write_text("\n".join(lines))

    def _render_concise(self, report: Report) -> List[str]:
        """Render concise report (< 2 screens, ~40-60 lines).

        Args:
            report: Report to render

        Returns:
            List of markdown lines
        """
        lines = [
            f"# {self.templates['title']}",
            "",
            f"**Project**: `{report.project_path}`",
            f"**Generated**: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Risk Score**: {report.risk_score}/100 ({report.status})",
            "",
            "---",
            "",
            f"## {self.templates['summary']}",
            "",
            f"- **{self.templates['files_scanned']}**: {report.files_scanned}",
            f"- **{self.templates['risk_score']}**: {report.risk_score}/100 ({report.status})",
            f"- **{self.templates['issues_found']}**:",
            f"  - {self.SEVERITY_TEXT[Severity.ERROR]} {self._severity_label(Severity.ERROR)}: {report.error_count}",
            f"  - {self.SEVERITY_TEXT[Severity.WARNING]} {self._severity_label(Severity.WARNING)}: {report.warning_count}",
            f"  - {self.SEVERITY_TEXT[Severity.INFO]} {self._severity_label(Severity.INFO)}: {report.info_count}",
            "",
        ]

        # Issues (limit to top 10 for concise)
        if report.issues:
            lines.extend(self._render_issues_concise(report.issues[:10]))

        return lines

    def _render_verbose(self, report: Report) -> List[str]:
        """Render verbose report (detailed, > 2 screens).

        Args:
            report: Report to render

        Returns:
            List of markdown lines
        """
        lines = [
            f"# {self.templates['title']}",
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

        # Issues (all issues with full details)
        if report.issues:
            lines.extend(self._render_issues_verbose(report.issues))

        # Recommendations
        if report.recommendations:
            lines.extend(self._render_recommendations(report.recommendations))

        return lines

    def _render_minimal(self, report: Report) -> List[str]:
        """Render minimal report (just issues, < 1 screen).

        Args:
            report: Report to render

        Returns:
            List of markdown lines
        """
        lines = [
            f"# {report.project_path}",
            "",
            f"Risk Score: {report.risk_score}/100",
            f"Issues: {len(report.issues)}",
            "",
            "---",
            "",
        ]

        # Only issues, minimal formatting
        if report.issues:
            for issue in report.issues[:20]:  # Top 20
                lines.append(f"## {issue.file}:{issue.line} - {issue.rule_id}")
                lines.append("")
                lines.append(f"{self.SEVERITY_TEXT[issue.severity]} {issue.message}")
                lines.append("")

        return lines

    def _render_issues_concise(self, issues: List[Issue]) -> List[str]:
        """Render issues in concise format.

        Args:
            issues: List of issues

        Returns:
            List of markdown lines
        """
        lines = [
            f"## {self.templates['detailed_findings']}",
            "",
        ]

        for i, issue in enumerate(issues, 1):
            location = f"{issue.file}:{issue.line}"
            if issue.column:
                location += f":{issue.column}"

            lines.append(f"### {i}. {location} - `{issue.rule_id}`")
            lines.append("")
            lines.append(f"**{self.templates['severity']}**: {self._severity_label(issue.severity)}")
            lines.append("")
            lines.append(f"**{self.templates['description']}**: {issue.message}")
            lines.append("")

            # Code snippet (minimal)
            if issue.code_snippet:
                lines.append(f"**{self.templates['code']}**:")
                lines.append("")
                lines.append("```c")
                # Show only relevant lines (first 5)
                code_lines = issue.code_snippet.split('\n')[:5]
                lines.append('\n'.join(code_lines))
                if len(issue.code_snippet.split('\n')) > 5:
                    lines.append("...")
                lines.append("```")
                lines.append("")

            # Suggestion (brief)
            if issue.suggestion:
                lines.append(f"**{self.templates['suggestion']}**:")
                lines.append("")
                # First line only
                suggestion_lines = issue.suggestion.split('\n')
                lines.append(suggestion_lines[0])
                lines.append("")

            lines.append("---")
            lines.append("")

        return lines

    def _render_issues_verbose(self, issues: List[Issue]) -> List[str]:
        """Render issues in verbose format.

        Args:
            issues: List of issues

        Returns:
            List of markdown lines
        """
        lines = [
            f"## {self.templates['detailed_findings']}",
            "",
        ]

        # Group by severity
        error_issues = [i for i in issues if i.severity == Severity.ERROR]
        warning_issues = [i for i in issues if i.severity == Severity.WARNING]
        info_issues = [i for i in issues if i.severity == Severity.INFO]

        # Render each group
        if error_issues:
            lines.extend(self._render_issue_group(
                f"{self._severity_label(Severity.ERROR)} ({Severity.ERROR.value})",
                error_issues
            ))

        if warning_issues:
            lines.extend(self._render_issue_group(
                f"{self._severity_label(Severity.WARNING)} ({Severity.WARNING.value})",
                warning_issues
            ))

        if info_issues:
            lines.extend(self._render_issue_group(
                f"{self._severity_label(Severity.INFO)} ({Severity.INFO.value})",
                info_issues
            ))

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

            lines.append(f"#### {i}. {location} - `{issue.rule_id}`")
            lines.append("")
            lines.append(f"**Severity**: {self._severity_label(issue.severity)}")
            lines.append("")
            lines.append(f"**{self.templates['description']}**: {issue.message}")
            lines.append("")

            if issue.code_snippet:
                lines.append(f"**{self.templates['code']}**:")
                lines.append("")
                lines.append("```c")
                lines.append(issue.code_snippet)
                lines.append("```")
                lines.append("")

            if issue.suggestion:
                lines.append(f"**{self.templates['suggestion']}**:")
                lines.append("")
                lines.append(issue.suggestion)
                lines.append("")

            if issue.verification:
                lines.append(f"**{self.templates['verification']}**:")
                lines.append("")
                lines.append(f"```bash")
                lines.append(issue.verification)
                lines.append(f"```")
                lines.append("")

            lines.append("---")
            lines.append("")

        return lines

    def _render_summary(self, report: Report) -> List[str]:
        """Render summary section.

        Args:
            report: Report to summarize

        Returns:
            List of markdown lines
        """
        return [
            f"## {self.templates['summary']}",
            "",
            f"- **{self.templates['files_scanned']}**: {report.files_scanned}",
            f"- **{self.templates['risk_score']}**: {report.risk_score}/100 ({report.status})",
            f"- **{self.templates['issues_found']}**:",
            f"  - {self.SEVERITY_TEXT[Severity.ERROR]} {self._severity_label(Severity.ERROR)}: {report.error_count}",
            f"  - {self.SEVERITY_TEXT[Severity.WARNING]} {self._severity_label(Severity.WARNING)}: {report.warning_count}",
            f"  - {self.SEVERITY_TEXT[Severity.INFO]} {self._severity_label(Severity.INFO)}: {report.info_count}",
            "",
            f"{report.summary}",
            "",
            "---",
            "",
        ]

    def _render_recommendations(self, recommendations: List[str]) -> List[str]:
        """Render recommendations section.

        Args:
            recommendations: List of recommendations

        Returns:
            List of markdown lines
        """
        lines = [
            f"## {self.templates['recommendations']}",
            "",
        ]

        for rec in recommendations:
            lines.append(f"- {rec}")

        lines.append("")
        lines.append("---")
        lines.append("")

        return lines

    def _score_badge(self, score: int) -> str:
        """Generate a score badge (only for verbose style).

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

    def _severity_label(self, severity: Severity) -> str:
        """Get severity label for current language.

        Args:
            severity: Severity level

        Returns:
            Severity label string
        """
        if self.language == 'en':
            return severity.value.upper()
        else:  # zh
            return {
                Severity.ERROR: "错误",
                Severity.WARNING: "警告",
                Severity.INFO: "信息",
            }[severity]
