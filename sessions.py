"""
StudySync -- Session Log (Ticket 2, Tinker 2B).

Session log helpers: a rerun-safe click counter (st.session_state), a
validated session list, a SessionDC dataclass alongside the hand-written
PlainSession, next_occurrence() for recurring sessions, and
find_conflicts() for sessions sharing a time slot.
"""

import warnings
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from itertools import combinations

FREQUENCY_DAYS = {"daily": 1, "weekly": 7}


class PlainSession:
    def __init__(self, subject, minutes, priority="medium"):
        self.subject = subject
        self.minutes = minutes
        self.priority = priority

    def __repr__(self):
        return f"PlainSession(subject={self.subject!r}, minutes={self.minutes}, priority={self.priority!r})"


@dataclass
class SessionDC:
    subject: str
    minutes: int
    priority: str = "medium"


def next_occurrence(last_date: date, frequency: str) -> date:
    """
    Return the next scheduled date given the last session date and a
    frequency label ("daily" or "weekly"), using FREQUENCY_DAYS and timedelta.
    """
    key = frequency.strip().lower() if isinstance(frequency, str) else frequency
    if key not in FREQUENCY_DAYS:
        raise ValueError(f"Unknown frequency {frequency!r}; expected one of {list(FREQUENCY_DAYS)}")
    return last_date + timedelta(days=FREQUENCY_DAYS[key])


def _normalize_slot(slot):
    """Return a comparable slot string, or None if the slot is unusable.

    "8:00", "08:00" and " 08:00 " all normalize to "08:00". Non-time labels
    are compared case-insensitively.
    """
    if not isinstance(slot, str) or not slot.strip():
        return None
    slot = slot.strip()
    try:
        return datetime.strptime(slot, "%H:%M").strftime("%H:%M")
    except ValueError:
        return slot.lower()


def find_conflicts(sessions: list) -> list:
    """
    sessions: list of dicts, each with a "slot" key, e.g. {"subject": "Calc II", "slot": "08:00"}.

    Return a list of (session_a, session_b) tuples for every pair that shares
    the same "slot". Must NOT crash on an empty list or a list with no conflicts.
    """
    # Keep only entries that can actually be compared: dicts with a usable slot.
    schedulable = []
    for s in sessions or []:
        slot = _normalize_slot(s.get("slot")) if isinstance(s, dict) else None
        if slot is None:
            warnings.warn(f"find_conflicts: skipping entry with no usable slot: {s!r}", stacklevel=2)
            continue
        schedulable.append((slot, s))

    # combinations() yields each unordered pair exactly once (and nothing for 0-1 items).
    return [(a, b) for (slot_a, a), (slot_b, b) in combinations(schedulable, 2) if slot_a == slot_b]


def render_session_log_tab():
    import streamlit as st

    st.subheader("Parts 1-2: Log a Session")

    # BUG (Part 1): this is a plain local variable, so Streamlit "forgets" it on every rerun.
    count = 0
    if st.button("Log a session (broken)"):
        count += 1
    st.metric("Sessions logged (broken)", count)

    # session_state persists across reruns; initialize only once.
    if "fixed_count" not in st.session_state:
        st.session_state.fixed_count = 0

    if st.button("Log a session (fixed)"):
        st.session_state.fixed_count += 1
    st.metric("Sessions logged (fixed)", st.session_state.fixed_count)

    st.divider()
    st.subheader("Part 2: Session List (with validation)")

    if "mini_sessions" not in st.session_state:
        st.session_state.mini_sessions = []

    subject = st.text_input("Subject")
    duration = st.number_input("Duration (minutes)", value=30, step=1)

    if st.button("Add session"):
        if not subject.strip():
            st.error("Subject cannot be empty or whitespace-only.")
        elif duration <= 0:
            st.error(f"Duration must be greater than 0 minutes (got {duration}).")
        else:
            st.session_state.mini_sessions.append({"subject": subject.strip(), "duration": duration})

    st.write(st.session_state.mini_sessions)

    st.divider()
    st.subheader("Part 4: Conflict Check")
    if st.button("Check for time conflicts"):
        sample = [
            {"subject": "Calc II", "slot": "08:00"},
            {"subject": "Chem Lab", "slot": "08:00"},
            {"subject": "History", "slot": "09:00"},
        ]
        conflicts = find_conflicts(sample)
        st.write(conflicts if conflicts else "No conflicts found.")


if __name__ == "__main__":
    plain = PlainSession("Study group: Calc II", 45, priority="high")
    print(plain)
    dc = SessionDC("Study group: Calc II", 45, priority="high")
    print(dc)

    print(next_occurrence(date(2026, 1, 1), "daily"))
    print(next_occurrence(date(2026, 1, 1), "weekly"))

    print(
        find_conflicts(
            [
                {"subject": "Calc II", "slot": "08:00"},
                {"subject": "Chem Lab", "slot": "08:00"},
                {"subject": "History", "slot": "09:00"},
            ]
        )
    )
    print(find_conflicts([]))
