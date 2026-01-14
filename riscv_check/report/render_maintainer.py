"""Maintainer-style report generator.

Based on BenBE's feedback:
- One screen
- No emojis
- Concise
- Evidence-based
"""

from typing import List
from riscv_check.report.model import Issue, Severity


class MaintainerRenderer:
    """Generate maintainer-style reports (one screen, professional)."""

    # Evidence levels
    E0_STATIC = "E0"  # Pure static suspicion
    E1_ABI = "E1"     # ABI reasoning + static proof
    E2_CRASH = "E2"  # Reproduced crash + trace

    def __init__(self):
        """Initialize maintainer renderer."""
        pass

    def render(self, issues: List[Issue], output_path):
        """Render maintainer-style report.

        Args:
            issues: List of issues
            output_path: Path to output file
        """
        lines = []

        # Header (minimal)
        lines.append("# RISC-V Alignment Issue Report")
        lines.append("")
        lines.append(f"**Analysis Tool**: riscv-check (static analysis)")
        lines.append(f"**Issues Found**: {len(issues)}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Each issue in maintainer format (max 5 issues)
        for i, issue in enumerate(issues[:5], 1):
            lines.extend(self._render_issue_maintainer_style(i, issue))
            lines.append("")
            lines.append("---")
            lines.append("")

        # Footer
        lines.append("**Next Steps**:")
        lines.append("")
        lines.append("1. Verify if this is a real alignment issue")
        lines.append("2. Check if the allocator returns aligned memory")
        lines.append("3. Test on actual RISC-V hardware or QEMU")
        lines.append("")

        # Write
        output_path.write_text("\n".join(lines))

    def _render_issue_maintainer_style(self, index: int, issue: Issue) -> List[str]:
        """Render single issue in maintainer format.

        Format:
        1. Summary (1 line)
        2. Location (file:line:func)
        3. Minimal code (3-8 lines)
        4. Claim (what rule is violated)
        5. Evidence (what proof we have)
        6. Status (what we need from maintainer)
        """
        lines = []

        # 1. Summary
        severity = self._get_severity_text(issue)
        evidence = self._get_evidence_level(issue)
        lines.append(f"## Issue {index}: {severity} - {evidence}")
        lines.append("")

        # 2. Location
        location = f"{issue.file}:{issue.line}"
        lines.append(f"**Location**: {location}")
        lines.append("")

        # 3. Minimal code
        if issue.code_snippet:
            lines.append("**Code**:")
            lines.append("```c")
            # Show minimal context (3-8 lines)
            code_lines = issue.code_snippet.split('\n')
            if len(code_lines) > 8:
                lines.append("...")
            else:
                lines.append(issue.code_snippet)
            lines.append("```")
            lines.append("")

        # 4. Claim
        lines.append(f"**Claim**: {issue.message}")
        lines.append("")

        # 5. Evidence
        lines.append("**Evidence**:")
        lines.append("")
        evidence_text = self._generate_evidence_text(issue)
        lines.append(evidence_text)
        lines.append("")

        # 6. Status
        lines.append("**Status**:")
        lines.append("")
        status_text = self._generate_status_text(issue)
        lines.append(status_text)
        lines.append("")

        return lines

    def _get_severity_text(self, issue: Issue) -> str:
        """Get severity text without emoji."""
        if issue.severity == Severity.ERROR:
            return "ERROR"
        elif issue.severity == Severity.WARNING:
            return "WARNING"
        else:
            return "INFO"

    def _get_evidence_level(self, issue: Issue) -> str:
        """Determine evidence level."""
        # Check if issue has verification/test method
        if issue.verification and "qemu" in issue.verification.lower():
            return self.E2_CRASH
        elif issue.code_snippet:
            return self.E1_ABI
        else:
            return self.E0_STATIC

    def _generate_evidence_text(self, issue: Issue) -> str:
        """Generate evidence description."""
        evidence = self._get_evidence_level(issue)

        if evidence == self.E0_STATIC:
            return "- Static analysis only"
            "\n- Tool detected potential misalignment"
            "\n- Needs human verification"
        elif evidence == self.E1_ABI:
            return "- Static analysis with code context"
            "\n- Type mismatch detected in AST"
            "\n- Actual impact depends on runtime allocator behavior"
        else:  # E2_CRASH
            return "- Reproducible crash"
            "\n- Test case available"

    def _generate_status_text(self, issue: Issue) -> str:
        """Generate status/next steps."""
        evidence = self._get_evidence_level(issue)

        if evidence == self.E0_STATIC:
            return ("This is a static analysis finding.\n"
                   "Likely false positive if the allocator returns aligned memory.\n"
                   "Please verify the allocator implementation.")
        elif evidence == self.E1_ABI:
            return ("Code shows type mismatch.\n"
                   "Check if the source function (allocator) guarantees alignment.\n"
                   "If unsure, please review and let me know.")
        else:  # E2_CRASH
            return ("Reproducible crash detected.\n"
                   "Please review the fix suggestions.")
