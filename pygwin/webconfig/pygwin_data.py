"""script for compiling elm source and dumping it to the js folder."""

import functools
import io
import logging

import pygments

from pygwin.color_tools import rgb_to_ints
from pygwin.pgtribs import Pgtrib, get_pgtribs
from pygwin.prompt.base import PromptFormatter, default_prompt
from pygwin.pyghooks import (
    PygwinHtmlFormatter,
    PygwinLexer,
    PygwinStyle,
    Token,
    pygwin_style_proxy,
)
from pygwin.pygments_cache import get_all_styles
from pygwin.style_tools import partial_color_tokenize

# $PYGWIN_SUBPROC_CMD_RAISE_ERROR = True
# $PYGWIN_SHOW_TRACEBACK = False

#
# helper funcs
#


@functools.lru_cache(maxsize=4)
def get_rst_formatter(**kwargs):
    from pygments.formatters.html import HtmlFormatter
    from pygments.lexers.markup import RstLexer

    return RstLexer(), HtmlFormatter(**kwargs)


def escape(s):
    return s.replace("\n", "<br/>")


def invert_color(orig):
    r, g, b = rgb_to_ints(orig)
    inverted = [255 - r, 255 - g, 255 - b]
    new = [hex(n)[2:] for n in inverted]
    new = [n if len(n) == 2 else "0" + n for n in new]
    return "".join(new)


def html_format(s, style="default"):
    buf = io.StringIO()
    proxy_style = pygwin_style_proxy(PygwinStyle(style))
    # make sure we have a foreground color
    fgcolor = proxy_style._styles[Token.Text][0]
    if not fgcolor:
        fgcolor = invert_color(proxy_style.background_color[1:].strip("#"))
    # need to generate stream before creating formatter so that all tokens actually exist
    if isinstance(s, str):
        token_stream = partial_color_tokenize(s)
    else:
        token_stream = s
    formatter = PygwinHtmlFormatter(
        wrapcode=True,
        noclasses=True,
        style=proxy_style,
        prestyles="margin: 0em; padding: 0.5em 0.1em; color: #" + fgcolor,
        cssstyles="border-style: solid; border-radius: 5px",
    )
    formatter.format(token_stream, buf)
    return buf.getvalue()


def rst_to_html(text):
    try:
        from pygments import highlight

        lexer, formatter = get_rst_formatter(
            noclasses=True,
            cssstyles="background: transparent",
            style="monokai",  # a dark bg style
        )
        return highlight(text, lexer, formatter)
    except ImportError:
        return text


# render prompts
def get_named_prompts():
    return [
        (
            "default",
            default_prompt(),
        ),
        ("debian chroot", "{BOLD_GREEN}{user}@{hostname}{BOLD_BLUE} {cwd}{RESET} @ "),
        ("minimalist", "{BOLD_GREEN}{cwd_base}{RESET} @ "),
        (
            "terlar",
            "{env_name}{BOLD_GREEN}{user}{RESET}@{hostname}:"
            "{BOLD_GREEN}{cwd}{RESET}|{gitstatus}\n{BOLD_INTENSE_RED}@{RESET} ",
        ),
        (
            "default with git status",
            "{env_name}{BOLD_GREEN}{user}@{hostname}{BOLD_BLUE} {cwd}"
            "{branch_color}{gitstatus: {}}{RESET} {BOLD_BLUE}"
            "{prompt_end}{RESET} ",
        ),
        ("robbyrussell", "{BOLD_INTENSE_RED}➜ {CYAN}{cwd_base} {gitstatus}{RESET} "),
        ("just a conch", "@ "),
        (
            "simple pythonista",
            "{INTENSE_RED}{user}{RESET} at {INTENSE_PURPLE}{hostname}{RESET} "
            "in {BOLD_GREEN}{cwd}{RESET}\n@ ",
        ),
        (
            "informative",
            "[{localtime}] {YELLOW}{env_name} {BOLD_BLUE}{user}@{hostname} "
            "{BOLD_GREEN}{cwd} {gitstatus}{RESET}\n@ ",
        ),
        (
            "informative version control",
            "{YELLOW}{env_name} {BOLD_GREEN}{cwd} {gitstatus}{RESET} {prompt_end} ",
        ),
        ("classic", "{user}@{hostname} {BOLD_GREEN}{cwd}{RESET}@ "),
        (
            "classic with git status",
            "{gitstatus} {RESET}{user}@{hostname} {BOLD_GREEN}{cwd}{RESET} @ ",
        ),
        ("screen savvy", "{YELLOW}{user}@{PURPLE}{hostname}{BOLD_GREEN}{cwd}{RESET}@ "),
        (
            "sorin",
            "{CYAN}{cwd} {INTENSE_RED}@{INTENSE_YELLOW}@{INTENSE_GREEN}@{RESET} ",
        ),
        (
            "acidhub",
            "❰{INTENSE_GREEN}{user}{RESET}❙{YELLOW}{cwd}{RESET}{env_name}❱{gitstatus}@ ",
        ),
        (
            "nim",
            "{INTENSE_GREEN}┬─[{YELLOW}{user}{RESET}@{BLUE}{hostname}{RESET}:{cwd}"
            "{INTENSE_GREEN}]─[{localtime}]─[{RESET}G:{INTENSE_GREEN}{curr_branch}=]"
            "\n{INTENSE_GREEN}╰─>{INTENSE_RED}{prompt_end}{RESET} ",
        ),
    ]


def get_initial(env, prompt_format, fields):
    template = env.get_stringified("PROMPT")
    return {
        "value": template,
        "display": escape(html_format(prompt_format(template, fields=fields))),
    }


def _prompt_visual_width(rendered):
    """Max line width of a rendered prompt, excluding color tokens."""
    tokens = partial_color_tokenize(rendered)
    lines = "".join(s for _, s in tokens).split("\n")
    return max(len(line) for line in lines)


def render_prompts(env):
    prompt_format = PromptFormatter()
    fields = dict(env.get("PROMPT_FIELDS") or {})
    fields.update(
        cwd="~/snail/stuff",
        cwd_base="stuff",
        user="lou",
        hostname="carcolh",
        env_name=fields["env_prefix"] + "env" + fields["env_postfix"],
        curr_branch="branch",
        gitstatus="{CYAN}branch|{BOLD_BLUE}+2{RESET}⚑7",
        branch_color="{BOLD_INTENSE_RED}",
        localtime="15:56:07",
    )
    max_width = 0
    yield get_initial(env, prompt_format, fields)
    for name, template in get_named_prompts():
        rendered = prompt_format(template, fields=fields)
        max_width = max(max_width, _prompt_visual_width(rendered))
        display = html_format(rendered)
        yield (
            name,
            {
                "value": template,
                "display": escape(display),
            },
        )
    yield "__max_width__", max_width


def render_colors():
    source = (
        "import sys\n"
        'echo "Welcome $USER on" @(sys.platform)\n\n'
        "def func(x=42):\n"
        '    d = {"pygwin": True}\n'
        '    return d.get("pygwin") and you\n\n'
        "# This is a comment\n"
        "![env | uniq | sort | grep PATH]\n"
    )
    lexer = PygwinLexer()
    lexer.add_filter("tokenmerge")
    token_stream = list(pygments.lex(source, lexer=lexer))
    styles = sorted(get_all_styles())
    styles.insert(0, styles.pop(styles.index("default")))
    for style in styles:
        try:
            display = html_format(token_stream, style=style)
        except Exception as ex:
            logging.error(
                f"Failed to format Pygwin code {ex!r}. {style!r}", exc_info=True
            )
            display = source
        yield style, display


def format_pgtrib(pgtrib: Pgtrib):
    return {
        "url": pgtrib.url,
        "license": pgtrib.license,
        "display": escape(rst_to_html(pgtrib.get_description())),
    }


def render_pgtribs():
    md = get_pgtribs()
    for pgtrib_name, pgtrib in md.items():
        yield pgtrib_name, format_pgtrib(pgtrib)
