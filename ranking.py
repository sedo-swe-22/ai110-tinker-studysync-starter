"""
StudySync -- Find a Study Spot (Ticket 3, Tinker 3B).

TICKET: none of the ranking logic is implemented yet -- every function
below is a stub.
"""

import csv

NOISE_ORDER = {"quiet": 0, "moderate": 1, "loud": 2}

# Noise matters most (can you focus?), then distance, then seats.
NOISE_WEIGHT = 2.0
DISTANCE_WEIGHT = 1.5
SEATS_WEIGHT = 1.0

# Penalties are tuned so noise and distance misses cost a similar amount:
# one noise level too loud ~ one mile too far. Neither is capped, so a
# spot is never buried by one factor alone.
NOISE_PENALTY_PER_LEVEL = 0.5
DISTANCE_PENALTY_PER_MILE = 1.0

# Small tie-breaker (smaller than any factor) so equal-fit spots aren't
# ordered by CSV position.
WIFI_BONUS = {"excellent": 0.2, "good": 0.1, "basic": 0.0}


def load_study_spots(csv_path: str) -> list:
    """
    Load study spots from a CSV into a list of dicts, converting
    "distance_miles" to float and "seats_available" to int.
    """
    spots = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            row["distance_miles"] = float(row["distance_miles"])
            row["seats_available"] = int(row["seats_available"])
            spots.append(row)
    return spots


def score_study_spot(profile: dict, spot: dict) -> tuple:
    """
    Score one study spot against a student profile.

    profile example: {"max_noise": "moderate", "max_distance": 1.0, "min_seats": 4}

    Return (score, reasons) where reasons is a list of short strings
    explaining what contributed to the score, e.g. ["quiet enough", "close enough"].
    """
    score = 0.0
    reasons = []

    noise_over = NOISE_ORDER[spot["noise_level"]] - NOISE_ORDER[profile["max_noise"]]
    if noise_over <= 0:
        score += NOISE_WEIGHT
        reasons.append(f"noise OK ({spot['noise_level']})")
    else:
        score -= NOISE_PENALTY_PER_LEVEL * noise_over
        reasons.append(f"too loud ({spot['noise_level']})")

    miles_over = spot["distance_miles"] - profile["max_distance"]
    if miles_over <= 0:
        score += DISTANCE_WEIGHT
        reasons.append(f"close enough ({spot['distance_miles']} mi)")
    else:
        score -= DISTANCE_PENALTY_PER_MILE * miles_over
        reasons.append(f"too far ({spot['distance_miles']} mi)")

    if spot["seats_available"] >= profile["min_seats"]:
        score += SEATS_WEIGHT
        reasons.append(f"enough seats ({spot['seats_available']})")
    else:
        score -= SEATS_WEIGHT
        reasons.append(f"too few seats ({spot['seats_available']})")

    wifi = spot.get("wifi_quality", "basic")
    score += WIFI_BONUS.get(wifi, 0.0)
    reasons.append(f"{wifi} wifi")

    return score, reasons


def rank_study_spots(profile: dict, spots: list, k: int = 3) -> list:
    """
    Score every study spot, then return the top k as (spot, score, reasons)
    tuples, sorted by score descending.
    """
    scored = []
    for spot in spots:
        score, reasons = score_study_spot(profile, spot)
        scored.append((spot, score, reasons))
    return sorted(scored, key=lambda item: item[1], reverse=True)[:k]


def format_results(ranked: list) -> None:
    """Print each ranked study spot with its score and reasons, one line each."""
    for i, (spot, score, reasons) in enumerate(ranked, start=1):
        print(f"{i}. {spot['name']} -- Score: {score:.1f} -- Because: {', '.join(reasons)}")


def render_study_spot_tab():
    import streamlit as st

    st.subheader("Find a Study Spot")
    max_noise = st.selectbox("Max noise level", ["quiet", "moderate", "loud"], index=1)
    max_distance = st.slider("Max distance (miles)", 0.0, 3.0, 1.0)
    min_seats = st.number_input("Minimum seats needed", min_value=1, value=4, step=1)

    if st.button("Find spots"):
        profile = {"max_noise": max_noise, "max_distance": max_distance, "min_seats": min_seats}
        try:
            spots = load_study_spots("data/study_spots.csv")
            ranked = rank_study_spots(profile, spots, k=3)
            for spot, score, reasons in ranked:
                st.write(f"**{spot['name']}** -- Score: {score:.1f} -- Because: {', '.join(reasons)}")
        except NotImplementedError:
            st.warning("🚧 Ranking isn't implemented yet -- that's Tinker 3B's ticket.")


if __name__ == "__main__":
    spots = load_study_spots("data/study_spots.csv")
    profile = {"max_noise": "moderate", "max_distance": 1.0, "min_seats": 4}
    ranked = rank_study_spots(profile, spots, k=3)
    format_results(ranked)
