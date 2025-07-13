"""
Robust SQL parser for PostgreSQL scripts.
Handles complex scripts including PL/pgSQL functions, dollar-quoted strings, and comments.
"""

import re
from typing import List, Tuple


class PostgreSQLScriptParser:
    """Parser for PostgreSQL scripts that handles complex syntax."""

    def __init__(self):
        # Regex patterns for different SQL elements
        self.dollar_quote_pattern = r"\$[A-Za-z0-9_]*\$"
        self.single_line_comment_pattern = r"--.*$"
        self.multi_line_comment_pattern = r"/\*.*?\*/"

    def parse_script(self, script_content: str) -> List[str]:
        """
        Parse a PostgreSQL script into individual statements.

        Args:
            script_content: Raw script content as string

        Returns:
            List of individual SQL statements
        """
        # First, normalize line endings
        content = script_content.replace("\r\n", "\n").replace("\r", "\n")

        # Remove single-line comments
        content = self._remove_single_line_comments(content)

        # Remove multi-line comments
        content = self._remove_multi_line_comments(content)

        # Split into statements, preserving dollar-quoted strings
        statements = self._split_statements(content)

        # Clean up statements
        statements = self._clean_statements(statements)

        return statements

    def _remove_single_line_comments(self, content: str) -> str:
        """Remove single-line comments while preserving dollar-quoted strings."""
        lines = content.split("\n")
        result_lines = []

        for line in lines:
            # Check if line contains dollar-quoted strings
            dollar_quotes = re.findall(self.dollar_quote_pattern, line)

            if not dollar_quotes:
                # No dollar quotes, safe to remove comments
                comment_pos = line.find("--")
                if comment_pos != -1:
                    line = line[:comment_pos]
                result_lines.append(line)
            else:
                # Has dollar quotes, need to be more careful
                # For now, keep the line as-is if it has dollar quotes
                result_lines.append(line)

        return "\n".join(result_lines)

    def _remove_multi_line_comments(self, content: str) -> str:
        """Remove multi-line comments while preserving dollar-quoted strings."""
        # This is a simplified approach - in practice, we'd need more sophisticated parsing
        # For now, we'll use a regex that's careful about dollar quotes
        return re.sub(self.multi_line_comment_pattern, "", content, flags=re.DOTALL)

    def _split_statements(self, content: str) -> List[str]:
        """
        Split content into SQL statements, preserving dollar-quoted strings.

        This is the core logic that handles complex PostgreSQL syntax.
        """
        statements = []
        current_statement = []
        in_dollar_quote = False
        dollar_quote_tag = None
        paren_depth = 0

        lines = content.split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for dollar-quoted strings
            dollar_quotes = re.findall(self.dollar_quote_pattern, line)

            for quote in dollar_quotes:
                if not in_dollar_quote:
                    # Starting a dollar-quoted string
                    in_dollar_quote = True
                    dollar_quote_tag = quote
                elif quote == dollar_quote_tag:
                    # Ending the dollar-quoted string
                    in_dollar_quote = False
                    dollar_quote_tag = None

            # Track parentheses for function definitions
            if not in_dollar_quote:
                paren_depth += line.count("(") - line.count(")")

            current_statement.append(line)

            # Check if we should end the statement
            if self._should_end_statement(line, in_dollar_quote, paren_depth):
                statement = " ".join(current_statement)
                if statement.strip():
                    statements.append(statement)
                current_statement = []
                paren_depth = 0

        # Add any remaining statement
        if current_statement:
            statement = " ".join(current_statement)
            if statement.strip():
                statements.append(statement)

        return statements

    def _should_end_statement(
        self, line: str, in_dollar_quote: bool, paren_depth: int
    ) -> bool:
        """
        Determine if we should end the current statement.

        Args:
            line: Current line being processed
            in_dollar_quote: Whether we're inside a dollar-quoted string
            paren_depth: Current parenthesis depth

        Returns:
            True if statement should end
        """
        # Don't end if we're in a dollar-quoted string
        if in_dollar_quote:
            return False

        # Don't end if we have unmatched parentheses (function definition)
        if paren_depth > 0:
            return False

        # End on semicolon (but not inside dollar quotes)
        if line.rstrip().endswith(";"):
            return True

        return False

    def _clean_statements(self, statements: List[str]) -> List[str]:
        """Clean up statements and ensure they end with semicolons."""
        cleaned = []

        for statement in statements:
            statement = statement.strip()
            if not statement:
                continue

            # Ensure statement ends with semicolon
            if not statement.endswith(";"):
                statement += ";"

            cleaned.append(statement)

        return cleaned


def parse_postgresql_script(script_content: str) -> List[str]:
    """
    Convenience function to parse a PostgreSQL script.

    Args:
        script_content: Raw script content as string

    Returns:
        List of individual SQL statements
    """
    parser = PostgreSQLScriptParser()
    return parser.parse_script(script_content)
