# glob-regex-utils

Convert glob patterns to anchored regular expressions.

```python
from glob_regex_utils import glob_to_regex

import re

rx = re.compile(glob_to_regex("*.txt"))
rx.match("notes.txt")   # <re.Match object; ...>
rx.match("notes.py")    # None
```

The library exists because the standard library does not expose the glob-to-regex
mapping directly; `fnmatch.translate` produces a regex but also wraps it in
`(?s:...)` and uses a different negation convention. When you need the raw,
anchored expression (to compose with other regexes, to store, or to introspect),
`glob_to_regex` returns exactly `^...$` and nothing more.

Supported syntax: `*`, `?`, and character classes `[abc]`, `[a-z]`, `[!abc]`, with
backslash escapes inside classes for `]` and `\\`. Everything else is treated
literally and regex-special characters in the literal text are escaped for you.

One edge worth stating plainly: an unclosed `[` is treated as a literal `[`, not
an error. This is the pragmatic choice for inputs that contain stray brackets
without intending a class. If you need strict validation, check the pattern
before calling this function.

The only exported name is `glob_to_regex`.
