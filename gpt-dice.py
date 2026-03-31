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
st.markdown(
    """
    <style>
    .stApp {
        max-width: 1400px;
        margin: 0 auto;
    }

    div.stButton > button {
        width: 100%;
        border-radius: 12px !important;
        font-weight: 700 !important;
    }

    .rolls-text {
        font-size: 1.6rem;
        font-weight: 700;
        margin: 0.75rem 0 1.75rem 0;
    }

    .dice-heading {
        font-size: 2rem;
        font-weight: 800;
        margin: 0.5rem 0 1rem 0;
    }

    .dice-wrapper {
        margin-bottom: 0.4rem;
    }

    .dice-tile {
        width: 120px;
        height: 120px;
        border: 4px solid #111111;
        border-radius: 14px;
        background: white;
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        grid-template-rows: 1fr 1fr 1fr;
        padding: 12px;
        box-sizing: border-box;
        margin: 0 auto 10px auto;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    }

    .dice-tile.selected {
        background: #ff4b4b;
        border-color: #ff4b4b;
    }

    .pip {
        width: 18px;
        height: 18px;
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

    .dice-btn button {
        height: 44px !important;
        font-size: 15px !important;
    }

    .trick-box {
        padding: 1rem;
        border: 1px solid rgba(128,128,128,0.25);
        border-radius: 12px;
        margin-top: 0.5rem;
        margin-bottom: 0.75rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

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
    "game_mode": "Play Dice",
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =========================================================
# 5. SIDEBAR
# =========================================================
with st.sidebar:
    st.title("🎲 Double Cameroon")
    st.session_state.game_mode = st.radio(
        "Mode",
        ["Play Dice", "Score Only"],
        index=0 if st.session_state.game_mode == "Play Dice" else 1,
    )

# =========================================================
# 6. GAME SETUP
# =========================================================
if not st.session_state.game_active and not st.session_state.game_over:
    st.title("Start Game")

    left, right = st.columns(2)

    with left:
        st.subheader("Players")
        players = st.multiselect("Select players", list(stats["Players"].keys()))
        new_player = st.text_input("Add new player")

        if st.button("Add Player") and new_player.strip():
            new_name = new_player.strip()
            if new_name not in stats["Players"]:
                stats["Players"][new_name] = {}
                save_data(stats)
                st.rerun()

    with right:
        st.subheader("Start")
        st.write("Choose your players, then start the game.")

        if st.button("Start Game", type="primary", use_container_width=True) and players:
            st.session_state.players = players
            st.session_state.current_player_idx = 0
            st.session_state.used_categories = {p: [] for p in players}
            st.session_state.dice = [0] * 10
            st.session_state.selected = []
            st.session_state.rolls_left = 3
            st.session_state.game_over = False

            st.session_state.master_scores = pd.DataFrame(
                "",
                index=[
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
                ],
                columns=players,
            )

            st.session_state.game_active = True
            st.rerun()

# =========================================================
# 7. GAMEPLAY
# =========================================================
if st.session_state.game_active and not st.session_state.game_over:
    player = st.session_state.players[st.session_state.current_player_idx]
    st.header(f"👤 {player}'s Turn")

    if st.session_state.game_mode == "Play Dice":
        # -------------------------------------------------
        # 7A. ROLL BUTTON
        # -------------------------------------------------
        if st.button(
            "🎲 ROLL DICE",
            use_container_width=True,
            type="primary",
            disabled=st.session_state.rolls_left == 0,
        ):
            for i in range(10):
                if i not in st.session_state.selected:
                    st.session_state.dice[i] = random.randint(1, 6)
            st.session_state.rolls_left -= 1
            st.rerun()

        st.markdown(
            f"<div class='rolls-text'>Rolls left: {st.session_state.rolls_left}</div>",
            unsafe_allow_html=True,
        )

        # -------------------------------------------------
        # 7B. DICE DISPLAY
        # -------------------------------------------------
        st.markdown("<div class='dice-heading'>🎲 Your Dice</div>", unsafe_allow_html=True)

        rows = [list(range(0, 5)), list(range(5, 10))]

        for row in rows:
            cols = st.columns(5)
            for col, i in zip(cols, row):
                val = st.session_state.dice[i]
                is_selected = i in st.session_state.selected

                with col:
                    st.markdown("<div class='dice-wrapper'>", unsafe_allow_html=True)
                    st.markdown(
                        render_dice_face(val, selected=is_selected),
                        unsafe_allow_html=True,
                    )
                    st.markdown("</div>", unsafe_allow_html=True)

                    st.markdown("<div class='dice-btn'>", unsafe_allow_html=True)
                    if st.button(
                        "Selected" if is_selected else "Select",
                        key=f"dice_{i}",
                        use_container_width=True,
                        type="primary" if is_selected else "secondary",
                    ):
                        if i in st.session_state.selected:
                            st.session_state.selected.remove(i)
                        else:
                            if len(st.session_state.selected) < 5:
                                st.session_state.selected.append(i)
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

        # -------------------------------------------------
        # 7C. TRICK PREVIEW
        # -------------------------------------------------
        selected_indices = sorted(st.session_state.selected[:5])
        trickA = sorted([st.session_state.dice[i] for i in selected_indices])
        trickB = sorted([st.session_state.dice[i] for i in range(10) if i not in selected_indices])

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("<div class='trick-box'>", unsafe_allow_html=True)
            st.subheader("Trick A")
            st.write(f"Selected dice: {len(trickA)}/5")
            st.write(trickA if trickA else [])
            st.markdown("</div>", unsafe_allow_html=True)

        with col_b:
            st.markdown("<div class='trick-box'>", unsafe_allow_html=True)
            st.subheader("Trick B")
            st.write(f"Remaining dice: {len(trickB)}/5")
            st.write(trickB if trickB else [])
            st.markdown("</div>", unsafe_allow_html=True)

        # -------------------------------------------------
        # 7D. CATEGORY SELECTION
        # -------------------------------------------------
        categories = [
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
        available = [c for c in categories if c not in st.session_state.used_categories[player]]

        select_col1, select_col2 = st.columns(2)
        with select_col1:
            catA = st.selectbox("Category A", [""] + available, key="cat_a")
        with select_col2:
            catB = st.selectbox(
                "Category B",
                [""] + [c for c in available if c != catA],
                key="cat_b",
            )

        # -------------------------------------------------
        # 7E. CONFIRM TURN
        # -------------------------------------------------
        ready_to_confirm = len(trickA) == 5 and len(trickB) == 5 and catA != "" and catB != ""

        if st.button(
            "Confirm Turn",
            type="primary",
            use_container_width=True,
            disabled=not ready_to_confirm,
        ):
            st.session_state.master_scores.at[catA, player] = score_category(catA, trickA)
            st.session_state.master_scores.at[catB, player] = score_category(catB, trickB)

            st.session_state.used_categories[player] += [catA, catB]
            st.session_state.selected = []
            st.session_state.rolls_left = 3
            st.session_state.dice = [0] * 10

            st.session_state.current_player_idx = (
                st.session_state.current_player_idx + 1
            ) % len(st.session_state.players)

            if "cat_a" in st.session_state:
                del st.session_state["cat_a"]
            if "cat_b" in st.session_state:
                del st.session_state["cat_b"]

            st.rerun()

    else:
        # -------------------------------------------------
        # 7F. SCORE ONLY MODE
        # -------------------------------------------------
        st.subheader("Manual Score Entry")
        st.info(
            "Physical Dice Mode: enter scores directly into the table below.\n\n"
            "Penalty scores:\n"
            "- Full House: 28\n"
            "- Low Straight: 25\n"
            "- High Straight: 30\n"
            "- 5 of a Kind: 30"
        )

        edited_df = st.data_editor(
            st.session_state.master_scores,
            use_container_width=True,
            key="manual_score_editor",
        )
        st.session_state.master_scores = edited_df

        for p in st.session_state.players:
            st.session_state.used_categories[p] = [
                cat
                for cat in st.session_state.master_scores.index
                if str(st.session_state.master_scores.at[cat, p]).strip() != ""
            ]

# =========================================================
# 8. TOTALS & GAME OVER
# =========================================================
if st.session_state.game_active or st.session_state.game_over:
    st.divider()
    st.subheader("Scores")

    totals = {
        p: st.session_state.master_scores[p].apply(
            lambda x: int(x) if str(x).isdigit() else 0
        ).sum()
        for p in st.session_state.players
    }

    score_cols = st.columns(len(st.session_state.players))
    lowest_score = min(totals.values()) if totals else 0

    for idx, p in enumerate(st.session_state.players):
        with score_cols[idx]:
            st.metric(
                label=f"{p}'s Score",
                value=totals[p],
                delta="Leading" if totals[p] == lowest_score else None,
            )

    st.dataframe(st.session_state.master_scores, use_container_width=True)

    all_finished = all(
        len(st.session_state.used_categories.get(p, [])) >= 10
        for p in st.session_state.players
    ) if st.session_state.players else False

    if all_finished and not st.session_state.game_over:
        st.session_state.game_over = True
        st.session_state.game_active = False
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
        st.session_state.selected = []
        st.session_state.rolls_left = 3
        st.session_state.current_player_idx = 0
        st.session_state.used_categories = {}
        st.session_state.players = []
        st.session_state.master_scores = None

        if "cat_a" in st.session_state:
            del st.session_state["cat_a"]
        if "cat_b" in st.session_state:
            del st.session_state["cat_b"]

        st.rerun()
