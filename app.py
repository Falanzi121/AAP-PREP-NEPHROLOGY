import json
import random
import time
from pathlib import Path
from typing import List

import streamlit as st

# Map year → JSON question file
YEAR_FILES = {
    "2015": "questions/prep_2015.json",
    "2016": "questions/prep_2016.json",
    "2017": "questions/prep_2017.json",
    "2019": "questions/prep_2019.json",
    "2021": "questions/prep_2021.json",
    "2022": "questions/prep_2022.json",
}


@st.cache_data
def load_questions(path: Path) -> List[dict]:
    with path.open(encoding="utf-8") as fp:
        return json.load(fp)


def init_practice_state(total_questions: int):
    if "order" not in st.session_state:
        order = list(range(total_questions))
        random.shuffle(order)
        st.session_state["order"] = order
    if "current_index" not in st.session_state:
        st.session_state["current_index"] = 0
    if "responses" not in st.session_state:
        st.session_state["responses"] = {}


def init_exam_state(total_questions: int):
    if "order" not in st.session_state:
        st.session_state["order"] = list(range(total_questions))
    if "exam_started" not in st.session_state:
        st.session_state["exam_started"] = False
    if "exam_finished" not in st.session_state:
        st.session_state["exam_finished"] = False
    if "exam_q_idx" not in st.session_state:
        st.session_state["exam_q_idx"] = 0


def reset_mode_state():
    for key in (
        "order",
        "current_index",
        "responses",
        "exam_answers",
        "exam_start_time",
        "exam_finished",
        "exam_started",
        "exam_q_idx",
    ):
        if key in st.session_state:
            del st.session_state[key]


def select_mode() -> str:
    if "mode" not in st.session_state:
        st.session_state["mode"] = "Practice"
    current_mode = st.session_state["mode"]
    selection = st.radio(
        "Mode",
        ["Practice", "Exam"],
        index=0 if current_mode == "Practice" else 1,
    )
    if selection != current_mode:
        reset_mode_state()
        st.session_state["mode"] = selection
    return st.session_state["mode"]


def clear_exam_session():
    for key in (
        "exam_started",
        "exam_finished",
        "exam_start_time",
        "exam_q_idx",
        "exam_answers",
    ):
        st.session_state.pop(key, None)


def format_time_mmss(seconds: float) -> str:
    total_seconds = max(0, int(seconds))
    minutes, secs = divmod(total_seconds, 60)
    return f"{minutes:02d}:{secs:02d}"


def move_exam_question(offset: int, total_questions: int):
    current = st.session_state.get("exam_q_idx", 0)
    new_index = max(0, min(current + offset, total_questions - 1))
    st.session_state["exam_q_idx"] = new_index


def navigate(offset: int):
    new_index = st.session_state["current_index"] + offset
    new_index = max(0, min(new_index, len(st.session_state["order"]) - 1))
    st.session_state["current_index"] = new_index


def record_response(question_id: int, option_index: int):
    st.session_state["responses"][question_id] = option_index
    st.rerun()


def main():
    st.set_page_config(page_title="PREP MCQs", layout="centered")

    # -------- Year selector --------
    years_list = list(YEAR_FILES.keys())
    default_year = st.session_state.get("current_year", "2021")
    default_index = years_list.index(default_year) if default_year in years_list else 0

    year = st.selectbox("Select PREP Year", years_list, index=default_index)

    # Reset all per-year state when year changes
    if st.session_state.get("current_year") != year:
        reset_mode_state()
        clear_exam_session()
        st.session_state["current_year"] = year

    st.title(f"PREP {year} MCQs")

    # Load questions for the chosen year
    data_path = Path(YEAR_FILES[year])
    questions = load_questions(data_path)
    total = len(questions)

    # -------- Mode selector --------
    mode = select_mode()

    # ==================== PRACTICE MODE ====================
    if mode == "Practice":
        init_practice_state(total)
        order = st.session_state["order"]
        current = st.session_state["current_index"]
        q_idx = order[current]
        question = questions[q_idx]

        st.caption(f"Question {current + 1} of {total}")
        st.markdown(f"**Stem**\n\n{question['stem']}")

        st.subheader("Options")
        stored_responses = st.session_state["responses"]
        selected_idx = stored_responses.get(q_idx)

        for opt_idx, option in enumerate(question["options"]):
            if st.button(option, key=f"opt-{q_idx}-{opt_idx}"):
                record_response(q_idx, opt_idx)

        if selected_idx is not None:
            chosen_text = question["options"][selected_idx]
            st.markdown("**Selected Option**")
            st.write(chosen_text)

            explanation = question.get("explanation")
            if explanation:
                st.markdown("**Explanation**")
                st.markdown(explanation)

        col_prev, col_next = st.columns(2)
        with col_prev:
            st.button(
                "Previous",
                on_click=lambda: navigate(-1),
                disabled=current == 0,
                key="prev-btn",
            )
        with col_next:
            st.button(
                "Next",
                on_click=lambda: navigate(1),
                disabled=current == total - 1,
                key="next-btn",
            )

    # ==================== EXAM MODE ====================
    else:
        init_exam_state(total)
        indices = list(range(total))
        total_seconds = total * 60
        exam_started = st.session_state.get("exam_started", False)
        exam_finished = st.session_state.get("exam_finished", False)

        # Start exam
        if (not exam_started) and (not exam_finished):
            if st.button("Start Exam", key="start-exam-btn"):
                st.session_state["exam_started"] = True
                st.session_state["exam_finished"] = False
                st.session_state["exam_start_time"] = time.time()
                st.session_state["exam_q_idx"] = 0
                st.session_state["exam_answers"] = {idx: None for idx in indices}
                st.rerun()
            return

        # Ensure exam_answers exists
        if exam_started and "exam_answers" not in st.session_state:
            st.session_state["exam_answers"] = {idx: None for idx in indices}

        # Timer
        if exam_started and not exam_finished:
            start_time = st.session_state.get("exam_start_time", time.time())
            elapsed = time.time() - start_time
            remaining_seconds = total_seconds - elapsed
            if remaining_seconds <= 0:
                st.session_state["exam_finished"] = True
                exam_finished = True
            else:
                st.markdown(
                    f"**Time Remaining:** {format_time_mmss(remaining_seconds)}"
                )

        # Summary view
        if st.session_state.get("exam_finished", False):
            st.header("Exam Summary")
            answers = st.session_state.get("exam_answers", {})
            table_rows = []
            answer_lines = []
            for idx in indices:
                choice = answers.get(idx)
                letter = chr(ord("A") + choice) if choice is not None else "-"
                table_rows.append({"Q#": idx + 1, "Answer": letter})
                answer_lines.append(f"{idx + 1}. {letter}")
            st.table(table_rows)
            answer_sheet = "\n".join(answer_lines)
            st.markdown("**Answer Sheet**")
            st.text(answer_sheet if answer_sheet else "-")
            st.download_button(
                "Download Answer Sheet",
                data=answer_sheet,
                file_name=f"prep_{year}_exam_answers.txt",
                mime="text/plain",
                key="download-exam-answers",
            )
            if st.button("Reset Exam", key="reset-exam-btn"):
                clear_exam_session()
                st.rerun()
            return

        # Question view
        q_idx = st.session_state.get("exam_q_idx", 0)
        q_idx = max(0, min(q_idx, total - 1))
        st.session_state["exam_q_idx"] = q_idx
        question = questions[q_idx]

        st.caption(f"Question {q_idx + 1} of {total}")
        st.markdown(f"**Stem**\n\n{question['stem']}")

        st.subheader("Options")
        stored_answers = st.session_state.get("exam_answers", {})
        selected_idx = stored_answers.get(q_idx)
        option_values = [None] + list(range(len(question["options"])))

        def format_choice(value):
            if value is None:
                return "Select an option"
            letter = chr(ord("A") + value)
            return f"{letter}. {question['options'][value]}"

        choice = st.radio(
            f"Options for Question {q_idx + 1}",
            option_values,
            index=0 if selected_idx is None else selected_idx + 1,
            format_func=format_choice,
            key=f"exam-options-{q_idx}",
        )

        if choice is None:
            if stored_answers.get(q_idx) is not None:
                st.session_state["exam_answers"][q_idx] = None
        else:
            if stored_answers.get(q_idx) != choice:
                st.session_state["exam_answers"][q_idx] = choice

        col_prev, col_next, col_finish = st.columns(3)
        with col_prev:
            st.button(
                "Previous",
                on_click=lambda: move_exam_question(-1, total),
                disabled=q_idx == 0,
                key="exam-prev-btn",
            )
        with col_next:
            st.button(
                "Next",
                on_click=lambda: move_exam_question(1, total),
                disabled=q_idx == total - 1,
                key="exam-next-btn",
            )
        with col_finish:
            st.button(
                "Finish Exam",
                on_click=lambda: st.session_state.update({"exam_finished": True}),
                key="finish-exam-btn",
            )


if __name__ == "__main__":
    main()