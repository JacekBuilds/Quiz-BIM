import streamlit as st
import random
import os
from dotenv import load_dotenv
from parser import parse_markdown_files

# Inicjalizacja środowiska
load_dotenv()
DATA_DIR = os.getenv("DATA_DIR", "data/input_md")
APP_TITLE = os.getenv("APP_TITLE", "Quiz Interaktywny")

st.set_page_config(page_title=APP_TITLE, layout="centered")

# --- MECHANIZM CACHE DLA DANYCH ---
@st.cache_data
def load_data():
    return parse_markdown_files(DATA_DIR)

# --- INICJALIZACJA STANÓW SESJI ---
def init_session_state():
    defaults = {
        'quiz_active': False,
        'quiz_pool': [],
        'current_index': 0,
        'score': 0,
        'answered': False,
        'selected_choice': None
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

def reset_quiz():
    st.session_state.quiz_active = False
    st.session_state.quiz_pool = []
    st.session_state.current_index = 0
    st.session_state.score = 0
    st.session_state.answered = False
    st.session_state.selected_choice = None

# --- GŁÓWNA LOGIKA ---
def main():
    init_session_state()
    all_questions = load_data()

    if not all_questions:
        st.error(f"Nie znaleziono poprawnych pytań w katalogu: `{DATA_DIR}`. Sprawdź format plików `.md`.")
        return

    st.title(APP_TITLE)

    # --- EKRAN STARTOWY ---
    if not st.session_state.quiz_active:
        st.markdown(f"**Baza zawiera łącznie {len(all_questions)} pytań.**")

        num_questions = st.number_input(
            "Ile pytań chcesz wylosować do testu?", 
            min_value=1, 
            max_value=len(all_questions), 
            value=min(10, len(all_questions))
        )

        if st.button("Rozpocznij Test", type="primary"):
            st.session_state.quiz_pool = random.sample(all_questions, num_questions)
            st.session_state.quiz_active = True
            st.session_state.current_index = 0
            st.session_state.score = 0
            st.session_state.answered = False
            st.rerun()

    # --- EKRAN QUIZU ---
    else:
        # Sprawdzenie czy to koniec testu
        if st.session_state.current_index >= len(st.session_state.quiz_pool):
            st.success("🎉 Test zakończony!")
            st.metric("Twój wynik", f"{st.session_state.score} / {len(st.session_state.quiz_pool)}")
            if st.button("Wróć do startu"):
                reset_quiz()
                st.rerun()
            return

        # Pobranie obecnego pytania
        current_q = st.session_state.quiz_pool[st.session_state.current_index]

        # Pasek postępu
        progress = (st.session_state.current_index) / len(st.session_state.quiz_pool)
        st.progress(progress, text=f"Pytanie {st.session_state.current_index + 1} z {len(st.session_state.quiz_pool)}")

        # Wyświetlenie pytania
        st.caption(f"Dział: {current_q['category']}")
        st.markdown(f"### {current_q['question']}")

        # Renderowanie opcji
        if not st.session_state.answered:
            choice = st.radio(
                "Wybierz odpowiedź:", 
                current_q['answers'], 
                index=None,
                key=f"q_{st.session_state.current_index}"
            )

            if st.button("Zatwierdź odpowiedź", type="primary"):
                if choice:
                    st.session_state.answered = True
                    st.session_state.selected_choice = choice
                    # Sprawdzenie poprawności (wyciągnięcie litery a, b, c, d z wybranego stringa)
                    selected_letter = choice.split(')')[0].strip().lower()
                    if selected_letter == current_q['correct_letter']:
                        st.session_state.score += 1
                    st.rerun()
                else:
                    st.warning("Musisz zaznaczyć odpowiedź przed zatwierdzeniem!")

        # Ekran po odpowiedzi na pytanie
        else:
            selected_letter = st.session_state.selected_choice.split(')')[0].strip().lower()
            is_correct = (selected_letter == current_q['correct_letter'])

            # Dezaktywowany radio (tylko do podglądu co zaznaczył użytkownik)
            st.radio(
                "Twoja odpowiedź:", 
                current_q['answers'], 
                index=current_q['answers'].index(st.session_state.selected_choice),
                disabled=True
            )

            # Komunikat o wyniku
            if is_correct:
                st.success("✅ Poprawna odpowiedź!")
            else:
                st.error(f"❌ Zła odpowiedź. Poprawna to: **{current_q['correct_letter']})**")

            # Uzasadnienie
            with st.expander("📖 Zobacz uzasadnienie", expanded=True):
                st.write(current_q['justification'])

            if st.button("Następne pytanie", type="primary"):
                st.session_state.current_index += 1
                st.session_state.answered = False
                st.session_state.selected_choice = None
                st.rerun()

if __name__ == "__main__":
    main()
