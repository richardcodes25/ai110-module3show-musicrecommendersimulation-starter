import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

# --- Algorithm Recipe weights (see README "How The System Works") ---
GENRE_WEIGHT = 2.0      # genre match: hardest taste boundary
ENERGY_WEIGHT = 2.0     # energy closeness: the core "vibe" dial (sliding 0 -> 2.0)
MOOD_WEIGHT = 1.0       # mood match: a refinement, worth less than genre
ACOUSTIC_WEIGHT = 0.5   # small nudge when the user likes acoustic songs
ACOUSTIC_THRESHOLD = 0.6

NUMERIC_FIELDS = ("energy", "tempo_bpm", "valence", "danceability", "acousticness")


def _score_features(
    genre_pref: Optional[str],
    mood_pref: Optional[str],
    energy_pref: Optional[float],
    likes_acoustic: bool,
    song_genre: str,
    song_mood: str,
    song_energy: float,
    song_acousticness: float,
) -> Tuple[float, List[str]]:
    """
    Shared scoring recipe used by both the functional and OOP paths.
    Rewards CLOSENESS on energy (not high/low), and exact matches on genre/mood.
    Returns (score, reasons).
    """
    score = 0.0
    reasons: List[str] = []

    # 1. Genre match (+2.0) — strongest taste boundary
    if genre_pref is not None and song_genre == genre_pref:
        score += GENRE_WEIGHT
        reasons.append(f"genre match: {song_genre} (+{GENRE_WEIGHT:.1f})")

    # 2. Energy closeness (0 -> +2.0) — rewards being near the target, not high or low
    if energy_pref is not None:
        energy_gap = abs(energy_pref - song_energy)      # 0.0 perfect, 1.0 opposite
        energy_points = (1 - energy_gap) * ENERGY_WEIGHT
        score += energy_points
        reasons.append(
            f"energy {song_energy:.2f} vs target {energy_pref:.2f} "
            f"(gap {energy_gap:.2f} -> +{energy_points:.2f})"
        )

    # 3. Mood match (+1.0) — refinement
    if mood_pref is not None and song_mood == mood_pref:
        score += MOOD_WEIGHT
        reasons.append(f"mood match: {song_mood} (+{MOOD_WEIGHT:.1f})")

    # 4. Acoustic preference (+0.5) — small tie-breaker nudge
    if likes_acoustic and song_acousticness > ACOUSTIC_THRESHOLD:
        score += ACOUSTIC_WEIGHT
        reasons.append(f"acoustic feel (+{ACOUSTIC_WEIGHT:.1f})")

    return score, reasons

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def _score(self, user: UserProfile, song: Song) -> Tuple[float, List[str]]:
        """Score one Song against a UserProfile; returns (score, reasons)."""
        return _score_features(
            genre_pref=user.favorite_genre,
            mood_pref=user.favorite_mood,
            energy_pref=user.target_energy,
            likes_acoustic=user.likes_acoustic,
            song_genre=song.genre,
            song_mood=song.mood,
            song_energy=song.energy,
            song_acousticness=song.acousticness,
        )

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top-k Songs for a user, ranked highest score first."""
        # Scoring Rule: score every song; Ranking Rule: sort desc, keep top k.
        scored = [(song, self._score(user, song)[0]) for song in self.songs]
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return [song for song, _score in scored[:k]]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a human-readable string of the song's score and reasons."""
        score, reasons = self._score(user, song)
        if reasons:
            return f"Score {score:.2f} — " + "; ".join(reasons)
        return f"Score {score:.2f} — included by ranking, but no strong feature matches"

def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file into a list of dicts, converting numeric
    columns from strings to numbers.
    Required by src/main.py
    """
    songs: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            row["id"] = int(row["id"])
            for field in NUMERIC_FIELDS:
                row[field] = float(row[field])
            songs.append(row)
    return songs

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """
    Scores a single song (dict) against user preferences (dict) using the
    Algorithm Recipe. Accepts either short keys (genre/mood/energy) or the
    UserProfile-style keys (favorite_genre/favorite_mood/target_energy).
    Returns (score, reasons).
    """
    genre_pref = user_prefs.get("genre", user_prefs.get("favorite_genre"))
    mood_pref = user_prefs.get("mood", user_prefs.get("favorite_mood"))
    energy_pref = user_prefs.get("energy", user_prefs.get("target_energy"))
    likes_acoustic = user_prefs.get("likes_acoustic", False)

    return _score_features(
        genre_pref=genre_pref,
        mood_pref=mood_pref,
        energy_pref=energy_pref,
        likes_acoustic=likes_acoustic,
        song_genre=song["genre"],
        song_mood=song["mood"],
        song_energy=song["energy"],
        song_acousticness=song["acousticness"],
    )

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """
    Functional recommendation: score every song (Scoring Rule), rank by score
    descending and keep the top k (Ranking Rule).
    Returns a list of (song_dict, score, explanation).
    Required by src/main.py
    """
    # Judge every song, then rank. Build (song, score, explanation) tuples...
    scored = [
        (song, score, "; ".join(reasons) if reasons else "no strong feature matches")
        for song in songs
        for score, reasons in [score_song(user_prefs, song)]
    ]

    # ...sort a NEW list highest-first (sorted() leaves `scored`/`songs` untouched),
    # then slice the top k.
    ranked = sorted(scored, key=lambda item: item[1], reverse=True)
    return ranked[:k]
