# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

Give your model a short, descriptive name.  
Example: **VibeFinder 1.0**  

---

## 2. Intended Use  

Describe what your recommender is designed to do and who it is for. 

Prompts:  

- What kind of recommendations does it generate  
- What assumptions does it make about the user  
- Is this for real users or classroom exploration  

---

## 3. How the Model Works  

Explain your scoring approach in simple language.  

Prompts:  

- What features of each song are used (genre, energy, mood, etc.)  
- What user preferences are considered  
- How does the model turn those into a score  
- What changes did you make from the starter logic  

Avoid code here. Pretend you are explaining the idea to a friend who does not program.

---

## 4. Data  

Describe the dataset the model uses.  

Prompts:  

- How many songs are in the catalog  
- What genres or moods are represented  
- Did you add or remove data  
- Are there parts of musical taste missing in the dataset  

---

## 5. Strengths  

Where does your system seem to work well  

Prompts:  

- User types for which it gives reasonable results  
- Any patterns you think your scoring captures correctly  
- Cases where the recommendations matched your intuition  

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

Ideas for how you would improve the model next.  

Prompts:  

- Additional features or preferences  
- Better ways to explain recommendations  
- Improving diversity among the top results  
- Handling more complex user tastes  

---

## 9. Personal Reflection  

A few sentences about your experience.  

Prompts:  

- What you learned about recommender systems  
- Something unexpected or interesting you discovered  
- How this changed the way you think about music recommendation apps  
