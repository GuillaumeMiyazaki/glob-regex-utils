import re
import unittest

from glob_regex_utils import glob_to_regex


class GlobToRegexTests(unittest.TestCase):
    """Behaviour tests for glob_to_regex.

    Each test compiles the returned regex with re.compile and runs match().
    This proves the output is a valid Python regex and behaves as documented.
    """

    def test_literal(self):
        rx = re.compile(glob_to_regex("hello.txt"))
        self.assertIsNotNone(rx.match("hello.txt"))
        self.assertIsNone(rx.match("helloXtxt"))

    def test_star_matches_empty(self):
        rx = re.compile(glob_to_regex("a*c"))
        self.assertIsNotNone(rx.match("ac"))
        self.assertIsNotNone(rx.match("abc"))
        self.assertIsNotNone(rx.match("abbbbbc"))
        self.assertIsNone(rx.match("ab"))

    def test_star_matches_anything(self):
        rx = re.compile(glob_to_regex("*"))
        self.assertIsNotNone(rx.match(""))
        self.assertIsNotNone(rx.match("anything at all"))

    def test_question_one_char(self):
        rx = re.compile(glob_to_regex("a?c"))
        self.assertIsNotNone(rx.match("abc"))
        self.assertIsNone(rx.match("ac"))
        self.assertIsNone(rx.match("abbc"))

    def test_anchored(self):
        rx = re.compile(glob_to_regex("abc"))
        self.assertIsNotNone(rx.match("abc"))
        self.assertIsNone(rx.match("abcd"))
        self.assertIsNone(rx.match("xabc"))

    def test_class_simple(self):
        rx = re.compile(glob_to_regex("[abc]"))
        self.assertIsNotNone(rx.match("a"))
        self.assertIsNotNone(rx.match("b"))
        self.assertIsNotNone(rx.match("c"))
        self.assertIsNone(rx.match("d"))

    def test_class_range(self):
        rx = re.compile(glob_to_regex("[a-c]"))
        self.assertIsNotNone(rx.match("a"))
        self.assertIsNotNone(rx.match("b"))
        self.assertIsNotNone(rx.match("c"))
        self.assertIsNone(rx.match("d"))

    def test_class_negation(self):
        rx = re.compile(glob_to_regex("[!abc]"))
        self.assertIsNone(rx.match("a"))
        self.assertIsNone(rx.match("b"))
        self.assertIsNone(rx.match("c"))
        self.assertIsNotNone(rx.match("d"))

    def test_class_with_star(self):
        rx = re.compile(glob_to_regex("[a-c]*"))
        self.assertIsNotNone(rx.match("cXYZ"))
        self.assertIsNone(rx.match("dXYZ"))

    def test_literal_dot_escaped(self):
        rx = re.compile(glob_to_regex("file.txt"))
        self.assertIsNotNone(rx.match("file.txt"))
        self.assertIsNone(rx.match("fileXtxt"))

    def test_plus_escaped(self):
        rx = re.compile(glob_to_regex("a+b"))
        self.assertIsNotNone(rx.match("a+b"))
        self.assertIsNone(rx.match("a+b".replace("+", "")))

    def test_parens_escaped(self):
        rx = re.compile(glob_to_regex("(group)"))
        self.assertIsNotNone(rx.match("(group)"))

    def test_literal_backslash_in_text(self):
        rx = re.compile(glob_to_regex("a\\b"))
        self.assertIsNotNone(rx.match("a\\b"))
        self.assertIsNone(rx.match("a"))

    def test_unclosed_bracket_is_literal(self):
        rx = re.compile(glob_to_regex("a[b"))
        self.assertIsNotNone(rx.match("a[b"))

    def test_empty_pattern_matches_only_empty(self):
        rx = re.compile(glob_to_regex(""))
        self.assertIsNotNone(rx.match(""))
        self.assertIsNone(rx.match("x"))

    def test_class_leading_close_is_literal(self):
        # []a] means: a class containing ] and a
        rx = re.compile(glob_to_regex("[]a]"))
        self.assertIsNotNone(rx.match("]"))
        self.assertIsNotNone(rx.match("a"))
        self.assertIsNone(rx.match("b"))

    def test_class_with_escaped_close(self):
        rx = re.compile(glob_to_regex("[a\\]]"))
        self.assertIsNotNone(rx.match("a"))
        self.assertIsNotNone(rx.match("]"))
        self.assertIsNone(rx.match("b"))

    def test_returns_string_type(self):
        self.assertIsInstance(glob_to_regex("abc"), str)

    def test_result_starts_and_ends_with_anchor(self):
        rx = glob_to_regex("abc")
        self.assertTrue(rx.startswith("^"))
        self.assertTrue(rx.endswith("$"))


if __name__ == "__main__":
    unittest.main()
