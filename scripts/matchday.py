"""Refresh the live parts of the profile README.

- MATCHDAY block: next gameweek's predictions from the Injury Time API
- JOKE block: one joke, rotated daily

Standard library only. If the API is down the MATCHDAY block is left as it was.
Optional: set the repository variable FPL_TEAM_ID to show your FPL rank too.
"""
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.request

API = os.environ.get("INJURY_TIME_API", "https://injury-time-api.onrender.com")
APP = "https://injury-time-frontend.vercel.app"
README = os.path.join(os.path.dirname(__file__), "..", "README.md")
FPL_TEAM_ID = os.environ.get("FPL_TEAM_ID", "").strip()

JOKES = [
    ("Why did the data scientist get a red card?", "Too many unforced errors in the validation set."),
    ("My model predicted a 1-1 draw nine times this gameweek.", "It's not wrong, it's just very Premier League."),
    ("Why do Python devs make good goalkeepers?", "They catch every exception."),
    ("Why did the FPL manager become a backend dev?", "Already used to everything breaking right before the deadline."),
    ("What's a footballer's favourite HTTP status?", "302: moved to another club."),
    ("Why was the API so calm after the derby?", "It had already handled the 500s."),
    ("I benched Haaland once.", "git blame still points at me."),
    ("Why don't defenders trust floating point?", "0.1 + 0.2 lets in a goal every time."),
    ("My code works and I don't know why.", "Same as my FPL captain picks."),
    ("How many ML engineers does it take to take a penalty?", "One. But first they need 10,000 labelled penalties."),
    ("What did the striker say to the merge conflict?", "Pass it to me, I'll finish it."),
    ("Why do ML engineers love penalty shootouts?", "Finally, a binary classification problem."),
    ("How do you calm an anxious backend?", "Give it a rest. Then a REST API."),
    ("Why did the junior dev bring a ball to stand-up?", "He heard the team was doing sprints."),
    ("My xG this season is 14.2.", "My actual goals are a 404."),
    ("Why did the referee use Flutter?", "One whistle, every platform."),
    ("What's the Dixon-Coles model's favourite chant?", "\"We're attacking, we're defending, we're time-decaying!\""),
    ("I asked the model who'll win the league.", "It said: 'please define \"win\" with a loss function'."),
]


def get(path, timeout=90):
    req = urllib.request.Request(API + path, headers={"User-Agent": "profile-readme-matchday"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def get_retry(path, tries=4):
    for i in range(tries):
        try:
            return get(path)
        except Exception as e:  # Render free tier sleeps; first calls can time out
            print(f"{path}: attempt {i + 1} failed: {e}", file=sys.stderr)
            time.sleep(20)
    raise RuntimeError(f"{path} unavailable")


def pct(p):
    return f"{round(p * 100)}%"


def kickoff(iso):
    t = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return t.strftime("%a %d %b · %H:%M")


def matchday_block():
    get_retry("/healthz")
    meta = get_retry("/api/meta")
    names = {t["short"]: t["name"] for t in meta["teams"]}
    fixtures = sorted(get_retry("/api/fixtures?horizon=1"), key=lambda f: f["kickoff"] or "")
    caps = get_retry("/api/picks?top=3")["captains"][:3]
    if not fixtures:
        raise RuntimeError("no fixtures")
    gw = fixtures[0]["gw"]

    rows = []
    for f in fixtures:
        h, d, a = f["p_home"], f["p_draw"], f["p_away"]
        best = max(h, d, a)
        cell = lambda p: f"**{pct(p)}**" if p == best else pct(p)
        rows.append(f"| {kickoff(f['kickoff'])} | {names.get(f['home'], f['home'])} vs {names.get(f['away'], f['away'])} "
                    f"| {cell(h)} | {cell(d)} | {cell(a)} | {f['xg_home']:.1f} – {f['xg_away']:.1f} |")

    fav = lambda f: (names.get(f["home"], f["home"]), f["p_home"]) if f["p_home"] >= f["p_away"] else (names.get(f["away"], f["away"]), f["p_away"])
    banker = max(fixtures, key=lambda f: fav(f)[1])
    flip = min(fixtures, key=lambda f: abs(f["p_home"] - f["p_away"]))
    draw = max(fixtures, key=lambda f: f["p_draw"])
    vs = lambda f: f"{names.get(f['home'], f['home'])} vs {names.get(f['away'], f['away'])}"

    lines = [
        f"**Gameweek {gw}.** The Dixon-Coles model's call for every match, refreshed every morning.",
        "",
        f"> 🔒 **Banker:** {fav(banker)[0]} ({pct(fav(banker)[1])}) &nbsp;·&nbsp; "
        f"🪙 **Coin flip:** {vs(flip)} &nbsp;·&nbsp; 🤝 **Draw magnet:** {vs(draw)} ({pct(draw['p_draw'])})",
        "",
        "| Kick-off (UTC) | Match | Home | Draw | Away | Expected goals |",
        "|:--|:--|:-:|:-:|:-:|:-:|",
        *rows,
        "",
        "<details>",
        "<summary><b>👑 Who should you captain?</b> &nbsp;(top 3 by expected FPL points)</summary>",
        "<br>",
        "",
        "| | Player | Club | Fixture | xPts |",
        "|:-:|:--|:--|:--|:-:|",
        *[f"| {['🥇', '🥈', '🥉'][i]} | **{c['name']}** | {names.get(c['team'], c['team'])} | {c['fixtures']} | {c['xpts']:.1f} |"
          for i, c in enumerate(caps)],
        "",
        "</details>",
    ]

    if FPL_TEAM_ID.isdigit():
        try:
            e = get_retry(f"/api/team/{FPL_TEAM_ID}", tries=2)["entry"]
            rank = f"{e['overall_rank']:,}" if e.get("overall_rank") else "n/a"
            lines += ["", "<details>",
                      f"<summary><b>📈 My own FPL season</b> ({e['name']})</summary>",
                      "<br>", "",
                      f"Overall rank **{rank}** with **{e['overall_points']}** points. "
                      "Yes, I use my own model. No, it doesn't always save me.",
                      "", "</details>"]
        except Exception as ex:
            print(f"FPL team lookup skipped: {ex}", file=sys.stderr)

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%d %b %Y, %H:%M UTC")
    lines += ["", f"<sub>Updated {stamp} by a GitHub Action calling the "
              f"[Injury Time]({APP}) API · probabilities are the model's, not betting advice.</sub>"]
    return "\n".join(lines)


def joke_block(today):
    q, a = JOKES[today.toordinal() % len(JOKES)]
    return "\n".join(["<details>", f"<summary><b>🤣 {q}</b> &nbsp;(click for the punchline)</summary>",
                      "<br>", "", f"**{a}**", "", f"<sub>New joke every day.</sub>", "", "</details>"])


def replace(src, tag, body):
    pat = re.compile(rf"(<!-- {tag}:START -->)(.*?)(<!-- {tag}:END -->)", re.S)
    if not pat.search(src):
        raise SystemExit(f"marker {tag} missing from README")
    return pat.sub(lambda m: f"{m.group(1)}\n{body}\n{m.group(3)}", src)


def main():
    with open(README, encoding="utf-8") as f:
        src = f.read()
    out = replace(src, "JOKE", joke_block(dt.date.today()))
    try:
        out = replace(out, "MATCHDAY", matchday_block())
    except Exception as e:
        print(f"matchday block kept as it was: {e}", file=sys.stderr)
    if out != src:
        with open(README, "w", encoding="utf-8", newline="\n") as f:
            f.write(out)
        print("README updated")
    else:
        print("no change")


if __name__ == "__main__":
    main()
