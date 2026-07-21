"""
Command line runner for the Music Recommender Simulation.

Demonstrates the stretch features:
- advanced song attributes (popularity, decade, instrumentalness, language, mood tags)
- multiple scoring modes (balanced / genre-first / mood-first / energy-focused)
- a diversity penalty that avoids repeating the same artist/genre
- a formatted results table (tabulate if installed, ASCII fallback otherwise)
"""

import textwrap

try:
    # When run as a module: python -m src.main
    from src.recommender import load_songs, recommend_songs, SCORING_MODES
except ModuleNotFoundError:
    # When run directly from inside src/: python main.py
    from recommender import load_songs, recommend_songs, SCORING_MODES

try:
    from tabulate import tabulate
    HAVE_TABULATE = True
except ImportError:
    HAVE_TABULATE = False


def format_table(recommendations: list) -> str:
    """Return a readable table of recommendations, including the reasons column."""
    rows = []
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        reasons = "\n".join(textwrap.wrap(explanation, width=48))
        rows.append([
            rank,
            song["title"],
            song["artist"],
            f"{song['genre']}/{song['mood']}",
            f"{score:.2f}",
            reasons,
        ])

    headers = ["#", "Title", "Artist", "Genre/Mood", "Score", "Why"]

    if HAVE_TABULATE:
        return tabulate(rows, headers=headers, tablefmt="fancy_grid")

    # --- ASCII fallback (no external dependency required) ---
    lines = []
    for row in rows:
        lines.append(f"{row[0]}. {row[1]} — {row[2]}")
        lines.append(f"   Score: {row[4]}  |  {row[3]}")
        for i, chunk in enumerate(row[5].split("\n")):
            prefix = "   Why:   " if i == 0 else "          "
            lines.append(prefix + chunk)
        lines.append("")
    return "\n".join(lines)


def show(title: str, user_prefs: dict, songs: list, **kwargs) -> None:
    """Run one recommendation and print it as a table with a header."""
    recs = recommend_songs(user_prefs, songs, k=5, **kwargs)
    print(f"\n### {title}")
    print(f"profile: {user_prefs}")
    print(format_table(recs))


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")
    print(f"tabulate installed: {HAVE_TABULATE} (ASCII fallback used if False)")
    print(f"available scoring modes: {list(SCORING_MODES)}")

    # A rich profile that exercises the new advanced features.
    studier = {
        "genre": "lofi", "mood": "chill", "energy": 0.4,
        "likes_acoustic": True, "prefers_instrumental": True,
        "desired_mood_tags": ["study", "calm"], "favorite_decade": 2020,
    }

    # Challenge 2: same profile, different scoring modes.
    print("\n" + "=" * 64 + "\n  CHALLENGE 2: SCORING MODES\n" + "=" * 64)
    for mode in ("balanced", "genre-first", "mood-first", "energy-focused"):
        show(f"mode = {mode}", studier, songs, mode=mode)

    # Challenge 3: diversity penalty. The lofi studier profile clusters hard —
    # LoRoom appears twice and lofi three times in the top results. Turning on the
    # penalty pushes a fresh artist/genre up instead of stacking the same ones.
    print("\n" + "=" * 64 + "\n  CHALLENGE 3: DIVERSITY PENALTY\n" + "=" * 64)
    show("diversity OFF", studier, songs, mode="balanced")
    show("diversity ON", studier, songs, mode="balanced",
         diversity=True, diversity_penalty=1.5)


if __name__ == "__main__":
    main()
