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

Genre and energy are the two heaviest signals (each worth up to +2.0), with mood a lighter
refinement (+1.0). Genre carries full weight because it's the strongest taste boundary
(a jazz fan rarely wants metal, no matter the mood); mood is weighted lower because it's
partly redundant with the numeric energy/valence signals. Exact point values are in the
finalized recipe below.

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

### Finalized Algorithm Recipe (as implemented)

Each song is scored against the user profile with this point budget (defined as constants
at the top of `src/recommender.py`, so they're easy to tune in the Experiments section):

| Rule | Points | Why |
|---|---|---|
| `genre` match | **+2.0** (exact match) | Hardest taste boundary — a lofi fan rarely wants metal |
| `energy` closeness | **0 → +2.0** sliding: `(1 - abs(target - energy)) * 2.0` | The core "vibe" dial; rewards *closeness*, not high/low |
| `mood` match | **+1.0** (exact match) | A refinement; partly redundant with energy, so worth less |
| `acousticness` fit | **+0.5** if `likes_acoustic` and `acousticness > 0.6` | Small tie-breaker nudge |

**Maximum possible score = 5.5.** Genre and mood are *binary* bonuses; energy is a
*continuous* slider — so when two songs share a genre and mood, the energy closeness
becomes the tie-breaker, and the system degrades gracefully to the numeric signal.

```
for each song in catalog:            # Scoring Rule (one song at a time)
    score, reasons = score_song(user, song)
sort all songs by score, descending  # Ranking Rule (the whole list)
return the top k
```

### The taste profile used for comparisons

The recommender compares every song against a user profile like this:

```python
user_prefs = {
    "favorite_genre": "lofi",     # strongest filter
    "favorite_mood":  "chill",
    "target_energy":  0.35,        # compared by closeness
    "likes_acoustic": True,
}
```

This describes a "focused study / relaxed" listener. It cleanly separates opposites
(e.g. intense rock vs. chill lofi score far apart on all four dimensions) while still
ranking similar songs by their energy gap.

### Potential biases I expect

Because this is a content-based system driven by a single-genre profile and fixed weights,
I expect these biases:

- **Genre over-prioritization.** With genre worth +2.0 as a hard match, a great song that
  nails the user's mood and energy but wears a *different* genre label can be ranked below a
  weaker same-genre song. The system may ignore excellent cross-genre matches.
- **Single-taste tunnel vision (over-specialization).** The profile names only one favorite
  genre and mood, so the recommender keeps serving "more of the same" and rarely surprises
  the user — the classic content-based *filter bubble*, with no collaborative signal to
  introduce serendipity.
- **Redundant-signal double-counting.** `mood` is partly derived from energy/valence, so
  rewarding both can over-count the same underlying vibe.
- **Small-catalog / label bias.** With only 18 songs and human-assigned genre/mood labels,
  a mislabeled or under-represented genre is effectively invisible to the ranker.

These are explored further in the **Limitations and Risks** section and `model_card.md`.

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

Below is illustrative output for a single `pop / happy / energy 0.8` profile against the
18-song catalog. (`python -m src.main` now runs several profiles back-to-back — see the
**Experiments You Tried** section for the full multi-profile stress test.)

```
Loaded songs: 18

============================================================
  MUSIC RECOMMENDER
  Profile: genre=pop, mood=happy, energy=0.8
============================================================

Top 5 recommendations:

1. Sunrise City — Neon Echo
   Score: 4.96  |  pop / happy
   Why:   genre match: pop (+2.0); energy 0.82 vs target 0.80 (gap 0.02 -> +1.96); mood match: happy (+1.0)

2. Gym Hero — Max Pulse
   Score: 3.74  |  pop / intense
   Why:   genre match: pop (+2.0); energy 0.93 vs target 0.80 (gap 0.13 -> +1.74)

3. Rooftop Lights — Indigo Parade
   Score: 2.92  |  indie pop / happy
   Why:   energy 0.76 vs target 0.80 (gap 0.04 -> +1.92); mood match: happy (+1.0)

4. Concrete Kings — Verse Mason
   Score: 1.90  |  hip hop / energetic
   Why:   energy 0.85 vs target 0.80 (gap 0.05 -> +1.90)

5. Night Drive Loop — Neon Echo
   Score: 1.90  |  synthwave / moody
   Why:   energy 0.75 vs target 0.80 (gap 0.05 -> +1.90)
```

The results match expectations: the pop + happy + high-energy track (*Sunrise City*) wins
decisively, the other pop track (*Gym Hero*) places second on its genre + energy match, and
*Rooftop Lights* (indie pop, but happy with near-perfect energy) rounds out the podium —
showing the score degrading gracefully to the numeric energy signal when genre/mood don't match.

---

## Experiments You Tried

### Stress test: diverse and adversarial profiles

I ran the recommender against six profiles defined in `src/main.py` — three realistic
listeners and three adversarial edge cases designed to try to "trick" the scoring logic.
Top-5 output for each is below.

**1. High-Energy Pop** — `{genre: pop, mood: happy, energy: 0.9}`

```
1. Sunrise City — Neon Echo
   Score: 4.84  |  pop / happy
   Why:   genre match: pop (+2.0); energy 0.82 vs target 0.90 (gap 0.08 -> +1.84); mood match: happy (+1.0)
2. Gym Hero — Max Pulse
   Score: 3.94  |  pop / intense
   Why:   genre match: pop (+2.0); energy 0.93 vs target 0.90 (gap 0.03 -> +1.94)
3. Rooftop Lights — Indigo Parade
   Score: 2.72  |  indie pop / happy
   Why:   energy 0.76 vs target 0.90 (gap 0.14 -> +1.72); mood match: happy (+1.0)
4. Storm Runner — Voltline
   Score: 1.98  |  rock / intense
   Why:   energy 0.91 vs target 0.90 (gap 0.01 -> +1.98)
5. Breakline — Circuit Fox
   Score: 1.94  |  drum and bass / euphoric
   Why:   energy 0.93 vs target 0.90 (gap 0.03 -> +1.94)
```

**2. Chill Lofi** — `{genre: lofi, mood: chill, energy: 0.35, likes_acoustic: True}`

```
1. Library Rain — Paper Lanterns
   Score: 5.50  |  lofi / chill
   Why:   genre match: lofi (+2.0); energy 0.35 vs target 0.35 (gap 0.00 -> +2.00); mood match: chill (+1.0); acoustic feel (+0.5)
2. Midnight Coding — LoRoom
   Score: 5.36  |  lofi / chill
   Why:   genre match: lofi (+2.0); energy 0.42 vs target 0.35 (gap 0.07 -> +1.86); mood match: chill (+1.0); acoustic feel (+0.5)
3. Focus Flow — LoRoom
   Score: 4.40  |  lofi / focused
   Why:   genre match: lofi (+2.0); energy 0.40 vs target 0.35 (gap 0.05 -> +1.90); acoustic feel (+0.5)
4. Spacewalk Thoughts — Orbit Bloom
   Score: 3.36  |  ambient / chill
   Why:   energy 0.28 vs target 0.35 (gap 0.07 -> +1.86); mood match: chill (+1.0); acoustic feel (+0.5)
5. Coffee Shop Stories — Slow Stereo
   Score: 2.46  |  jazz / relaxed
   Why:   energy 0.37 vs target 0.35 (gap 0.02 -> +1.96); acoustic feel (+0.5)
```

**3. Deep Intense Rock** — `{genre: rock, mood: intense, energy: 0.9}`

```
1. Storm Runner — Voltline
   Score: 4.98  |  rock / intense
   Why:   genre match: rock (+2.0); energy 0.91 vs target 0.90 (gap 0.01 -> +1.98); mood match: intense (+1.0)
2. Gym Hero — Max Pulse
   Score: 2.94  |  pop / intense
   Why:   energy 0.93 vs target 0.90 (gap 0.03 -> +1.94); mood match: intense (+1.0)
3. Breakline — Circuit Fox
   Score: 1.94  |  drum and bass / euphoric
   Why:   energy 0.93 vs target 0.90 (gap 0.03 -> +1.94)
4. Pulse Horizon — Volt Signal
   Score: 1.90  |  edm / uplifting
   Why:   energy 0.95 vs target 0.90 (gap 0.05 -> +1.90)
5. Concrete Kings — Verse Mason
   Score: 1.90  |  hip hop / energetic
   Why:   energy 0.85 vs target 0.90 (gap 0.05 -> +1.90)
```

**4. Adversarial — Conflicting (high energy + chill mood)** — `{genre: lofi, mood: chill, energy: 0.95}`

```
1. Midnight Coding — LoRoom
   Score: 3.94  |  lofi / chill
   Why:   genre match: lofi (+2.0); energy 0.42 vs target 0.95 (gap 0.53 -> +0.94); mood match: chill (+1.0)
2. Library Rain — Paper Lanterns
   Score: 3.80  |  lofi / chill
   Why:   genre match: lofi (+2.0); energy 0.35 vs target 0.95 (gap 0.60 -> +0.80); mood match: chill (+1.0)
3. Focus Flow — LoRoom
   Score: 2.90  |  lofi / focused
   Why:   genre match: lofi (+2.0); energy 0.40 vs target 0.95 (gap 0.55 -> +0.90)
4. Pulse Horizon — Volt Signal
   Score: 2.00  |  edm / uplifting
   Why:   energy 0.95 vs target 0.95 (gap 0.00 -> +2.00)
5. Gym Hero — Max Pulse
   Score: 1.96  |  pop / intense
   Why:   energy 0.93 vs target 0.95 (gap 0.02 -> +1.96)
```

*Observation:* the genre (+2.0) and mood (+1.0) bonuses outweigh a large energy penalty, so
low-energy lofi tracks still top a "high energy" request. The scoring is doing exactly what
the weights say — but it exposes that categorical matches can overpower a strong numeric
mismatch (a real bias, discussed below).

**5. Adversarial — Nonexistent genre (k-pop)** — `{genre: k-pop, mood: happy, energy: 0.5}`

```
1. Rooftop Lights — Indigo Parade
   Score: 2.48  |  indie pop / happy
   Why:   energy 0.76 vs target 0.50 (gap 0.26 -> +1.48); mood match: happy (+1.0)
2. Sunrise City — Neon Echo
   Score: 2.36  |  pop / happy
   Why:   energy 0.82 vs target 0.50 (gap 0.32 -> +1.36); mood match: happy (+1.0)
3. Velvet Hours — Mika Rose
   Score: 2.00  |  r&b / dreamy
   Why:   energy 0.50 vs target 0.50 (gap 0.00 -> +2.00)
4. Island Time — Sunny Groove
   Score: 1.90  |  reggae / playful
   Why:   energy 0.55 vs target 0.50 (gap 0.05 -> +1.90)
5. Midnight Coding — LoRoom
   Score: 1.84  |  lofi / chill
   Why:   energy 0.42 vs target 0.50 (gap 0.08 -> +1.84)
```

*Observation:* a genre no song has simply earns 0 genre points for everyone — the system
degrades gracefully to mood + energy instead of crashing or returning nothing.

**6. Adversarial — Sparse profile (energy only)** — `{energy: 0.5}`

```
1. Velvet Hours — Mika Rose
   Score: 2.00  |  r&b / dreamy
   Why:   energy 0.50 vs target 0.50 (gap 0.00 -> +2.00)
2. Island Time — Sunny Groove
   Score: 1.90  |  reggae / playful
   Why:   energy 0.55 vs target 0.50 (gap 0.05 -> +1.90)
3. Midnight Coding — LoRoom
   Score: 1.84  |  lofi / chill
   Why:   energy 0.42 vs target 0.50 (gap 0.08 -> +1.84)
4. Focus Flow — LoRoom
   Score: 1.80  |  lofi / focused
   Why:   energy 0.40 vs target 0.50 (gap 0.10 -> +1.80)
5. Dust and Roads — The Willows
   Score: 1.80  |  folk / nostalgic
   Why:   energy 0.40 vs target 0.50 (gap 0.10 -> +1.80)
```

*Observation:* with missing keys, `score_song` uses `.get()` and skips the genre/mood terms,
so ranking falls back entirely to energy closeness — no crash on an incomplete profile.

### Weight-shift experiment: double energy, halve genre

To test the profile-4 bias (genre + mood overpowering a strong energy mismatch), I ran one
controlled change: `ENERGY_WEIGHT 2.0 -> 4.0` and `GENRE_WEIGHT 2.0 -> 1.0`. The math stays
valid (energy still ranges `0 -> ENERGY_WEIGHT`; new max score = 6.5). Both tests still pass.

**Conflicting profile `{genre: lofi, mood: chill, energy: 0.95}` — before vs. after:**

| Rank | Baseline (genre 2.0 / energy 2.0) | Experiment (genre 1.0 / energy 4.0) |
|---|---|---|
| 1 | Midnight Coding (lofi, energy 0.42) | **Pulse Horizon (edm, energy 0.95)** |
| 2 | Library Rain (lofi, energy 0.35) | Gym Hero (pop, energy 0.93) |
| 3 | Focus Flow (lofi, energy 0.40) | Breakline (dnb, energy 0.93) |
| 5 | Pulse Horizon | Midnight Coding (lofi) drops to #5 |

The change **fixed the conflicting case**: high-energy songs now correctly top a
high-energy request, and the mismatched low-energy lofi tracks fall to the bottom.

**Did it hurt the normal profiles?** No — the **Chill Lofi** ranking kept the exact same
top-5 order (only the absolute scores grew), because for that profile genre and energy
already agree. So for this catalog the shift was **more accurate, not just different.**

**Why I reverted to 2.0 / 2.0 anyway:** at energy 4.0, genre contributes only ~15% of the
max score, which undermines a *content-based, genre-first* design — a user asking for "lofi"
could be served edm/metal purely on an energy match. The baseline is a better general-purpose
balance; the experiment is documented here rather than kept as the default.

### Ideas to try next

- Add a **valence/tempo** term so "mood" is honored numerically, not just as a categorical label.
- Try a middle ground (e.g. genre 1.5 / energy 2.5) to soften the conflicting-profile bias
  without abandoning the genre-first premise.

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

This project made recommenders feel a lot less like magic. I learned that turning data into a
prediction is really just two steps: score every song against what the user wants (the
Scoring Rule), then sort the scores and keep the best few (the Ranking Rule). A handful of
simple point rules — genre, mood, and energy closeness — was enough to produce results that
genuinely "feel" like recommendations, which showed me that big platforms start from these
same basic ideas before adding more complex methods.

I also saw how easily bias can sneak in. Because half my catalog is high-energy, loud songs
kept showing up even for users who didn't ask for them, and weighting genre heavily created a
"filter bubble" that hid great cross-genre matches. It made me realize that a recommender's
output is only as fair as its data and its weights — and that unfairness can appear without
anyone intending it. A fuller reflection is in the Model Card's **Personal Reflection** section.



