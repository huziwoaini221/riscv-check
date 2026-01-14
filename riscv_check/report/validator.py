"""Report validation utilities."""

import re
from typing import List, Tuple
from pathlib import Path


class ReportValidator:
    """Validator for report quality checks."""

    # Patterns that indicate AI-generated content
    AI_PATTERNS = [
        r'🚀|💡|🔍|📖|🙏|❌|✅|🎯|⚡|🔨',  # Emojis
        r'Revolutionary|Groundbreaking|Game-changing|Cutting-edge',  # Marketing speak
        r'(Very|Really|Extremely)\s+(important|critical)',  # Over-emphasis
        r'Leverage|Utilize\s+(AI|machine learning)',  # Buzzwords
    ]

    # Patterns for professional technical writing
    PROFESSIONAL_REPLACEMENTS = {
        "a lot of": "multiple",
        "very fast": "efficient",
        "really good": "effective",
        "super important": "critical",
        "kind of": "approximately",
        "sort of": "partially",
    }

    @staticmethod
    def check_length(report_text: str, max_lines: int = 80) -> Tuple[bool, int]:
        """Check if report fits in specified number of lines.

        Args:
            report_text: Report content to check
            max_lines: Maximum allowed lines (default: 80 = 2 screens)

        Returns:
            Tuple of (is_valid, actual_line_count)
        """
        lines = report_text.count('\n')
        is_valid = lines <= max_lines
        return is_valid, lines

    @staticmethod
    def extract_links(text: str) -> List[str]:
        """Extract all URLs from text.

        Args:
            text: Text to search for URLs

        Returns:
            List of URLs found
        """
        # Match http/https URLs
        url_pattern = r'https?://[^\s\)\]>"]+'
        return re.findall(url_pattern, text)

    @staticmethod
    def validate_links(text: str, timeout: int = 5) -> Tuple[int, int, List[str]]:
        """Validate all links in text.

        Args:
            text: Text containing URLs
            timeout: Request timeout in seconds

        Returns:
            Tuple of (valid_count, invalid_count, broken_urls)
        """
        links = ReportValidator.extract_links(text)

        if not links:
            return 0, 0, []

        valid = 0
        broken = []

        try:
            import requests
        except ImportError:
            # If requests not available, assume all links are valid
            return len(links), 0, []

        for link in links:
            try:
                response = requests.head(link, timeout=timeout, allow_redirects=True)
                if response.status_code == 200:
                    valid += 1
                else:
                    broken.append(link)
            except Exception:
                broken.append(link)

        invalid = len(broken)
        return valid, invalid, broken

    @staticmethod
    def check_emojis(text: str) -> List[str]:
        """Check for emoji usage in text.

        Args:
            text: Text to check

        Returns:
            List of found emojis (empty if none)
        """
        try:
            import emoji
        except ImportError:
            # Fallback: check common emoji ranges
            emoji_pattern = re.compile(
                "["
                "\U0001F600-\U0001F64F"  # emoticons
                "\U0001F300-\U0001F5FF"  # symbols & pictographs
                "\U0001F680-\U0001F6FF"  # transport & map symbols
                "\U0001F1E0-\U0001F1FF"  # flags
                "\U00002702-\U000027B0"
                "\U000024C2-\U0001F251"
                "]+",
                flags=re.UNICODE
            )
            return emoji_pattern.findall(text)

        # Use emoji library if available
        emojis = []
        for char in text:
            if emoji.is_emoji(char):
                emojis.append(char)
        return emojis

    @staticmethod
    def check_ai_patterns(text: str) -> List[str]:
        """Check for AI-generated content patterns.

        Args:
            text: Text to check

        Returns:
            List of matched patterns
        """
        found = []

        for pattern in ReportValidator.AI_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                found.extend(matches)

        return found

    @staticmethod
    def validate_report_quality(
        report_text: str,
        check_links: bool = True,
        max_screens: int = 2
    ) -> Tuple[bool, List[str]]:
        """Comprehensive report quality validation.

        Args:
            report_text: Report content to validate
            check_links: Whether to validate URLs
            max_screens: Maximum allowed screens (1 screen = 40 lines)

        Returns:
            Tuple of (is_valid, list_of_warnings)
        """
        warnings = []
        max_lines = max_screens * 40

        # Check length
        is_valid_length, line_count = ReportValidator.check_length(report_text, max_lines)
        if not is_valid_length:
            warnings.append(
                f"Report too long: {line_count} lines (max {max_lines} = {max_screens} screens)"
            )

        # Check emojis
        emojis = ReportValidator.check_emojis(report_text)
        if emojis:
            warnings.append(f"Found {len(emojis)} emoji(s): {', '.join(set(emojis))}")

        # Check AI patterns
        ai_patterns = ReportValidator.check_ai_patterns(report_text)
        if ai_patterns:
            warnings.append(f"Found AI-generated patterns: {', '.join(set(ai_patterns))}")

        # Check links
        if check_links:
            valid, invalid, broken = ReportValidator.validate_links(report_text)
            if invalid > 0:
                warnings.append(
                    f"Found {invalid} broken link(s): {', '.join(broken[:3])}"
                )

        is_valid = len(warnings) == 0
        return is_valid, warnings

    @staticmethod
    def make_professional(text: str) -> str:
        """Replace informal language with professional alternatives.

        Args:
            text: Text to improve

        Returns:
            Improved text
        """
        result = text

        for old, new in ReportValidator.PROFESSIONAL_REPLACEMENTS.items():
            result = re.sub(old, new, result, flags=re.IGNORECASE)

        return result
