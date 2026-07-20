# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

**VibeFinder 1.0** — a small, vibe-first music recommender.

**Goal / Task:** VibeFinder tries to suggest songs that match a user's taste. The user says
what genre, mood, and energy level they want, and the system predicts which songs in the
catalog fit best. It returns a short ranked list with a plain-language reason for each pick.

---

## 2. Intended Use  

**Intended use.** VibeFinder is a classroom project for learning how content-based
recommenders work. It is meant for exploration and demos, not real users. It assumes the
user can describe their taste as a genre, a mood, and an energy level, and that a good
recommendation is a song whose attributes are close to those preferences.

**Non-intended use.** It should not be used as a real product or to make decisions that
matter. It only knows 18 songs, so it cannot represent real musical variety. It should not
be used to judge artists, rank "good" vs. "bad" music, or power anything commercial. It has
no user history, so it cannot learn or personalize over time.

---

## 3. How the Model Works  

Think of it like a scorecard. The user picks a favorite genre, a favorite mood, and a target
energy level (calm to hyped). VibeFinder looks at every song and gives it points. A song
earns points for matching the genre, for matching the mood, and for having an energy level
close to what the user asked for. There is also a small bonus for acoustic songs if the user
likes acoustic music.

The most important idea is that energy is scored by *closeness*, not by high or low. A song
whose energy is almost exactly what the user wanted earns almost full energy points, and the
points shrink as the gap grows. After every song has a score, the system sorts them from
highest to lowest and shows the top few, along with the reasons each one scored well.

Compared to the starter code, I filled in the empty scoring logic, added clear point weights
(genre and energy count most, mood counts less), made every recommendation explain itself,
and expanded the song catalog.

---

## 4. Data  

The catalog has **18 songs**, stored in `data/songs.csv`. It started with 10 songs and I
added 8 more to cover a wider range of genres and moods. Each song has ten fields: id, title,
artist, genre, mood, and five number features (energy, tempo, valence, danceability, and
acousticness), each on a 0–1 scale except tempo.

There are 15 genres (pop, lofi, rock, jazz, edm, metal, hip hop, and more) and 14 moods.
Some limits: the dataset is tiny, half the songs are high-energy so calm music is
underrepresented, and lofi is the most common genre. Big parts of real musical taste are
missing — there are no lyrics, no language, no release year, and no sense of what is popular.

---

## 5. Strengths  

VibeFinder works well when a user's preferences line up with each other. For a clear taste
like "chill acoustic lofi" or "intense rock," it puts the obvious best song right at the top
and the results match my own intuition. Because energy is scored by closeness, it is good at
ranking similar songs by how well they fit a target vibe.

It is also transparent and sturdy. Every recommendation comes with a reason showing exactly
where its points came from, so it is easy to understand *why* a song was picked. And it
handles messy input gracefully — an unknown genre or a half-filled profile still returns
sensible results instead of crashing.

---

## 6. Limitations and Bias 

**High-energy filler bias (the main weakness I found).** Half of the catalog (9 of 18 songs)
is high-energy (≥ 0.7) and the average energy is 0.64, so the dataset itself leans loud and
fast. Because my scoring rewards energy *closeness*, high-energy tracks like *Gym Hero*,
*Breakline*, and *Storm Runner* repeatedly turn up in the lower ranks of many different
profiles — even ones that never asked for that vibe — simply because there are so many of
them near the top of the energy range. Meanwhile a listener who wants calm music (target
energy ~0.2–0.3) has only about four songs to choose from, so low-energy users get far less
variety and a weaker "filter bubble" forms around energetic music.

**Two related biases** compound this: (1) genre is a hard +2.0 match, so a great mood-and-
energy fit in a *different* genre gets buried under a weaker same-genre song (a filter
bubble around the user's one stated genre); and (2) similar genres like `pop` and
`indie pop` are treated as completely unrelated, so an indie-pop fan is never shown pop and
vice versa, even though they sound alike. The system also ignores lyrics, language, artist
familiarity, and listening context entirely.

---

## 7. Evaluation  

**Profiles tested.** I stress-tested the recommender with six profiles (defined in
`src/main.py`): three realistic listeners — **High-Energy Pop**, **Chill Lofi**, and
**Deep Intense Rock** — and three adversarial edge cases — a **Conflicting** profile
(chill lofi mood but energy 0.95), a **Nonexistent genre** (k-pop), and a **Sparse** profile
(energy only). For each I looked at the top 5 songs, their scores, and the "reasons" the
system gave.

**What surprised me.** Three things. First, all six profiles produced a *different* #1 song,
which told me the catalog is varied enough and no single track dominates. Second, the
Conflicting profile "tricked" the system: asking for high energy still returned calm lofi
songs at the top, because a genre match (+2.0) plus a mood match (+1.0) outweighs a big
energy penalty. Third, the broken cases failed *gracefully* — the fake k-pop genre and the
missing-keys profile both still returned sensible energy-based results instead of crashing.

**Profile-by-profile comparisons.**

- **High-Energy Pop vs. Chill Lofi:** the pop profile floats loud, upbeat tracks
  (*Sunrise City*, *Gym Hero*) to the top, while the lofi profile shifts entirely toward
  quiet, acoustic study music (*Library Rain*, *Midnight Coding*). This makes sense — they
  ask for opposite ends of the energy dial and different genres, so almost nothing overlaps.

- **High-Energy Pop vs. Deep Intense Rock:** both want high energy, so they *share* several
  fast songs in the lower ranks (*Gym Hero*, *Breakline*), but each still crowns its own
  genre first (*Sunrise City* for pop, *Storm Runner* for rock). This shows genre acting as
  the tie-breaker between two otherwise similar high-energy tastes.

- **Chill Lofi vs. Deep Intense Rock:** these are near-mirror opposites and share zero songs
  in their top 5 — the lofi list is all low-energy/acoustic, the rock list is all
  high-energy/aggressive. This is the clearest sign the profiles are actually testing
  different things.

- **Deep Intense Rock vs. Conflicting profile:** both effectively want high energy, but the
  Conflicting profile's `lofi` + `chill` labels drag calm lofi songs to the top instead,
  proving that categorical matches can override the numeric energy request.

**Plain-language example — why does "Gym Hero" keep showing up for "Happy Pop"?**
Imagine each song earns points like a scorecard. When someone asks for happy pop, *Gym Hero*
already wins big points just for being a pop song, and more points for being high-energy like
they wanted. It loses the "happy" point because it's actually an "intense" song — but that
single missing point isn't enough to knock it down. So a high-energy pop workout song keeps
crashing the party for someone who really just wanted something cheerful, because the system
counts *genre* and *energy* much more heavily than *mood*.

---

## 8. Future Work  

If I kept developing VibeFinder, I would:

1. **Balance the dataset and add more songs** so calm and niche tastes have as many options
   as high-energy ones, which would reduce the high-energy filler bias.
2. **Score mood with numbers, not just labels.** I would use valence and tempo to measure
   mood, so a "happy but calm" song is understood even if its mood tag doesn't match exactly.
3. **Support richer tastes and more variety.** I would let users pick more than one favorite
   genre, treat similar genres (like pop and indie pop) as related, and add a rule that
   keeps the top results from all sounding the same.

---

## 9. Personal Reflection  

**Biggest learning moment.** The moment things clicked was seeing that a "recommendation" is
really just scoring every item and sorting the list. Once I understood that a Scoring Rule
(judging one song) and a Ranking Rule (ordering all of them) work together, the whole system
stopped feeling like magic and started feeling like a scorecard I controlled.

**How AI tools helped, and where I checked them.** AI tools were great for brainstorming the
scoring recipe, explaining ideas like `.sort()` vs. `sorted()`, and drafting documentation
quickly. But I had to stay in control of the logic. I double-checked the actual weights and
math, made sure the code matched what I intended, and treated experiment results as something
to verify by running the program myself — not just accept because the AI suggested it.

**What surprised me.** I was surprised how much a few simple point rules can "feel" like a
real recommendation. There is no machine learning here, yet the top picks genuinely match a
vibe. It made me realize that even Spotify and YouTube start from these same basic ideas
before layering on more complex methods.

**What I'd try next.** I would extend the project by adding collaborative filtering (learning
from what similar users like) on top of my content-based scoring, so the system could
introduce pleasant surprises instead of always recommending "more of the same." This project
changed how I think about recommendation apps — I now notice the trade-off between showing me
what I already like and helping me discover something new.
