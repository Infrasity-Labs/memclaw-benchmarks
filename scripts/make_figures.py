"""Generate the README figures as SVG, one light and one dark variant each.

GitHub strips CSS from markdown and renders its mermaid blocks in a default
blue with zoom chrome and colliding axis labels, so the figures are committed
images instead and paired through <picture> for theme.

Every number is declared once, at the top, and the drawing code derives bar
geometry from it. A figure therefore cannot drift away from the data: change
a count here and the bars, the labels and the axis all move together.

Run: python scripts/make_figures.py
"""
import os

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

# --- the data ---------------------------------------------------------------
TOTAL_SUBTASKS = 440

TIERS = [
    # label,             caura, mem0, none,  p-value text
    ("gpt-4.1",            115, None,   82, "p = 0.00007"),
    ("gemini-3.6-flash",   166,  131,  115, "p = 1.4e-08"),
    ("gpt-5.6-sol",        182, None,  150, "p = 0.001"),
]

# Advantage in percentage points, pooled and domain-stratified.
EFFECT = [("gpt-4.1", 7.50), ("gemini-3.6-flash", 11.59), ("gpt-5.6-sol", 7.27)]

# --- palette, both validated by the dataviz colour checks --------------------
THEMES = {
    "light": dict(bg="#FAF9F7", panel="#FFFFFF", edge="#E1DFD8", ink="#141E1C",
                  ink2="#3D4A47", muted="#66756F", grid="#EBE9E2",
                  caura="#0D8C77", mem0="#5757C9", none="#A96420"),
    "dark": dict(bg="#0E1316", panel="#161E22", edge="#243136", ink="#E6EEEF",
                 ink2="#C0CFD1", muted="#8CA0A6", grid="#1E282C",
                 caura="#33A492", mem0="#8B8AD6", none="#C4853F"),
}

MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def header(w, h, t):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img">'
            f'<rect width="{w}" height="{h}" fill="{t["bg"]}"/>')


# --- figure 1: headline strip -----------------------------------------------
def headline(t):
    """Left-aligned tier columns split by hairlines. Deliberately not a
    centered card with oversized numerals: this reads as a results strip in a
    report, which is what it is."""
    w, h = 900, 186
    p = [header(w, h, t)]
    p.append(f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" fill="{t["panel"]}" '
             f'stroke="{t["edge"]}" rx="6"/>')
    p.append(f'<text x="34" y="38" font-family="{MONO}" font-size="11" font-weight="600" '
             f'letter-spacing="1.7" fill="{t["muted"]}">SUBTASKS SOLVED VS NO MEMORY, BOTH DOMAINS POOLED</text>')
    p.append(f'<line x1="34" y1="54" x2="{w-34}" y2="54" stroke="{t["edge"]}"/>')

    colw = (w - 68) / 3
    for i, (label, caura, _m, none, pv) in enumerate(TIERS):
        x = 34 + i * colw
        lift = round((caura - none) / none * 100)
        if i:
            p.append(f'<line x1="{x-1:.0f}" y1="72" x2="{x-1:.0f}" y2="158" stroke="{t["edge"]}"/>')
        p.append(f'<text x="{x+22:.0f}" y="118" font-family="{MONO}" font-size="44" '
                 f'font-weight="600" fill="{t["caura"]}">+{lift}%</text>')
        p.append(f'<text x="{x+22:.0f}" y="140" font-family="{MONO}" font-size="12.5" '
                 f'fill="{t["ink2"]}">{esc(label)}</text>')
        p.append(f'<text x="{x+22:.0f}" y="158" font-family="{MONO}" font-size="11" '
                 f'fill="{t["muted"]}">{caura} vs {none} of {TOTAL_SUBTASKS} &#183; {pv}</text>')
    p.append("</svg>")
    return "".join(p)


# --- figure 2: pooled subtasks solved ---------------------------------------
def pooled(t):
    """Grouped horizontal bars with a real zeroed axis. Horizontal because the
    category labels are long model names, which collide when set vertically:
    that collision is exactly what the mermaid version did."""
    rows = []
    for label, caura, mem0, none, _pv in TIERS:
        rows.append(("group", label))
        rows.append(("Caura", caura, t["caura"]))
        if mem0 is not None:
            rows.append(("mem0", mem0, t["mem0"]))
        rows.append(("No memory", none, t["none"]))

    x0, barw = 190, 560
    axis_max = 200
    top = 74
    row_h, group_h = 30, 34
    h = top + sum(group_h if r[0] == "group" else row_h for r in rows) + 52
    w = 900

    p = [header(w, h, t)]
    p.append(f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" fill="{t["panel"]}" '
             f'stroke="{t["edge"]}" rx="6"/>')
    p.append(f'<text x="34" y="34" font-family="{SANS}" font-size="15" font-weight="600" '
             f'fill="{t["ink"]}">Subtasks solved, both reasoning domains pooled</text>')
    p.append(f'<text x="34" y="54" font-family="{SANS}" font-size="12.5" '
             f'fill="{t["muted"]}">60 papers and {TOTAL_SUBTASKS} scored subtasks per arm. '
             f'Paired: every arm ran the same papers.</text>')

    y = top
    bottom = top
    for r in rows:
        bottom += group_h if r[0] == "group" else row_h

    # gridlines behind the bars
    for gv in range(0, axis_max + 1, 50):
        gx = x0 + barw * gv / axis_max
        p.append(f'<line x1="{gx:.1f}" y1="{top-6}" x2="{gx:.1f}" y2="{bottom}" '
                 f'stroke="{t["grid"]}"/>')
        p.append(f'<text x="{gx:.1f}" y="{bottom+20}" font-family="{MONO}" font-size="10.5" '
                 f'fill="{t["muted"]}" text-anchor="middle">{gv}</text>')

    for r in rows:
        if r[0] == "group":
            y += group_h
            p.append(f'<text x="{x0}" y="{y-11}" font-family="{MONO}" font-size="10.5" '
                     f'font-weight="600" letter-spacing="1.2" fill="{t["muted"]}">'
                     f'{esc(r[1]).upper()}</text>')
            continue
        name, val, colour = r
        bw = barw * val / axis_max
        cy = y + row_h / 2
        weight = "600" if name == "Caura" else "400"
        fill = t["ink"] if name == "Caura" else t["ink2"]
        p.append(f'<text x="{x0-14}" y="{cy+4:.1f}" font-family="{MONO}" font-size="12" '
                 f'font-weight="{weight}" fill="{fill}" text-anchor="end">{esc(name)}</text>')
        p.append(f'<rect x="{x0}" y="{cy-9:.1f}" width="{bw:.1f}" height="18" rx="2" fill="{colour}"/>')
        p.append(f'<text x="{x0+bw+11:.1f}" y="{cy+4:.1f}" font-family="{MONO}" font-size="12" '
                 f'font-weight="{weight}" fill="{fill}">{val}</text>')
        y += row_h

    p.append(f'<line x1="{x0}" y1="{top-6}" x2="{x0}" y2="{bottom}" stroke="{t["edge"]}"/>')
    p.append(f'<text x="{x0+barw/2:.0f}" y="{h-14}" font-family="{SANS}" font-size="11.5" '
             f'fill="{t["muted"]}" text-anchor="middle">Subtasks solved</text>')
    p.append("</svg>")
    return "".join(p)


# --- figure 3: effect size ---------------------------------------------------
def effect(t):
    x0, barw, axis_max = 190, 560, 12.0
    top, row_h = 74, 38
    h = top + len(EFFECT) * row_h + 52
    w = 900
    p = [header(w, h, t)]
    p.append(f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" fill="{t["panel"]}" '
             f'stroke="{t["edge"]}" rx="6"/>')
    p.append(f'<text x="34" y="34" font-family="{SANS}" font-size="15" font-weight="600" '
             f'fill="{t["ink"]}">Caura advantage over no memory</text>')
    p.append(f'<text x="34" y="54" font-family="{SANS}" font-size="12.5" fill="{t["muted"]}">'
             f'Within-tier paired gaps, so judge and temperature differences between tiers cancel out.</text>')

    bottom = top + len(EFFECT) * row_h
    for gv in range(0, int(axis_max) + 1, 3):
        gx = x0 + barw * gv / axis_max
        p.append(f'<line x1="{gx:.1f}" y1="{top-6}" x2="{gx:.1f}" y2="{bottom}" stroke="{t["grid"]}"/>')
        p.append(f'<text x="{gx:.1f}" y="{bottom+20}" font-family="{MONO}" font-size="10.5" '
                 f'fill="{t["muted"]}" text-anchor="middle">{gv}</text>')

    for i, (label, pp) in enumerate(EFFECT):
        cy = top + i * row_h + row_h / 2
        bw = barw * pp / axis_max
        p.append(f'<text x="{x0-14}" y="{cy+4:.1f}" font-family="{MONO}" font-size="12" '
                 f'fill="{t["ink"]}" text-anchor="end">{esc(label)}</text>')
        p.append(f'<rect x="{x0}" y="{cy-9:.1f}" width="{bw:.1f}" height="18" rx="2" fill="{t["caura"]}"/>')
        p.append(f'<text x="{x0+bw+11:.1f}" y="{cy+4:.1f}" font-family="{MONO}" font-size="12" '
                 f'font-weight="600" fill="{t["ink"]}">+{pp:.2f}pp</text>')

    p.append(f'<line x1="{x0}" y1="{top-6}" x2="{x0}" y2="{bottom}" stroke="{t["edge"]}"/>')
    p.append(f'<text x="{x0+barw/2:.0f}" y="{h-14}" font-family="{SANS}" font-size="11.5" '
             f'fill="{t["muted"]}" text-anchor="middle">Percentage points</text>')
    p.append("</svg>")
    return "".join(p)


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, fn in (("headline", headline), ("pooled", pooled), ("effect", effect)):
        for theme, tokens in THEMES.items():
            path = os.path.join(OUT, f"fig-{name}-{theme}.svg")
            with open(path, "w", encoding="utf-8") as f:
                f.write(fn(tokens))
            print("wrote", os.path.relpath(path, os.path.dirname(OUT)))


if __name__ == "__main__":
    main()
