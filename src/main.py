"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

try:
    # When run as a module: python -m src.main
    from src.recommender import load_songs, recommend_songs
except ModuleNotFoundError:
    # When run directly from inside src/: python main.py
    from recommender import load_songs, recommend_songs


# Named profiles used to stress-test the recommender.
# The first three are realistic "normal" listeners; the rest are adversarial
# edge cases designed to see if the scoring logic can be tricked.
PROFILES = [
    ("High-Energy Pop",
     {"genre": "pop", "mood": "happy", "energy": 0.9}),
    ("Chill Lofi",
     {"genre": "lofi", "mood": "chill", "energy": 0.35, "likes_acoustic": True}),
    ("Deep Intense Rock",
     {"genre": "rock", "mood": "intense", "energy": 0.9}),

    # --- Adversarial / edge cases ---
    ("Conflicting (high energy + chill mood)",
     {"genre": "lofi", "mood": "chill", "energy": 0.95}),
    ("Nonexistent genre (k-pop)",
     {"genre": "k-pop", "mood": "happy", "energy": 0.5}),
    ("Sparse profile (energy only)",
     {"energy": 0.5}),
]


def print_recommendations(name: str, user_prefs: dict, songs: list) -> None:
    """Run the recommender for one named profile and print the top 5 results."""
    recommendations = recommend_songs(user_prefs, songs, k=5)

    print()
    print("=" * 64)
    print(f"  PROFILE: {name}")
    print(f"  {user_prefs}")
    print("=" * 64)
    print(f"\nTop {len(recommendations)} recommendations:\n")

    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"{rank}. {song['title']} — {song['artist']}")
        print(f"   Score: {score:.2f}  |  {song['genre']} / {song['mood']}")
        print(f"   Why:   {explanation}")
        print()


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    for name, user_prefs in PROFILES:
        print_recommendations(name, user_prefs, songs)


if __name__ == "__main__":
    main()
