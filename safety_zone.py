import streamlit as st
from streamlit_mic_recorder import mic_recorder
import google.generativeai as genai
import random
import datetime
import os

# --- 1. CONFIG ---
API_KEY = os.environ["GEMINI_KEY"]
genai.configure(api_key=API_KEY)

try:
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    if available_models:
        model_to_use = available_models[0]
        model = genai.GenerativeModel(model_to_use)
    else:
        st.error("Google says there are no available models. Check your API key!")
        st.stop()
except Exception as e:
    st.error(f"Error connecting to Google: {e}")
    st.stop()

st.set_page_config(page_title="The Safety Zone", page_icon="🎙️", layout="wide")

# =========================================================================
#   explain_lang  -> the language the STUDENT understands (UI text, and
#                     the meaning/translation of new words, idioms, books)
#   practice_lang -> the language the STUDENT IS PRACTICING SPEAKING
#   level         -> only shown/used for languages in LEVELED_LANGS
# =========================================================================

EXPLAIN_LANGS = ["kk", "ru", "en"]
EXPLAIN_LABELS = {"kk": "ҚАЗ", "ru": "РУС", "en": "ENG"}

PRACTICE_LANGS = {
    "en": {"label": "English", "flag": "🇬🇧"},
    "de": {"label": "Deutsch", "flag": "🇩🇪"},
    "ru": {"label": "Русский", "flag": "🇷🇺"},
    "kk": {"label": "Қазақша", "flag": "🇰🇿"},
    "es": {"label": "Español", "flag": "🇪🇸"},
    "it": {"label": "Italiano", "flag": "🇮🇹"},
    "fr": {"label": "Français", "flag": "🇫🇷"},
}

LEVELED_LANGS = {"de", "en", "es", "it", "fr"}   # ru and kk stay single-tier (B1-B2+)
LEVELS = ["A1-A2", "B1-B2", "C1-C2"]

if "explain_lang" not in st.session_state:
    st.session_state.explain_lang = "en"
if "practice_lang" not in st.session_state:
    st.session_state.practice_lang = "en"
if "level" not in st.session_state:
    st.session_state.level = "B1-B2"

top1, top2, top3 = st.columns([3, 2, 2])
with top1:
    st.session_state.explain_lang = st.radio(
        "Explain in / Объясняй на / Түсіндір",
        options=EXPLAIN_LANGS,
        format_func=lambda c: EXPLAIN_LABELS[c],
        index=EXPLAIN_LANGS.index(st.session_state.explain_lang),
        horizontal=True,
        key="explain_lang_picker",
    )
with top2:
    new_practice = st.selectbox(
        "Practice language",
        options=list(PRACTICE_LANGS.keys()),
        format_func=lambda code: f"{PRACTICE_LANGS[code]['flag']} {PRACTICE_LANGS[code]['label']}",
        index=list(PRACTICE_LANGS.keys()).index(st.session_state.practice_lang),
        key="practice_lang_picker",
    )
if new_practice != st.session_state.practice_lang:
    st.session_state.practice_lang = new_practice
    st.session_state.topic = None
with top3:
    if st.session_state.practice_lang in LEVELED_LANGS:
        st.session_state.level = st.selectbox(
            "Level",
            options=LEVELS,
            index=LEVELS.index(st.session_state.level),
            key="level_picker",
        )

explain_lang = st.session_state.explain_lang
practice_lang = st.session_state.practice_lang
# languages without levels always behave as B1-B2+ internally
level = st.session_state.level if practice_lang in LEVELED_LANGS else "B1-B2"

# --- 2. UI TEXT (driven by explain_lang) ---
UI = {
    "en": {
        "sidebar_header": "📚 Study Materials",
        "word_of_day": "🌟 Word of the Day:",
        "idiom_of_day": "🗣️ Idiom of the Day:",
        "articles_header": "📰 Recommended Articles & News",
        "books_header": "📖 Weekly Recommendations",
        "vocab_header": "✨ Vocab from these sources",
        "title": "🎙️ The Safety Zone",
        "subtitle": "Read the materials in the sidebar, pick a topic, and record your speech!",
        "click_button": "Click the button below!",
        "get_topic": "🎲 Get a Topic",
        "current_topic": "Current Topic:",
        "step1": "Step 1: Record your answer",
        "step2": "Step 2: AI Analysis",
        "start_recording": "🔴 Start Recording",
        "stop_recording": "⏹️ Stop & Send",
        "analyzing": "Analyzing...",
        "feedback_ready": "Feedback ready!",
        "error": "Error:",
    },
    "ru": {
        "sidebar_header": "📚 Учебные материалы",
        "word_of_day": "🌟 Слово дня:",
        "idiom_of_day": "🗣️ Идиома дня:",
        "articles_header": "📰 Рекомендованные статьи и новости",
        "books_header": "📖 Рекомендации недели",
        "vocab_header": "✨ Слова из этих источников",
        "title": "🎙️ The Safety Zone",
        "subtitle": "Прочитай материалы на боковой панели, выбери тему и запиши свой ответ!",
        "click_button": "Нажми на кнопку ниже!",
        "get_topic": "🎲 Получить тему",
        "current_topic": "Текущая тема:",
        "step1": "Шаг 1: Запиши свой ответ",
        "step2": "Шаг 2: Анализ ИИ",
        "start_recording": "🔴 Начать запись",
        "stop_recording": "⏹️ Остановить и отправить",
        "analyzing": "Анализирую...",
        "feedback_ready": "Отзыв готов!",
        "error": "Ошибка:",
    },
    "kk": {
        "sidebar_header": "📚 Оқу материалдары",
        "word_of_day": "🌟 Күннің сөзі:",
        "idiom_of_day": "🗣️ Күннің мақалы:",
        "articles_header": "📰 Ұсынылған мақалалар мен жаңалықтар",
        "books_header": "📖 Апталық ұсыныстар",
        "vocab_header": "✨ Осы дереккөздердегі сөздер",
        "title": "🎙️ The Safety Zone",
        "subtitle": "Бүйірдегі материалдарды оқы, тақырып таңда және жауабыңды жазып ал!",
        "click_button": "Төмендегі батырманы бас!",
        "get_topic": "🎲 Тақырып алу",
        "current_topic": "Ағымдағы тақырып:",
        "step1": "1-қадам: Жауабыңды жазып ал",
        "step2": "2-қадам: ЖИ талдауы",
        "start_recording": "🔴 Жазуды бастау",
        "stop_recording": "⏹️ Тоқтату және жіберу",
        "analyzing": "Талдауда...",
        "feedback_ready": "Пікір дайын!",
        "error": "Қате:",
    },
}
t = UI[explain_lang]

# --- 3. WORDS (word itself in practice_lang, meaning translated per explain_lang) ---
WORDS_EN = {
    "A1-A2": [
        {"word": "Happy", "def": {"en": "feeling joy or pleasure.", "ru": "чувствующий радость.", "kk": "қуанышты, көңілді."}},
        {"word": "Big", "def": {"en": "large in size.", "ru": "большой по размеру.", "kk": "үлкен көлемді."}},
        {"word": "Friend", "def": {"en": "a person you like and trust.", "ru": "человек, которому доверяешь.", "kk": "сенетін, ұнататын адам."}},
        {"word": "Weather", "def": {"en": "the condition of the sky and temperature.", "ru": "состояние неба и температуры.", "kk": "ауа-райының жағдайы."}},
        {"word": "Family", "def": {"en": "the people related to you.", "ru": "родственники, семья.", "kk": "туыстар, отбасы."}},
    ],
    "B1-B2": [
        {"word": "Ambiguous", "def": {"en": "having more than one possible meaning; unclear.", "ru": "имеющий более одного значения; неясный.", "kk": "бірнеше мағынасы бар, түсініксіз."}},
        {"word": "Eloquent", "def": {"en": "fluent or persuasive in speaking or writing.", "ru": "красноречивый, убедительный в речи или письме.", "kk": "сөйлеу немесе жазуда шешен, сендіре білетін."}},
        {"word": "Pragmatic", "def": {"en": "dealing with things sensibly and realistically.", "ru": "практичный, реалистичный подход к делу.", "kk": "іске байыппен әрі шынайы қарайтын."}},
        {"word": "Ubiquitous", "def": {"en": "present, appearing, or found everywhere.", "ru": "повсеместный, встречающийся повсюду.", "kk": "барлық жерде кездесетін."}},
        {"word": "Meticulous", "def": {"en": "showing great attention to detail; very careful.", "ru": "очень внимательный к деталям, скрупулёзный.", "kk": "егжей-тегжейіне дейін ұқыпты қарайтын."}},
    ],
    "C1-C2": [
        {"word": "Ephemeral", "def": {"en": "lasting for a very short time.", "ru": "мимолётный, недолговечный.", "kk": "өте қысқа мерзімге созылатын."}},
        {"word": "Ineffable", "def": {"en": "too great to be expressed in words.", "ru": "невыразимый словами.", "kk": "сөзбен айтып жеткізе алмайтын."}},
        {"word": "Cognizant", "def": {"en": "aware of or knowing something.", "ru": "осведомлённый о чём-либо.", "kk": "бір нәрсені білетін, хабардар."}},
        {"word": "Ostensible", "def": {"en": "appearing to be true, but not necessarily so.", "ru": "кажущийся, показной.", "kk": "сырт көрінісінде ғана дұрыс болып көрінетін."}},
        {"word": "Perspicacious", "def": {"en": "having keen insight or judgment.", "ru": "проницательный.", "kk": "өткір пайымды, зерек."}},
    ],
}

WORDS_DE = {
    "A1-A2": [
        {"word": "Haus", "def": {"en": "house", "ru": "дом", "kk": "үй"}},
        {"word": "Freund", "def": {"en": "friend", "ru": "друг", "kk": "дос"}},
        {"word": "Schule", "def": {"en": "school", "ru": "школа", "kk": "мектеп"}},
        {"word": "Familie", "def": {"en": "family", "ru": "семья", "kk": "отбасы"}},
        {"word": "Wetter", "def": {"en": "weather", "ru": "погода", "kk": "ауа райы"}},
    ],
    "B1-B2": [
        {"word": "Zwiespältig", "def": {"en": "conflicting, mixed feelings about something.", "ru": "противоречивый, двойственный.", "kk": "қарама-қайшы, екіұдай сезім тудыратын."}},
        {"word": "Pragmatisch", "def": {"en": "practical and realistic.", "ru": "практичный, реалистичный.", "kk": "тәжірибелік әрі шынайы."}},
        {"word": "Allgegenwärtig", "def": {"en": "present everywhere.", "ru": "вездесущий, повсеместный.", "kk": "барлық жерде бар."}},
        {"word": "Plausibel", "def": {"en": "believable, reasonable.", "ru": "правдоподобный, обоснованный.", "kk": "сенімді, нанымды."}},
        {"word": "Akribisch", "def": {"en": "extremely careful and precise.", "ru": "очень тщательный, скрупулёзный.", "kk": "аса мұқият әрі дәл."}},
    ],
    "C1-C2": [
        {"word": "Unwiderruflich", "def": {"en": "irrevocable, cannot be undone.", "ru": "безвозвратный, необратимый.", "kk": "қайтарымсыз, өзгертілмейтін."}},
        {"word": "Ambivalent", "def": {"en": "having mixed, contradictory feelings.", "ru": "амбивалентный, двойственный.", "kk": "қарама-қайшы сезімдер тудыратын."}},
        {"word": "Nuanciert", "def": {"en": "showing subtle shades of meaning.", "ru": "нюансированный, тонко проработанный.", "kk": "нәзік реңктермен ерекшеленетін."}},
        {"word": "Kontrovers", "def": {"en": "controversial, causing disagreement.", "ru": "спорный, вызывающий разногласия.", "kk": "пікірталас тудыратын, даулы."}},
        {"word": "Facettenreich", "def": {"en": "multifaceted, having many sides.", "ru": "многогранный.", "kk": "көп қырлы."}},
    ],
}

WORDS_RU = [
    {"word": "Двусмысленный", "def": {"en": "having more than one possible meaning.", "ru": "имеющий более одного значения; неясный.", "kk": "бірнеше мағынасы бар, түсініксіз."}},
    {"word": "Красноречивый", "def": {"en": "eloquent, fluent and persuasive in speech.", "ru": "умеющий говорить выразительно и убедительно.", "kk": "сөйлеуде шешен әрі сендіре білетін."}},
    {"word": "Практичный", "def": {"en": "practical, dealing with things realistically.", "ru": "реалистично подходящий к делу.", "kk": "іске шынайы қарайтын."}},
    {"word": "Повсеместный", "def": {"en": "found everywhere.", "ru": "встречающийся повсюду.", "kk": "барлық жерде кездесетін."}},
    {"word": "Скрупулёзный", "def": {"en": "extremely careful about details.", "ru": "крайне внимательный к деталям.", "kk": "егжей-тегжейіне аса ұқыпты қарайтын."}},
]

WORDS_KK = [
    {"word": "Абстрактілі", "def": {"kk": "нақты емес, тек ойша қабылданатын.", "ru": "абстрактный, воспринимаемый лишь мысленно.", "en": "abstract, existing only as an idea."}},
    {"word": "Талғампаз", "def": {"kk": "талғамы биік, талапшыл.", "ru": "привередливый, разборчивый во вкусах.", "en": "having refined, discerning taste."}},
    {"word": "Ұтымды", "def": {"kk": "тиімді әрі орынды.", "ru": "эффективный и уместный.", "en": "efficient and apt."}},
    {"word": "Кең тараған", "def": {"kk": "барлық жерде кездесетін.", "ru": "распространённый повсюду.", "en": "widespread, found everywhere."}},
    {"word": "Сенімді", "def": {"kk": "нанымды, шындыққа жанасымды.", "ru": "правдоподобный, заслуживающий доверия.", "en": "plausible, credible."}},
]

WORDS_ES = {
    "A1-A2": [
        {"word": "Casa", "def": {"en": "house", "ru": "дом", "kk": "үй"}},
        {"word": "Amigo", "def": {"en": "friend", "ru": "друг", "kk": "дос"}},
        {"word": "Escuela", "def": {"en": "school", "ru": "школа", "kk": "мектеп"}},
        {"word": "Familia", "def": {"en": "family", "ru": "семья", "kk": "отбасы"}},
        {"word": "Clima", "def": {"en": "weather", "ru": "погода", "kk": "ауа райы"}},
    ],
    "B1-B2": [
        {"word": "Ambiguo", "def": {"en": "having more than one meaning; unclear.", "ru": "неоднозначный, неясный.", "kk": "бірнеше мағынасы бар, түсініксіз."}},
        {"word": "Elocuente", "def": {"en": "fluent and persuasive in speech.", "ru": "красноречивый.", "kk": "шешен, сендіре білетін."}},
        {"word": "Pragmático", "def": {"en": "practical and realistic.", "ru": "практичный, реалистичный.", "kk": "тәжірибелік әрі шынайы."}},
        {"word": "Omnipresente", "def": {"en": "present everywhere.", "ru": "вездесущий.", "kk": "барлық жерде бар."}},
        {"word": "Meticuloso", "def": {"en": "extremely careful and precise.", "ru": "очень тщательный.", "kk": "аса мұқият әрі дәл."}},
    ],
    "C1-C2": [
        {"word": "Efímero", "def": {"en": "lasting for a very short time.", "ru": "мимолётный.", "kk": "өте қысқа мерзімге созылатын."}},
        {"word": "Inefable", "def": {"en": "too great to be expressed in words.", "ru": "невыразимый словами.", "kk": "сөзбен айтып жеткізе алмайтын."}},
        {"word": "Perspicaz", "def": {"en": "having keen insight or judgment.", "ru": "проницательный.", "kk": "өткір пайымды, зерек."}},
        {"word": "Ostensible", "def": {"en": "apparent, seemingly true.", "ru": "кажущийся, показной.", "kk": "сырт көрінісінде дұрыс болып көрінетін."}},
        {"word": "Ambivalente", "def": {"en": "having mixed, contradictory feelings.", "ru": "амбивалентный, двойственный.", "kk": "қарама-қайшы сезімдер тудыратын."}},
    ],
}

WORDS_IT = {
    "A1-A2": [
        {"word": "Casa", "def": {"en": "house", "ru": "дом", "kk": "үй"}},
        {"word": "Amico", "def": {"en": "friend", "ru": "друг", "kk": "дос"}},
        {"word": "Scuola", "def": {"en": "school", "ru": "школа", "kk": "мектеп"}},
        {"word": "Famiglia", "def": {"en": "family", "ru": "семья", "kk": "отбасы"}},
        {"word": "Meteo", "def": {"en": "weather", "ru": "погода", "kk": "ауа райы"}},
    ],
    "B1-B2": [
        {"word": "Ambiguo", "def": {"en": "having more than one meaning; unclear.", "ru": "неоднозначный.", "kk": "бірнеше мағынасы бар."}},
        {"word": "Eloquente", "def": {"en": "fluent and persuasive in speech.", "ru": "красноречивый.", "kk": "шешен."}},
        {"word": "Pragmatico", "def": {"en": "practical and realistic.", "ru": "практичный.", "kk": "тәжірибелік әрі шынайы."}},
        {"word": "Onnipresente", "def": {"en": "present everywhere.", "ru": "вездесущий.", "kk": "барлық жерде бар."}},
        {"word": "Meticoloso", "def": {"en": "extremely careful and precise.", "ru": "очень тщательный.", "kk": "аса мұқият."}},
    ],
    "C1-C2": [
        {"word": "Effimero", "def": {"en": "lasting for a very short time.", "ru": "мимолётный.", "kk": "өте қысқа мерзімге созылатын."}},
        {"word": "Ineffabile", "def": {"en": "too great to be expressed in words.", "ru": "невыразимый.", "kk": "сөзбен жеткізе алмайтын."}},
        {"word": "Perspicace", "def": {"en": "having keen insight.", "ru": "проницательный.", "kk": "зерек, өткір пайымды."}},
        {"word": "Apparente", "def": {"en": "apparent, seemingly true.", "ru": "кажущийся.", "kk": "сырт көрінісінде дұрыс болып көрінетін."}},
        {"word": "Ambivalente", "def": {"en": "having mixed feelings.", "ru": "двойственный.", "kk": "қарама-қайшы сезімдер тудыратын."}},
    ],
}

WORDS_FR = {
    "A1-A2": [
        {"word": "Maison", "def": {"en": "house", "ru": "дом", "kk": "үй"}},
        {"word": "Ami", "def": {"en": "friend", "ru": "друг", "kk": "дос"}},
        {"word": "École", "def": {"en": "school", "ru": "школа", "kk": "мектеп"}},
        {"word": "Famille", "def": {"en": "family", "ru": "семья", "kk": "отбасы"}},
        {"word": "Météo", "def": {"en": "weather", "ru": "погода", "kk": "ауа райы"}},
    ],
    "B1-B2": [
        {"word": "Ambigu", "def": {"en": "having more than one meaning; unclear.", "ru": "неоднозначный.", "kk": "бірнеше мағынасы бар."}},
        {"word": "Éloquent", "def": {"en": "fluent and persuasive in speech.", "ru": "красноречивый.", "kk": "шешен."}},
        {"word": "Pragmatique", "def": {"en": "practical and realistic.", "ru": "практичный.", "kk": "тәжірибелік әрі шынайы."}},
        {"word": "Omniprésent", "def": {"en": "present everywhere.", "ru": "вездесущий.", "kk": "барлық жерде бар."}},
        {"word": "Méticuleux", "def": {"en": "extremely careful and precise.", "ru": "очень тщательный.", "kk": "аса мұқият."}},
    ],
    "C1-C2": [
        {"word": "Éphémère", "def": {"en": "lasting for a very short time.", "ru": "мимолётный.", "kk": "өте қысқа мерзімге созылатын."}},
        {"word": "Ineffable", "def": {"en": "too great to be expressed in words.", "ru": "невыразимый.", "kk": "сөзбен жеткізе алмайтын."}},
        {"word": "Perspicace", "def": {"en": "having keen insight.", "ru": "проницательный.", "kk": "зерек, өткір пайымды."}},
        {"word": "Ostensible", "def": {"en": "apparent, seemingly true.", "ru": "кажущийся.", "kk": "сырт көрінісінде дұрыс болып көрінетін."}},
        {"word": "Ambivalent", "def": {"en": "having mixed feelings.", "ru": "двойственный.", "kk": "қарама-қайшы сезімдер тудыратын."}},
    ],
}

# --- 4. IDIOMS ---
IDIOMS_EN = {
    "A1-A2": [
        {"idiom": "Nice to meet you", "meaning": {"en": "a polite greeting when meeting someone new.", "ru": "вежливое приветствие при знакомстве.", "kk": "танысу кезіндегі сыпайы сәлемдесу."}},
        {"idiom": "No worries", "meaning": {"en": "it's okay, don't worry.", "ru": "всё в порядке, не переживай.", "kk": "бәрі жақсы, алаңдама."}},
        {"idiom": "See you later", "meaning": {"en": "a casual way to say goodbye.", "ru": "неформальное прощание.", "kk": "бейресми қоштасу тіркесі."}},
        {"idiom": "Good job!", "meaning": {"en": "well done, praise for good work.", "ru": "молодец, похвала за хорошую работу.", "kk": "жарайсың, жақсы жұмыс үшін мақтау."}},
        {"idiom": "Take it easy", "meaning": {"en": "relax, don't stress.", "ru": "не напрягайся, расслабься.", "kk": "қобалжыма, тыныш бол."}},
    ],
    "B1-B2": [
        {"idiom": "A double-edged sword", "meaning": {"en": "something with both good and bad consequences.", "ru": "нечто имеющее и хорошие, и плохие последствия.", "kk": "жақсы да, жаман да салдары бар нәрсе."}},
        {"idiom": "To play devil's advocate", "meaning": {"en": "to argue against an idea to test it.", "ru": "спорить против идеи, чтобы проверить её.", "kk": "идеяны тексеру үшін оған қарсы дәлел айту."}},
        {"idiom": "The tip of the iceberg", "meaning": {"en": "a small visible part of a much bigger problem.", "ru": "малая видимая часть гораздо большей проблемы.", "kk": "үлкен мәселенің көрінетін кішкене бөлігі."}},
        {"idiom": "To hit the nail on the head", "meaning": {"en": "to describe exactly what is causing something.", "ru": "точно определить суть дела.", "kk": "мәселенің нақ өзін дәл айту."}},
        {"idiom": "Once in a blue moon", "meaning": {"en": "something that happens very rarely.", "ru": "то, что случается очень редко.", "kk": "өте сирек болатын нәрсе."}},
    ],
    "C1-C2": [
        {"idiom": "To read between the lines", "meaning": {"en": "to understand a hidden meaning.", "ru": "читать между строк.", "kk": "жасырын мағынаны түсіну."}},
        {"idiom": "A blessing in disguise", "meaning": {"en": "something good that seemed bad at first.", "ru": "нет худа без добра.", "kk": "алғашында жаман көрінген, кейін пайдалы болған нәрсе."}},
        {"idiom": "To bite the bullet", "meaning": {"en": "to face a difficult situation bravely.", "ru": "стиснуть зубы и терпеть.", "kk": "қиындықты батыл қабылдау."}},
        {"idiom": "To go the extra mile", "meaning": {"en": "to make more effort than expected.", "ru": "приложить больше усилий, чем требуется.", "kk": "қажеттіден артық күш салу."}},
        {"idiom": "Actions speak louder than words", "meaning": {"en": "what you do matters more than what you say.", "ru": "дела важнее слов.", "kk": "істің сөзден маңыздылығы."}},
    ],
}

IDIOMS_DE = {
    "A1-A2": [
        {"idiom": "Wie geht's?", "meaning": {"en": "How are you? (greeting)", "ru": "Как дела? (приветствие)", "kk": "Қалың қалай? (сәлемдесу тіркесі)"}},
        {"idiom": "Kein Problem", "meaning": {"en": "No problem.", "ru": "Без проблем.", "kk": "Ешбір мәселе жоқ."}},
        {"idiom": "Viel Spaß!", "meaning": {"en": "Have fun!", "ru": "Удачи, веселись!", "kk": "Сәттілік, көңілді өткіз!"}},
        {"idiom": "Alles klar!", "meaning": {"en": "Got it! All clear!", "ru": "Всё ясно!", "kk": "Бәрі түсінікті!"}},
        {"idiom": "Ich verstehe nicht.", "meaning": {"en": "I don't understand.", "ru": "Я не понимаю.", "kk": "Мен түсінбеймін."}},
    ],
    "B1-B2": [
        {"idiom": "Da liegt der Hund begraben", "meaning": {"en": "that's the real core of the problem.", "ru": "вот где собака зарыта (суть проблемы).", "kk": "мәселенің түйіні дәл осында."}},
        {"idiom": "Die Katze im Sack kaufen", "meaning": {"en": "to accept something without checking it first.", "ru": "купить кота в мешке.", "kk": "тексермей-ақ бірдеңені алу."}},
        {"idiom": "Den Nagel auf den Kopf treffen", "meaning": {"en": "to describe exactly what's essential.", "ru": "попасть в самую точку.", "kk": "мәселенің дәл өзін айту."}},
        {"idiom": "Um den heißen Brei reden", "meaning": {"en": "to avoid the main topic.", "ru": "ходить вокруг да около.", "kk": "негізгі тақырыпты айналып өту."}},
        {"idiom": "Die Nase voll haben", "meaning": {"en": "to have had enough of something.", "ru": "быть сытым по горло чем-то.", "kk": "бір нәрседен түңілу, жалығу."}},
    ],
    "C1-C2": [
        {"idiom": "Jemandem einen Bären aufbinden", "meaning": {"en": "to trick or deceive someone.", "ru": "обмануть, разыграть кого-то.", "kk": "біреуді алдау, ойнату."}},
        {"idiom": "Auf Wolke sieben schweben", "meaning": {"en": "to be extremely happy (on cloud nine).", "ru": "быть на седьмом небе от счастья.", "kk": "бақыттан ұшып жүру."}},
        {"idiom": "Etwas auf die lange Bank schieben", "meaning": {"en": "to postpone something indefinitely.", "ru": "откладывать в долгий ящик.", "kk": "бір нәрсені созбалаңға салу."}},
        {"idiom": "Den Wald vor lauter Bäumen nicht sehen", "meaning": {"en": "can't see the big picture for the details.", "ru": "за деревьями не видеть леса.", "kk": "ұсақ-түйекке бола үлкен суретті көрмеу."}},
        {"idiom": "Sich etwas zu Herzen nehmen", "meaning": {"en": "to take something to heart.", "ru": "принимать что-то близко к сердцу.", "kk": "бір нәрсені жүрекке жақын алу."}},
    ],
}

IDIOMS_RU = [
    {"idiom": "Сесть в лужу", "meaning": {"en": "to end up in an embarrassing situation.", "ru": "оказаться в неловком положении.", "kk": "ыңғайсыз жағдайға тап болу."}},
    {"idiom": "Водить за нос", "meaning": {"en": "to deceive someone.", "ru": "обманывать кого-то.", "kk": "біреуді алдау."}},
    {"idiom": "Бить баклуши", "meaning": {"en": "to be idle, waste time doing nothing.", "ru": "бездельничать.", "kk": "бос уақыт өткізу, еш нәрсе істемеу."}},
    {"idiom": "Держать язык за зубами", "meaning": {"en": "to keep quiet about something.", "ru": "молчать о чём-то, не выдавать секрет.", "kk": "бір нәрсе жайлы үндемеу, құпияны сақтау."}},
    {"idiom": "Как две капли воды", "meaning": {"en": "to look exactly alike.", "ru": "быть очень похожими друг на друга.", "kk": "бір-біріне өте ұқсас болу."}},
]

IDIOMS_KK = [
    {"idiom": "Тілі байланды", "meaning": {"kk": "сөйлей алмай, есінен танғандай халге түсу.", "ru": "лишиться дара речи от неожиданности.", "en": "to become speechless with shock."}},
    {"idiom": "Көзінің қарасындай көру", "meaning": {"kk": "біреуді немесе бірдеңені қатты қастерлеу.", "ru": "беречь кого-то как зеницу ока.", "en": "to cherish someone like the apple of one's eye."}},
    {"idiom": "Мұрнын көкке көтеру", "meaning": {"kk": "тым тәкаппар, паң болу.", "ru": "задирать нос, важничать.", "en": "to become arrogant."}},
    {"idiom": "Екі езуі құлағында", "meaning": {"kk": "өте қуанышты, риза болу.", "ru": "улыбаться до ушей от радости.", "en": "to be grinning from ear to ear."}},
    {"idiom": "Ит арқасы қияда", "meaning": {"kk": "істің оңға басып, сәті түсуі.", "ru": "дела идут в гору, всё складывается удачно.", "en": "things are going smoothly."}},
]

IDIOMS_ES = {
    "A1-A2": [
        {"idiom": "Mucho gusto", "meaning": {"en": "nice to meet you.", "ru": "приятно познакомиться.", "kk": "танысқаныма қуаныштымын."}},
        {"idiom": "No pasa nada", "meaning": {"en": "no worries, it's fine.", "ru": "ничего страшного.", "kk": "ештеңе етпейді."}},
        {"idiom": "Hasta luego", "meaning": {"en": "see you later.", "ru": "до скорого.", "kk": "кездескенше."}},
        {"idiom": "¡Buen trabajo!", "meaning": {"en": "good job!", "ru": "хорошая работа!", "kk": "жарайсың!"}},
        {"idiom": "Tranquilo/a", "meaning": {"en": "take it easy, relax.", "ru": "не переживай, расслабься.", "kk": "алаңдама, тыныш бол."}},
    ],
    "B1-B2": [
        {"idiom": "Estar en las nubes", "meaning": {"en": "to be daydreaming, absent-minded.", "ru": "витать в облаках.", "kk": "ойға шомып кету."}},
        {"idiom": "Costar un ojo de la cara", "meaning": {"en": "to cost a fortune.", "ru": "стоить целое состояние.", "kk": "өте қымбатқа түсу."}},
        {"idiom": "Meter la pata", "meaning": {"en": "to make a blunder.", "ru": "сделать промах.", "kk": "қателік жіберу."}},
        {"idiom": "No tener pelos en la lengua", "meaning": {"en": "to speak bluntly, without holding back.", "ru": "говорить без обиняков.", "kk": "тіке, ашық сөйлеу."}},
        {"idiom": "Ser pan comido", "meaning": {"en": "to be very easy (a piece of cake).", "ru": "быть проще простого.", "kk": "өте оңай болу."}},
    ],
    "C1-C2": [
        {"idiom": "Tirar la casa por la ventana", "meaning": {"en": "to spare no expense.", "ru": "не жалеть денег, шиковать.", "kk": "шығынды аямай жұмсау."}},
        {"idiom": "Hablar por los codos", "meaning": {"en": "to talk nonstop.", "ru": "говорить без умолку.", "kk": "тоқтаусыз сөйлеу."}},
        {"idiom": "Dar en el clavo", "meaning": {"en": "to hit the nail on the head.", "ru": "попасть в самую точку.", "kk": "мәселенің дәл өзін айту."}},
        {"idiom": "Irse por las ramas", "meaning": {"en": "to beat around the bush.", "ru": "ходить вокруг да около.", "kk": "негізгі тақырыпты айналып өту."}},
        {"idiom": "Poner los puntos sobre las íes", "meaning": {"en": "to clarify something precisely.", "ru": "расставить все точки над и.", "kk": "бәрін нақтылап түсіндіру."}},
    ],
}

IDIOMS_IT = {
    "A1-A2": [
        {"idiom": "Piacere di conoscerti", "meaning": {"en": "nice to meet you.", "ru": "приятно познакомиться.", "kk": "танысқаныма қуаныштымын."}},
        {"idiom": "Non c'è problema", "meaning": {"en": "no problem.", "ru": "нет проблем.", "kk": "мәселе жоқ."}},
        {"idiom": "Ci vediamo dopo", "meaning": {"en": "see you later.", "ru": "увидимся позже.", "kk": "кейін кездесеміз."}},
        {"idiom": "Ottimo lavoro!", "meaning": {"en": "great job!", "ru": "отличная работа!", "kk": "керемет жұмыс!"}},
        {"idiom": "Stai tranquillo/a", "meaning": {"en": "take it easy.", "ru": "не переживай.", "kk": "алаңдама."}},
    ],
    "B1-B2": [
        {"idiom": "In bocca al lupo", "meaning": {"en": "good luck.", "ru": "ни пуха ни пера.", "kk": "сәттілік."}},
        {"idiom": "Avere le mani in pasta", "meaning": {"en": "to be involved in something.", "ru": "быть причастным к делу.", "kk": "бір іске араласу."}},
        {"idiom": "Prendere due piccioni con una fava", "meaning": {"en": "to kill two birds with one stone.", "ru": "убить двух зайцев.", "kk": "бір оқпен екі қоян ату."}},
        {"idiom": "Non vedere l'ora", "meaning": {"en": "to be unable to wait for something.", "ru": "с нетерпением ждать.", "kk": "асыға күту."}},
        {"idiom": "Fare orecchie da mercante", "meaning": {"en": "to pretend not to hear.", "ru": "делать вид, что не слышишь.", "kk": "естімегенсіп жасалу."}},
    ],
    "C1-C2": [
        {"idiom": "Toccare il cielo con un dito", "meaning": {"en": "to be extremely happy.", "ru": "быть на седьмом небе от счастья.", "kk": "бақыттан ұшып жүру."}},
        {"idiom": "Rompere il ghiaccio", "meaning": {"en": "to break the ice.", "ru": "растопить лёд (в разговоре).", "kk": "мұзды еріту (сөйлесуде)."}},
        {"idiom": "Avere la coda di paglia", "meaning": {"en": "to have a guilty conscience.", "ru": "иметь нечистую совесть.", "kk": "ар-ұяты таза болмау."}},
        {"idiom": "Menare il can per l'aia", "meaning": {"en": "to beat around the bush.", "ru": "ходить вокруг да около.", "kk": "негізгі тақырыпты айналып өту."}},
        {"idiom": "Mettere il carro davanti ai buoi", "meaning": {"en": "to put the cart before the horse.", "ru": "ставить телегу впереди лошади.", "kk": "ретсіз, кезексіз іс істеу."}},
    ],
}

IDIOMS_FR = {
    "A1-A2": [
        {"idiom": "Enchanté(e)", "meaning": {"en": "nice to meet you.", "ru": "приятно познакомиться.", "kk": "танысқаныма қуаныштымын."}},
        {"idiom": "Pas de problème", "meaning": {"en": "no problem.", "ru": "без проблем.", "kk": "мәселе жоқ."}},
        {"idiom": "À plus tard", "meaning": {"en": "see you later.", "ru": "до скорого.", "kk": "кездескенше."}},
        {"idiom": "Bon travail !", "meaning": {"en": "good job!", "ru": "хорошая работа!", "kk": "жарайсың!"}},
        {"idiom": "Ne t'en fais pas", "meaning": {"en": "take it easy, don't worry.", "ru": "не переживай.", "kk": "алаңдама."}},
    ],
    "B1-B2": [
        {"idiom": "Avoir le cafard", "meaning": {"en": "to feel down, blue.", "ru": "хандрить, грустить.", "kk": "көңіл-күйі түсу."}},
        {"idiom": "Casser les pieds", "meaning": {"en": "to annoy someone.", "ru": "надоедать кому-то.", "kk": "біреуді мазалау."}},
        {"idiom": "Poser un lapin", "meaning": {"en": "to stand someone up.", "ru": "не прийти на встречу.", "kk": "кездесуге келмей қою."}},
        {"idiom": "Coûter les yeux de la tête", "meaning": {"en": "to cost a fortune.", "ru": "стоить целое состояние.", "kk": "өте қымбатқа түсу."}},
        {"idiom": "Avoir un chat dans la gorge", "meaning": {"en": "to have a frog in one's throat.", "ru": "першить в горле.", "kk": "тамақ ашуы."}},
    ],
    "C1-C2": [
        {"idiom": "Mettre les points sur les i", "meaning": {"en": "to clarify something precisely.", "ru": "расставить все точки над и.", "kk": "бәрін нақтылап түсіндіру."}},
        {"idiom": "Tourner autour du pot", "meaning": {"en": "to beat around the bush.", "ru": "ходить вокруг да около.", "kk": "негізгі тақырыпты айналып өту."}},
        {"idiom": "Ne pas y aller par quatre chemins", "meaning": {"en": "to get straight to the point.", "ru": "говорить без обиняков.", "kk": "тіке, ашық айту."}},
        {"idiom": "Avoir d'autres chats à fouetter", "meaning": {"en": "to have other priorities.", "ru": "иметь дела поважнее.", "kk": "маңыздырақ істері болу."}},
        {"idiom": "Se serrer les coudes", "meaning": {"en": "to stick together, support each other.", "ru": "держаться сообща.", "kk": "бірлесе қолдау көрсету."}},
    ],
}

# --- 5. BOOKS ---
# "term" = the actual word from the book, in the PRACTICE language.
# "meaning" = translation of what it means, per explain_lang (en/ru/kk).
# Leveled languages get DIFFERENT books per level (a beginner can't read '1984').
BOOKS_EN = {
    "A1-A2": [
        {"title": "'Diary of a Wimpy Kid' by Jeff Kinney", "tag": "Humor", "term": "Awkward", "meaning": {"en": "feeling embarrassed or uncomfortable.", "ru": "чувствующий смущение или неловкость.", "kk": "ыңғайсыздық немесе ұялу сезімін сезінетін."}},
        {"title": "'Charlotte's Web' by E.B. White", "tag": "Friendship", "term": "Runt", "meaning": {"en": "the smallest animal in a litter.", "ru": "самый маленький детёныш в помёте.", "kk": "төлдегі ең кішкентай төл."}},
        {"title": "'Because of Winn-Dixie' by Kate DiCamillo", "tag": "Friendship", "term": "Lonely", "meaning": {"en": "feeling sad because you are alone.", "ru": "чувствующий грусть от одиночества.", "kk": "жалғыздықтан мұңды сезінетін."}},
        {"title": "'Judy Moody' by Megan McDonald", "tag": "School Life", "term": "Mood", "meaning": {"en": "a temporary state of feeling.", "ru": "временное состояние настроения.", "kk": "уақытша көңіл-күй."}},
    ],
    "B1-B2": [
        {"title": "'Wonder' by R.J. Palacio", "tag": "School Life", "term": "Empathy", "meaning": {"en": "understanding others' feelings.", "ru": "понимание чувств других.", "kk": "басқалардың сезімін түсіну."}},
        {"title": "'The Giver' by Lois Lowry", "tag": "Society", "term": "Utopia", "meaning": {"en": "an imagined perfect place.", "ru": "воображаемое идеальное место.", "kk": "қиялдағы мінсіз орын."}},
        {"title": "'Animal Farm' by George Orwell", "tag": "Politics", "term": "Allegory", "meaning": {"en": "a story with a hidden meaning.", "ru": "история со скрытым смыслом.", "kk": "жасырын мағынасы бар әңгіме."}},
        {"title": "'Holes' by Louis Sachar", "tag": "Adventure", "term": "Injustice", "meaning": {"en": "unfair treatment of someone.", "ru": "несправедливое обращение с кем-то.", "kk": "біреуге әділетсіз қарау."}},
    ],
    "C1-C2": [
        {"title": "'1984' by George Orwell", "tag": "Freedom", "term": "Totalitarianism", "meaning": {"en": "absolute state control.", "ru": "абсолютный контроль государства.", "kk": "мемлекеттің толық бақылауы."}},
        {"title": "'Fahrenheit 451' by Ray Bradbury", "tag": "Media", "term": "Censorship", "meaning": {"en": "suppressing information.", "ru": "подавление информации.", "kk": "ақпаратты тежеу."}},
        {"title": "'Brave New World' by Aldous Huxley", "tag": "Society", "term": "Conditioning", "meaning": {"en": "training someone to behave a certain way.", "ru": "обучение кого-либо определённому поведению.", "kk": "біреуді белгілі бір тәртіпке үйрету."}},
        {"title": "'Lord of the Flies' by William Golding", "tag": "Human Nature", "term": "Savagery", "meaning": {"en": "extremely cruel or violent behavior.", "ru": "крайне жестокое поведение.", "kk": "өте қатыгез мінез-құлық."}},
    ],
}

BOOKS_DE = {
    "A1-A2": [
        {"title": "«Rico, Oskar und die Tieferschatten» – Andreas Steinhöfel", "tag": "Freundschaft", "term": "Ängstlich", "meaning": {"en": "fearful, anxious.", "ru": "тревожный, боязливый.", "kk": "қорқынышты, үрейлі."}},
        {"title": "«Die Sams» – Paul Maar", "tag": "Fantasie", "term": "Wunsch", "meaning": {"en": "a desire or wish.", "ru": "желание.", "kk": "тілек."}},
        {"title": "«Emil und die Detektive» – Erich Kästner", "tag": "Abenteuer", "term": "Zusammenhalt", "meaning": {"en": "acting together for a goal.", "ru": "совместные действия ради цели.", "kk": "ортақ мақсат үшін бірге әрекет ету."}},
        {"title": "«Das doppelte Lottchen» – Erich Kästner", "tag": "Familie", "term": "Zwilling", "meaning": {"en": "a twin.", "ru": "близнец.", "kk": "егіз."}},
    ],
    "B1-B2": [
        {"title": "«Die Welle» – Todd Strasser", "tag": "Gesellschaft", "term": "Konformität", "meaning": {"en": "going along with the group.", "ru": "подчинение группе.", "kk": "топқа бағыну."}},
        {"title": "«Tschick» – Wolfgang Herrndorf", "tag": "Freundschaft", "term": "Außenseiter", "meaning": {"en": "someone who doesn't belong.", "ru": "тот, кто не вписывается.", "kk": "топқа сыймайтын адам."}},
        {"title": "«Momo» – Michael Ende", "tag": "Zeit", "term": "Achtsamkeit", "meaning": {"en": "being aware of the present.", "ru": "внимание к настоящему моменту.", "kk": "қазіргі сәтке мән беру."}},
        {"title": "«Krabat» – Otfried Preußler", "tag": "Fantasie", "term": "Macht", "meaning": {"en": "control or power over others.", "ru": "власть, контроль над другими.", "kk": "басқаларға билік жүргізу."}},
    ],
    "C1-C2": [
        {"title": "«Die Verwandlung» – Franz Kafka", "tag": "Identität", "term": "Entfremdung", "meaning": {"en": "feeling disconnected from others.", "ru": "чувство оторванности от других.", "kk": "басқалардан алшақтау сезімі."}},
        {"title": "«Der Steppenwolf» – Hermann Hesse", "tag": "Philosophie", "term": "Zerrissenheit", "meaning": {"en": "inner conflict, being torn between two selves.", "ru": "внутренний разлад, раздвоенность.", "kk": "ішкі қайшылық, екіге бөлінген күй."}},
        {"title": "«Der Vorleser» – Bernhard Schlink", "tag": "Geschichte", "term": "Schuld", "meaning": {"en": "guilt, responsibility for wrongdoing.", "ru": "вина, ответственность за проступок.", "kk": "кінә, жасаған қателігі үшін жауапкершілік."}},
        {"title": "«Homo Faber» – Max Frisch", "tag": "Schicksal", "term": "Zufall", "meaning": {"en": "chance, coincidence.", "ru": "случайность.", "kk": "кездейсоқтық."}},
    ],
}

BOOKS_RU = [
    {"title": "«Мастер и Маргарита» — Михаил Булгаков", "tag": "Философия", "term": "Аллегория", "meaning": {"en": "a story with a hidden meaning.", "ru": "история со скрытым смыслом.", "kk": "жасырын мағынасы бар әңгіме."}},
    {"title": "«Дети подземелья» — Владимир Короленко", "tag": "Общество", "term": "Сострадание", "meaning": {"en": "sympathy for others.", "ru": "сочувствие другим.", "kk": "басқаларға жанашырлық."}},
    {"title": "«Дубровский» — Александр Пушкин", "tag": "Справедливость", "term": "Справедливость", "meaning": {"en": "fairness and moral rightness.", "ru": "нравственная правота.", "kk": "адалдық пен растық."}},
    {"title": "«Судьба человека» — Михаил Шолохов", "tag": "Война", "term": "Стойкость", "meaning": {"en": "the ability to recover from hardship.", "ru": "способность преодолевать трудности.", "kk": "қиындықтан қайта қалпына келу қабілеті."}},
]

BOOKS_KK = [
    {"title": "«Абай жолы» – Мұхтар Әуезов", "tag": "Тарих", "term": "Тағдыр", "meaning": {"kk": "адам өмірінің бағыты.", "ru": "предопределённый ход жизни человека.", "en": "the predetermined course of one's life."}},
    {"title": "«Менің атым Қожа» – Бердібек Соқпақбаев", "tag": "Мектеп өмірі", "term": "Жауапкершілік", "meaning": {"kk": "өз әрекетің үшін жауап беру.", "ru": "обязанность отвечать за свои поступки.", "en": "being accountable for one's actions."}},
    {"title": "«Көшпенділер» – Ілияс Есенберлин", "tag": "Тарих", "term": "Азаттық", "meaning": {"kk": "тәуелсіздік, еркіндік.", "ru": "независимость.", "en": "independence."}},
    {"title": "«Ұлпан» – Ғабит Мүсірепов", "tag": "Қоғам", "term": "Әділдік", "meaning": {"kk": "растық пен адалдық.", "ru": "правда и честность.", "en": "fairness and honesty."}},
]

BOOKS_ES = {
    "A1-A2": [
        {"title": "'El Principito' – Antoine de Saint-Exupéry", "tag": "Filosofía", "term": "Esencial", "meaning": {"en": "what truly matters.", "ru": "то, что действительно важно.", "kk": "шынымен мәні бар нәрсе."}},
        {"title": "'Platero y yo' – Juan Ramón Jiménez", "tag": "Naturaleza", "term": "Ternura", "meaning": {"en": "tenderness, gentle affection.", "ru": "нежность.", "kk": "нәзіктік."}},
        {"title": "'Cuentos de la selva' – Horacio Quiroga", "tag": "Aventura", "term": "Selva", "meaning": {"en": "jungle, forest.", "ru": "джунгли, лес.", "kk": "джунгли, орман."}},
        {"title": "'Marcelino Pan y Vino' – José María Sánchez Silva", "tag": "Amistad", "term": "Bondad", "meaning": {"en": "kindness, goodness.", "ru": "доброта.", "kk": "мейірімділік."}},
    ],
    "B1-B2": [
        {"title": "'Como agua para chocolate' – Laura Esquivel", "tag": "Tradición", "term": "Pasión", "meaning": {"en": "intense, powerful emotion.", "ru": "сильное, глубокое чувство.", "kk": "қатты, терең сезім."}},
        {"title": "'El túnel' – Ernesto Sabato", "tag": "Psicología", "term": "Obsesión", "meaning": {"en": "a fixed, intense preoccupation.", "ru": "навязчивая, сильная поглощённость чем-то.", "kk": "бір нәрсеге қатты құмарту."}},
        {"title": "'La casa de los espíritus' – Isabel Allende", "tag": "Familia", "term": "Destino", "meaning": {"en": "the predetermined course of events.", "ru": "предопределённый ход событий.", "kk": "алдын ала белгіленген өмір барысы."}},
        {"title": "'Réquiem por un campesino español' – Ramón J. Sender", "tag": "Guerra", "term": "Traición", "meaning": {"en": "betrayal.", "ru": "предательство.", "kk": "опасыздық."}},
    ],
    "C1-C2": [
        {"title": "'Cien años de soledad' – Gabriel García Márquez", "tag": "Realismo mágico", "term": "Soledad", "meaning": {"en": "the state of being alone.", "ru": "состояние уединения.", "kk": "жалғыз қалу күйі."}},
        {"title": "'Rayuela' – Julio Cortázar", "tag": "Literatura experimental", "term": "Ambigüedad", "meaning": {"en": "ambiguity.", "ru": "двусмысленность.", "kk": "екіұштылық."}},
        {"title": "'Pedro Páramo' – Juan Rulfo", "tag": "Realismo mágico", "term": "Fantasma", "meaning": {"en": "ghost, apparition.", "ru": "призрак.", "kk": "елес, аруақ."}},
        {"title": "'La casa de Bernarda Alba' – Federico García Lorca", "tag": "Teatro", "term": "Represión", "meaning": {"en": "repression.", "ru": "подавление, репрессия.", "kk": "басып-жаншу, репрессия."}},
    ],
}

BOOKS_IT = {
    "A1-A2": [
        {"title": "'Il piccolo principe' – Antoine de Saint-Exupéry", "tag": "Filosofia", "term": "Essenziale", "meaning": {"en": "what truly matters.", "ru": "то, что действительно важно.", "kk": "шынымен мәні бар нәрсе."}},
        {"title": "'Pinocchio' – Carlo Collodi", "tag": "Avventura", "term": "Bugia", "meaning": {"en": "a lie.", "ru": "ложь.", "kk": "өтірік."}},
        {"title": "'Cuore' – Edmondo De Amicis", "tag": "Scuola", "term": "Amicizia", "meaning": {"en": "friendship.", "ru": "дружба.", "kk": "достық."}},
        {"title": "'Marcovaldo' – Italo Calvino", "tag": "Vita quotidiana", "term": "Nostalgia", "meaning": {"en": "nostalgia.", "ru": "ностальгия.", "kk": "аңсау сезімі."}},
    ],
    "B1-B2": [
        {"title": "'Io non ho paura' – Niccolò Ammaniti", "tag": "Infanzia", "term": "Paura", "meaning": {"en": "fear.", "ru": "страх.", "kk": "қорқыныш."}},
        {"title": "'L'isola di Arturo' – Elsa Morante", "tag": "Crescita", "term": "Solitudine", "meaning": {"en": "solitude.", "ru": "одиночество.", "kk": "жалғыздық."}},
        {"title": "'Va' dove ti porta il cuore' – Susanna Tamaro", "tag": "Famiglia", "term": "Rimpianto", "meaning": {"en": "regret.", "ru": "сожаление.", "kk": "өкіну."}},
        {"title": "'Il nome della rosa' – Umberto Eco", "tag": "Mistero", "term": "Verità", "meaning": {"en": "what is actually real.", "ru": "то, что действительно реально.", "kk": "шынайы болған нәрсе."}},
    ],
    "C1-C2": [
        {"title": "'Il fu Mattia Pascal' – Luigi Pirandello", "tag": "Identità", "term": "Identità", "meaning": {"en": "who a person truly is.", "ru": "то, кем человек является на самом деле.", "kk": "адамның шынайы болмысы."}},
        {"title": "'Se questo è un uomo' – Primo Levi", "tag": "Memoria", "term": "Dignità", "meaning": {"en": "the value and worth of a person.", "ru": "ценность и значимость человека.", "kk": "адамның құндылығы."}},
        {"title": "'La coscienza di Zeno' – Italo Svevo", "tag": "Psicologia", "term": "Coscienza", "meaning": {"en": "awareness of oneself.", "ru": "осознание себя.", "kk": "өзін-өзі түйсіну."}},
        {"title": "'Se una notte d'inverno un viaggiatore' – Italo Calvino", "tag": "Metaletteratura", "term": "Narrazione", "meaning": {"en": "storytelling, narration.", "ru": "повествование.", "kk": "әңгімелеу."}},
    ],
}

BOOKS_FR = {
    "A1-A2": [
        {"title": "'Le Petit Prince' – Antoine de Saint-Exupéry", "tag": "Philosophie", "term": "Essentiel", "meaning": {"en": "what truly matters.", "ru": "то, что действительно важно.", "kk": "шынымен мәні бар нәрсе."}},
        {"title": "'Le Petit Nicolas' – René Goscinny", "tag": "École", "term": "Bêtise", "meaning": {"en": "a silly or foolish act.", "ru": "глупый поступок.", "kk": "ақымақтық іс."}},
        {"title": "'Charlie et la Chocolaterie' – Roald Dahl", "tag": "Aventure", "term": "Gourmandise", "meaning": {"en": "greed for food or sweets.", "ru": "чревоугодие, жадность до сладкого.", "kk": "тәтті нәрсеге құмарлық."}},
        {"title": "'Poil de Carotte' – Jules Renard", "tag": "Famille", "term": "Injustice", "meaning": {"en": "unfair treatment.", "ru": "несправедливость.", "kk": "әділетсіздік."}},
    ],
    "B1-B2": [
        {"title": "'No et moi' – Delphine de Vigan", "tag": "Société", "term": "Solitude", "meaning": {"en": "the state of being alone.", "ru": "состояние уединения.", "kk": "жалғыз қалу күйі."}},
        {"title": "'L'Élégance du hérisson' – Muriel Barbery", "tag": "Société", "term": "Apparence", "meaning": {"en": "outward appearance versus reality.", "ru": "внешний вид в противовес реальности.", "kk": "сырт көрінісі мен шынайылықтың айырмашылығы."}},
        {"title": "'Kiffe kiffe demain' – Faïza Guène", "tag": "Identité", "term": "Banlieue", "meaning": {"en": "suburb, outskirts of a city.", "ru": "пригород, окраина города.", "kk": "қала маңы."}},
        {"title": "'La Gloire de mon père' – Marcel Pagnol", "tag": "Enfance", "term": "Souvenir", "meaning": {"en": "a memory.", "ru": "воспоминание.", "kk": "естелік."}},
    ],
    "C1-C2": [
        {"title": "'L'Étranger' – Albert Camus", "tag": "Philosophie", "term": "Absurde", "meaning": {"en": "lacking apparent logical meaning.", "ru": "лишённое видимого логического смысла.", "kk": "логикалық мағынасы жоқтай көрінетін."}},
        {"title": "'Les Misérables' – Victor Hugo", "tag": "Justice sociale", "term": "Rédemption", "meaning": {"en": "being saved from wrongdoing.", "ru": "освобождение от вины через исправление.", "kk": "кінәні түзету арқылы құтылу."}},
        {"title": "'Huis clos' – Jean-Paul Sartre", "tag": "Philosophie", "term": "Enfer", "meaning": {"en": "hell (here, a metaphor for other people).", "ru": "ад (здесь — метафора для других людей).", "kk": "тозақ (мұнда — басқа адамдарға метафора)."}},
        {"title": "'Madame Bovary' – Gustave Flaubert", "tag": "Société", "term": "Désillusion", "meaning": {"en": "disillusionment.", "ru": "разочарование.", "kk": "көңілі қалу."}},
    ],
}

BOOKS = {"en": BOOKS_EN, "de": BOOKS_DE, "ru": BOOKS_RU, "kk": BOOKS_KK, "es": BOOKS_ES, "it": BOOKS_IT, "fr": BOOKS_FR}

def get_books_pool(p_lang, lvl):
    if p_lang in LEVELED_LANGS:
        return BOOKS[p_lang][lvl]
    return BOOKS[p_lang]

# --- helpers to fetch the right pool ---
def get_word_pool(p_lang, lvl):
    if p_lang in LEVELED_LANGS:
        return {"en": WORDS_EN, "de": WORDS_DE, "es": WORDS_ES, "it": WORDS_IT, "fr": WORDS_FR}[p_lang][lvl]
    return {"ru": WORDS_RU, "kk": WORDS_KK}[p_lang]

def get_idiom_pool(p_lang, lvl):
    if p_lang in LEVELED_LANGS:
        return {"en": IDIOMS_EN, "de": IDIOMS_DE, "es": IDIOMS_ES, "it": IDIOMS_IT, "fr": IDIOMS_FR}[p_lang][lvl]
    return {"ru": IDIOMS_RU, "kk": IDIOMS_KK}[p_lang]

word_pool = get_word_pool(practice_lang, level)
idiom_pool = get_idiom_pool(practice_lang, level)

day_of_year = datetime.date.today().timetuple().tm_yday
today_word = word_pool[day_of_year % len(word_pool)]
today_idiom = idiom_pool[day_of_year % len(idiom_pool)]

# --- 6. SIDEBAR ---
with st.sidebar:
    header_suffix = f" ({PRACTICE_LANGS[practice_lang]['label']}, {level})" if practice_lang in LEVELED_LANGS else f" ({PRACTICE_LANGS[practice_lang]['label']})"
    st.header(t["sidebar_header"] + header_suffix)

    st.success(f"**{t['word_of_day']}**\n\n**{today_word['word']}** — {today_word['def'][explain_lang]}")
    st.info(f"**{t['idiom_of_day']}**\n\n**'{today_idiom['idiom']}'** — {today_idiom['meaning'][explain_lang]}")
    st.write("---")

    st.subheader(t["articles_header"])
    ARTICLES = {
        "en": {
            "A1-A2": [("News in Levels (Level 1-2)", "https://www.newsinlevels.com/"),
                      ("BBC Learning English", "https://www.bbc.co.uk/learningenglish/")],
            "B1-B2": [("News in Levels (Level 3)", "https://www.newsinlevels.com/"),
                      ("BBC Learning English - 6 Minute English", "https://www.bbc.co.uk/learningenglish/english/features/6-minute-english")],
            "C1-C2": [("Teen Vogue", "https://www.teenvogue.com/"),
                      ("BBC News", "https://www.bbc.com/news")],
        },
        "de": {
            "A1-A2": [("Nachrichtenleicht", "https://www.nachrichtenleicht.de/"),
                      ("DW Learn German", "https://learngerman.dw.com/")],
            "B1-B2": [("DW Learn German - Nachrichten", "https://learngerman.dw.com/"),
                      ("Nachrichtenleicht", "https://www.nachrichtenleicht.de/")],
            "C1-C2": [("Deutsche Welle", "https://www.dw.com/de/themen/s-9077"),
                      ("Tagesschau", "https://www.tagesschau.de/")],
        },
        "es": {
            "A1-A2": [("Duolingo Stories", "https://stories.duolingo.com/"),
                      ("Spanish Playground", "https://spanishplayground.net/")],
            "B1-B2": [("20 Minutos", "https://www.20minutos.es/"),
                      ("BBC Mundo", "https://www.bbc.com/mundo")],
            "C1-C2": [("El País", "https://elpais.com/"),
                      ("BBC Mundo", "https://www.bbc.com/mundo")],
        },
        "it": {
            "A1-A2": [("Podcast Italiano (transcript facili)", "https://podcastitaliano.com/"),
                      ("One World Italiano", "https://oneworlditaliano.com/")],
            "B1-B2": [("Il Post", "https://www.ilpost.it/"),
                      ("Podcast Italiano", "https://podcastitaliano.com/")],
            "C1-C2": [("Corriere della Sera", "https://www.corriere.it/"),
                      ("Internazionale", "https://www.internazionale.it/")],
        },
        "fr": {
            "A1-A2": [("Podcast Français Facile", "https://www.podcastfrancaisfacile.com/"),
                      ("1jour1actu", "https://www.1jour1actu.com/")],
            "B1-B2": [("1jour1actu", "https://www.1jour1actu.com/"),
                      ("RFI Savoirs", "https://savoirs.rfi.fr/")],
            "C1-C2": [("RFI", "https://www.rfi.fr/fr/"),
                      ("France Culture", "https://www.radiofrance.fr/franceculture")],
        },
        "ru": [("N+1", "https://nplus1.ru/"), ("ПостНаука", "https://postnauka.ru/"), ("Arzamas", "https://arzamas.academy/")],
        "kk": [("Abai.kz", "https://abai.kz/"), ("Adebiportal.kz", "https://adebiportal.kz/"), ("Massaget.kz", "https://massaget.kz/")],
    }

    if practice_lang in LEVELED_LANGS:
        article_links = ARTICLES[practice_lang][level]
    else:
        article_links = ARTICLES[practice_lang]

    st.markdown("\n".join(f"* **[{name}]({url})**" for name, url in article_links))

    books_pool = get_books_pool(practice_lang, level)
    week_num = datetime.date.today().isocalendar()[1]
    random.seed(week_num)
    weekly_selection = random.sample(books_pool, min(4, len(books_pool)))

    st.subheader(f"{t['books_header']} ({week_num})")
    for book in weekly_selection:
        st.markdown(f"* **{book['title']}** ({book['tag']})")

    st.write("---")
    st.subheader(t["vocab_header"])
    for book in weekly_selection:
        st.info(f"**{book['title']}**\n\n**{book['term']}** — {book['meaning'][explain_lang]}")

# --- 7. TOPICS ---
TOPICS_EN = {
    "A1-A2": [
        "Talk about your family.",
        "What is your favorite food?",
        "Describe your bedroom.",
        "What do you do on weekends?",
        "Talk about your best friend.",
        "What is your favorite season?",
        "What is your favorite school subject?",
        "Describe a normal school day.",
    ],
    "B1-B2": [
        "School Uniform: Does it destroy our individuality?",
        "Homework: Should it be banned for more free time?",
        "Social Media: Does Instagram make us feel more insecure?",
        "Video Games: Are they a waste of time or develop logic?",
        "Friendship: Is it better to have one best friend or many acquaintances?",
        "Travel: Does visiting other countries change our worldview?",
        "Conformity: Is it better to be like everyone else or to be a rebel?",
        "Digital Literacy: Should we trust everything we read in the news?",
        "Society: Is a perfect 'Utopia' actually possible or is it boring?",
        "Boredom: In a world of smartphones, have we forgotten how to just think?",
    ],
    "C1-C2": [
        "Should artificial intelligence have the right to create art?",
        "Is a perfect 'Utopia' actually possible, or would it be boring?",
        "Should parents have the right to check their children's phones?",
        "Should we spend money exploring Mars, or fix Earth first?",
        "How can we implement sustainable habits at school?",
        "In a world full of smartphones, have we forgotten how to just think?",
        "Is conformity safer than rebellion, in the end?",
        "Can algorithms ever create 'real' art, or is it just imitation?",
    ],
}

TOPICS_DE = {
    "A1-A2": [
        "Erzähle über deine Familie.",
        "Was isst du gern zum Frühstück?",
        "Beschreibe dein Zimmer.",
        "Was machst du am Wochenende?",
        "Erzähle über deinen besten Freund.",
        "Welche Jahreszeit magst du am meisten?",
        "Was ist dein Lieblingsfach in der Schule?",
        "Beschreibe einen typischen Schultag.",
    ],
    "B1-B2": [
        "Schuluniform: Zerstört sie unsere Individualität?",
        "Hausaufgaben: Sollten sie abgeschafft werden, um mehr Freizeit zu haben?",
        "Soziale Medien: Macht Instagram uns unsicherer?",
        "Videospiele: Zeitverschwendung oder fördern sie logisches Denken?",
        "Sport: Sollte Sportunterricht freiwillig sein?",
        "Freundschaft: Ist es besser, einen besten Freund zu haben oder viele Bekannte?",
        "Taschengeld: Sollten Eltern Kinder für Hausarbeit bezahlen?",
        "Reisen: Verändert das Besuchen anderer Länder unsere Weltsicht?",
        "Energydrinks: Sollten sie für Jugendliche unter 16 verboten werden?",
        "Online-Freunde: Kann jemand, den man nie getroffen hat, ein echter bester Freund sein?",
    ],
    "C1-C2": [
        "Künstliche Intelligenz: Sollte sie das Recht haben, kreative Werke zu schaffen?",
        "Digitale Kompetenz: Sollten wir allem glauben, was wir in den Nachrichten lesen?",
        "Konformität: Ist es besser, wie alle anderen zu sein, oder ein Rebell zu sein?",
        "Gesellschaft: Ist eine perfekte 'Utopie' überhaupt möglich, oder wäre sie langweilig?",
        "Privatsphäre vs. Sicherheit: Sollten Eltern das Recht haben, die Handys ihrer Kinder zu überprüfen?",
        "Weltraumforschung: Sollten wir Geld für den Mars ausgeben oder zuerst die Erde retten?",
        "Nachhaltigkeit: Wie können wir grüne Gewohnheiten in unserer Schule umsetzen?",
        "Langeweile: Haben wir in einer Welt voller Smartphones verlernt, einfach nachzudenken?",
    ],
}

TOPICS_RU = [
    "Можно ли простить, если не можешь забыть?",
    "Меняет ли язык, на котором мы думаем, то, как мы видим мир?",
    "Свобода — это отсутствие ограничений или способность выбирать между ними?",
    "Что важнее: быть понятым или быть услышанным?",
    "Может ли ностальгия быть опаснее забвения?",
    "Если бы можно было прожить жизнь заново, изменили бы вы главное решение?",
    "Где заканчивается традиция и начинается застой?",
    "Можно ли быть по-настоящему собой среди чужих ожиданий?",
    "Что определяет человека больше — его выбор или его обстоятельства?",
    "Существует ли объективная истина, или всё — вопрос перспективы?",
]

TOPICS_KK = [
    "Кешіру мен ұмыту бір нәрсе ме, әлде екеуі мүлдем бөлек пе?",
    "Ойлайтын тіліміз дүниені қабылдау тәсілімізді өзгерте ме?",
    "Еркіндік — шектеудің жоқтығы ма, әлде таңдау жасай білу қабілеті ме?",
    "Түсінілу маңызды ма, әлде тыңдалу маңызды ма?",
    "Ностальгия ұмытудан да қауіпті бола ала ма?",
    "Өмірді қайта бастауға мүмкіндік болса, басты шешіміңді өзгертер ме едің?",
    "Дәстүр қай жерде аяқталып, тоқырау қай жерден басталады?",
    "Басқалардың күтулері арасында шынайы өзің бола алу мүмкін бе?",
    "Адамды таңдауы анықтай ма, әлде оның жағдайлары ма?",
    "Объективті ақиқат бар ма, әлде бәрі көзқарасқа байланысты ма?",
]

TOPICS_ES = {
    "A1-A2": [
        "Cuéntame sobre tu familia.",
        "¿Qué te gusta comer los fines de semana?",
        "Describe tu ciudad.",
        "¿Cuál es tu deporte favorito?",
        "Habla sobre tu mejor amigo.",
        "¿Qué haces en tus vacaciones?",
        "Describe un día típico en tu escuela.",
        "¿Cuál es tu color favorito y por qué?",
    ],
    "B1-B2": [
        "Las redes sociales: ¿nos acercan o nos aíslan?",
        "¿Deberían los jóvenes trabajar mientras estudian?",
        "El fútbol: ¿un deporte o una religión en algunos países?",
        "¿Es mejor vivir en una ciudad grande o en un pueblo pequeño?",
        "Las tradiciones familiares: ¿deberíamos mantenerlas o modernizarlas?",
        "¿Debería prohibirse el uso del celular en las escuelas?",
        "La fama en redes sociales: ¿es un logro real?",
        "El turismo: ¿beneficia o daña a las comunidades locales?",
        "¿Deberían los adolescentes tener más independencia?",
        "¿Es mejor aprender de los propios errores o de los consejos de otros?",
    ],
    "C1-C2": [
        "¿Puede una lengua morir junto con sus últimos hablantes, o sobrevive de otra forma?",
        "¿La identidad cultural es algo que se hereda o algo que se elige?",
        "¿Es posible ser bilingüe sin pertenecer completamente a ninguna de las dos culturas?",
        "¿La globalización enriquece las culturas locales o las borra?",
        "¿El arte debe tener un propósito social, o basta con que sea bello?",
        "¿Podemos confiar plenamente en la memoria colectiva de un pueblo?",
        "¿La libertad individual debe ceder ante el bien común?",
        "¿Existe una verdadera meritocracia, o es solo una ilusión conveniente?",
    ],
}

TOPICS_IT = {
    "A1-A2": [
        "Parlami della tua famiglia.",
        "Cosa ti piace mangiare la domenica?",
        "Descrivi la tua città.",
        "Qual è il tuo sport preferito?",
        "Parlami del tuo migliore amico.",
        "Cosa fai durante le vacanze?",
        "Descrivi una giornata tipica a scuola.",
        "Qual è il tuo colore preferito e perché?",
    ],
    "B1-B2": [
        "I social media: ci avvicinano o ci isolano?",
        "È giusto che gli adolescenti lavorino mentre studiano?",
        "Il calcio: uno sport o una vera passione nazionale?",
        "Meglio vivere in una grande città o in un piccolo paese?",
        "Le tradizioni di famiglia: mantenerle o modernizzarle?",
        "Bisognerebbe vietare i cellulari a scuola?",
        "La fama sui social è un vero successo?",
        "Il turismo di massa danneggia le città d'arte?",
        "Gli adolescenti dovrebbero avere più indipendenza?",
        "È meglio imparare dai propri errori o dai consigli degli altri?",
    ],
    "C1-C2": [
        "Una lingua può morire con i suoi ultimi parlanti, o sopravvive in altre forme?",
        "L'identità culturale si eredita o si sceglie?",
        "Si può essere bilingue senza appartenere del tutto a nessuna delle due culture?",
        "La globalizzazione arricchisce le culture locali o le cancella?",
        "L'arte deve avere uno scopo sociale, o basta che sia bella?",
        "Possiamo fidarci pienamente della memoria collettiva di un popolo?",
        "La libertà individuale deve cedere di fronte al bene comune?",
        "Esiste una vera meritocrazia, o è solo un'illusione comoda?",
    ],
}

TOPICS_FR = {
    "A1-A2": [
        "Parle-moi de ta famille.",
        "Qu'est-ce que tu aimes manger le week-end?",
        "Décris ta ville.",
        "Quel est ton sport préféré?",
        "Parle-moi de ton meilleur ami.",
        "Que fais-tu pendant les vacances?",
        "Décris une journée typique à l'école.",
        "Quelle est ta couleur préférée et pourquoi?",
    ],
    "B1-B2": [
        "Les réseaux sociaux nous rapprochent-ils ou nous isolent-ils?",
        "Les adolescents devraient-ils travailler pendant leurs études?",
        "Le football: un sport ou une véritable passion nationale?",
        "Vaut-il mieux vivre dans une grande ville ou un petit village?",
        "Les traditions familiales: faut-il les garder ou les moderniser?",
        "Faudrait-il interdire les téléphones portables à l'école?",
        "La célébrité sur les réseaux sociaux est-elle une vraie réussite?",
        "Le tourisme de masse nuit-il aux villes historiques?",
        "Les adolescents devraient-ils avoir plus d'indépendance?",
        "Vaut-il mieux apprendre de ses propres erreurs ou des conseils des autres?",
    ],
    "C1-C2": [
        "Une langue peut-elle mourir avec ses derniers locuteurs, ou survit-elle autrement?",
        "L'identité culturelle s'hérite-t-elle ou se choisit-elle?",
        "Peut-on être bilingue sans appartenir pleinement à aucune des deux cultures?",
        "La mondialisation enrichit-elle les cultures locales ou les efface-t-elle?",
        "L'art doit-il avoir un but social, ou suffit-il qu'il soit beau?",
        "Peut-on vraiment faire confiance à la mémoire collective d'un peuple?",
        "La liberté individuelle doit-elle céder face au bien commun?",
        "Existe-t-il une véritable méritocratie, ou n'est-ce qu'une illusion commode?",
    ],
}

def get_topic_pool(p_lang, lvl):
    if p_lang in LEVELED_LANGS:
        return {"en": TOPICS_EN, "de": TOPICS_DE, "es": TOPICS_ES, "it": TOPICS_IT, "fr": TOPICS_FR}[p_lang][lvl]
    return {"ru": TOPICS_RU, "kk": TOPICS_KK}[p_lang]

# --- 8. MAIN INTERFACE ---
st.title(t["title"])
st.write(t["subtitle"])

if "topic" not in st.session_state or st.session_state.topic is None:
    st.session_state.topic = t["click_button"]

if st.button(t["get_topic"]):
    random.seed()
    st.session_state.topic = random.choice(get_topic_pool(practice_lang, level))

st.warning(f"**{t['current_topic']}** {st.session_state.topic}")

# --- 9. THE RECORDER ---
st.subheader(t["step1"])
audio = mic_recorder(
    start_prompt=t["start_recording"],
    stop_prompt=t["stop_recording"],
    key='recorder'
)

if audio:
    st.audio(audio['bytes'])
    st.subheader(t["step2"])
    with st.spinner(t["analyzing"]):
        try:
            audio_data = {"mime_type": "audio/wav", "data": audio['bytes']}

            feedback_lang_name = {"en": "English", "ru": "Russian", "kk": "Kazakh"}[explain_lang]
            practice_lang_name = PRACTICE_LANGS[practice_lang]["label"]
            level_note = f" The student's level is {level}." if practice_lang in LEVELED_LANGS else ""

            prompt = (
                f"Topic (spoken in {practice_lang_name}): {st.session_state.topic}. "
                f"{level_note} Evaluate the student's grammar and vocabulary in {practice_lang_name}, "
                f"and give 3 tips to improve. "
                f"Write your entire feedback in {feedback_lang_name}, since the student may not yet "
                f"understand {practice_lang_name} explanations. "
                f"Speak as a supportive tutor for a school student."
            )

            response = model.generate_content([prompt, audio_data])
            st.success(t["feedback_ready"])
            st.markdown(response.text)
        except Exception as e:
            st.error(f"{t['error']} {e}")
