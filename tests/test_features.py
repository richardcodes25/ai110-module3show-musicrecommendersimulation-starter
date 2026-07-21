"""
Tests for the stretch features: advanced attributes (C1), scoring modes (C2),
diversity penalty (C3), and the Streamlit UI helpers.
"""

import streamlit_app as app
from src.recommender import (
    load_songs,
    score_song,
    recommend_songs,
    SCORING_MODES,
    DEFAULT_MODE,
    _resolve_weights,
)

CSV_PATH = "data/songs.csv"


# --- Challenge 1: advanced features & loading --------------------------------

def test_load_songs_converts_types_and_splits_tags():
    songs = load_songs(CSV_PATH)
    assert len(songs) == 18
    first = songs[0]
    assert isinstance(first["id"], int)
    assert isinstance(first["popularity"], int)
    assert isinstance(first["release_decade"], int)
    assert isinstance(first["energy"], float)
    assert isinstance(first["instrumentalness"], float)
    # mood_tags is split from the pipe-string into a clean list
    assert isinstance(first["mood_tags"], list)
    assert "uplifting" in first["mood_tags"]


def test_mood_tag_overlap_adds_points():
    song = {"genre": "lofi", "mood": "chill", "energy": 0.4,
            "acousticness": 0.8, "mood_tags": ["calm", "study", "focus"]}
    with_tags, reasons = score_song({"desired_mood_tags": ["calm", "study"]}, song)
    without_tags, _ = score_song({}, song)
    assert with_tags > without_tags
    assert any("mood tags" in r for r in reasons)


def test_decade_match_adds_points():
    song = {"genre": "lofi", "mood": "chill", "energy": 0.4,
            "acousticness": 0.8, "release_decade": 2020}
    matched, _ = score_song({"favorite_decade": 2020}, song)
    missed, _ = score_song({"favorite_decade": 1980}, song)
    assert matched > missed


def test_popularity_is_scaled_not_raw():
    # A popularity of 88 must contribute far less than 88 points.
    song = {"genre": "x", "mood": "y", "energy": 0.5,
            "acousticness": 0.1, "popularity": 88}
    score, reasons = score_song({"prefers_popular": True, "energy": 0.5}, song)
    assert score < 5.0
    assert any("popularity" in r for r in reasons)


def test_instrumental_and_language_rules():
    song = {"genre": "lofi", "mood": "chill", "energy": 0.4, "acousticness": 0.8,
            "instrumentalness": 0.9, "language": "instrumental"}
    instr, _ = score_song({"prefers_instrumental": True}, song)
    base, _ = score_song({}, song)
    assert instr > base
    lang, _ = score_song({"language": "instrumental"}, song)
    assert lang > base


# --- Challenge 2: scoring modes (Strategy pattern) ---------------------------

def test_all_modes_registered():
    assert set(SCORING_MODES) == {"balanced", "genre-first",
                                  "mood-first", "energy-focused"}


def test_genre_first_weights_genre_higher_than_balanced():
    assert SCORING_MODES["genre-first"].genre > SCORING_MODES["balanced"].genre


def test_unknown_mode_falls_back_to_default():
    assert _resolve_weights("does-not-exist") is SCORING_MODES[DEFAULT_MODE]


def test_mode_changes_ranking():
    songs = load_songs(CSV_PATH)
    prefs = {"genre": "lofi", "mood": "chill", "energy": 0.95}
    balanced = recommend_songs(prefs, songs, k=1, mode="balanced")[0][0]["title"]
    energy = recommend_songs(prefs, songs, k=1, mode="energy-focused")[0][0]["title"]
    # A conflicting profile ranks differently once energy dominates.
    assert balanced != energy


# --- Challenge 3: diversity penalty ------------------------------------------

def test_diversity_reduces_repeated_artist():
    songs = load_songs(CSV_PATH)
    prefs = {"genre": "lofi", "mood": "chill", "energy": 0.4,
             "likes_acoustic": True}
    plain = recommend_songs(prefs, songs, k=5, mode="balanced")
    diverse = recommend_songs(prefs, songs, k=5, mode="balanced",
                              diversity=True, diversity_penalty=1.5)
    # Diversity should not increase how often the top artist repeats.
    def top_artist_count(recs):
        artists = [s["artist"] for s, _sc, _w in recs]
        return max(artists.count(a) for a in set(artists))
    assert top_artist_count(diverse) <= top_artist_count(plain)


def test_diversity_notes_penalty_in_reasons():
    songs = load_songs(CSV_PATH)
    prefs = {"genre": "lofi", "mood": "chill", "energy": 0.4}
    diverse = recommend_songs(prefs, songs, k=5, mode="balanced",
                              diversity=True, diversity_penalty=1.5)
    assert any("diversity penalty" in why for _s, _sc, why in diverse)


# --- Streamlit UI helpers ----------------------------------------------------

def test_catalog_options():
    songs = load_songs(CSV_PATH)
    genres, moods, decades, languages, tags = app.catalog_options(songs)
    assert "lofi" in genres and "metal" in genres
    assert 2020 in decades
    assert "calm" in tags


def test_build_prefs_omits_any_selections():
    prefs = app.build_prefs(app.ANY, app.ANY, 0.5, False, False, False,
                            app.ANY, app.ANY, [])
    assert "genre" not in prefs and "mood" not in prefs
    assert "favorite_decade" not in prefs and "language" not in prefs
    assert prefs["energy"] == 0.5


def test_build_prefs_includes_real_selections():
    prefs = app.build_prefs("lofi", "chill", 0.4, True, True, True,
                            "2020", "instrumental", ["calm"])
    assert prefs["genre"] == "lofi"
    assert prefs["favorite_decade"] == 2020
    assert prefs["desired_mood_tags"] == ["calm"]
    assert prefs["prefers_popular"] is True
