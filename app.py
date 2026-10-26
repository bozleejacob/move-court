import re

import streamlit as st

from agents import (
    SPECIALISTS,
    aggregate_scores,
    conflict_check,
    future_you_narrative,
    score_dimension,
    verdict,
)
from client import UsageTracker

st.set_page_config(page_title="Move Court", page_icon="\U0001F3DB️", layout="wide")

EMOJI = {
    "career": "\U0001F4BC",
    "cost": "\U0001F4B0",
    "community": "\U0001F389",
    "family": "❤️",
    "climate": "☀️",
    "conflict": "\U0001F575️",
    "future_you": "\U0001F52E",
    "verdict": "⚖️",
}

META_AGENTS = [
    {"key": "conflict", "name": "Conflict Agent"},
    {"key": "future_you", "name": "Future You Agent"},
    {"key": "verdict", "name": "Verdict Agent"},
]
ALL_AGENTS = SPECIALISTS + META_AGENTS

st.markdown(
    """
<style>
@keyframes popin { 0% {transform: scale(0.9); opacity: 0;} 100% {transform: scale(1); opacity: 1;} }
@keyframes pulse { 0% {opacity: 1;} 50% {opacity: 0.45;} 100% {opacity: 1;} }
.mc-hero {
    background: linear-gradient(135deg, #2b3a67 0%, #6a3093 50%, #c0392b 100%);
    padding: 28px 28px 22px; border-radius: 18px; color: white; margin-bottom: 18px;
    animation: popin 0.4s ease-out;
}
.mc-hero-title { font-size: 2.2em; font-weight: 800; color: white; }
.mc-hero-sub { margin: 6px 0 0; opacity: 0.9; color: white; }
.mc-steps { display: flex; gap: 6px; margin-bottom: 18px; }
.mc-step { flex: 1; text-align: center; padding: 8px 4px; border-radius: 10px; font-size: 0.85em;
    background: #eee; color: #888; font-weight: 600; }
.mc-step.active { background: #2b3a67; color: white; transform: scale(1.05); }
.mc-step.done { background: #27ae60; color: white; }
.mc-bubble { background: #f3f0ff; border: 2px solid #6a3093; border-radius: 16px 16px 16px 4px;
    padding: 18px 20px; margin: 10px 0 16px; animation: popin 0.3s ease-out; }
.mc-bubble .who { font-weight: 700; color: #6a3093; margin-bottom: 4px; }
.mc-verdict { background: linear-gradient(135deg, #fdf6e3, #fff); border: 3px solid #c0392b;
    border-radius: 16px; padding: 20px 24px; margin: 10px 0 22px; animation: popin 0.4s ease-out; }
.mc-verdict-title { font-size: 1.5em; font-weight: 800; color: #c0392b; margin-bottom: 8px; }
.mc-city-card { border-radius: 14px; padding: 14px 18px; margin: 10px 0; color: white;
    animation: popin 0.3s ease-out; }
.mc-chip { display: inline-block; background: rgba(255,255,255,0.25); border-radius: 20px;
    padding: 3px 10px; margin: 2px 4px 2px 0; font-size: 0.82em; }
.mc-rank { font-size: 1.6em; font-weight: 800; margin-right: 8px; }

.mc-agent-card { border-radius: 12px; padding: 10px 12px; margin-bottom: 8px; border: 2px solid;
    font-size: 0.85em; transition: all 0.2s ease; }
.mc-agent-card.idle { border-color: #ddd; background: #fafafa; color: #999; }
.mc-agent-card.thinking { border-color: #e2a93a; background: #fff8ec; color: #7a5a1a;
    animation: pulse 1.2s ease-in-out infinite; }
.mc-agent-card.done { border-color: #27ae60; background: #f1fbf4; color: #1e5c34; }
.mc-agent-name { font-weight: 700; margin-bottom: 2px; }
.mc-agent-thought { font-size: 0.92em; line-height: 1.3; }
</style>
""",
    unsafe_allow_html=True,
)

if "step" not in st.session_state:
    st.session_state.step = 0
    st.session_state.answers = {}
    st.session_state.weights = {}
    st.session_state.dim_scores = {}
    st.session_state.result = None
    st.session_state.tracker = UsageTracker()
    st.session_state.agent_status = {a["key"]: "idle" for a in ALL_AGENTS}
    st.session_state.agent_thought = {a["key"]: "" for a in ALL_AGENTS}

total_steps = len(SPECIALISTS)


def to_html(text):
    """Minimal markdown->HTML so LLM text displays correctly inside raw HTML blocks
    (Streamlit's markdown parser does not process markdown nested inside raw HTML)."""
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    return text.replace("\n", "<br>")


def score_color(score):
    if score >= 7.5:
        return "#27ae60"
    if score >= 5.5:
        return "#e2a93a"
    return "#c0392b"


def headline_for(dim_key, scores):
    if not scores:
        return "No scores returned."
    top_city, entry = max(scores.items(), key=lambda kv: kv[1]["score"])
    return f"Top pick: <strong>{top_city}</strong> ({entry['score']}/10) -- {entry['reason']}"


def agent_card_html(agent, status, thought):
    name = agent["name"]
    emoji = EMOJI.get(agent["key"], "\U0001F916")
    label = {"idle": "Waiting...", "thinking": "\U0001F914 Thinking...", "done": "✅ Done"}[status]
    body = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", thought) if (status == "done" and thought) else ""
    return (
        f'<div class="mc-agent-card {status}">'
        f'<div class="mc-agent-name">{emoji} {name}</div>'
        f'<div>{label}</div>'
        + (f'<div class="mc-agent-thought">{body}</div>' if body else "")
        + "</div>"
    )


def render_sidebar():
    st.sidebar.markdown("### \U0001F3DB️ The Panel")
    placeholders = {}
    for agent in ALL_AGENTS:
        ph = st.sidebar.empty()
        placeholders[agent["key"]] = ph
        ph.markdown(
            agent_card_html(
                agent,
                st.session_state.agent_status[agent["key"]],
                st.session_state.agent_thought[agent["key"]],
            ),
            unsafe_allow_html=True,
        )
    return placeholders


def set_agent(placeholders, key, status, thought=None):
    st.session_state.agent_status[key] = status
    if thought is not None:
        st.session_state.agent_thought[key] = thought
    agent = next(a for a in ALL_AGENTS if a["key"] == key)
    placeholders[key].markdown(
        agent_card_html(agent, status, st.session_state.agent_thought[key]),
        unsafe_allow_html=True,
    )


placeholders = render_sidebar()

main = st.container()
with main:
    st.markdown(
        """
    <div class="mc-hero">
    <div class="mc-hero-title">\U0001F3DB️ Move Court</div>
    <div class="mc-hero-sub">Eight agents cross-examine the 25 largest US cities against what actually matters to you --
    then render a verdict. Watch them think in the panel on the left.</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # --- Step indicator ---
    if st.session_state.step <= total_steps and not st.session_state.get("result"):
        cols_html = ""
        for i, spec in enumerate(SPECIALISTS):
            cls = "done" if i < st.session_state.step else ("active" if i == st.session_state.step else "")
            cols_html += f'<div class="mc-step {cls}">{EMOJI[spec["key"]]} {spec["name"].replace(" Agent", "")}</div>'
        last_cls = "active" if st.session_state.step == total_steps else ""
        cols_html += f'<div class="mc-step {last_cls}">\U0001F9EE Final details</div>'
        st.markdown(f'<div class="mc-steps">{cols_html}</div>', unsafe_allow_html=True)

    # --- Step 0..N-1: one specialist question at a time ---
    if st.session_state.step < total_steps:
        spec = SPECIALISTS[st.session_state.step]
        st.markdown(
            f"""<div class="mc-bubble">
            <div class="who">{EMOJI[spec['key']]} {spec['name']} asks:</div>
            {spec['question']}
            </div>""",
            unsafe_allow_html=True,
        )
        answer = st.text_area(
            "Your answer", key=f"answer_{spec['key']}", label_visibility="collapsed",
            placeholder="Type your answer here...",
        )
        weight = st.slider(
            "⚖️ How much should this matter to your final score?", 1, 5, 3, key=f"weight_{spec['key']}"
        )
        if st.button("Next →", type="primary"):
            st.session_state.answers[spec["key"]] = answer
            st.session_state.weights[spec["key"]] = weight

            prior_answers = {k: v for k, v in st.session_state.answers.items() if k != spec["key"]}

            set_agent(placeholders, spec["key"], "thinking")
            with st.spinner(f"{EMOJI[spec['key']]} {spec['name']} is scoring all 25 cities..."):
                scores = score_dimension(spec, answer, st.session_state.tracker, prior_answers=prior_answers)
            st.session_state.dim_scores[spec["key"]] = scores
            set_agent(placeholders, spec["key"], "done", headline_for(spec["key"], scores))

            st.session_state.step += 1
            st.rerun()

    # --- Final step: optional context + run ---
    elif st.session_state.step == total_steps:
        st.markdown(
            """<div class="mc-bubble">
            <div class="who">\U0001F9EE Last thing</div>
            A couple of optional extras to sharpen the verdict.
            </div>""",
            unsafe_allow_html=True,
        )
        other_people = st.text_area(
            "\U0001F46A Optional: what do other people in your life (parents, partner, friends) "
            "want for your move? Mention any pressure or disagreement.",
            key="other_people",
        )
        user_profile = st.text_area(
            "✨ Optional: anything else about you (hobbies, personality) for the narrative agent?",
            key="user_profile",
        )
        c1, c2 = st.columns([1, 1])
        run_clicked = c1.button("\U0001F3DB️ Run the Court", type="primary", use_container_width=True)
        start_over_clicked = c2.button("↺ Start over", use_container_width=True)

        if run_clicked:
            ranked = aggregate_scores(st.session_state.dim_scores, st.session_state.weights)
            priorities_text = "; ".join(f"{k}: {v}" for k, v in st.session_state.answers.items())

            set_agent(placeholders, "conflict", "thinking")
            with st.spinner("\U0001F575️ Checking for conflicts..."):
                conflicts = conflict_check(priorities_text, other_people, st.session_state.tracker)
            set_agent(placeholders, "conflict", "done", conflicts[:140] + ("..." if len(conflicts) > 140 else ""))

            set_agent(placeholders, "future_you", "thinking")
            narratives = {}
            with st.spinner("\U0001F52E Writing Future You narratives..."):
                for row in ranked[:2]:
                    narratives[row["city"]] = future_you_narrative(
                        row["city"], user_profile, st.session_state.tracker
                    )
            preview = " / ".join(narratives.keys())
            set_agent(placeholders, "future_you", "done", f"Wrote narratives for: {preview}")

            set_agent(placeholders, "verdict", "thinking")
            with st.spinner("⚖️ Rendering verdict..."):
                final_verdict = verdict(ranked, conflicts, priorities_text, st.session_state.tracker)
            set_agent(placeholders, "verdict", "done", final_verdict[:140] + ("..." if len(final_verdict) > 140 else ""))

            st.session_state.result = {
                "ranked": ranked,
                "conflicts": conflicts,
                "narratives": narratives,
                "verdict": final_verdict,
                "tracker": st.session_state.tracker,
            }
            st.rerun()

        if start_over_clicked:
            for k in [
                "step", "answers", "weights", "dim_scores", "result", "tracker",
                "agent_status", "agent_thought", "other_people", "user_profile",
            ]:
                st.session_state.pop(k, None)
            st.rerun()

    # --- Results ---
    if st.session_state.get("result"):
        r = st.session_state.result
        st.balloons()

        st.markdown(
            f"""<div class="mc-verdict">
            <div class="mc-verdict-title">⚖️ The Verdict</div>
            {to_html(r['verdict'])}
            </div>""",
            unsafe_allow_html=True,
        )

        st.subheader("\U0001F3C6 Top 5 cities")
        medals = ["\U0001F947", "\U0001F948", "\U0001F949", "4️⃣", "5️⃣"]
        for medal, row in zip(medals, r["ranked"][:5]):
            color = score_color(row["weighted_score"])
            chips = "".join(
                f'<span class="mc-chip">{EMOJI.get(dim, "")} {dim}: {entry["score"]}/10</span>'
                for dim, entry in row["reasons"].items()
            )
            st.markdown(
                f"""<div class="mc-city-card" style="background:{color};">
                <span class="mc-rank">{medal}</span>
                <strong style="font-size:1.3em;">{row['city']}</strong>
                <span style="float:right; font-weight:700;">{row['weighted_score']}/10</span>
                <div style="margin-top:8px;">{chips}</div>
                </div>""",
                unsafe_allow_html=True,
            )
            with st.expander(f"Why {row['city']}?"):
                for dim, entry in row["reasons"].items():
                    st.write(f"**{EMOJI.get(dim, '')} {dim}** ({entry['score']}/10): {entry['reason']}")

        st.subheader("\U0001F575️ Conflicts with what others want")
        st.info(r["conflicts"])

        st.subheader("\U0001F52E Future You")
        fy_cols = st.columns(len(r["narratives"]) or 1)
        for col, (city, narrative) in zip(fy_cols, r["narratives"].items()):
            with col:
                st.markdown(f"**{city}**")
                st.write(narrative)

        with st.expander("\U0001F4CA Tokenomics (measured this run)"):
            rows = r["tracker"].as_rows()
            st.table(rows)
            c1, c2 = st.columns(2)
            c1.metric("Total input tokens", r["tracker"].total_input)
            c2.metric("Total output tokens", r["tracker"].total_output)
