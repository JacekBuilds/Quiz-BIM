import streamlit as st
import random
import os
import datetime
import gdown
from dotenv import load_dotenv
from parser import parse_markdown_files

# Inicjalizacja środowiska
load_dotenv()
DATA_DIR = os.getenv("DATA_DIR", "data/input_md")
APP_TITLE = os.getenv("APP_TITLE", "Quiz Interaktywny")
GDRIVE_URL = os.getenv("GDRIVE_URL", "")

st.set_page_config(page_title=APP_TITLE, layout="centered")


# --- FUNKCJA POBIERANIA Z DYSKU ---
def sync_google_drive():
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        gdown.download_folder(url=GDRIVE_URL, output=DATA_DIR, quiet=True, use_cookies=False)
        return True
    except Exception as e:
        print(f"Błąd pobierania: {e}")
        return False


# --- MECHANIZM CACHE DLA DANYCH ---
@st.cache_data
def load_data():
    return parse_markdown_files(DATA_DIR)


# --- FUNKCJA ZAPISU ZGŁOSZEŃ ---
def zapisz_zgloszenie(pytanie_data, komentarz):
    log_dir = "data/logs"
    os.makedirs(log_dir, exist_ok=True)
    filepath = os.path.join(log_dir, "zgloszenia.txt")

    with open(filepath, "a", encoding="utf-8") as f:
        f.write(f"--- DATA: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        f.write(f"KOMENTARZ UŻYTKOWNIKA: {komentarz}\n")
        f.write("--- SUROWE PYTANIE Z BAZY ---\n")
        f.write(f"{pytanie_data.get('raw_text', 'Brak surowego tekstu')}\n")
        f.write("=" * 50 + "\n\n")


# --- INICJALIZACJA STANÓW SESJI ---
def init_session_state():
    defaults = {
        'quiz_active': False,
        'quiz_pool': [],
        'current_index': 0,
        'score': 0,
        'answered': False,
        'selected_choice': None,
        'drive_synced': False,
        'sync_message': ""
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

    # --- AUTOMATYCZNA SYNCHRONIZACJA NA STARCIE SESJI ---
    if not st.session_state.drive_synced:
        if GDRIVE_URL:
            with st.spinner("Trwa łączenie z Google Drive i pobieranie pytań..."):
                sync_google_drive()
                load_data.clear()

                if os.path.exists(DATA_DIR):
                    liczba_plikow = len([f for f in os.listdir(DATA_DIR) if f.endswith('.md')])
                else:
                    liczba_plikow = 0

                st.session_state.sync_message = f"✅ Pobrano i zaktualizowano dane. Znaleziono **{liczba_plikow}** plików `.md`."
        st.session_state.drive_synced = True

    all_questions = load_data()
    st.title(APP_TITLE)

    if not all_questions:
        st.error(f"Nie znaleziono poprawnych pytań w katalogu: `{DATA_DIR}`.")
        return

    # --- EKRAN STARTOWY ---
    if not st.session_state.quiz_active:
        if st.session_state.sync_message:
            st.info(st.session_state.sync_message)

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
        if st.session_state.current_index >= len(st.session_state.quiz_pool):
            st.success("🎉 Test zakończony!")
            st.metric("Twój wynik", f"{st.session_state.score} / {len(st.session_state.quiz_pool)}")
            if st.button("Wróć do startu"):
                reset_quiz()
                st.rerun()
            return

        current_q = st.session_state.quiz_pool[st.session_state.current_index]

        progress = (st.session_state.current_index) / len(st.session_state.quiz_pool)
        st.progress(progress, text=f"Pytanie {st.session_state.current_index + 1} z {len(st.session_state.quiz_pool)}")

        st.caption(f"Dział: {current_q['category']}")
        st.markdown(f"### {current_q['question']}")

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
                    selected_letter = choice.split(')')[0].strip().lower()
                    if selected_letter == current_q['correct_letter']:
                        st.session_state.score += 1
                    st.rerun()
                else:
                    st.warning("Musisz zaznaczyć odpowiedź przed zatwierdzeniem!")


        else:

            # --- WYSZUKIWANIE PEŁNEJ TREŚCI ODPOWIEDZI ---

            pelna_poprawna = next(
                (ans for ans in current_q['answers']
                 if ans.lower().startswith(current_q['correct_letter'] + ")")),
                f"{current_q['correct_letter']}) (Treść niedostępna)"
            )

            selected_letter = st.session_state.selected_choice.split(')')[0].strip().lower()
            is_correct = (selected_letter == current_q['correct_letter'])

            st.radio(
                "Twoja odpowiedź:",
                current_q['answers'],
                index=current_q['answers'].index(st.session_state.selected_choice),
                disabled=True
            )

            if is_correct:
                st.success(f"✅ Poprawna odpowiedź: **{pelna_poprawna}**")
            else:
                st.error(f"❌ Zła odpowiedź. Poprawna to: **{pelna_poprawna}**")
            # Uzasadnienie ukryte defaultowo (expanded=False)
            with st.expander("📖 Zobacz uzasadnienie", expanded=False):
                st.write(current_q['justification'])
            # Brak st.divider() - bezpośrednio pod formularz zgłoszeniowy
            with st.expander("⚠️ Zgłoś błąd w tym pytaniu"):
                with st.form(key=f"zgloszenie_{st.session_state.current_index}"):
                    komentarz_usera = st.text_area(
                        "Co jest nie tak? (np. zła odpowiedź, literówka, niejasne uzasadnienie)")
                    wyslano = st.form_submit_button("Wyślij zgłoszenie")
                    if wyslano:
                        if komentarz_usera.strip() == "":
                            st.warning("Wpisz jakiś komentarz przed wysłaniem.")
                        else:
                            zapisz_zgloszenie(current_q, komentarz_usera)
                            st.success("Dzięki! Zgłoszenie zostało zapisane w logach.")

            if st.button("Następne pytanie", type="primary"):
                st.session_state.current_index += 1
                st.session_state.answered = False
                st.session_state.selected_choice = None
                st.rerun()


if __name__ == "__main__":
    main()