"""Rotate the joke of the day in the profile README. Standard library only."""
import datetime as dt
import os
import re

README = os.path.join(os.path.dirname(__file__), "..", "README.md")

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
    if out != src:
        with open(README, "w", encoding="utf-8", newline="\n") as f:
            f.write(out)
        print("README updated")
    else:
        print("no change")


if __name__ == "__main__":
    main()
