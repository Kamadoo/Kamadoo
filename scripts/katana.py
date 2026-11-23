"""Gera o gráfico de contribuições com uma katana em chamas cortando os dias.

Uso: GITHUB_TOKEN=... python scripts/katana.py <usuario> <pasta_de_saida>
Gera katana-dark.svg e katana-light.svg. Só usa a biblioteca padrão.
"""
import json
import os
import random
import sys
import urllib.request
from pathlib import Path

QUERY = """query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{
totalContributions weeks{contributionDays{date contributionCount contributionLevel}}}}}}"""
LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}

THEMES = {
    "dark": dict(bg="#17110e", text="#fbeee0", muted="#a8917f", cells=["#241a15", "#1f4a37", "#2f6b4f", "#3d8a63", "#56b081"]),
    "light": dict(bg="#fff8f1", text="#2a1b13", muted="#8a6f5c", cells=["#efe3d5", "#bfdccb", "#86bc9c", "#4f9a72", "#2f6b4f"]),
}
EMBER, HOT, DEEP, WHITE = "#fb923c", "#fbbf24", "#c2410c", "#fff7d6"

# katana na vertical, com lâmina longa para cobrir as 7 linhas do gráfico
KATANA = ["....kkk....", "....hgh....", "....ghg....", "....hgh....", "....ghg....", "....hgh....",
          "....ghg....", "..ttttttt..", ".tTTTTTTTt.", "..ttttttt..", "....aaa...."] + ["....dse...."] * 25 + [".....se...."]
KCOL = {"k": "#3a2a20", "h": "#141414", "g": "#2f6b4f", "t": "#5b4a2a", "T": "#b8862b",
        "a": "#d4a640", "d": "#7d8794", "s": "#c9d1db", "e": "#f4f7fa"}
FLAME_A = ["..r..", ".ro.r", "royor", "oywyo", ".ooo."]
FLAME_B = ["...r.", "r.or.", "royor", "oyyyo", ".ooo."]


def fetch(login, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": "katana-contrib"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        cal = json.load(r)["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = [[LEVELS[d["contributionLevel"]] for d in w["contributionDays"]] for w in cal["weeks"]]
    return weeks, cal["totalContributions"]


def pixels(grid, x0, y0, s, colors):
    return "".join(f'<rect x="{x0 + c * s:.1f}" y="{y0 + r * s:.1f}" width="{s}" height="{s}" fill="{colors[ch]}"/>'
                   for r, row in enumerate(grid) for c, ch in enumerate(row) if ch in colors)


def render(weeks, total, t):
    cell, gap = 11, 3
    step = cell + gap
    gx, gy = 44, 52
    W = gx * 2 + len(weeks) * step - gap
    H = gy + 7 * step + 34
    T = 14.0           # duração do ciclo
    travel = 0.62      # fração do ciclo em que a katana atravessa
    kpx = 3.5
    kw = 11 * kpx
    start, end = -kw - 10, W + 10

    def t_at(x):  # segundo em que a lâmina passa pelo x
        return T * travel * (x + kw / 2 - start - kw / 2) / (end - start)

    css = [f"""
      text{{font-family:'Segoe UI','Helvetica Neue',Arial,sans-serif}}
      .k{{animation:sweep {T}s linear infinite}}
      @keyframes sweep{{0%{{transform:translateX({start}px);opacity:1}}{travel * 100:.1f}%{{transform:translateX({end}px);opacity:1}}{travel * 100 + .1:.1f}%,100%{{transform:translateX({end}px);opacity:0}}}}
      .fa{{animation:fa .4s steps(1) infinite}}.fb{{animation:fb .4s steps(1) infinite}}
      @keyframes fa{{0%{{opacity:1}}50%{{opacity:0}}}}@keyframes fb{{0%{{opacity:0}}50%{{opacity:1}}}}
      .spark{{opacity:0;animation:spark {T}s ease-out infinite}}
      @keyframes spark{{0%{{opacity:1;transform:translate(0,0)}}10%{{opacity:.9}}22%{{opacity:0;transform:translate(var(--dx),-46px)}}100%{{opacity:0}}}}
    """]
    for lvl in range(5):
        base = t["cells"][lvl]
        if lvl == 0:
            css.append(f"@keyframes b0{{0%{{fill:{EMBER};fill-opacity:.35}}4%,100%{{fill:{base};fill-opacity:1}}}}")
        else:
            css.append(f"@keyframes b{lvl}{{0%{{fill:{WHITE}}}4%{{fill:{HOT}}}10%{{fill:{EMBER}}}22%{{fill:{DEEP}}}"
                       f"45%{{fill:#7c2d12}}80%,100%{{fill:{base}}}}}")
        css.append(f".c{lvl}{{animation:b{lvl} {T}s linear infinite}}")

    rnd = random.Random(42)
    cells, sparks = [], []
    for wi, week in enumerate(weeks):
        x = gx + wi * step
        delay = t_at(x)
        for di, lvl in enumerate(week):
            y = gy + di * step
            cells.append(f'<rect class="c{lvl}" style="animation-delay:{delay:.2f}s" x="{x}" y="{y}" width="{cell}" '
                         f'height="{cell}" rx="2" fill="{t["cells"][lvl]}"/>')
            if lvl >= 2 and rnd.random() < 0.35 * lvl / 4 + 0.1:
                sparks.append(f'<circle class="spark" style="--dx:{rnd.uniform(-10, 10):.0f}px;animation-delay:{delay + rnd.uniform(0, .3):.2f}s" '
                              f'cx="{x + cell / 2 + rnd.uniform(-3, 3):.1f}" cy="{y:.1f}" r="{rnd.uniform(1, 2.2):.1f}" '
                              f'fill="{HOT if rnd.random() < .5 else EMBER}"/>')

    ky = gy - 11 * kpx - 2
    fcol = {"r": DEEP, "o": EMBER, "y": HOT, "w": WHITE}
    fx = 11 * kpx / 2 - 2.5 * 4
    flames = (f'<g class="fa">{pixels(FLAME_A, fx, gy + 7 * step - 14, 4, fcol)}</g>'
              f'<g class="fb">{pixels(FLAME_B, fx, gy + 7 * step - 14, 4, fcol)}</g>')
    katana = f'<g class="k">{pixels(KATANA, 0, ky, kpx, KCOL)}{flames}</g>'

    label = f"{total} contribuições no último ano"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{label}">
  <title>{label}</title>
  <style>{''.join(css)}</style>
  <rect width="{W}" height="{H}" rx="12" fill="{t['bg']}"/>
  {''.join(cells)}
  {''.join(sparks)}
  {katana}
  <text x="{gx}" y="{H - 12}" font-size="12" fill="{t['muted']}">{label}</text>
  <text x="{W - gx}" y="{H - 12}" font-size="12" fill="{t['muted']}" text-anchor="end">全集中</text>
</svg>
"""


def main():
    login, out = sys.argv[1], Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    weeks, total = fetch(login, os.environ["GITHUB_TOKEN"])
    for name, theme in THEMES.items():
        (out / f"katana-{name}.svg").write_text(render(weeks, total, theme), encoding="utf-8")
    print(f"ok: {len(weeks)} semanas, {total} contribuições")


if __name__ == "__main__":
    main()
