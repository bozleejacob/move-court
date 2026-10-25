import base64
from pathlib import Path

ROOT = Path(__file__).parent
ASSETS = ROOT / "assets"
TMP = ROOT / "_reveal_tmp"


def b64(name):
    data = (ASSETS / name).read_bytes()
    return "data:image/jpeg;base64," + base64.b64encode(data).decode()


IMG_START = b64("screenshot-start.jpg")
IMG_VERDICT = b64("screenshot-verdict.jpg")
IMG_SAFETY = b64("screenshot-safety-defense.jpg")
IMG_TOKENOMICS = b64("screenshot-tokenomics.jpg")

reveal_css = (TMP / "reveal.css").read_text(encoding="utf-8")
theme_css = (TMP / "theme.css").read_text(encoding="utf-8")
reveal_js = (TMP / "reveal.js").read_text(encoding="utf-8")

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Move Court -- Slides</title>
<style>
{reveal_css}
{theme_css}
.reveal h1, .reveal h2 {{ color: #f2a65a; }}
.reveal table {{ font-size: 0.65em; }}
.reveal table th, .reveal table td {{ border: 1px solid #555; padding: 4px 8px; }}
.reveal img {{ border: 3px solid #555; border-radius: 6px; }}
.reveal .small {{ font-size: 0.6em; }}
.reveal .agent-row {{ display:flex; gap:10px; justify-content:center; margin: 20px 0; flex-wrap: wrap; }}
.reveal .agent-pill {{ background:#2b3a67; color:white; padding:8px 14px; border-radius:20px; font-size:0.5em; }}
</style>
</head>
<body>
<div class="reveal">
<div class="slides">

<section>
  <h1>Move Court</h1>
  <h3>An AI agent panel decides where you should move after school</h3>
  <p class="small">Jake Bozlee &middot; MGT 409, Fall 2026</p>
</section>

<section>
  <h2>The problem</h2>
  <p>Every graduating senior faces one of the highest-stakes decisions of their
  life -- where to live -- with almost no practice, and pressure from parents,
  partners, and friends who want different things for them.</p>
  <p class="small">Who has it: every graduating student weighing multiple
  cities, job offers, or "stay near family vs. chase career" tradeoffs.</p>
</section>

<section>
  <h2>What's new</h2>
  <ul>
    <li>Niche / Livability: generic, unweighted category scores</li>
    <li>Teleport / Numbeo: raw data, no reasoning</li>
    <li>Generic chatbot: no structure, no dataset, no conflict detection</li>
  </ul>
  <p><strong>Move Court</strong> interviews you, surfaces conflicts with people
  in your life, and makes the outcome concrete with a Future You narrative.</p>
</section>

<section>
  <h2>How the agents work</h2>
  <div class="agent-row">
    <div class="agent-pill">Career</div>
    <div class="agent-pill">Cost of Living</div>
    <div class="agent-pill">Community</div>
    <div class="agent-pill">Family &amp; Friends</div>
    <div class="agent-pill">Climate</div>
  </div>
  <p class="small">&#8595; weighted aggregation (code, not LLM) &#8595;</p>
  <div class="agent-row">
    <div class="agent-pill">Conflict Agent</div>
    <div class="agent-pill">Future You Agent</div>
  </div>
  <p class="small">&#8595;</p>
  <div class="agent-row">
    <div class="agent-pill" style="background:#c0392b;">Verdict Agent</div>
  </div>
</section>

<section>
  <h2>Demo</h2>
  <img src="{IMG_START}" style="height:480px;">
</section>

<section>
  <h2>Demo: the verdict</h2>
  <img src="{IMG_VERDICT}" style="height:480px;">
</section>

<section>
  <h2>Cost to run</h2>
  <table>
    <tr><th>Metric</th><th>Value</th></tr>
    <tr><td>Calls per run</td><td>8</td></tr>
    <tr><td>Input / output tokens</td><td>7,533 / 6,419</td></tr>
    <tr><td>Cost per run (assumed pricing)</td><td>&asymp; $0.005</td></tr>
    <tr><td>At 10,000 users/month</td><td>&asymp; $100/month</td></tr>
  </table>
  <p class="small">Pricing assumed at GPT-4o-mini-class rates; course's gpt-6-luna
  proxy pricing not publicly exposed.</p>
</section>

<section>
  <h2>Safety: a real defense, shown working</h2>
  <p class="small">A prompt-injection test tripped the provider's own content
  filter and crashed the first version of the app. Every call is now wrapped
  to fail gracefully instead:</p>
  <img src="{IMG_SAFETY}" style="height:400px;">
</section>

<section>
  <h2>Impact (honest status)</h2>
  <p>Tested by the author on a real decision (software engineering, cost vs.
  family proximity). Independent user testing is the clear next step --
  not yet done given the project timeline.</p>
  <p class="small">Unaided process took ~30-45 min across 3 sites with no
  explicit conflict reconciliation. Move Court: under 3 minutes, names the
  conflict directly.</p>
</section>

<section>
  <h2>What's next</h2>
  <ul>
    <li>Get 2-3 real graduating seniors to run it on their actual decision</li>
    <li>Replace assumed pricing with real gpt-6-luna billing data</li>
    <li>Soften content-filter false positives with a retry step</li>
    <li>Let users save and compare multiple weight configurations</li>
  </ul>
</section>

</div>
</div>
<script>
{reveal_js}
</script>
<script>
  Reveal.initialize({{ hash: true }});
</script>
</body>
</html>
"""

out = ROOT / "slides.html"
out.write_text(html, encoding="utf-8")
print(f"Wrote {out} ({len(html):,} chars)")
