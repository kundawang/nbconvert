"""Regression tests for mistune compatibility.

The markdown filter supports both mistune 2.x and 3.x. mistune 3.1 renamed
the ``axt_heading`` block rule to ``atx_heading``; a stale rule override then
pointed at a rule without a matching ``parse_*`` method and broke parser
construction (and with it every HTML export). These tests guard that
interface directly so they fail on such renames regardless of mistune version.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import pytest

mistune = pytest.importorskip("mistune")

from nbconvert.filters.markdown_mistune import (  # noqa: E402
    MISTUNE_V3,
    IPythonRenderer,
    MarkdownWithMath,
    MathBlockParser,
    MathInlineParser,
    import_plugin,
    markdown2html_mistune,
)


def _rule_names(parser):
    """Return the rule names mistune resolves to ``parse_*`` methods."""
    if MISTUNE_V3:
        # BlockParser resolves every SPECIFICATION entry, InlineParser only
        # its active rules (SPECIFICATION also holds precedence-scan rules
        # such as ``prec_auto_link`` that have no ``parse_*`` method).
        if hasattr(parser, "SPECIFICATION") and not hasattr(parser, "rules"):
            return [name for name in parser.SPECIFICATION if not name.startswith("_")]
        return list(parser.rules)
    return list(parser.RULE_NAMES)


def test_block_parser_rules_have_parse_methods():
    """Every registered block rule must resolve to a ``parse_*`` method."""
    parser = MathBlockParser()
    for name in _rule_names(parser):
        assert callable(getattr(parser, f"parse_{name}", None)), f"missing parse_{name}"


def test_inline_parser_rules_have_parse_methods():
    """Every registered inline rule must resolve to a ``parse_*`` method."""
    if MISTUNE_V3:
        parser = MathInlineParser(hard_wrap=False)
    else:
        parser = MathInlineParser(IPythonRenderer(), hard_wrap=False)
    for name in _rule_names(parser):
        assert callable(getattr(parser, f"parse_{name}", None)), f"missing parse_{name}"


def test_default_plugins_are_importable():
    """All default plugins must load through mistune's plugin interface."""
    for name in MarkdownWithMath.DEFAULT_PLUGINS:
        assert callable(import_plugin(name)), f"plugin {name!r} is not importable"


def test_markdown_with_math_constructs():
    """Building the full parser/renderer stack must not raise."""
    MarkdownWithMath(renderer=IPythonRenderer(escape=False))


def test_heading_without_space_after_hash():
    """Headings without a space after '#' must keep rendering as headings."""
    html = markdown2html_mistune("#test")
    assert "<h1" in html
    assert ">test<" in html


def test_builtin_plugins_render():
    """The default plugins must produce their expected HTML fragments."""
    assert "<del>strike</del>" in markdown2html_mistune("~~strike~~")
    assert "<table>" in markdown2html_mistune("| a |\n| - |\n| 1 |")
    assert "checkbox" in markdown2html_mistune("- [x] done")
    assert "<dl>" in markdown2html_mistune("Term\n: definition")
    assert '<a href="https://example.com">' in markdown2html_mistune("https://example.com")


def test_math_still_renders():
    """Math pass-through must survive the parser wiring."""
    assert "$$x^2$$" in markdown2html_mistune("$$x^2$$")
    assert "$x^2$" in markdown2html_mistune("$x^2$")
