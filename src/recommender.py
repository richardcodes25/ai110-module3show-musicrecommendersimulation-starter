import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Scoring weights ("Algorithm Recipe"). Each scoring MODE is a set of weights,
# which is a lightweight Strategy pattern: swapping the weights swaps the
# ranking strategy without changing any scoring code. See SCORING_MODES below.
# ---------------------------------------------------------------------------

ACOUSTIC_THRESHOLD = 0.6        # a song counts as "acoustic" above this
INSTRUMENTAL_THRESHOLD = 0.6    # a song counts as "instrumental" above this


@dataclass
class Weights:
    """One scoring strategy: how many points each matching feature is worth."""
    genre: float = 2.0          # exact genre match
    energy: float = 2.0         # energy closeness (sliding 0 -> energy)
    mood: float = 1.0           # exact mood match
    acoustic: float = 0.5       # acoustic bonus when user likes acoustic
    mood_tags: float = 0.5      # per overlapping detailed mood tag (capped at 2)
    decade: float = 0.5         # release-decade match
    popularity: float = 1.0     # scaled by popularity/100 when user wants popular
    instrumental: float = 0.5   # instrumental bonus when user wants instrumental
    language: float = 0.5       # language match


# Strategy registry: name -> Weights. main.py lets the user switch between these.
SCORING_MODES: Dict[str, Weights] = {
    "balanced": Weights(),
    "genre-first": Weights(genre=4.0, energy=1.0, mood=0.5, acoustic=0.25,
                           mood_tags=0.25, decade=0.5, popularity=0.5,
                           instrumental=0.25, language=0.5),
    "mood-first": Weights(genre=1.0, energy=1.0, mood=2.5, acoustic=0.5,
                          mood_tags=1.0, decade=0.25, popularity=0.5,
                          instrumental=0.25, language=0.25),
    "energy-focused": Weights(genre=1.0, energy=4.0, mood=0.5, acoustic=0.25,
                              mood_tags=0.25, decade=0.25, popularity=0.5,
                              instrumental=0.25, language=0.25),
}

DEFAULT_MODE = "balanced"

# Fields load_songs() converts from strings.
INT_FIELDS = ("id", "popularity", "release_decade")
FLOAT_FIELDS = ("energy", "tempo_bpm", "valence", "danceability",
                "acousticness", "instrumentalness")


def _as_tags(value) -> List[str]:
    """Normalize a mood_tags value (pipe-string or list) into a clean list."""
    if isinstance(value, str):
        value = value.split("|")
    return [t.strip() for t in (value or []) if t and t.strip()]


def _score_core(prefs: Dict, song: Dict, weights: Weights) -> Tuple[float, List[str]]:
    """
    Single source of truth for scoring one song (dict) against prefs (dict) using
    a Weights strategy. Rewards CLOSENESS on energy and exact matches elsewhere.
    Returns (score, reasons).
    """
    # Preferences (accept both short keys and UserProfile-style keys).
    genre_pref = prefs.get("genre", prefs.get("favorite_genre"))
    mood_pref = prefs.get("mood", prefs.get("favorite_mood"))
    energy_pref = prefs.get("energy")
    if energy_pref is None:
        energy_pref = prefs.get("target_energy")
    likes_acoustic = prefs.get("likes_acoustic", False)
    desired_tags = _as_tags(prefs.get("mood_tags", prefs.get("desired_mood_tags")))
    decade_pref = prefs.get("decade", prefs.get("favorite_decade"))
    prefers_popular = prefs.get("prefers_popular", False)
    prefers_instrumental = prefs.get("prefers_instrumental", False)
    language_pref = prefs.get("language", prefs.get("language_pref"))

    # Song attributes (defaults keep older/partial data safe).
    s_genre = song.get("genre")
    s_mood = song.get("mood")
    s_energy = song.get("energy", 0.0)
    s_acoustic = song.get("acousticness", 0.0)
    s_tags = _as_tags(song.get("mood_tags"))
    s_decade = song.get("release_decade")
    s_pop = song.get("popularity", 0)
    s_instr = song.get("instrumentalness", 0.0)
    s_language = song.get("language")

    score = 0.0
    reasons: List[str] = []

    # 1. Genre match
    if genre_pref is not None and s_genre == genre_pref and weights.genre:
        score += weights.genre
        reasons.append(f"genre match: {s_genre} (+{weights.genre:.1f})")

    # 2. Energy closeness (rewards being near the target, not high or low)
    if energy_pref is not None and weights.energy:
        gap = abs(energy_pref - s_energy)
        pts = (1 - gap) * weights.energy
        score += pts
        reasons.append(f"energy {s_energy:.2f} vs target {energy_pref:.2f} "
                       f"(gap {gap:.2f} -> +{pts:.2f})")

    # 3. Mood match
    if mood_pref is not None and s_mood == mood_pref and weights.mood:
        score += weights.mood
        reasons.append(f"mood match: {s_mood} (+{weights.mood:.1f})")

    # 4. Acoustic preference
    if likes_acoustic and s_acoustic > ACOUSTIC_THRESHOLD and weights.acoustic:
        score += weights.acoustic
        reasons.append(f"acoustic feel (+{weights.acoustic:.1f})")

    # 5. Detailed mood tags (overlap between wanted tags and the song's tags)
    if desired_tags and s_tags and weights.mood_tags:
        overlap = [t for t in s_tags if t in desired_tags]
        if overlap:
            n = min(len(overlap), 2)     # cap so many tags can't dominate
            pts = n * weights.mood_tags
            score += pts
            reasons.append(f"mood tags: {', '.join(overlap[:2])} (+{pts:.2f})")

    # 6. Release decade match
    if decade_pref is not None and s_decade == decade_pref and weights.decade:
        score += weights.decade
        reasons.append(f"decade match: {s_decade}s (+{weights.decade:.1f})")

    # 7. Popularity (only when the user wants popular songs -> popularity bias)
    if prefers_popular and weights.popularity:
        pts = (s_pop / 100.0) * weights.popularity
        score += pts
        reasons.append(f"popularity {s_pop} (+{pts:.2f})")

    # 8. Instrumental preference
    if prefers_instrumental and s_instr > INSTRUMENTAL_THRESHOLD and weights.instrumental:
        score += weights.instrumental
        reasons.append(f"instrumental (+{weights.instrumental:.1f})")

    # 9. Language match
    if language_pref is not None and s_language == language_pref and weights.language:
        score += weights.language
        reasons.append(f"language: {s_language} (+{weights.language:.1f})")

    return score, reasons


def _resolve_weights(mode: str) -> Weights:
    """Look up a scoring strategy by name, defaulting to balanced."""
    return SCORING_MODES.get(mode, SCORING_MODES[DEFAULT_MODE])


@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py. New advanced features have defaults
    so existing code (and tests) that build a Song with the core fields still work.
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
    # --- advanced features (Challenge 1) ---
    popularity: int = 50
    release_decade: int = 2020
    instrumentalness: float = 0.0
    language: str = "english"
    mood_tags: str = ""             # pipe-separated, e.g. "calm|study"


@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py. Advanced preferences are optional.
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    # --- advanced preferences (Challenge 1) ---
    desired_mood_tags: List[str] = field(default_factory=list)
    favorite_decade: Optional[int] = None
    prefers_popular: bool = False
    prefers_instrumental: bool = False
    language_pref: Optional[str] = None


def _song_to_dict(song: Song) -> Dict:
    """Convert a Song dataclass into the dict shape _score_core expects."""
    return {
        "genre": song.genre, "mood": song.mood, "energy": song.energy,
        "acousticness": song.acousticness, "mood_tags": song.mood_tags,
        "release_decade": song.release_decade, "popularity": song.popularity,
        "instrumentalness": song.instrumentalness, "language": song.language,
        "artist": song.artist,
    }


def _profile_to_prefs(user: UserProfile) -> Dict:
    """Convert a UserProfile dataclass into the prefs dict _score_core expects."""
    return {
        "favorite_genre": user.favorite_genre, "favorite_mood": user.favorite_mood,
        "target_energy": user.target_energy, "likes_acoustic": user.likes_acoustic,
        "desired_mood_tags": user.desired_mood_tags,
        "favorite_decade": user.favorite_decade,
        "prefers_popular": user.prefers_popular,
        "prefers_instrumental": user.prefers_instrumental,
        "language_pref": user.language_pref,
    }


class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def _score(self, user: UserProfile, song: Song,
               mode: str = DEFAULT_MODE) -> Tuple[float, List[str]]:
        """Score one Song against a UserProfile; returns (score, reasons)."""
        return _score_core(_profile_to_prefs(user), _song_to_dict(song),
                           _resolve_weights(mode))

    def recommend(self, user: UserProfile, k: int = 5,
                  mode: str = DEFAULT_MODE) -> List[Song]:
        """Return the top-k Songs for a user, ranked highest score first."""
        # Scoring Rule: score every song; Ranking Rule: sort desc, keep top k.
        scored = [(song, self._score(user, song, mode)[0]) for song in self.songs]
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return [song for song, _s in scored[:k]]

    def explain_recommendation(self, user: UserProfile, song: Song,
                               mode: str = DEFAULT_MODE) -> str:
        """Return a human-readable string of the song's score and reasons."""
        score, reasons = self._score(user, song, mode)
        if reasons:
            return f"Score {score:.2f} — " + "; ".join(reasons)
        return f"Score {score:.2f} — included by ranking, but no strong feature matches"


def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file into a list of dicts, converting numeric columns
    to numbers and splitting mood_tags into a list.
    Required by src/main.py
    """
    songs: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            for field_name in INT_FIELDS:
                if field_name in row and row[field_name] != "":
                    row[field_name] = int(row[field_name])
            for field_name in FLOAT_FIELDS:
                if field_name in row and row[field_name] != "":
                    row[field_name] = float(row[field_name])
            if "mood_tags" in row:
                row["mood_tags"] = _as_tags(row["mood_tags"])
            songs.append(row)
    return songs


def score_song(user_prefs: Dict, song: Dict,
               mode: str = DEFAULT_MODE) -> Tuple[float, List[str]]:
    """
    Scores a single song (dict) against user preferences (dict) using the chosen
    scoring mode. Accepts short keys (genre/mood/energy) or UserProfile-style keys.
    Returns (score, reasons).
    """
    return _score_core(user_prefs, song, _resolve_weights(mode))


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5,
                    mode: str = DEFAULT_MODE, diversity: bool = False,
                    diversity_penalty: float = 1.0) -> List[Tuple[Dict, float, str]]:
    """
    Functional recommendation: score every song (Scoring Rule) then rank (Ranking
    Rule). With diversity=True, greedily re-ranks so repeated artists/genres in the
    top-k are penalized (Challenge 3). Returns (song_dict, score, explanation).
    Required by src/main.py
    """
    scored = [(song, *score_song(user_prefs, song, mode)) for song in songs]

    if not diversity:
        ranked = sorted(scored, key=lambda item: item[1], reverse=True)
        return [(s, sc, _explain(rs)) for s, sc, rs in ranked[:k]]

    return _diverse_rank(scored, k, diversity_penalty)


def _explain(reasons: List[str]) -> str:
    """Join reasons into one explanation string."""
    return "; ".join(reasons) if reasons else "no strong feature matches"


def _diverse_rank(scored: List[Tuple[Dict, float, List[str]]], k: int,
                  penalty: float) -> List[Tuple[Dict, float, str]]:
    """
    Greedy re-ranking: repeatedly pick the highest-scoring song after subtracting a
    penalty for each already-selected song sharing its artist (full penalty) or
    genre (half penalty). Keeps the top results varied instead of one-artist-heavy.
    """
    pool = [[s, sc, list(rs)] for s, sc, rs in scored]
    selected: List[Tuple[Dict, float, str]] = []
    seen_artists: Dict[str, int] = {}
    seen_genres: Dict[str, int] = {}

    while pool and len(selected) < k:
        best_item = None
        best_adj = None
        best_pen = 0.0
        for item in pool:
            song, base, _reasons = item
            pen = penalty * seen_artists.get(song.get("artist"), 0) \
                + 0.5 * penalty * seen_genres.get(song.get("genre"), 0)
            adj = base - pen
            if best_adj is None or adj > best_adj:
                best_item, best_adj, best_pen = item, adj, pen

        pool.remove(best_item)
        song, base, reasons = best_item
        if best_pen > 0:
            reasons.append(f"diversity penalty (-{best_pen:.2f})")
        selected.append((song, best_adj, _explain(reasons)))
        seen_artists[song.get("artist")] = seen_artists.get(song.get("artist"), 0) + 1
        seen_genres[song.get("genre")] = seen_genres.get(song.get("genre"), 0) + 1

    return selected
