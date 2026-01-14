"""Console report rendering with Rich."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from riscv_check.report.model import Report, Issue, Severity


class ConsoleRenderer:
    """Renderer for console output using Rich."""

    # Text indicators (no emojis per P0-3 requirement)
    SEVERITY_TEXT = {
        Severity.ERROR: "[ERROR]",
        Severity.WARNING: "[WARNING]",
        Severity.INFO: "[INFO]",
    }

    def __init__(self, console: Console = None):
        """Initialize the renderer.

        Args:
            console: Rich console instance, creates new one if None
        """
        self.console = console or Console()

    def render(self, report: Report):
        """Render report to console.

        Args:
            report: Report to render
        """
        # Title
        self.console.print()
        self.console.print(
            "[bold cyan]RISC-V Migration Risk Report[/bold cyan]"
        )
        self.console.print("=" * 50)

        # Summary
        self._print_summary(report)

        # Issues
        if report.issues:
            self._print_issues(report.issues)

        # Recommendations
        self._print_recommendations(report)

    def _print_summary(self, report: Report):
        """Print report summary.

        Args:
            report: Report to summarize
        """
        error_count = report.error_count
        warn_count = report.warning_count
        info_count = report.info_count

        # Determine color based on score
        if report.risk_score >= 80:
            score_color = "green"
        elif report.risk_score >= 50:
            score_color = "yellow"
        else:
            score_color = "red"

        # Create summary panel
        panel_text = (
            f"Project: {report.project_path}\n"
            f"Files scanned: [bold]{report.files_scanned}[/bold]\n"
            f"Risk Score: [{score_color}]{report.risk_score}/100[/ {score_color}] - {report.status}\n"
            f"\n"
            f"Summary:\n"
            f"  {self.SEVERITY_TEXT[Severity.ERROR]} ERROR: {error_count} issues\n"
            f"  {self.SEVERITY_TEXT[Severity.WARNING]} WARNING: {warn_count} issues\n"
            f"  {self.SEVERITY_TEXT[Severity.INFO]} INFO: {info_count} issues"
        )

        panel = Panel(
            panel_text,
            title="[bold]Summary[/bold]",
            border_style="cyan",
        )

        self.console.print(panel)

    def _print_issues(self, issues: list[Issue]):
        """Print issues grouped by severity.

        Args:
            issues: List of issues to print
        """
        # Group by severity
        error_issues = [i for i in issues if i.severity == Severity.ERROR]
        warning_issues = [i for i in issues if i.severity == Severity.WARNING]
        info_issues = [i for i in issues if i.severity == Severity.INFO]

        # Print critical issues
        if error_issues:
            self.console.print("\n[bold red]Critical Issues (must fix):[/bold red]")
            for i in error_issues[:20]:  # Limit to 20
                self._print_issue(i)
            if len(error_issues) > 20:
                self.console.print(
                    f"  ... and {len(error_issues) - 20} more ERRORs"
                )

        # Print warnings
        if warning_issues:
            self.console.print("\n[bold yellow]Warnings:[/bold yellow]")
            for i in warning_issues[:10]:  # Limit to 10
                self._print_issue(i)
            if len(warning_issues) > 10:
                self.console.print(
                    f"  ... and {len(warning_issues) - 10} more WARNINGs"
                )

        # Print info
        if info_issues:
            self.console.print("\n[bold blue]Info:[/bold blue]")
            for i in info_issues[:5]:  # Limit to 5
                self._print_issue(i)
            if len(info_issues) > 5:
                self.console.print(
                    f"  ... and {len(info_issues) - 5} more INFOs"
                )

    def _print_issue(self, issue: Issue):
        """Print a single issue.

        Args:
            issue: Issue to print
        """
        location = f"{issue.file}:{issue.line}"
        if issue.column:
            location += f":{issue.column}"

        self.console.print(
            f"  {self.SEVERITY_TEXT[issue.severity]} "
            f"[cyan]{location}[/cyan] "
            f"[bold]{issue.rule_id}[/bold]"
        )
        self.console.print(f"      → {issue.message}")

        if issue.suggestion:
            self.console.print(f"      Suggestion: {issue.suggestion}")

        self.console.print()

    def _print_recommendations(self, report: Report):
        """Print recommendations.

        Args:
            report: Report with recommendations
        """
        if not report.recommendations:
            return

        rec_text = "\n".join(f"• {rec}" for rec in report.recommendations)

        panel = Panel(
            rec_text,
            title="[bold]Recommendations[/bold]",
            border_style="yellow",
        )

        self.console.print("\n")
        self.console.print(panel)
