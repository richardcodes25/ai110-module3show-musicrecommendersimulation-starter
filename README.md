# 🎵 Music Recommender Simulation - Musicology

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

---

## How The System Works

Real-world recommenders (Spotify, YouTube) mostly blend two ideas: **collaborative
filtering** ("people who liked what you liked also enjoyed this") and **content-based
filtering** ("this song *sounds like* the songs you already enjoy"). Big platforms lean
heavily on collaborative signals — likes, skips, watch time, playlist adds — because they
have millions of users to learn patterns from. My simulation doesn't have that crowd data,
so it is a **content-based recommender**: it prioritizes matching the intrinsic attributes
of each song to a user's stated taste profile. Specifically, it prioritizes getting the
**vibe** right — genre first (a hard taste boundary), then how closely a song's *energy*
matches what the user wants, then finer mood and acoustic preferences.

### The Algorithm Recipe

The system uses two rules working together:

- **Scoring Rule** — measures how good a *single* song is for the user, and returns a
  number plus a list of human-readable reasons.
- **Ranking Rule** — scores *every* song, sorts them from best to worst, and returns only
  the top `k`. (A score alone isn't a recommendation; the ranking turns a pile of numbers
  into an ordered answer.)

For numeric features like `energy`, the score rewards **closeness**, not high or low
values: `energy_score = 1 - abs(user.target_energy - song.energy)`. A perfect match scores
`1.0` and the score falls off as the gap grows. (Note: `tempo_bpm` must be normalized to a
0–1 scale before it can be mixed in this way.)

Categorical features are scored by match with weights, in this priority order — **genre >
energy > mood**. Genre is weighted highest because it's the strongest taste boundary
(a jazz fan rarely wants metal, no matter the mood); mood is weighted lower because it's
partly redundant with the numeric energy/valence signals.

### Features used in this simulation

Each **`Song`** uses these attributes (listed in the same order as the columns in
`data/songs.csv`):

- `id` — identity only, not scored
- `title` — display only, not scored
- `artist` — display only, not scored
- `genre` — categorical taste boundary (highest weight)
- `mood` — categorical refinement (happy, chill, intense, …)
- `energy` (0–1) — the core "vibe" dial, scored by closeness
- `tempo_bpm` — supporting signal (normalized before scoring)
- `valence` (0–1) — emotional tone (bright vs. dark)
- `danceability` (0–1) — supporting signal
- `acousticness` (0–1) — acoustic/organic vs. electronic feel

Each **`UserProfile`** stores the user's stated taste:

- `favorite_genre` — the genre they want to hear
- `favorite_mood` — the mood they're going for
- `target_energy` (0–1) — the energy level they want, compared by closeness
- `likes_acoustic` — whether to reward high-acousticness songs

### Weights (starting point, tuned in the Experiments section)

| Feature | Weight | Why |
|---|---|---|
| `genre` match | 3.0 | Strongest taste boundary |
| `energy` closeness | 2.0 | Core "vibe" dial |
| `mood` match | 1.5 | Refinement; partly redundant with energy |
| `acousticness` fit | 1.0 | Supports the `likes_acoustic` preference |

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output

Paste a sample of your recommender's output here as a text block so a reader can see what it produces:

```
# e.g.:
# User profile: genre=indie, mood=chill, energy=low
# Recommendations:
#   1. ...
#   2. ...
#   3. ...
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this



