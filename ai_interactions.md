# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agentic Workflow (SF8)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

I asked the agent to add advanced song features (Challenge 1) and wire them into the
scoring logic — a multi-file change touching the dataset, the data loader, the scoring
function, and the data models.

**Prompts used:**

- "Add 5 advanced attributes to `data/songs.csv` that aren't in the baseline: popularity
  (0–100), release_decade, instrumentalness (0–1), language, and detailed mood_tags like
  'nostalgic' or 'euphoric'. Fill sensible values for all 18 songs and keep the CSV valid."
- "Update `src/recommender.py` so scoring accounts for the new attributes. Convert the new
  numeric columns to numbers in `load_songs`, add the fields to the `Song` and `UserProfile`
  dataclasses with defaults so existing tests still pass, and give each new feature its own
  weighted rule with a human-readable reason. Verify the math stays valid."

**What did the agent generate or change?**

- `data/songs.csv`: added 5 columns (`popularity`, `release_decade`, `instrumentalness`,
  `language`, `mood_tags`) to the header and all 18 rows.
- `src/recommender.py`: extended `INT_FIELDS`/`FLOAT_FIELDS` and `load_songs` (splitting
  `mood_tags` on `|` into a list), added the new fields to `Song` and `UserProfile` with
  defaults, and added scoring rules 5–9 (mood-tag overlap, decade, popularity,
  instrumentalness, language) inside the shared `_score_core` function.

**What did you verify or fix manually?**

- Confirmed the new dataclass fields had **defaults**, because `tests/test_recommender.py`
  builds a `Song`/`UserProfile` with only the core fields — without defaults the tests break.
- Ran `pytest` (2 passing) and `python -m src.main` to confirm the new features appeared in
  the reasons and that popularity was scaled by `/100` (not added raw, which would have
  dominated the score). Checked that a missing/empty `mood_tags` didn't crash the loader.

---

## Design Pattern (SF10)

> Document how AI helped you choose or implement a design pattern.

**Which design pattern did you use?**

The **Strategy pattern**, to support multiple scoring modes (Challenge 2): `balanced`,
`genre-first`, `mood-first`, and `energy-focused`.

**How did AI help you brainstorm or implement it?**

I attached `recommender.py` and asked the AI for a modular way to let a user switch ranking
strategies without duplicating the scoring code. It suggested a lightweight Strategy pattern:
instead of writing four separate scoring functions, capture each strategy as a *set of
weights* and have one scoring function read whichever weight set is active. It also
recommended a registry dict (`SCORING_MODES`) mapping a mode name to its weights, so adding
a new mode is a one-line change and `main.py` can list the available modes dynamically.

**How does the pattern appear in your final code?**

- `Weights` (dataclass) — one interchangeable strategy (the points each feature is worth).
- `SCORING_MODES: Dict[str, Weights]` — the registry of named strategies.
- `_score_core(prefs, song, weights)` — the single scoring function that consumes whichever
  strategy is passed in; `score_song(...)`/`recommend_songs(...)` take a `mode` argument and
  resolve it via `_resolve_weights(mode)`.

---

## Diversity / Fairness Logic (SF – Challenge 3)

> A "diversity penalty" that keeps the top results from stacking the same artist or genre.

**Prompt used:**

"In `recommend_songs`, add a rule that penalizes a song's score if its artist is already
present in the recommendations chosen so far (and a smaller penalty for a repeated genre),
so the top-k list stays varied. Explain the approach."

**How it works:** `_diverse_rank` does a greedy re-ranking (a simple Maximal Marginal
Relevance idea): it repeatedly picks the highest-scoring remaining song after subtracting a
penalty for each already-selected song sharing its artist (full penalty) or genre (half
penalty), and notes the deduction in that song's reasons. Enabled with `diversity=True`.

**Verification:** For the lofi "studier" profile, `LoRoom` appeared twice and `lofi` three
times in the top 5. With the penalty on, the third `LoRoom`/`lofi` song (*Focus Flow*) was
pushed down and a fresh artist/genre (*Spacewalk Thoughts*, ambient) rose into its place.

---

## Formatted Output Table (SF – Challenge 4)

> A readable results table including the reasons for each score.

**Prompt used:**

"Suggest a way to display my top recommendations as a formatted table using `tabulate`, with
an ASCII fallback if it isn't installed. The table must include a column for the 'reasons'
behind each score."

**Result:** `format_table` in `src/main.py` builds rows (rank, title, artist, genre/mood,
score, wrapped reasons) and renders them with `tabulate` (`fancy_grid`) when available, or a
hand-rolled ASCII layout otherwise. `tabulate` was added to `requirements.txt`.
