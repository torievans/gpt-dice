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


def render_dice_face(value, selected_for=None):
    pip_map = {
        0: [],
        1: [5],
        2: [1, 9],
        3: [1, 5, 9],
        4: [1, 3, 7, 9],
        5: [1, 3, 5, 7, 9],
        6: [1, 3, 4, 6, 7, 9],
    }

    css_class = "dice-tile"
    if selected_for == "A":
        css_class += " selected-a"
    elif selected_for == "B":
        css_class += " selected-b"

    html = f'<div class="{css_class}">'
    for pos in pip_map.get(value, []):
        html += f'<div class="pip dice-slot-{pos}"></div>'
    html += "</div>"
    return html


def get_categories():
    return [
        "1s",
        "2s",
        "3s",
        "4s",
        "5s",
        "6s",
        "Full House",
        "Low Straight",
        "High Straight",
        "5 of a Kind",
    ]


def get_available_categories(player):
    return [c for c in get_categories() if c not in st.session_state.used_categories[player]]


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

.dice-tile.selected-a {
    background: #ff4b4b;
    border-color: #ff4b4b;
}

.dice-tile.selected-b {
    background: #1f77b4;
    border-color: #1f77b4;
}

.pip {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: black;
    align-self: center;
    justify-self: center;
}

.dice-tile.selected-a .pip,
.dice-tile.selected-b .pip {
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

.summary-title {
    font-weight: 700;
    font-size: 18px;
    margin-bottom: 6px;
}

/* A buttons */
div[data-testid="stButton"] > button[kind="primary"] {
    background-color: #ff4b4b;
    border-color: #ff4b4b;
    color: white;
}

/* B buttons when selected */
div[data-testid="stButton"] > button[kind="secondary"].selected-b-button {
    background-color: #1f77b4 !important;
    border-color: #1f77b4 !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 4. SESSION STATE
# =========================================================
defaults = {
    "game_active": False,
    "game_over": False,
    "dice": [0] * 10,
    "rolls_left": 3,
    "current_player_idx": 0,
    "used_categories": {},
    "players": [],
    "master_scores": None,
    "trick_a_indices": [],
    "trick_b_indices": [],
    "trick_a_category": "",
    "trick_b_category": "",
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =========================================================
# 5. SETUP
# =========================================================
if not st.session_state.game_active and not st.session_state.game_over:
    st.title("Start Game")

    players = st.multiselect("Select players", list(stats["Players"].keys()))
    new_player = st.text_input("Add new player")

    if st.button("Add Player") and new_player.strip():
        new_name = new_player.strip()
        if new_name not in stats["Players"]:
            stats["Players"][new_name] = {}
            save_data(stats)
            st.rerun()

    if st.button("Start") and players:
        st.session_state.players = players
        st.session_state.master_scores = pd.DataFrame(
            "",
            index=get_categories(),
            columns=players
        )
        st.session_state.used_categories = {p: [] for p in players}
        st.session_state.game_active = True
        st.session_state.game_over = False
        st.session_state.dice = [0] * 10
        st.session_state.rolls_left = 3
        st.session_state.current_player_idx = 0
        st.session_state.trick_a_indices = []
        st.session_state.trick_b_indices = []
        st.session_state.trick_a_category = ""
        st.session_state.trick_b_category = ""
        st.rerun()

# =========================================================
# 6. GAMEPLAY
# =========================================================
if st.session_state.game_active and not st.session_state.game_over:
    player = st.session_state.players[st.session_state.current_player_idx]
    st.header(f"{player}'s turn")

    # =====================================================
    # 6A. ROLL BUTTON
    # =====================================================
    locked_indices = st.session_state.trick_a_indices + st.session_state.trick_b_indices

    if st.button(
        "🎲 ROLL DICE",
        use_container_width=True,
        type="primary",
        disabled=st.session_state.rolls_left <= 0
    ):
        for i in range(10):
            if i not in locked_indices:
                st.session_state.dice[i] = random.randint(1, 6)
        st.session_state.rolls_left -= 1
        st.rerun()

    st.write(f"**Rolls left:** {st.session_state.rolls_left}")

       # =====================================================
    # 6B. DICE DISPLAY
    # =====================================================
    st.markdown("### 🎲 Your Dice")

    cols = st.columns(10)

    for i, col in enumerate(cols):
        val = st.session_state.dice[i]

        selected_for = None
        if i in st.session_state.trick_a_indices:
            selected_for = "A"
        elif i in st.session_state.trick_b_indices:
            selected_for = "B"

        with col:
            st.markdown(render_dice_face(val, selected_for), unsafe_allow_html=True)

            subcol1, subcol2 = st.columns(2)

            with subcol1:
                if st.button(
                    "A",
                    key=f"a_{i}",
                    use_container_width=True,
                    type="primary" if selected_for == "A" else "secondary",
                    disabled=(
                        (selected_for != "A" and len(st.session_state.trick_a_indices) >= 5)
                        or val == 0
                    ),
                ):
                    if i in st.session_state.trick_a_indices:
                        st.session_state.trick_a_indices.remove(i)
                    else:
                        if i in st.session_state.trick_b_indices:
                            st.session_state.trick_b_indices.remove(i)
                        st.session_state.trick_a_indices.append(i)

                    if len(st.session_state.trick_a_indices) < 5:
                        st.session_state.trick_a_category = ""
                    st.rerun()

            with subcol2:
                b_label = "🔵 B" if selected_for == "B" else "B"

                if st.button(
                    b_label,
                    key=f"b_{i}",
                    use_container_width=True,
                    type="primary" if selected_for == "B" else "secondary",
                    disabled=(
                        (selected_for != "B" and len(st.session_state.trick_b_indices) >= 5)
                        or val == 0
                    ),
                ):
                    if i in st.session_state.trick_b_indices:
                        st.session_state.trick_b_indices.remove(i)
                    else:
                        if i in st.session_state.trick_a_indices:
                            st.session_state.trick_a_indices.remove(i)
                        st.session_state.trick_b_indices.append(i)

                    if len(st.session_state.trick_b_indices) < 5:
                        st.session_state.trick_b_category = ""
                    st.rerun()
                    
           # =====================================================
    # 6C. SELECTION SUMMARY
    # =====================================================
    trick_a_vals = sorted([st.session_state.dice[i] for i in st.session_state.trick_a_indices])
    trick_b_vals = sorted([st.session_state.dice[i] for i in st.session_state.trick_b_indices])

    summary_col1, summary_col2 = st.columns(2)

    with summary_col1:
        st.markdown('<div class="summary-title">🔴 Trick A</div>', unsafe_allow_html=True)
        st.write(f"Selected: {len(trick_a_vals)}/5")
        st.write(f"Dice: {trick_a_vals if trick_a_vals else []}")

        available_a = get_available_categories(player)
        selected_b_current = st.session_state.trick_b_category

        if len(trick_a_vals) == 5:
            a_options = [""] + [c for c in available_a if c != selected_b_current]
            current_a = (
                st.session_state.trick_a_category
                if st.session_state.trick_a_category in a_options
                else ""
            )

            st.session_state.trick_a_category = st.selectbox(
                "Choose category for Trick A",
                a_options,
                index=a_options.index(current_a) if current_a in a_options else 0,
                key="trick_a_dropdown",
            )
        else:
            st.caption("Select 5 dice for Trick A to choose a category.")

    with summary_col2:
        st.markdown('<div class="summary-title">🔵 Trick B</div>', unsafe_allow_html=True)
        st.write(f"Selected: {len(trick_b_vals)}/5")
        st.write(f"Dice: {trick_b_vals if trick_b_vals else []}")

        available_b = get_available_categories(player)
        selected_a_current = st.session_state.trick_a_category

        if len(trick_b_vals) == 5:
            b_options = [""] + [c for c in available_b if c != selected_a_current]
            current_b = (
                st.session_state.trick_b_category
                if st.session_state.trick_b_category in b_options
                else ""
            )

            st.session_state.trick_b_category = st.selectbox(
                "Choose category for Trick B",
                b_options,
                index=b_options.index(current_b) if current_b in b_options else 0,
                key="trick_b_dropdown",
            )
        else:
            st.caption("Select 5 dice for Trick B to choose a category.")

    # =====================================================
    # 6D. CONFIRM TURN
    # =====================================================
    ready_to_confirm = (
        len(trick_a_vals) == 5
        and len(trick_b_vals) == 5
        and st.session_state.trick_a_category != ""
        and st.session_state.trick_b_category != ""
        and st.session_state.trick_a_category != st.session_state.trick_b_category
    )

    if not ready_to_confirm:
        if len(trick_a_vals) < 5 or len(trick_b_vals) < 5:
            st.info("Choose 5 dice for Trick A and 5 dice for Trick B.")
        else:
            st.info("Choose a different category for each trick before confirming.")

    if st.button(
        "Confirm Turn",
        type="primary",
        use_container_width=True,
        disabled=not ready_to_confirm
    ):
        cat_a = st.session_state.trick_a_category
        cat_b = st.session_state.trick_b_category

        st.session_state.master_scores.at[cat_a, player] = score_category(cat_a, trick_a_vals)
        st.session_state.master_scores.at[cat_b, player] = score_category(cat_b, trick_b_vals)

        st.session_state.used_categories[player] += [cat_a, cat_b]
        st.session_state.dice = [0] * 10
        st.session_state.rolls_left = 3
        st.session_state.trick_a_indices = []
        st.session_state.trick_b_indices = []
        st.session_state.trick_a_category = ""
        st.session_state.trick_b_category = ""

        st.session_state.current_player_idx = (
            st.session_state.current_player_idx + 1
        ) % len(st.session_state.players)

        st.rerun()

# =========================================================
# 7. SCOREBOARD
# =========================================================
if st.session_state.game_active or st.session_state.game_over:
    st.subheader("Scores")

    totals = {
        p: st.session_state.master_scores[p].apply(
            lambda x: int(x) if str(x).isdigit() else 0
        ).sum()
        for p in st.session_state.players
    }

    if totals:
        score_cols = st.columns(len(st.session_state.players))
        lowest = min(totals.values())

        for idx, p in enumerate(st.session_state.players):
            with score_cols[idx]:
                st.metric(
                    label=f"{p}'s Score",
                    value=totals[p],
                    delta="Leading" if totals[p] == lowest else None
                )

    st.dataframe(st.session_state.master_scores, use_container_width=True)

# =========================================================
# 8. GAME OVER CHECK
# =========================================================
if st.session_state.game_active and st.session_state.players:
    all_finished = all(
        len(st.session_state.used_categories.get(p, [])) >= 10
        for p in st.session_state.players
    )

    if all_finished:
        st.session_state.game_active = False
        st.session_state.game_over = True
        st.rerun()

# =========================================================
# 9. WINNER SCREEN
# =========================================================
if st.session_state.game_over and st.session_state.players:
    totals = {
        p: st.session_state.master_scores[p].apply(
            lambda x: int(x) if str(x).isdigit() else 0
        ).sum()
        for p in st.session_state.players
    }

    winner_name = min(totals, key=totals.get)
    winner_score = totals[winner_name]

    st.success(f"🏆 Winner: {winner_name} with {winner_score} penalty points")

    if st.button("Play Again", type="primary", use_container_width=True):
        st.session_state.game_active = False
        st.session_state.game_over = False
        st.session_state.dice = [0] * 10
        st.session_state.rolls_left = 3
        st.session_state.current_player_idx = 0
        st.session_state.used_categories = {}
        st.session_state.players = []
        st.session_state.master_scores = None
        st.session_state.trick_a_indices = []
        st.session_state.trick_b_indices = []
        st.session_state.trick_a_category = ""
        st.session_state.trick_b_category = ""
        st.rerun()
