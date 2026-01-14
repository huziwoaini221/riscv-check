"""Command-line interface for riscv-check."""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn

from riscv_check.analyzers.alignment import AlignmentAnalyzer
from riscv_check.analyzers.archdeps import ArchDepAnalyzer
from riscv_check.compiler.cross_compile import CrossCompileValidator
from riscv_check.core.project import Project, ProjectScanner
from riscv_check.report.model import Report, Severity
from riscv_check.report.render_console import ConsoleRenderer
from riscv_check.report.render_markdown import MarkdownRenderer

# Default console
console = Console()


@click.command()
@click.argument(
    "project_path",
    type=click.Path(exists=True, path_type=Path),
    required=True,
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output markdown report to file",
)
@click.option(
    "--no-compile",
    is_flag=True,
    help="Skip cross-compilation validation",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Show detailed output",
)
@click.option(
    "--ignore",
    multiple=True,
    type=str,
    help="Ignore specific rules (e.g., ALIGN_PTR_CAST)",
)
@click.version_option(version="0.1.0")
def main(
    project_path: Path,
    output: Optional[Path],
    no_compile: bool,
    verbose: bool,
    ignore: tuple,
):
    """RISC-V migration risk detector for C/C++ projects.

    \b
    Example:
        riscv-check /path/to/project
        riscv-check /path/to/project --output report.md
        riscv-check /path/to/project --ignore ARCH_ASM

    For more information, see: https://github.com/yourusername/riscv-check
    """
    # Convert project path to absolute
    project_path = project_path.resolve()

    # Step 1: Scan project
    with console.status("[bold green]Scanning project..."):
        try:
            project = ProjectScanner.scan(project_path)
        except Exception as e:
            console.print(f"[red]Error scanning project:[/red] {e}")
            sys.exit(1)

    console.print(f"[green]✓[/green] Found {len(project.files)} files")

    if not project.files:
        console.print("[yellow]No C/C++ files found in project.[/yellow]")
        sys.exit(0)

    # Step 2: Run analyzers
    all_issues = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(
            "[cyan]Analyzing...",
            total=len(project.files),
        )

        # Initialize analyzers
        analyzers = [
            ArchDepAnalyzer(verbose=verbose),
            AlignmentAnalyzer(verbose=verbose),
        ]

        # Filter by ignored rules
        ignored_rules = set(ignore)

        # Analyze each file
        for file in project.files:
            # Skip non-C/C++ files
            if file.suffix not in {".c", ".cpp", ".cc", ".cxx", ".h", ".hpp", ".hxx", ".hh"}:
                progress.update(task, advance=1)
                continue

            if verbose:
                console.print(f"  Analyzing: {file.relative_to(project_path)}")

            # Run all analyzers
            for analyzer in analyzers:
                try:
                    for issue in analyzer.analyze_file(file):
                        # Skip if rule is ignored
                        if issue.rule_id in ignored_rules:
                            continue
                        all_issues.append(issue)
                except Exception as e:
                    if verbose:
                        console.print(f"[yellow]Warning:[/yellow] {file}: {e}")

            progress.update(task, advance=1)

    # Step 3: Cross-compilation validation (if not skipped)
    build_success = True
    build_errors = []

    if not no_compile:
        console.print()
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                "[yellow]Cross-compiling for RISC-V...",
                total=len(project.files),
            )

            validator = CrossCompileValidator(verbose=verbose)
            c_files = [
                f for f in project.files
                if f.suffix in {".c", ".cpp", ".cc", ".cxx"}
            ]

            for file in c_files:
                result = validator.check_file(file)

                if result.skipped:
                    # Compiler not found, skip remaining files
                    if verbose:
                        console.print("[yellow]Cross-compiler not found, skipping validation[/yellow]")
                    break

                if not result.success:
                    build_success = False
                    for error in result.errors:
                        if error.strip():
                            build_errors.append(f"{file.relative_to(project_path)}: {error}")

                if result.warnings and verbose:
                    for warning in result.warnings:
                        console.print(f"[yellow]  Warning: {warning}[/yellow]")

                progress.update(task, advance=1)

            if build_success:
                console.print("[green]✓[/green] Cross-compilation [green]successful[/green]")
            elif build_errors:
                console.print("[red]✗[/red] Cross-compilation [red]failed[/red]")

    # Step 4: Generate report
    console.print()

    report = Report.from_analysis_results(
        project_path=str(project_path),
        files_scanned=len(project.files),
        issues=all_issues,
        build_success=build_success,
        build_errors=build_errors if build_errors else None,
    )

    # Step 5: Output to console
    ConsoleRenderer(console).render(report)

    # Step 6: Save to file if requested
    if output:
        try:
            MarkdownRenderer().render(report, output)
            console.print(f"\n[green]✓[/green] Full report saved to: [cyan]{output}[/cyan]")
        except Exception as e:
            console.print(f"[red]Error saving report:[/red] {e}")
            sys.exit(1)

    # Exit with error code if issues found
    error_count = report.error_count
    if error_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
