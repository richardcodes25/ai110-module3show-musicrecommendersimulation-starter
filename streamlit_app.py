"""
Web UI for the Music Recommender Simulation.

Run it from the project root with:

    streamlit run streamlit_app.py

The user fills in their taste (genre, mood, energy, and advanced options) in the
sidebar, and the app shows a ranked list of song suggestions with the reasons for
each pick. All the recommendation logic is reused from src/recommender.py.
"""

import streamlit as st

from src.recommender import load_songs, recommend_songs, SCORING_MODES

CSV_PATH = "data/songs.csv"
ANY = "Any"


# --- pure helpers (no Streamlit calls, so they can be unit-tested) -----------

def catalog_options(songs):
    """Collect the distinct genres, moods, decades, languages, and mood tags."""
    genres = sorted({s["genre"] for s in songs})
    moods = sorted({s["mood"] for s in songs})
    decades = sorted({s["release_decade"] for s in songs})
    languages = sorted({s["language"] for s in songs})
    tags = sorted({t for s in songs for t in s.get("mood_tags", [])})
    return genres, moods, decades, languages, tags


def build_prefs(genre, mood, energy, likes_acoustic, prefers_instrumental,
                prefers_popular, decade, language, tags):
    """Turn the UI selections into the prefs dict recommend_songs expects.

    'Any' selections are omitted so that feature simply isn't scored.
    """
    prefs = {"energy": energy, "likes_acoustic": likes_acoustic,
             "prefers_instrumental": prefers_instrumental,
             "prefers_popular": prefers_popular}
    if genre != ANY:
        prefs["genre"] = genre
    if mood != ANY:
        prefs["mood"] = mood
    if decade != ANY:
        prefs["favorite_decade"] = int(decade)
    if language != ANY:
        prefs["language"] = language
    if tags:
        prefs["desired_mood_tags"] = tags
    return prefs


# --- the UI ------------------------------------------------------------------

def render():
    st.set_page_config(page_title="VibeFinder", page_icon="🎵", layout="wide")
    st.title("🎵 VibeFinder — Music Recommender")
    st.caption("Tell us your taste and we'll rank the catalog for you.")

    songs = load_songs(CSV_PATH)
    genres, moods, decades, languages, tags = catalog_options(songs)

    with st.sidebar:
        st.header("Your taste")
        genre = st.selectbox("Favorite genre", [ANY] + genres)
        mood = st.selectbox("Favorite mood", [ANY] + moods)
        energy = st.slider("Target energy", 0.0, 1.0, 0.5, 0.05,
                           help="0 = calm, 1 = high energy. We reward songs close to this.")

        st.subheader("Advanced")
        tag_choices = st.multiselect("Desired mood tags", tags)
        decade = st.selectbox("Favorite decade", [ANY] + [str(d) for d in decades])
        language = st.selectbox("Language", [ANY] + languages)
        likes_acoustic = st.checkbox("Prefer acoustic")
        prefers_instrumental = st.checkbox("Prefer instrumental")
        prefers_popular = st.checkbox("Prefer popular songs")

        st.header("How to rank")
        mode = st.selectbox("Scoring mode", list(SCORING_MODES),
                            help="Changes which features matter most.")
        diversity = st.checkbox("Diversity penalty",
                                help="Avoid repeating the same artist/genre in the results.")
        penalty = st.slider("Penalty strength", 0.0, 3.0, 1.5, 0.5,
                            disabled=not diversity)
        k = st.slider("How many songs?", 1, 10, 5)

    prefs = build_prefs(genre, mood, energy, likes_acoustic, prefers_instrumental,
                        prefers_popular, decade, language, tag_choices)

    recs = recommend_songs(prefs, songs, k=k, mode=mode,
                           diversity=diversity, diversity_penalty=penalty)

    st.subheader(f"Top {len(recs)} recommendations")
    st.write(f"**Mode:** `{mode}`  •  **Diversity:** {'on' if diversity else 'off'}")

    if not recs:
        st.info("No songs to show — try widening your preferences.")
        return

    table = [
        {"#": i, "Title": s["title"], "Artist": s["artist"],
         "Genre": s["genre"], "Mood": s["mood"], "Score": round(score, 2)}
        for i, (s, score, _why) in enumerate(recs, start=1)
    ]
    st.dataframe(table, use_container_width=True, hide_index=True)

    st.subheader("Why these picks?")
    for i, (s, score, why) in enumerate(recs, start=1):
        with st.expander(f"{i}. {s['title']} — {s['artist']}  (score {score:.2f})"):
            st.write(why)

    with st.expander("See your preference profile (what we sent to the recommender)"):
        st.json(prefs)


if __name__ == "__main__":
    render()
