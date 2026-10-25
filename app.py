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

st.set_page_config(page_title="Move Court", page_icon="\U0001F3DB️")
st.title("\U0001F3DB️ Move Court")
st.caption(
    "A panel of agents cross-examines the 25 largest US cities against what "
    "actually matters to you -- then renders a verdict."
)

if "step" not in st.session_state:
    st.session_state.step = 0
    st.session_state.answers = {}
    st.session_state.weights = {}
    st.session_state.result = None

total_steps = len(SPECIALISTS)

# --- Step 0..N-1: one specialist question at a time ---
if st.session_state.step < total_steps:
    spec = SPECIALISTS[st.session_state.step]
    st.subheader(f"{spec['name']} asks:")
    st.write(spec["question"])
    answer = st.text_area("Your answer", key=f"answer_{spec['key']}")
    weight = st.slider(
        "How much should this matter to your final score?", 1, 5, 3, key=f"weight_{spec['key']}"
    )
    if st.button("Next"):
        st.session_state.answers[spec["key"]] = answer
        st.session_state.weights[spec["key"]] = weight
        st.session_state.step += 1
        st.rerun()

# --- Final step: optional context + run ---
elif st.session_state.step == total_steps:
    st.subheader("Last thing")
    other_people = st.text_area(
        "Optional: what do other people in your life (parents, partner, friends) "
        "want for your move? Mention any pressure or disagreement.",
        key="other_people",
    )
    user_profile = st.text_area(
        "Optional: anything else about you (hobbies, personality) for the narrative agent?",
        key="user_profile",
    )
    if st.button("Run the Court"):
        tracker = UsageTracker()
        dim_scores = {}
        progress = st.progress(0, text="Specialist agents are scoring all 25 cities...")
        for i, spec in enumerate(SPECIALISTS):
            dim_scores[spec["key"]] = score_dimension(
                spec, st.session_state.answers.get(spec["key"], ""), tracker
            )
            progress.progress((i + 1) / (total_steps + 3), text=f"{spec['name']} done")

        ranked = aggregate_scores(dim_scores, st.session_state.weights)
        progress.progress((total_steps + 1) / (total_steps + 3), text="Checking for conflicts...")
        priorities_text = "; ".join(
            f"{k}: {v}" for k, v in st.session_state.answers.items()
        )
        conflicts = conflict_check(priorities_text, other_people, tracker)

        progress.progress((total_steps + 2) / (total_steps + 3), text="Writing Future You narratives...")
        narratives = {
            row["city"]: future_you_narrative(row["city"], user_profile, tracker)
            for row in ranked[:2]
        }

        progress.progress(1.0, text="Rendering verdict...")
        final_verdict = verdict(ranked, conflicts, priorities_text, tracker)

        st.session_state.result = {
            "ranked": ranked,
            "conflicts": conflicts,
            "narratives": narratives,
            "verdict": final_verdict,
            "tracker": tracker,
        }
        st.rerun()

    if st.button("Start over"):
        for k in ["step", "answers", "weights", "result"]:
            st.session_state.pop(k, None)
        st.rerun()

# --- Results ---
if st.session_state.get("result"):
    r = st.session_state.result
    st.header("Verdict")
    st.write(r["verdict"])

    st.header("Top 5 cities")
    for row in r["ranked"][:5]:
        with st.expander(f"{row['city']} -- {row['weighted_score']}/10"):
            for dim, entry in row["reasons"].items():
                st.write(f"**{dim}** ({entry['score']}/10): {entry['reason']}")

    st.header("Conflicts with what others want")
    st.write(r["conflicts"])

    st.header("Future You")
    for city, narrative in r["narratives"].items():
        st.subheader(city)
        st.write(narrative)

    with st.expander("Tokenomics (measured this run)"):
        rows = r["tracker"].as_rows()
        st.table(rows)
        st.write(f"Total input tokens: {r['tracker'].total_input}")
        st.write(f"Total output tokens: {r['tracker'].total_output}")
