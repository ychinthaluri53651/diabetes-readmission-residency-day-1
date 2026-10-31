"""
Renders the notebook cells tagged "shot:<key>" to PNG images for the report.

Each image is drawn from the EXECUTED notebook (code exactly as it ran, plus its real
stdout), so a screenshot can never disagree with the notebook.  Layout follows a
notebook cell: an execution-count gutter, a light code panel with Python syntax colors,
and the printed output beneath.

Run after build_notebook.py:  python3 render_screenshots.py
"""

from pathlib import Path
import textwrap

import nbformat
from PIL import Image, ImageDraw, ImageFont
from pygments import lex
from pygments.lexers import PythonLexer
from pygments.token import Comment, Keyword, Name, Number, Operator, String, Token

HERE = Path(__file__).resolve().parent
NB_PATH = HERE / "Diabetes_Readmission_D1_Chinthaluri.ipynb"
OUT = HERE / "figures"

FONT_PATH = "/System/Library/Fonts/Menlo.ttc"
SIZE, LINE_H = 22, 31                     # px; rendered at 2x for print sharpness
GUTTER, PAD = 92, 22
WRAP = 96                                 # characters per output line
# Width is fitted to the longest line, so the image fills the page at the largest
# legible type size (about 7.5 pt for a 92-character line at 6.5 in).

# Light notebook palette (close to Colab's default light theme).
COLORS = [
    (Comment, "#008000"), (String, "#A31515"), (Number, "#098658"),
    (Keyword, "#AF00DB"), (Name.Builtin, "#267F99"), (Name.Function, "#795E26"),
    (Name.Class, "#267F99"), (Name.Decorator, "#795E26"), (Operator, "#333333"),
]
DEFAULT, CODE_BG, BORDER, OUT_FG, GUTTER_FG = "#1F1F1F", "#F7F7F7", "#E0E0E0", "#212121", "#7A7A7A"


def color_for(tok):
    for ttype, col in COLORS:
        if tok in ttype:
            return col
    return DEFAULT


def code_lines(src):
    """Split source into lines of (text, color) runs."""
    lines, cur = [], []
    for tok, val in lex(src, PythonLexer()):
        parts = val.split("\n")
        for i, part in enumerate(parts):
            if part:
                cur.append((part, color_for(tok)))
            if i < len(parts) - 1:
                lines.append(cur); cur = []
    if cur:
        lines.append(cur)
    while lines and not lines[-1]:
        lines.pop()
    return lines


def output_text(cell):
    chunks = []
    for o in cell.get("outputs", []):
        if o.output_type == "stream" and o.name == "stdout":
            chunks.append(o.text)
        elif o.output_type == "execute_result" and "text/plain" in o.data:
            chunks.append(o.data["text/plain"])
    lines = []
    for ln in "".join(chunks).rstrip("\n").split("\n"):
        lines += textwrap.wrap(ln, WRAP, replace_whitespace=False, drop_whitespace=False) or [""]
    return lines


def render(cell, path):
    font = ImageFont.truetype(FONT_PATH, SIZE)
    code = code_lines(cell.source)
    out = output_text(cell)
    code_h = PAD * 2 + LINE_H * len(code)
    out_h = (PAD * 2 + LINE_H * len(out)) if out else 0
    longest = max([sum(font.getlength(t) for t, _ in runs) for runs in code] +
                  [font.getlength(ln) for ln in out])
    WIDTH = int(GUTTER + 2 * PAD + longest + 12)
    img = Image.new("RGB", (WIDTH, code_h + out_h + 8), "white")
    d = ImageDraw.Draw(img)

    # code panel
    d.rectangle([GUTTER, 4, WIDTH - 6, 4 + code_h], fill=CODE_BG, outline=BORDER, width=2)
    d.text((10, 4 + PAD), f"[{cell.execution_count}]", font=font, fill=GUTTER_FG)
    y = 4 + PAD
    for runs in code:
        x = GUTTER + PAD
        for text, col in runs:
            d.text((x, y), text, font=font, fill=col)
            x += font.getlength(text)
        y += LINE_H

    # output panel
    if out:
        y = 4 + code_h + PAD
        d.line([GUTTER, 4 + code_h + 6, WIDTH - 6, 4 + code_h + 6], fill=BORDER, width=1)
        for ln in out:
            d.text((GUTTER + PAD, y), ln, font=font, fill=OUT_FG)
            y += LINE_H
    img.save(path, dpi=(250, 250))


def main():
    nb = nbformat.read(NB_PATH, as_version=4)
    n = 0
    for cell in nb.cells:
        for tag in cell.metadata.get("tags", []):
            if tag.startswith("shot:"):
                key = tag.split(":", 1)[1]
                render(cell, OUT / f"shot_{key}.png")
                n += 1
                print(f"rendered shot_{key}.png (cell [{cell.execution_count}])")
    if not n:
        raise SystemExit("no tagged cells found; run build_notebook.py first")


if __name__ == "__main__":
    main()
