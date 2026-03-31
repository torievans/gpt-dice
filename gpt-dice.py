import streamlit as st
import pandas as pd
import json
import os
import random
from collections import Counter

# =========================================================
# 1. SCORE ENGINE
# =========================================================
def calculate_score(dice, category):
    dice = sorted(dice)
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


def score_category(cat, vals):
    vals = sorted(vals)

    if len(vals) != 5:
        return ""

    if cat == "Low Straight":
        return "👌" if vals == [1, 2, 3, 4, 5] else "25"

    if cat == "High Straight":
        return "👌" if vals == [2, 3, 4, 5, 6] else "30"

    if cat == "5 of a Kind":
        return "👌" if len(set(vals)) == 1 else "30"

    if cat == "Full House":
        counts = sorted(Counter(vals).values(), reverse=True)
        if counts == [3, 2] or counts == [5]:
            return calculate_score(vals, cat)
        return "28"

    return calculate_score(vals, cat)


def render_dice_face(value, selected=False):
    pip_map = {
        0: [],
        1: [5],
        2: [1, 9],
        3: [1, 5, 9],
        4: [1, 3, 7, 9],
        5: [1, 3, 5, 7, 9],
        6: [1, 3, 4, 6, 7, 9],
    }

    selected_class = " selected" if selected else ""
    html = f'<div class="dice-tile{selected_class}">'
    for pos in pip_map.get(value, []):
        html += f'<div class="pip dice-slot-{pos}"></div>'
    html += "</div>"
    return html


# =========================================================
# 2. CONFIG & DATA
# =========================================================
st.set_page_config(page_title="Double Cameroon", layout="wide")
DB_FILE = "cameroon_stats.json"


def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {"Players": {}}
    return {"Players": {}}


def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)


stats = load_data()

# =========================================================
# 3. UI STYLES
# =========================================================
st.markdown("""
<style>
.dice-tile {
    width: 80px;
    height: 80px;
    border: 3px solid #111;
    border-radius: 12px;
    background: white;
    display: grid;
    grid-template-columns: repeat(3,1fr);
    grid-template-rows: repeat(3,1fr);
    padding: 6px;
    margin: 0 auto 6px auto;
}

.dice-tile.selected {
    background: #ff4b4b;
    border-color: #ff4b4b;
}

.pip {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: black;
    align-self: center;
    justify-self: center;
}

.dice-tile.selected .pip {
    background: white;
}

.dice-slot-1 { grid-column: 1; grid-row: 1; }
.dice-slot-2 { grid-column: 2; grid-row: 1; }
.dice-slot-3 { grid-column: 3; grid-row: 1; }
.dice-slot-4 { grid-column: 1; grid-row: 2; }
.dice-slot-5 { grid-column: 2; grid-row: 2; }
.dice-slot-6 { grid-column: 3; grid-row: 2; }
.dice-slot-7 { grid-column: 1; grid-row: 3; }
.dice-slot-8 { grid-column: 2; grid-row: 3; }
.dice-slot-9 { grid-column: 3; grid-row: 3; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# 4. SESSION STATE
# =========================================================
defaults = {
    "game_active": False,
    "game_over": False,
    "dice": [0] * 10,
    "selected": [],
    "rolls_left": 3,
    "current_player_idx": 0,
    "used_categories": {},
    "players": [],
    "master_scores": None,
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =========================================================
# 5. SETUP
# =========================================================
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

# =========================================================
# 6. GAMEPLAY
# =========================================================
if st.session_state.game_active:
    player = st.session_state.players[st.session_state.current_player_idx]
    st.header(f"{player}'s turn")

    if st.button("🎲 ROLL DICE", use_container_width=True):
        for i in range(10):
            if i not in st.session_state.selected:
                st.session_state.dice[i] = random.randint(1, 6)
        st.session_state.rolls_left -= 1
        st.rerun()

    st.write(f"Rolls left: {st.session_state.rolls_left}")

    st.markdown("### 🎲 Your Dice")

    cols = st.columns(10)

    for i, col in enumerate(cols):
        val = st.session_state.dice[i]
        selected = i in st.session_state.selected

        with col:
            st.markdown(render_dice_face(val, selected), unsafe_allow_html=True)

            if st.button(
                "✓" if selected else "Select",
                key=f"d{i}",
                use_container_width=True
            ):
                if selected:
                    st.session_state.selected.remove(i)
                else:
                    if len(st.session_state.selected) < 5:
                        st.session_state.selected.append(i)
                st.rerun()

# =========================================================
# 7. SCOREBOARD
# =========================================================
if st.session_state.game_active:
    st.subheader("Scores")
    st.dataframe(st.session_state.master_scores)
