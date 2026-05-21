import os
import re

def parse_markdown_files(directory_path: str) -> list:
    '''Skanuje katalog w poszukiwaniu plików .md i wyciąga z nich pytania.'''
    questions_db = []

    if not os.path.exists(directory_path):
        return questions_db

    for filename in os.listdir(directory_path):
        if filename.endswith(".md"):
            filepath = os.path.join(directory_path, filename)
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()

                # Podział na pytania po separatorze (ciąg znaków '=')
                blocks = re.split(r'={10,}', content)
                for block in blocks:
                    if block.strip():
                        parsed_q = parse_single_block(block)
                        if parsed_q:
                            questions_db.append(parsed_q)

    return questions_db

def parse_single_block(block: str) -> dict:
    '''Rozkłada pojedynczy blok tekstu na słownik danych.'''
    try:
        # Regex wyciągające poszczególne sekcje
        q_match = re.search(r'# Pytanie\s*(.*?)\s*## Odpowiedzi', block, re.DOTALL)
        ans_match = re.search(r'## Odpowiedzi\s*(.*?)\s*## Poprawna odpowiedź', block, re.DOTALL)
        corr_match = re.search(r'## Poprawna odpowiedź\s*(.*?)\s*## Dział', block, re.DOTALL)
        cat_match = re.search(r'## Dział\s*(.*?)\s*## Uzasadnienie', block, re.DOTALL)
        just_match = re.search(r'## Uzasadnienie\s*(.*)', block, re.DOTALL)

        if not (q_match and ans_match and corr_match):
            return None

        # Czyszczenie i przygotowanie listy odpowiedzi
        answers_raw = ans_match.group(1).strip()
        answers_list = re.findall(r'###\s*(.*?)(?=\n###|\Z)', answers_raw, re.DOTALL)

        # Wyodrębnienie samej litery poprawnej odpowiedzi (np. "a" z "a)")
        correct_raw = corr_match.group(1).strip()
        correct_letter = correct_raw.replace(')', '').strip().lower()

        return {
            "question": q_match.group(1).strip(),
            "answers": [a.strip() for a in answers_list if a.strip()],
            "correct_letter": correct_letter,
            "category": cat_match.group(1).strip() if cat_match else "Brak działu",
            "justification": just_match.group(1).strip() if just_match else "Brak uzasadnienia.",
            "raw_text": block.strip()  # <--- DODANA LINIJKA
        }
    except Exception as e:
        return None
