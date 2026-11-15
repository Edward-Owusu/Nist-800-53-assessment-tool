"""Shared look for the open-source GRC tool series by Edward Owusu.

Every tool in the series uses this file for its header band, controls, tiles, cards and footer, so
they read as one family. Each tool keeps its own colour palette and its own page layout.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from html import escape

import streamlit as st

SERIES_URL = "https://edward-owusu.github.io"
SEV_COLORS = {"critical": "#B42318", "high": "#C2410C", "medium": "#A16207", "low": "#64748B"}


@dataclass(frozen=True)
class Palette:
    accent: str          # main colour of the tool
    band: str            # header band background
    band_text: str       # header band title colour
    band_sub: str        # header band body text colour
    card: str            # card and tile background
    line: str            # borders
    ink: str             # main text on cards
    muted: str           # secondary text


CSS = """
<style>
[data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none; }
.block-container { padding-top: 3.4rem; max-width: 1280px; }
.g-band { background: @BAND@; border-radius: 16px; padding: 22px 28px 18px; margin-bottom: 16px;
  border-left: 8px solid @ACCENT@; }
.g-band .k { font: 700 12px/1.2 Arial, sans-serif; letter-spacing: .16em; text-transform: uppercase; color: @ACCENT@; }
.g-band h1 { font-family: Georgia, 'Times New Roman', serif; font-size: 32px; font-weight: 600; color: @BANDTEXT@;
  margin: 6px 0 4px; padding: 0; line-height: 1.15; }
.g-band p { margin: 0; color: @BANDSUB@; font-size: 15px; max-width: 980px; }
.g-tile { background: @CARD@; border: 1px solid @LINE@; border-radius: 12px; padding: 14px 16px; min-height: 86px;
  border-top: 4px solid @TOP@; }
.g-tile b { display: block; font-size: 28px; line-height: 1.15; color: @INK@; }
.g-tile span { color: @MUTED@; font-size: 13px; }
.g-card { background: @CARD@; border: 1px solid @LINE@; border-left: 5px solid @ACCENT@; border-radius: 10px;
  padding: 12px 14px; margin: 0 0 10px; color: @INK@; }
.g-card .h { font-weight: 650; font-size: 15px; color: @INK@; }
.g-card .s { color: @MUTED@; font-size: 13px; }
.g-card .d { font-size: 14px; margin: 4px 0; color: @INK@; }
.g-card .f { font-size: 13.5px; color: @ACCENT@; }
.g-pill { display: inline-block; padding: 1px 9px; border-radius: 999px; color: #fff; font-size: 11.5px;
  font-weight: 650; margin-right: 5px; text-transform: capitalize; vertical-align: middle; }
.g-bar { height: 8px; background: @LINE@; border-radius: 6px; overflow: hidden; margin: 8px 0 4px; }
.g-bar i { display: block; height: 100%; }
.g-sec { font-family: Georgia, serif; font-size: 21px; font-weight: 600; color: @INK@; margin: 18px 0 6px; }
.g-foot { color: @MUTED@; font-size: 12.5px; margin-top: 28px; border-top: 1px solid @LINE@; padding-top: 10px; }
.g-foot a { color: @ACCENT@; }
.g-empty { color: @MUTED@; font-size: 13px; padding: 8px 2px; }
</style>
"""


def setup(title: str, kicker: str, tagline: str, icon: str, pal: Palette) -> None:
    """Page config, shared styles and the header band. Call once, first."""
    st.set_page_config(page_title=title, page_icon=icon, layout="wide", initial_sidebar_state="collapsed")
    css = CSS
    for token, value in {"@BAND@": pal.band, "@ACCENT@": pal.accent, "@BANDTEXT@": pal.band_text,
                         "@BANDSUB@": pal.band_sub, "@CARD@": pal.card, "@LINE@": pal.line, "@INK@": pal.ink,
                         "@MUTED@": pal.muted, "@TOP@": pal.accent}.items():
        css = css.replace(token, value)
    st.markdown(css, unsafe_allow_html=True)
    st.markdown(f"<div class='g-band'><div class='k'>{escape(kicker)}</div><h1>{escape(title)}</h1>"
                f"<p>{escape(tagline)}</p></div>", unsafe_allow_html=True)


def choose(label: str, options: list, key: str, default=None, format_func=str):
    """Segmented buttons on Streamlit 1.40+, a horizontal radio on older versions."""
    options = list(options)
    default = options[0] if default is None or default not in options else default
    if hasattr(st, "segmented_control"):
        picked = st.segmented_control(label, options, default=default, key=key, format_func=format_func,
                                      label_visibility="collapsed")
        return default if picked is None else picked
    return st.radio(label, options, index=options.index(default), key=key, horizontal=True,
                    format_func=format_func, label_visibility="collapsed")


def multi(label: str, options: list, key: str, format_func=str) -> list:
    """Toggle chips (all on by default) on Streamlit 1.40+, a multiselect otherwise."""
    options = list(options)
    if not options:
        return []
    if hasattr(st, "pills"):
        picked = st.pills(label, options, selection_mode="multi", default=options, key=key,
                          format_func=format_func, label_visibility="collapsed")
        return list(picked or [])
    return st.multiselect(label, options, default=options, key=key, format_func=format_func,
                          label_visibility="collapsed")


def pill(text: str, color: str) -> str:
    return f"<span class='g-pill' style='background:{color}'>{escape(str(text))}</span>"


def sev_pill(severity: str) -> str:
    return pill(severity, SEV_COLORS.get(severity.lower(), "#64748B"))


def tiles(items: list[tuple], pal: Palette) -> None:
    """A row of number tiles: (value, label) or (value, label, top colour)."""
    cols = st.columns(len(items))
    for col, item in zip(cols, items):
        value, label = item[0], item[1]
        top = item[2] if len(item) > 2 else pal.accent
        col.markdown(f"<div class='g-tile' style='border-top-color:{top}'><b>{escape(str(value))}</b>"
                     f"<span>{escape(str(label))}</span></div>", unsafe_allow_html=True)


def bar(pct: float | None, color: str) -> str:
    width = 0 if pct is None else max(0.0, min(100.0, float(pct)))
    return f"<div class='g-bar'><i style='width:{width:.0f}%;background:{color}'></i></div>"


def card(head: str, body: str = "", accent: str | None = None) -> None:
    """A bordered card. `head` and `body` are trusted HTML built by the caller (escape user text first)."""
    style = f" style='border-left-color:{accent}'" if accent else ""
    st.markdown(f"<div class='g-card'{style}>{head}{body}</div>", unsafe_allow_html=True)


def section(title: str, caption: str | None = None) -> None:
    st.markdown(f"<div class='g-sec'>{escape(title)}</div>", unsafe_allow_html=True)
    if caption:
        st.caption(caption)


def gauge(score: float, label: str, color: str, pal: Palette, higher_is_better: bool = True,
          caption: str = "") -> str:
    """Half-circle gauge, 0 to 100. Returns SVG."""
    score = max(0.0, min(100.0, float(score)))
    angle = math.pi * (1 - score / 100)
    x, y = 100 + 80 * math.cos(angle), 100 - 80 * math.sin(angle)
    note = f"<text x='100' y='138' text-anchor='middle' font-size='11' fill='{pal.muted}' " \
           f"font-family='Arial'>{escape(caption)}</text>" if caption else ""
    return (f"<svg viewBox='0 0 200 {145 if caption else 124}' width='100%' style='max-width:280px'>"
            f"<path d='M20 100 A80 80 0 0 1 180 100' fill='none' stroke='{pal.line}' stroke-width='16' "
            f"stroke-linecap='round'/>"
            f"<path d='M20 100 A80 80 0 0 1 {x:.1f} {y:.1f}' fill='none' stroke='{color}' stroke-width='16' "
            f"stroke-linecap='round'/>"
            f"<text x='100' y='92' text-anchor='middle' font-size='34' font-weight='700' fill='{pal.ink}' "
            f"font-family='Georgia, serif'>{score:.0f}</text>"
            f"<text x='100' y='117' text-anchor='middle' font-size='13' font-weight='700' fill='{color}' "
            f"font-family='Arial'>{escape(label)}</text>{note}</svg>")


def downloads(files: list[tuple[str, str, str, str]]) -> None:
    """files: (label, data, file name, mime type)."""
    section("Download the report")
    cols = st.columns(len(files))
    for col, (label, data, name, mime) in zip(cols, files):
        col.download_button(label, data, name, mime, use_container_width=True)


def footer(tool: str, version: str, repo: str, disclaimer: str = "") -> None:
    st.markdown(
        f"<div class='g-foot'>{escape(tool)} {escape(version)} · Edward Owusu, CISA · "
        f"<a href='https://github.com/Edward-Owusu/{repo}'>Source on GitHub</a> · "
        f"Part of a series of <a href='{SERIES_URL}'>free, open-source GRC tools</a>. "
        f"Data you enter is processed in memory for this session and not saved."
        f"{'<br>' + escape(disclaimer) if disclaimer else ''}</div>", unsafe_allow_html=True)


def source_label(option: str) -> str:
    """Short button text for the data-source choice, so all three options fit on one line."""
    if option.startswith("Use a sample"):
        return "Sample"
    if option.startswith("Fill in"):
        return "Form"
    return "Upload"
