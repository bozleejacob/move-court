# Move Court

A panel of 8 AI agents cross-examines the 25 largest US cities against what
actually matters to *you* -- then renders a verdict on where to move after
school.

Five specialist agents (Career, Cost of Living, Community, Family & Friends,
Climate & Lifestyle) each ask you one question, then score all 25 cities on
their dimension. A Conflict Agent checks your priorities against what other
people in your life want. A Future You Agent writes a day-in-the-life vignette
for your top 2 cities. A Verdict Agent renders the final call.

## Run it (should take under 10 minutes)

1. Clone this repo.
2. Make sure a `.env` file exists either in this folder or **one folder
   above it**, containing:
   ```
   PORTKEY_API_KEY=your-portkey-key-here
   ```
   (`.env.example` shows the exact format -- never commit a real `.env`.)
3. From this folder, create a virtual environment and install dependencies:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
4. Run the app:
   ```powershell
   streamlit run app.py
   ```
5. Your browser opens to `http://localhost:8501`. Answer each agent's
   question, optionally add what other people in your life want, then click
   "Run the Court."

## Project layout

- `app.py` -- Streamlit UI / wizard flow
- `agents.py` -- the 8 agent prompts, scoring, and safety handling
- `client.py` -- Portkey/OpenAI client setup and token-usage tracker
- `data/cities.csv` -- the dataset of the 25 largest US cities (population,
  cost of living, median rent/income, top industries, climate, walkability,
  nightlife/outdoors/diversity scores, safety index, commute time)

## Switching datasets

The app is hardcoded to read `data/cities.csv`. To test with a different or
larger dataset, replace that file with another CSV using the same columns
(see the header row in `data/cities.csv` for the exact schema), or point
`agents.py`'s `CITIES = pd.read_csv(...)` line at a different path.

## Model and keys

- Uses `gpt-6-luna` via Portkey (`https://api.portkey.ai/v1`), per course
  requirements.
- `client.py` checks for `.env` in this folder first, then one folder above,
  and reads `PORTKEY_API_KEY` (or `OPENAI_API_KEY` as a fallback).

## Safety note

Agent calls are wrapped so that a blocked/filtered response (e.g. the
provider's own content filter tripping) fails gracefully into a visible
"blocked and skipped" message instead of crashing the whole app. See the
report's Safety section for a before/after example.
