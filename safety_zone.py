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
# TWO SEPARATE LANGUAGE CONCEPTS:
#   explain_lang  -> the language the STUDENT understands (UI text, and
#                     the meaning/translation of new words, idioms, books)
#   practice_lang -> the language the STUDENT IS PRACTICING SPEAKING
#                     (the topic itself + the AI's spoken-language grading)
# Some practice languages (currently German) also have a LEVEL, because
# a beginner and an advanced student need completely different topics.
# =========================================================================
 
EXPLAIN_LANGS = ["kk", "ru", "en"]
EXPLAIN_LABELS = {"kk": "ҚАЗ", "ru": "РУС", "en": "ENG"}
 
PRACTICE_LANGS = {
    "en": {"label": "English", "flag": "🇬🇧"},
    "de": {"label": "Deutsch", "flag": "🇩🇪"},
}
 
# languages that have level-specific content (topics/words/idioms differ per level)
LEVELED_LANGS = {"de"}
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
level = st.session_state.level
 
# --- 2. UI TEXT (driven by explain_lang — this is the language the student reads) ---
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
 
# --- 3. WORDS / IDIOMS — the WORD ITSELF is in practice_lang, but the
#         MEANING is a dict keyed by explain_lang, so a beginner never has
#         to read a German definition of a German word.
 
WORDS_EN = [
    {"word": "Ambiguous", "def": {"en": "having more than one possible meaning; unclear.",
                                   "ru": "имеющий более одного значения; неясный.",
                                   "kk": "бірнеше мағынасы бар, түсініксіз."}},
    {"word": "Eloquent", "def": {"en": "fluent or persuasive in speaking or writing.",
                                  "ru": "красноречивый, убедительный в речи или письме.",
                                  "kk": "сөйлеу немесе жазуда шешен, сендіре білетін."}},
    {"word": "Pragmatic", "def": {"en": "dealing with things sensibly and realistically.",
                                   "ru": "практичный, реалистичный подход к делу.",
                                   "kk": "іске байыппен әрі шынайы қарайтын."}},
    {"word": "Ubiquitous", "def": {"en": "present, appearing, or found everywhere.",
                                    "ru": "повсеместный, встречающийся повсюду.",
                                    "kk": "барлық жерде кездесетін."}},
    {"word": "Meticulous", "def": {"en": "showing great attention to detail; very careful.",
                                    "ru": "очень внимательный к деталям, скрупулёзный.",
                                    "kk": "егжей-тегжейіне дейін ұқыпты қарайтын."}},
]
 
IDIOMS_EN = [
    {"idiom": "A double-edged sword", "meaning": {"en": "something with both good and bad consequences.",
                                                    "ru": "нечто имеющее и хорошие, и плохие последствия.",
                                                    "kk": "жақсы да, жаман да салдары бар нәрсе."}},
    {"idiom": "To play devil's advocate", "meaning": {"en": "to argue against an idea to test it.",
                                                        "ru": "спорить против идеи, чтобы проверить её.",
                                                        "kk": "идеяны тексеру үшін оған қарсы дәлел айту."}},
    {"idiom": "The tip of the iceberg", "meaning": {"en": "a small visible part of a much bigger problem.",
                                                      "ru": "малая видимая часть гораздо большей проблемы.",
                                                      "kk": "үлкен мәселенің көрінетін кішкене бөлігі."}},
    {"idiom": "To hit the nail on the head", "meaning": {"en": "to describe exactly what is causing something.",
                                                           "ru": "точно определить суть дела.",
                                                           "kk": "мәселенің нақ өзін дәл айту."}},
    {"idiom": "Once in a blue moon", "meaning": {"en": "something that happens very rarely.",
                                                   "ru": "то, что случается очень редко.",
                                                   "kk": "өте сирек болатын нәрсе."}},
]
 
WORDS_DE = {
    "A1-A2": [
        {"word": "Haus", "def": {"en": "house", "ru": "дом", "kk": "үй"}},
        {"word": "Freund", "def": {"en": "friend", "ru": "друг", "kk": "дос"}},
        {"word": "Schule", "def": {"en": "school", "ru": "школа", "kk": "мектеп"}},
        {"word": "Familie", "def": {"en": "family", "ru": "семья", "kk": "отбасы"}},
        {"word": "Wetter", "def": {"en": "weather", "ru": "погода", "kk": "ауа райы"}},
    ],
    "B1-B2": [
        {"word": "Zwiespältig", "def": {"en": "conflicting, mixed feelings about something.",
                                          "ru": "противоречивый, двойственный.",
                                          "kk": "қарама-қайшы, екіұдай сезім тудыратын."}},
        {"word": "Pragmatisch", "def": {"en": "practical and realistic.",
                                          "ru": "практичный, реалистичный.",
                                          "kk": "тәжірибелік әрі шынайы."}},
        {"word": "Allgegenwärtig", "def": {"en": "present everywhere.",
                                             "ru": "вездесущий, повсеместный.",
                                             "kk": "барлық жерде бар."}},
        {"word": "Plausibel", "def": {"en": "believable, reasonable.",
                                        "ru": "правдоподобный, обоснованный.",
                                        "kk": "сенімді, нанымды."}},
        {"word": "Akribisch", "def": {"en": "extremely careful and precise.",
                                        "ru": "очень тщательный, скрупулёзный.",
                                        "kk": "аса мұқият әрі дәл."}},
    ],
    "C1-C2": [
        {"word": "Unwiderruflich", "def": {"en": "irrevocable, cannot be undone.",
                                             "ru": "безвозвратный, необратимый.",
                                             "kk": "қайтарымсыз, өзгертілмейтін."}},
        {"word": "Ambivalent", "def": {"en": "having mixed, contradictory feelings.",
                                         "ru": "амбивалентный, двойственный.",
                                         "kk": "қарама-қайшы сезімдер тудыратын."}},
        {"word": "Nuanciert", "def": {"en": "showing subtle shades of meaning.",
                                        "ru": "нюансированный, тонко проработанный.",
                                        "kk": "нәзік реңктермен ерекшеленетін."}},
        {"word": "Kontrovers", "def": {"en": "controversial, causing disagreement.",
                                         "ru": "спорный, вызывающий разногласия.",
                                         "kk": "пікірталас тудыратын, даулы."}},
        {"word": "Facettenreich", "def": {"en": "multifaceted, having many sides.",
                                            "ru": "многогранный.",
                                            "kk": "көп қырлы."}},
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
        {"idiom": "Da liegt der Hund begraben", "meaning": {"en": "that's the real core of the problem.",
                                                              "ru": "вот где собака зарыта (суть проблемы).",
                                                              "kk": "мәселенің түйіні дәл осында."}},
        {"idiom": "Die Katze im Sack kaufen", "meaning": {"en": "to accept something without checking it first.",
                                                             "ru": "купить кота в мешке.",
                                                             "kk": "тексермей-ақ бірдеңені алу."}},
        {"idiom": "Den Nagel auf den Kopf treffen", "meaning": {"en": "to describe exactly what's essential.",
                                                                  "ru": "попасть в самую точку.",
                                                                  "kk": "мәселенің дәл өзін айту."}},
        {"idiom": "Um den heißen Brei reden", "meaning": {"en": "to avoid the main topic.",
                                                            "ru": "ходить вокруг да около.",
                                                            "kk": "негізгі тақырыпты айналып өту."}},
        {"idiom": "Die Nase voll haben", "meaning": {"en": "to have had enough of something.",
                                                       "ru": "быть сытым по горло чем-то.",
                                                       "kk": "бір нәрседен түңілу, жалығу."}},
    ],
    "C1-C2": [
        {"idiom": "Jemandem einen Bären aufbinden", "meaning": {"en": "to trick or deceive someone.",
                                                                  "ru": "обмануть, разыграть кого-то.",
                                                                  "kk": "біреуді алдау, ойнату."}},
        {"idiom": "Auf Wolke sieben schweben", "meaning": {"en": "to be extremely happy (on cloud nine).",
                                                              "ru": "быть на седьмом небе от счастья.",
                                                              "kk": "бақыттан ұшып жүру."}},
        {"idiom": "Etwas auf die lange Bank schieben", "meaning": {"en": "to postpone something indefinitely.",
                                                                     "ru": "откладывать в долгий ящик.",
                                                                     "kk": "бір нәрсені созбалаңға салу."}},
        {"idiom": "Den Wald vor lauter Bäumen nicht sehen", "meaning": {"en": "can't see the big picture for the details.",
                                                                          "ru": "за деревьями не видеть леса.",
                                                                          "kk": "ұсақ-түйекке бола үлкен суретті көрмеу."}},
        {"idiom": "Sich etwas zu Herzen nehmen", "meaning": {"en": "to take something to heart.",
                                                                "ru": "принимать что-то близко к сердцу.",
                                                                "kk": "бір нәрсені жүрекке жақын алу."}},
    ],
}
 
if practice_lang == "de":
    word_pool = WORDS_DE[level]
    idiom_pool = IDIOMS_DE[level]
else:
    word_pool = WORDS_EN
    idiom_pool = IDIOMS_EN
 
day_of_year = datetime.date.today().timetuple().tm_yday
today_word = word_pool[day_of_year % len(word_pool)]
today_idiom = idiom_pool[day_of_year % len(idiom_pool)]
 
# --- 4. BOOKS (title stays in practice_lang, vocab note translated by explain_lang) ---
BOOKS_EN = [
    {"title": "'Animal Farm' by George Orwell", "tag": "Politics", "vocab": {"en": "Allegory — a story with a hidden meaning.", "ru": "Аллегория — история со скрытым смыслом.", "kk": "Аллегория — жасырын мағынасы бар әңгіме."}},
    {"title": "'The Giver' by Lois Lowry", "tag": "Society", "vocab": {"en": "Utopia — an imagined perfect place.", "ru": "Утопия — воображаемое идеальное место.", "kk": "Утопия — қиялдағы мінсіз орын."}},
    {"title": "'Fahrenheit 451' by Ray Bradbury", "tag": "Media", "vocab": {"en": "Censorship — suppressing information.", "ru": "Цензура — подавление информации.", "kk": "Цензура — ақпаратты тежеу."}},
    {"title": "'Wonder' by R.J. Palacio", "tag": "School Life", "vocab": {"en": "Empathy — understanding others' feelings.", "ru": "Эмпатия — понимание чувств других.", "kk": "Эмпатия — басқалардың сезімін түсіну."}},
    {"title": "'1984' by George Orwell", "tag": "Freedom", "vocab": {"en": "Totalitarianism — absolute state control.", "ru": "Тоталитаризм — абсолютный контроль государства.", "kk": "Тоталитаризм — мемлекеттің толық бақылауы."}},
]
 
BOOKS_DE = [
    {"title": "«Die Welle» – Todd Strasser", "tag": "Gesellschaft", "vocab": {"en": "Conformity — going along with the group.", "ru": "Конформизм — подчинение группе.", "kk": "Конформизм — топқа бағыну."}},
    {"title": "«Tschick» – Wolfgang Herrndorf", "tag": "Freundschaft", "vocab": {"en": "Outsider — someone who doesn't belong.", "ru": "Аутсайдер — тот, кто не вписывается.", "kk": "Аутсайдер — топқа сыймайтын адам."}},
    {"title": "«Momo» – Michael Ende", "tag": "Zeit", "vocab": {"en": "Mindfulness — being aware of the present.", "ru": "Осознанность — внимание к настоящему моменту.", "kk": "Зейін қою — қазіргі сәтке мән беру."}},
    {"title": "«Emil und die Detektive» – Erich Kästner", "tag": "Abenteuer", "vocab": {"en": "Solidarity — acting together for a goal.", "ru": "Солидарность — совместные действия ради цели.", "kk": "Ынтымақтастық — ортақ мақсат үшін бірге әрекет ету."}},
    {"title": "«Die Verwandlung» – Franz Kafka", "tag": "Identität", "vocab": {"en": "Alienation — feeling disconnected from others.", "ru": "Отчуждение — чувство оторванности от других.", "kk": "Оқшаулану — басқалардан алшақтау сезімі."}},
]
 
with st.sidebar:
    st.header(t["sidebar_header"] + f" ({PRACTICE_LANGS[practice_lang]['label']}" + (f", {level})" if practice_lang in LEVELED_LANGS else ")"))
 
    st.success(f"**{t['word_of_day']}**\n\n**{today_word['word']}** — {today_word['def'][explain_lang]}")
    st.info(f"**{t['idiom_of_day']}**\n\n**'{today_idiom['idiom']}'** — {today_idiom['meaning'][explain_lang]}")
    st.write("---")
 
    st.subheader(t["articles_header"])
    if practice_lang == "de":
        st.markdown("""
        * **[Nachrichtenleicht](https://www.nachrichtenleicht.de/)**
        * **[DW Learn German](https://learngerman.dw.com/)**
        * **[Deutsche Welle](https://www.dw.com/de/themen/s-9077)**
        """)
    else:
        st.markdown("""
        * **[News in Levels](https://www.newsinlevels.com/)**
        * **[BBC Learning English](https://www.bbc.co.uk/learningenglish/english/features/6-minute-english)**
        * **[Teen Vogue - Politics](https://www.teenvogue.com/politics)**
        """)
 
    books_pool = BOOKS_DE if practice_lang == "de" else BOOKS_EN
    week_num = datetime.date.today().isocalendar()[1]
    random.seed(week_num)
    weekly_selection = random.sample(books_pool, min(4, len(books_pool)))
 
    st.subheader(f"{t['books_header']} ({week_num})")
    for book in weekly_selection:
        st.markdown(f"* **{book['title']}** ({book['tag']})")
 
    st.write("---")
    st.subheader(t["vocab_header"])
    for book in weekly_selection:
        st.info(f"**{book['title']}**\n\n{book['vocab'][explain_lang]}")
 
# --- 5. TOPICS (leveled for German; single list for English) ---
TOPICS_EN = [
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
]
 
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
 
# --- 6. MAIN INTERFACE ---
st.title(t["title"])
st.write(t["subtitle"])
 
if "topic" not in st.session_state or st.session_state.topic is None:
    st.session_state.topic = t["click_button"]
 
if st.button(t["get_topic"]):
    random.seed()
    pool = TOPICS_DE[level] if practice_lang == "de" else TOPICS_EN
    st.session_state.topic = random.choice(pool)
 
st.warning(f"**{t['current_topic']}** {st.session_state.topic}")
 
# --- 7. THE RECORDER ---
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
