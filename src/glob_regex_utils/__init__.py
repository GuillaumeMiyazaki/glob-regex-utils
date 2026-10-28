# glob_regex_utils package
#
# This package contains exactly one public entry point: glob_to_regex, which
# converts a glob pattern into an anchored regular expression string.
#
# The module re-exports the function and does not expose any other names.
# Keeping the public surface to one function avoids accidental coupling: if
# the implementation needs to grow, callers will only depend on the contract
# documented in core.glob_to_regex.

from glob_regex_utils.core import glob_to_regex

__all__ = ["glob_to_regex"]
