# core implementation of glob -> regex conversion
#
# Why char-by-char scanning instead of re.sub tricks:
#
# Glob patterns are NOT regular languages in the general case, but the subset
# most people actually use ( * ? [ ] ) is regular and maps cleanly onto regex.
# The danger is in *character classes*: [abc] is a literal character class in
# both glob and regex, but [a-z] uses a hyphen in both too, so the only real work
# is escaping the characters that are regex-special but glob-literal. A scan
# with an index lets us consume a whole class in one pass and copy its body
# verbatim, which is far less error-prone than per-character substitution.
#
# The result is ANCHORED at both ends ( ^...$ ). This is a deliberate choice:
# callers who want unanchored matching can strip the anchors; callers who want
# anchored matching (the common case for "does this filename match this glob")
# get it for free.


def _is_glob_meta(c: str) -> bool:
    """Return True for characters with special meaning in a glob pattern."""
    return c in ("*", "?", "[")


def _is_regex_meta(c: str) -> bool:
    """Return True for characters that must be escaped in a regex body.

    The list below is intentionally the set of characters that are significant
    in the default (non-verbose) Python regular expression syntax. We include
    '-' even though it is only special *inside* a character class; escaping it
    in the top-level body is harmless and makes the class-body handling simpler.
    """
    return c in "\\^$.|*+?()[]{}"


def glob_to_regex(pattern: str) -> str:
    """Convert a glob pattern into an anchored regular expression string.

    Supported glob syntax:
      *      matches any run of characters (including none)
      ?      matches exactly one character
      [ ]    a character class; body is copied verbatim except that an unescaped
             backslash in the glob is preserved so escapes like [\\]] still work

    Behaviour choices (stated plainly so callers are not surprised):
      * The result is ANCHORED: it begins with ^ and ends with $.
      * Backslashes in the glob are treated as literal backslashes in the
        regex, EXCEPT when they escape a character-class closer inside a [ ].
        This means a Windows-style path like dir\\file is accepted and matches
        a literal backslash; it does NOT turn the glob into a regex-escaping
        language.
      * Character classes support ranges, negation (leading !), and backslash
        escapes for ] and \\.
      * If '[' is not closed, it is treated as a literal '['. This is the
        pragmatic choice: many real inputs contain stray brackets.
    """
    out: list[str] = ["^"]
    i = 0
    n = len(pattern)

    while i < n:
        c = pattern[i]

        if c == "*":
            # Single star -> .* is the conventional mapping. We do NOT try to
            # make '**' mean "cross directory" because that would require a
            # path-separator convention the caller may not share.
            out.append(".*")
            i += 1
            continue

        if c == "?":
            out.append(".")
            i += 1
            continue

        if c == "[":
            close_idx = _find_class_close(pattern, i)
            if close_idx == -1:
                # Unclosed bracket is treated as a literal. See docstring.
                out.append(r"\[")
                i += 1
                continue

            class_body = pattern[i + 1 : close_idx]
            out.append("[")
            out.append(_convert_class_body(class_body))
            out.append("]")
            i = close_idx + 1
            continue

        if _is_regex_meta(c):
            out.append("\\" + c)
        else:
            out.append(c)
        i += 1

    out.append("$")
    return "".join(out)


def _find_class_close(pattern: str, open_idx: int) -> int:
    """Return the index of the ']' that closes the class opened at open_idx.

    Returns -1 if there is no closing bracket.

    Rules:
      * The first character after '[' may be '!' to negate; it is not a close.
      * A ']' as the very first character of the class body (or the first after
        a leading '!') is a literal member, not the close. This mirrors POSIX.
      * A backslash escapes the next character, so ]\\]] has the close at the
        final ']', not the one after the backslash.
    """
    n = len(pattern)
    j = open_idx + 1

    # leading ! negates; skip it so a following ] is treated as literal
    if j < n and pattern[j] == "!":
        j += 1

    # a leading ] is a literal member
    if j < n and pattern[j] == "]":
        j += 1

    while j < n:
        if pattern[j] == "\\":
            j += 2  # skip the escaped char
            continue
        if pattern[j] == "]":
            return j
        j += 1

    return -1


def _convert_class_body(body: str) -> str:
    """Render a glob character-class body as a regex character-class body.

    The body is the text between the brackets, exclusive. We:
      * Convert a leading '!' (negation) to '^' as required by regex syntax.
      * Pass ranges (a-z) through unchanged.
      * Escape a few characters that would otherwise be misread inside a regex
        class: backslash, and the close bracket when not already escaped.
    """
    if not body:
        # An empty class [] is not meaningful; we choose to match nothing by
        # emitting a class that can never satisfy (a-z inverted against the
        # empty set). This is safer than emitting [] which is a regex error.
        return "^\\\\\\s\\S"

    result: list[str] = []
    i = 0
    n = len(body)

    if body[0] == "!":
        result.append("^")
        i = 1
    elif body[0] == "^":
        # A literal leading ^ in the glob would be interpreted as regex
        # negation, so escape it to keep the class positive.
        result.append(r"\^")
        i = 1

    while i < n:
        c = body[i]
        if c == "\\":
            # Preserve backslash and the following character verbatim. This
            # keeps user-written escapes like ] and \\ working as intended.
            if i + 1 < n:
                result.append(body[i])
                result.append(body[i + 1])
                i += 2
            else:
                # Trailing lone backslash: escape it so the regex is valid.
                result.append(r"\\\\")
                i += 1
            continue
        if c == "]":
            # An unescaped ] inside the body. _find_class_close already handled
            # the leading-] case, so this is a genuine literal close bracket
            # that must be escaped to keep the regex class valid.
            result.append(r"\]")
            i += 1
            continue
        result.append(c)
        i += 1

    return "".join(result)
