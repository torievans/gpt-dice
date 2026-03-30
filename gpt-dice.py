import streamlit as st
import json
import os
from collections import Counter

# =========================
# 0. SYNC FUNCTION (CRUCIAL)
# =========================
def sync_manual_scores():
    if "main_table" in st.session_state:
        for player, scores in st.session_state.main_table.items():
            if player not in st.session_state.master_scores:
                st.session_state.master_scores[player] = {}
            st.session_state.master_scores[player].update(scores)

# Run sync BEFORE anything else
if "master_scores" not in st.session_state:
    st.session_state.master_scores = {}
if "used_categories" not in st.session_state:
    st.session_state.used_categories = {}
if "player_profiles" not in st.session_state:
    st.session_state.player_profiles = []

sync_manual_scores()

# =========================
# 1. SCORING ENGINE
# =========================
def calculate_score(dice, category):
    counts = Counter(dice)

    if category in ["1s", "2s", "3s", "4s", "5s", "6s"]:
        target = int(category[0])
        count = counts[target]
        return (5 - count) * target

    if category == "Full House":
        if sorted(counts.values()) == [2, 3]:
            triple = max(counts, key=lambda x: counts[x] if counts[x] == 3 else 0)
            pair = max(counts, key=lambda x: counts[x] if counts[x] == 2 else 0)
            return ((6 - triple) * 3) + ((5 - pair) * 2)
        return 28

    if category == "Low Straight":
        return 0 if sorted(dice) == [1,2,3,4,5] else 15

    if category == "High Straight":
        return 0 if sorted(dice) == [2,3,4,5,6] else 20

    if category == "5 of a Kind":
        if len(counts) == 1:
            val = dice[0]
            return (6 - val) * 5
        return 30

    return 0

# =========================
# 2. PLAYER PROFILE STORAGE
# =========================
PROFILE_FILE = "cameroon_stats.json"

def load_profiles():
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "r") as f:
            return json.load(f)
    return []


def save_profiles(profiles):
    with open(PROFILE_FILE, "w") as f:
        json.dump(profiles, f)

# =========================
# 3. UI SETUP
# =========================
st.set_page_config(page_title="Double Cameroon", layout="wide")

st.title("🎲 Double Cameroon Digital Engine & Scorecard")

mode = st.sidebar.selectbox("Select Mode", ["Play Dice", "Score Only"])

# =========================
# 4. PLAYER SETUP
# =========================
profiles = load_profiles()

new_player = st.sidebar.text_input("Add Player")
if st.sidebar.button("Add") and new_player:
    profiles.append(new_player)
    save_profiles(profiles)

players = st.sidebar.multiselect("Select Players", profiles)

for p in players:
    if p not in st.session_state.master_scores:
        st.session_state.master_scores[p] = {}

categories = [
    "1s","2s","3s","4s","5s","6s",
    "Full House","Low Straight","High Straight","5 of a Kind"
]

# =========================
# 5. SCOREBOARD HEADER
# =========================
st.subheader("Score (Lowest Wins!)")

totals = {}
for p in players:
    total = sum(st.session_state.master_scores[p].values())
    totals[p] = total

if totals:
    leader = min(totals, key=totals.get)

cols = st.columns(len(players))
for i, p in enumerate(players):
    score = totals.get(p, 0)
    delta = "⭐ LEADING" if p == leader else ""
    cols[i].metric(p, score, delta)

# =========================
# 6. PLAY MODE
# =========================
if mode == "Play Dice":
    import random

    st.header("Play Dice")

    if "dice" not in st.session_state:
        st.session_state.dice = [random.randint(1,6) for _ in range(10)]
        st.session_state.rolls = 0

    if st.button("Roll Dice") and st.session_state.rolls < 3:
        st.session_state.dice = [random.randint(1,6) for _ in range(10)]
        st.session_state.rolls += 1

    st.write("Rolls used:", st.session_state.rolls)
    st.write("Dice:", st.session_state.dice)

    st.subheader("Assign Dice to Tricks")
    trick_a = st.multiselect("Trick A (5 dice)", st.session_state.dice, max_selections=5)
    trick_b = st.multiselect("Trick B (5 dice)", st.session_state.dice, max_selections=5)

    if len(trick_a) == 5 and len(trick_b) == 5:
        cat_a = st.selectbox("Category for Trick A", categories, key="catA")
        cat_b = st.selectbox("Category for Trick B", categories, key="catB")

        player = st.selectbox("Player", players)

        if st.button("Submit Scores"):
            score_a = calculate_score(trick_a, cat_a)
            score_b = calculate_score(trick_b, cat_b)

            st.session_state.master_scores[player][cat_a] = score_a
            st.session_state.master_scores[player][cat_b] = score_b

            st.success("Scores recorded!")

# =========================
# 7. SCORE ONLY MODE
# =========================
if mode == "Score Only":
    st.header("Manual Score Entry")

    if "main_table" not in st.session_state:
        st.session_state.main_table = {
            p: {c: "" for c in categories} for p in players
        }

    for p in players:
        st.subheader(p)
        for c in categories:
            val = st.text_input(f"{p} - {c}", key=f"{p}_{c}")
            if val:
                try:
                    st.session_state.main_table[p][c] = int(val)
                except:
                    pass

# =========================
# 8. DISPLAY SCORE TABLE
# =========================
st.header("Score Table")

for p in players:
    st.subheader(p)
    for c in categories:
        val = st.session_state.master_scores[p].get(c, "")
        display = "👌" if val == 0 else val
        st.write(f"{c}: {display}")

# =========================
# 9. WIN CONDITION
# =========================
complete = all(
    len(st.session_state.master_scores[p]) == len(categories)
    for p in players
) if players else False

if complete:
    winner = min(totals, key=totals.get)
    st.balloons()
    st.markdown(f"## 🔴 WINNER: {winner} 🔴")
