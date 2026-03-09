"""
Generate the wavelength.sqlite database for the SQL for Data Engineering module.
A music streaming startup database with artists, albums, tracks, users, and listening history.
"""

import sqlite3
import random
import os
from datetime import datetime, timedelta

random.seed(42)

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "wavelength.sqlite")

# Remove existing database if present
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# --- Schema ---
cur.executescript("""
CREATE TABLE artists (
    artist_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    genre TEXT,
    country TEXT,
    formed_year INTEGER
);

CREATE TABLE albums (
    album_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    artist_id INTEGER REFERENCES artists(artist_id),
    release_year INTEGER,
    label TEXT
);

CREATE TABLE tracks (
    track_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    album_id INTEGER REFERENCES albums(album_id),
    artist_id INTEGER REFERENCES artists(artist_id),
    duration_seconds INTEGER,
    genre TEXT,
    play_count INTEGER
);

CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    email TEXT,
    country TEXT,
    signup_date TEXT,
    subscription_type TEXT
);

CREATE TABLE listens (
    listen_id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    track_id INTEGER REFERENCES tracks(track_id),
    listened_at TEXT,
    duration_seconds INTEGER
);

CREATE TABLE playlists (
    playlist_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    user_id INTEGER REFERENCES users(user_id),
    created_at TEXT
);

CREATE TABLE playlist_tracks (
    playlist_id INTEGER REFERENCES playlists(playlist_id),
    track_id INTEGER REFERENCES tracks(track_id),
    position INTEGER
);
""")

# --- Artists (50+) ---
# Some artists will have no albums (for LEFT JOIN exercises)
artists_data = [
    # Rock
    ("The Midnight Voltage", "rock", "UK", 1998),
    ("Broken Compass", "rock", "US", 2003),
    ("Velvet Thunderstorm", "rock", "UK", 1995),
    ("Iron Meadow", "rock", "US", 2010),
    ("The Glass Hammers", "rock", "Australia", 2007),
    ("Crimson Tide", "rock", "Canada", 2001),
    ("Echo Chamber", "rock", "UK", 2015),
    ("Rust and Gold", "rock", "US", 1999),
    # Pop
    ("Luna Park", "pop", "UK", 2012),
    ("Stellar Drift", "pop", "US", 2016),
    ("Neon Hearts", "pop", "Sweden", 2018),
    ("Paper Lanterns", "pop", "Japan", 2014),
    ("Silver Lining", "pop", "UK", 2020),
    ("The Daydreamers", "pop", "US", 2011),
    ("Cherry Blossom", "pop", "South Korea", 2019),
    ("Moth and Flame", "pop", "Ireland", 2017),
    # Electronic
    ("Circuit Breaker", "electronic", "Germany", 2008),
    ("Binary Sunset", "electronic", "Netherlands", 2013),
    ("Neon Pulse", "electronic", "UK", 2016),
    ("Waveform", "electronic", "France", 2010),
    ("The Algorithm", "electronic", "Sweden", 2019),
    ("Pixel Dreams", "electronic", "Japan", 2015),
    ("Voltage Drop", "electronic", "US", 2021),
    ("Deep Frequency", "electronic", "Germany", 2006),
    # Hip-hop
    ("Lyric Storm", "hip-hop", "US", 2009),
    ("Concrete Poets", "hip-hop", "UK", 2014),
    ("Mic Check", "hip-hop", "US", 2017),
    ("Beats and Prose", "hip-hop", "Canada", 2012),
    ("The Wordsmiths", "hip-hop", "UK", 2020),
    ("Flow State", "hip-hop", "US", 2016),
    ("Urban Canvas", "hip-hop", "France", 2018),
    ("Rhythm Section", "hip-hop", "US", 2011),
    # Jazz
    ("Blue Note Collective", "jazz", "US", 1985),
    ("The Swing Set", "jazz", "US", 1992),
    ("Midnight Sax", "jazz", "UK", 2000),
    ("Ivory Tower Trio", "jazz", "Japan", 2005),
    ("Smooth Operator", "jazz", "US", 2010),
    ("The Improvists", "jazz", "France", 2008),
    ("Velvet Keys", "jazz", "US", 2015),
    ("Brass Horizon", "jazz", "South Africa", 2012),
    # Classical
    ("Aurora Strings", "classical", "Austria", 1990),
    ("The Philharmonic Project", "classical", "Germany", 1988),
    ("Chamber Echoes", "classical", "UK", 2002),
    ("Nordic Symphony", "classical", "Finland", 1995),
    ("Piano Noir", "classical", "France", 2010),
    ("Cello Landscapes", "classical", "Italy", 2008),
    # No-album artists (for LEFT JOIN exercises)
    ("Ghost Frequency", "electronic", "UK", 2023),
    ("Unnamed Roads", "rock", "US", 2024),
    ("Silent Orchestra", "classical", "Austria", 2023),
    ("The Echoes", "pop", "UK", 2024),
]

for i, (name, genre, country, year) in enumerate(artists_data, 1):
    cur.execute("INSERT INTO artists VALUES (?, ?, ?, ?, ?)",
                (i, name, genre, country, year))

num_artists = len(artists_data)
# Artists with no albums: last 4 (IDs 47-50)
artists_with_albums = list(range(1, num_artists - 3))

# --- Albums (~200) ---
labels = [
    "Wavelength Records", "Sonic Press", "Night Owl Music", "Peak Records",
    "Crystal Sound", "Deep Cut Records", "Firefly Audio", "Horizon Music",
    "Tangent Records", "Prism Audio", "Velvet Records", "Atlas Music"
]

album_adjectives = [
    "Electric", "Midnight", "Golden", "Silver", "Broken", "Infinite",
    "Silent", "Burning", "Frozen", "Digital", "Analog", "Hollow",
    "Phantom", "Velvet", "Chrome", "Neon", "Faded", "Vivid",
    "Lost", "Hidden", "Distant", "Ancient", "Modern", "Wild"
]

album_nouns = [
    "Dreams", "Echoes", "Waves", "Roads", "Skies", "Rivers",
    "Mountains", "Horizons", "Signals", "Shadows", "Lights", "Stories",
    "Memories", "Seasons", "Futures", "Bridges", "Gardens", "Cities",
    "Oceans", "Storms", "Whispers", "Heartbeats", "Frequencies", "Visions"
]

album_id = 1
album_artist_map = {}  # album_id -> artist_id

for artist_id in artists_with_albums:
    # Each artist gets 3-6 albums
    n_albums = random.randint(3, 6)
    artist_year = artists_data[artist_id - 1][3]

    for j in range(n_albums):
        title = f"{random.choice(album_adjectives)} {random.choice(album_nouns)}"
        release_year = random.randint(max(artist_year, 2000), 2025)
        label = random.choice(labels)
        cur.execute("INSERT INTO albums VALUES (?, ?, ?, ?, ?)",
                    (album_id, title, artist_id, release_year, label))
        album_artist_map[album_id] = artist_id
        album_id += 1

total_albums = album_id - 1

# --- Tracks (~1000) ---
track_words_a = [
    "Falling", "Running", "Dancing", "Burning", "Breaking", "Waiting",
    "Dreaming", "Floating", "Shining", "Spinning", "Rising", "Fading",
    "Walking", "Breathing", "Crashing", "Glowing", "Howling", "Drifting",
    "Chasing", "Calling", "Wishing", "Losing", "Finding", "Turning"
]

track_words_b = [
    "Stars", "Rain", "Fire", "Light", "Smoke", "Dust", "Glass",
    "Thunder", "Lightning", "Snow", "Waves", "Wind", "Shadow",
    "Sun", "Moon", "Night", "Dawn", "Dusk", "Sky", "Clouds",
    "Stone", "Steel", "Gold", "Silver", "Ice", "Flame"
]

track_words_c = [
    "Home", "Away", "Again", "Forever", "Tonight", "Tomorrow",
    "Yesterday", "Always", "Never", "Slowly", "Quickly", "Softly",
    "Loudly", "Gently", "Brightly", "Darkly"
]

genre_for_artist = {i + 1: artists_data[i][1] for i in range(num_artists)}

track_id = 1
track_data = []

for aid in range(1, total_albums + 1):
    artist_id = album_artist_map[aid]
    genre = genre_for_artist[artist_id]
    n_tracks = random.randint(4, 8)

    for t in range(n_tracks):
        # Generate track title
        pattern = random.choice([
            lambda: f"{random.choice(track_words_a)} {random.choice(track_words_b)}",
            lambda: f"{random.choice(track_words_b)} {random.choice(track_words_c)}",
            lambda: f"The {random.choice(track_words_b)}",
            lambda: f"{random.choice(track_words_a)} {random.choice(track_words_c)}",
            lambda: random.choice(track_words_b),
        ])
        title = pattern()

        duration = random.randint(120, 420)  # 2-7 minutes
        if genre == "classical":
            duration = random.randint(180, 720)  # classical tracks longer

        # ~10% of tracks have NULL play_count
        if random.random() < 0.10:
            play_count = None
        else:
            # Skewed distribution: most tracks modest, a few huge
            play_count = int(random.expovariate(1 / 5000))
            play_count = max(play_count, random.randint(10, 500))

        cur.execute("INSERT INTO tracks VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (track_id, title, aid, artist_id, duration, genre, play_count))
        track_data.append((track_id, artist_id, duration, play_count))
        track_id += 1

total_tracks = track_id - 1
print(f"Generated {total_tracks} tracks across {total_albums} albums for {num_artists} artists")

# --- Users (500) ---
first_names = [
    "Alex", "Jordan", "Sam", "Morgan", "Casey", "Riley", "Taylor", "Jamie",
    "Quinn", "Avery", "Blake", "Cameron", "Drew", "Ellis", "Frankie", "Harper",
    "Hayden", "Jesse", "Kelly", "Lane", "Logan", "Mackenzie", "Nico", "Oakley",
    "Parker", "Reese", "Robin", "Sage", "Skyler", "Sydney", "Tatum", "Val",
    "Rowan", "Emery", "Dakota", "Finley", "Charlie", "Aria", "Kai", "Indigo",
    "Phoenix", "River", "Storm", "Winter", "August", "Eden", "Haven", "Marlowe",
    "Remy", "Wren", "Zephyr", "Ash", "Bay", "Clover", "Echo", "Fern",
    "Glen", "Holly", "Ivy", "Jade", "Kit", "Lark", "Moss", "Onyx"
]

last_names = [
    "Smith", "Jones", "Williams", "Brown", "Taylor", "Davies", "Wilson",
    "Evans", "Thomas", "Johnson", "Roberts", "Walker", "Wright", "Robinson",
    "Thompson", "White", "Hughes", "Edwards", "Green", "Hall", "Lewis",
    "Harris", "Clark", "Patel", "Jackson", "Wood", "Turner", "Martin",
    "Cooper", "Hill", "Ward", "Morris", "Moore", "King", "Watson",
    "Harrison", "Morgan", "Allen", "James", "Scott", "Baker", "Price"
]

countries = ["UK", "US", "Canada", "Australia", "Germany", "France", "Sweden",
             "Japan", "South Korea", "Brazil", "India", "Ireland", "Netherlands"]

for user_id in range(1, 501):
    fname = random.choice(first_names)
    lname = random.choice(last_names)
    username = f"{fname.lower()}{lname.lower()}{random.randint(1, 999)}"
    email = f"{username}@{'gmail.com' if random.random() < 0.5 else 'outlook.com'}"
    country = random.choice(countries)
    # Signup dates spread over 2 years
    signup = datetime(2023, 1, 1) + timedelta(days=random.randint(0, 730))
    sub_type = random.choice(["free", "free", "premium"])  # 2:1 free:premium
    cur.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, username, email, country, signup.strftime("%Y-%m-%d"), sub_type))

# --- Listens (~15,000) ---
# Create varied listen patterns: some heavy users, some light
listen_id = 1
base_date = datetime(2025, 2, 1)  # Spanning February 2025

# Assign user weights (some users listen a lot, some barely)
user_weights = {}
for uid in range(1, 501):
    r = random.random()
    if r < 0.05:
        user_weights[uid] = random.randint(100, 300)  # power users
    elif r < 0.3:
        user_weights[uid] = random.randint(30, 80)    # regular users
    else:
        user_weights[uid] = random.randint(2, 20)     # casual users

# Build track popularity weights
track_popularity = {}
for tid, artist_id, dur, pc in track_data:
    if pc is None:
        track_popularity[tid] = 50
    else:
        track_popularity[tid] = max(pc, 50)

track_ids_list = list(range(1, total_tracks + 1))
track_weights = [track_popularity[t] for t in track_ids_list]

total_listens_target = 15000
listens_generated = 0

for uid in range(1, 501):
    n_listens = user_weights[uid]
    for _ in range(n_listens):
        tid = random.choices(track_ids_list, weights=track_weights, k=1)[0]
        # Random time in the month
        ts = base_date + timedelta(
            days=random.randint(0, 27),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59)
        )
        # Duration listened: usually most of the track, sometimes partial
        track_dur = track_data[tid - 1][2]
        if random.random() < 0.7:
            listen_dur = track_dur  # listened to the whole track
        else:
            listen_dur = random.randint(15, track_dur)  # partial listen

        cur.execute("INSERT INTO listens VALUES (?, ?, ?, ?, ?)",
                    (listen_id, uid, tid, ts.strftime("%Y-%m-%dT%H:%M:%S"), listen_dur))
        listen_id += 1
        listens_generated += 1

        if listens_generated >= total_listens_target:
            break
    if listens_generated >= total_listens_target:
        break

# If we haven't hit target, add more listens from random users
while listens_generated < total_listens_target:
    uid = random.randint(1, 500)
    tid = random.choices(track_ids_list, weights=track_weights, k=1)[0]
    ts = base_date + timedelta(
        days=random.randint(0, 27),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59)
    )
    track_dur = track_data[tid - 1][2]
    listen_dur = track_dur if random.random() < 0.7 else random.randint(15, track_dur)
    cur.execute("INSERT INTO listens VALUES (?, ?, ?, ?, ?)",
                (listen_id, uid, tid, ts.strftime("%Y-%m-%dT%H:%M:%S"), listen_dur))
    listen_id += 1
    listens_generated += 1

print(f"Generated {listens_generated} listens")

# --- Playlists (100) ---
playlist_names = [
    "Morning Vibes", "Late Night Grooves", "Workout Mix", "Focus Flow",
    "Road Trip", "Sunday Morning", "Party Starter", "Chill Out",
    "Deep Cuts", "New Discoveries", "Throwback Thursday", "Rainy Day",
    "Summer Anthems", "Winter Warmers", "Indie Gems", "Jazz & Coffee",
    "Electronic Escape", "Hip-Hop Heads", "Rock Classics", "Pop Perfection",
    "Study Session", "Cooking Tunes", "Walk the Dog", "Weekend Wind Down",
    "Gym Beats", "After Hours", "Commuter Playlist", "Dinner Party",
    "Festival Favourites", "Bedroom Pop", "Lo-Fi Beats", "High Energy",
    "Melancholy Monday", "Feel Good Friday", "Acoustic Sessions",
    "Bass Heavy", "Guitar Heroes", "Piano Moods", "Synth Wave",
    "Old School", "Fresh Finds", "Top Tracks", "Hidden Gems",
    "Dance Floor", "Sunset Sounds", "Midnight Oil", "Early Bird",
    "Office Hours", "Happy Hour", "Night Drive"
]

for pid in range(1, 101):
    uid = random.randint(1, 500)
    name = random.choice(playlist_names) + (f" {random.randint(1, 9)}" if random.random() < 0.3 else "")
    created = base_date + timedelta(days=random.randint(0, 27))
    cur.execute("INSERT INTO playlists VALUES (?, ?, ?, ?)",
                (pid, name, uid, created.strftime("%Y-%m-%d")))

    # Add 5-25 tracks per playlist
    n_playlist_tracks = random.randint(5, 25)
    chosen_tracks = random.sample(range(1, total_tracks + 1), min(n_playlist_tracks, total_tracks))
    for pos, tid in enumerate(chosen_tracks, 1):
        cur.execute("INSERT INTO playlist_tracks VALUES (?, ?, ?)",
                    (pid, tid, pos))

conn.commit()

# Verify counts
for table in ["artists", "albums", "tracks", "users", "listens", "playlists", "playlist_tracks"]:
    count = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"  {table}: {count} rows")

# Check NULLs in play_count
null_count = cur.execute("SELECT COUNT(*) FROM tracks WHERE play_count IS NULL").fetchone()[0]
print(f"  tracks with NULL play_count: {null_count}")

# Check artists without albums
no_album = cur.execute("""
    SELECT COUNT(*) FROM artists a
    LEFT JOIN albums al ON a.artist_id = al.artist_id
    WHERE al.album_id IS NULL
""").fetchone()[0]
print(f"  artists with no albums: {no_album}")

conn.close()
print(f"\nDatabase written to {DB_PATH}")
