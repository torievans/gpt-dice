import streamlit as st
import pandas as pd
import json
import os
import random
from collections import Counter

# --- SCORE ENGINE ---
def calculate_score(dice, category):
    dice.sort()
    counts = Counter(dice)
    target_map = {"1s": 1, "2s": 2, "3s": 3, "4s": 4, "5s": 5, "6s": 6}
    
    if category in target_map:
        target = target_map[category]
        score = sum(1 for d in dice if d != target) * target
        return "👌" if score == 0 else str(score)
    
    if category == "Full House":
        sorted_items = sorted(counts.items(), key=lambda x: (x[1], x[0]), reverse=True)
        three_val = sorted_items[0][0]
        two_val = sorted_items[1][0] if len(sorted_items) > 1 else three_val
        score = ((6 - three_val) * 3) + ((5 - two_val) * 2)
        return "👌" if score == 0 else str(score)
    return "0"

# --- CONFIG ---
st.set_page_config(page_title="Double Cameroon")
DB_FILE = "cameroon_stats.json"

def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {"Players": {}}

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

stats = load_data()

# --- SESSION STATE ---
defaults = {
    "game_active": False,
    "game_over": False,
    "dice": [0]*10,
    "selected": [],
    "rolls_left": 3,
    "current_player_idx": 0,
    "used_categories": {}
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# --- SIDEBAR ---
with st.sidebar:
    st.title("🎲 Double Cameroon")
    mode = st.radio("Mode", ["Play Dice", "Score Only"])

# --- SETUP ---
if not st.session_state.game_active:
    st.title("Start Game")

    players = st.multiselect("Select players", list(stats["Players"].keys()))
    new_player = st.text_input("Add new player")

    if st.button("Add Player") and new_player:
        stats["Players"][new_player] = {}
        save_data(stats)
        st.rerun()

    if st.button("Start") and players:
        st.session_state.players = players
        st.session_state.master_scores = pd.DataFrame(
            "",
            index=["1s","2s","3s","4s","5s","6s","Full House","Low Straight","High Straight","5 of a Kind"],
            columns=players
        )
        st.session_state.used_categories = {p: [] for p in players}
        st.session_state.game_active = True
        st.rerun()

# --- GAME ---
if st.session_state.game_active and not st.session_state.game_over:

    player = st.session_state.players[st.session_state.current_player_idx]
    st.header(f"{player}'s turn")

    # --- ROLL ---
    if st.button("🎲 Roll", disabled=st.session_state.rolls_left == 0):
        for i in range(10):
            if i not in st.session_state.selected:
                st.session_state.dice[i] = random.randint(1, 6)
        st.session_state.rolls_left -= 1
        st.rerun()

    st.write(f"Rolls left: {st.session_state.rolls_left}")

    # --- DICE DISPLAY ---
    faces = ["?", "⚀","⚁","⚂","⚃","⚄","⚅"]

    dice_labels = [
        f"{faces[d]} ({i})" for i, d in enumerate(st.session_state.dice)
    ]

    selected = st.multiselect(
        "Select dice for Trick A (first 5)",
        range(10),
        default=st.session_state.selected
    )

    st.session_state.selected = selected

    trickA = [st.session_state.dice[i] for i in selected[:5]]
    trickB = [st.session_state.dice[i] for i in range(10) if i not in selected[:5]]

    st.write("**Trick A:**", sorted(trickA))
    st.write("**Trick B:**", sorted(trickB))

    # --- CATEGORY ---
    categories = ["1s","2s","3s","4s","5s","6s","Full House","Low Straight","High Straight","5 of a Kind"]
    available = [c for c in categories if c not in st.session_state.used_categories[player]]

    col1, col2 = st.columns(2)
    catA = col1.selectbox("Category A", [""] + available)
    catB = col2.selectbox("Category B", [""] + [c for c in available if c != catA])

    # --- CONFIRM ---
    if st.button("Confirm Turn"):

        def score(cat, vals):
            if cat == "Low Straight":
                return "👌" if sorted(vals) == [1,2,3,4,5] else "25"
            if cat == "High Straight":
                return "👌" if sorted(vals) == [2,3,4,5,6] else "30"
            if cat == "5 of a Kind":
                return "👌" if len(set(vals)) == 1 else "30"
            return calculate_score(vals, cat)

        st.session_state.master_scores.at[catA, player] = score(catA, trickA)
        st.session_state.master_scores.at[catB, player] = score(catB, trickB)

        st.session_state.used_categories[player] += [catA, catB]
        st.session_state.selected = []
        st.session_state.rolls_left = 3
        st.session_state.dice = [0]*10

        st.session_state.current_player_idx = (
            st.session_state.current_player_idx + 1
        ) % len(st.session_state.players)

        st.rerun()

# --- SCOREBOARD ---
if st.session_state.game_active:
    st.subheader("Scores")

    totals = {
        p: st.session_state.master_scores[p].apply(
            lambda x: int(x) if str(x).isdigit() else 0
        ).sum()
        for p in st.session_state.players
    }

    for p, score in totals.items():
        st.metric(p, score)

    st.dataframe(st.session_state.master_scores)
