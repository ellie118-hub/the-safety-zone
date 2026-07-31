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



EXPLAIN_LANGS = ["kk", "ru", "en"]
EXPLAIN_LABELS = {"kk": "ҚАЗ", "ru": "РУС", "en": "ENG"}

PRACTICE_LANGS = {
    "en": {"label": "English", "flag": "🇬🇧"},
    "kk": {"label": "Қазақша", "flag": "🇰🇿"},
    "ru": {"label": "Русский", "flag": "🇷🇺"},
    "de": {"label": "Deutsch", "flag": "🇩🇪"},
    "es": {"label": "Español", "flag": "🇪🇸"},
    "it": {"label": "Italiano", "flag": "🇮🇹"},
    "fr": {"label": "Français", "flag": "🇫🇷"},
    "zh": {"label": "中文", "flag": "🇨🇳"},
    "ja": {"label": "日本語", "flag": "🇯🇵"},
    "ko": {"label": "한국어", "flag": "🇰🇷"},
}

# each leveled language uses ITS OWN proficiency scale, not one shared A1-C2 scale
LEVELS_BY_LANG = {
    "en": ["A1-A2", "B1-B2", "C1-C2"],
    "de": ["A1-A2", "B1-B2", "C1-C2"],
    "es": ["A1-A2", "B1-B2", "C1-C2"],
    "it": ["A1-A2", "B1-B2", "C1-C2"],
    "fr": ["A1-A2", "B1-B2", "C1-C2"],
    "zh": ["HSK 1-3", "HSK 4-6", "HSK 7-9"],
    "ja": ["N5-N4", "N3-N2", "N1"],
    "ko": ["TOPIK 1-2", "TOPIK 3-4", "TOPIK 5-6"],
}
LEVELED_LANGS = set(LEVELS_BY_LANG.keys())   # ru and kk stay single-tier (B1-B2+)

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
    # each language has its own level labels, so reset to that language's first tier
    if new_practice in LEVELS_BY_LANG:
        st.session_state.level = LEVELS_BY_LANG[new_practice][0]
with top3:
    if st.session_state.practice_lang in LEVELED_LANGS:
        lvl_options = LEVELS_BY_LANG[st.session_state.practice_lang]
        if st.session_state.level not in lvl_options:
            st.session_state.level = lvl_options[0]
        st.session_state.level = st.selectbox(
            "Level",
            options=lvl_options,
            index=lvl_options.index(st.session_state.level),
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
        {"word": "School", "def": {"en": "a place where you go to learn.", "ru": "место, где учатся.", "kk": "оқитын орын."}},
        {"word": "Book", "def": {"en": "pages with writing that you read.", "ru": "предмет для чтения со страницами.", "kk": "оқуға арналған беттері бар зат."}},
        {"word": "Music", "def": {"en": "sounds arranged in a pleasing way.", "ru": "приятно организованные звуки.", "kk": "жағымды үйлестірілген дыбыстар."}},
        {"word": "Animal", "def": {"en": "a living creature that is not a plant.", "ru": "живое существо, не растение.", "kk": "өсімдік емес тірі жәндік."}},
        {"word": "Tired", "def": {"en": "needing rest or sleep.", "ru": "нуждающийся в отдыхе.", "kk": "демалу қажет ететін."}},
    ],
    "B1-B2": [
        {"word": "Ambiguous", "def": {"en": "having more than one possible meaning; unclear.", "ru": "имеющий более одного значения; неясный.", "kk": "бірнеше мағынасы бар, түсініксіз."}},
        {"word": "Eloquent", "def": {"en": "fluent or persuasive in speaking or writing.", "ru": "красноречивый, убедительный в речи или письме.", "kk": "сөйлеу немесе жазуда шешен, сендіре білетін."}},
        {"word": "Pragmatic", "def": {"en": "dealing with things sensibly and realistically.", "ru": "практичный, реалистичный подход к делу.", "kk": "іске байыппен әрі шынайы қарайтын."}},
        {"word": "Ubiquitous", "def": {"en": "present, appearing, or found everywhere.", "ru": "повсеместный, встречающийся повсюду.", "kk": "барлық жерде кездесетін."}},
        {"word": "Meticulous", "def": {"en": "showing great attention to detail; very careful.", "ru": "очень внимательный к деталям, скрупулёзный.", "kk": "егжей-тегжейіне дейін ұқыпты қарайтын."}},
        {"word": "Candid", "def": {"en": "honest and direct, even if blunt.", "ru": "честный и прямой, откровенный.", "kk": "ашық әрі турашыл."}},
        {"word": "Resilient", "def": {"en": "able to recover quickly from difficulty.", "ru": "способный быстро восстанавливаться после трудностей.", "kk": "қиындықтан тез қалпына келе алатын."}},
        {"word": "Superficial", "def": {"en": "shallow, not deep or thorough.", "ru": "поверхностный, неглубокий.", "kk": "терең емес, беткейлі."}},
        {"word": "Versatile", "def": {"en": "able to adapt to many different uses.", "ru": "универсальный, приспосабливающийся.", "kk": "көп нәрсеге бейімделе алатын."}},
        {"word": "Skeptical", "def": {"en": "having doubts about something.", "ru": "скептический, сомневающийся.", "kk": "күмәнмен қарайтын."}},
    ],
    "C1-C2": [
        {"word": "Ephemeral", "def": {"en": "lasting for a very short time.", "ru": "мимолётный, недолговечный.", "kk": "өте қысқа мерзімге созылатын."}},
        {"word": "Ineffable", "def": {"en": "too great to be expressed in words.", "ru": "невыразимый словами.", "kk": "сөзбен айтып жеткізе алмайтын."}},
        {"word": "Cognizant", "def": {"en": "aware of or knowing something.", "ru": "осведомлённый о чём-либо.", "kk": "бір нәрсені білетін, хабардар."}},
        {"word": "Ostensible", "def": {"en": "appearing to be true, but not necessarily so.", "ru": "кажущийся, показной.", "kk": "сырт көрінісінде ғана дұрыс болып көрінетін."}},
        {"word": "Perspicacious", "def": {"en": "having keen insight or judgment.", "ru": "проницательный.", "kk": "өткір пайымды, зерек."}},
        {"word": "Enigmatic", "def": {"en": "mysterious, difficult to understand.", "ru": "загадочный, труднообъяснимый.", "kk": "жұмбақ, түсінуге қиын."}},
        {"word": "Paradoxical", "def": {"en": "seemingly contradictory yet possibly true.", "ru": "парадоксальный, кажущийся противоречивым.", "kk": "қайшылықты көрінетін, бірақ шындыққа сай болуы мүмкін."}},
        {"word": "Quintessential", "def": {"en": "representing the most perfect example of something.", "ru": "являющийся самым типичным примером чего-либо.", "kk": "бір нәрсенің ең үлгілі мысалы."}},
        {"word": "Superfluous", "def": {"en": "unnecessary, more than needed.", "ru": "излишний, ненужный.", "kk": "артық, қажетсіз."}},
        {"word": "Ambivalent", "def": {"en": "having mixed or contradictory feelings.", "ru": "испытывающий смешанные, противоречивые чувства.", "kk": "қарама-қайшы сезім тудыратын."}},
    ],
}

WORDS_DE = {
    "A1-A2": [
        {"word": "Haus", "def": {"en": "house", "ru": "дом", "kk": "үй"}},
        {"word": "Freund", "def": {"en": "friend", "ru": "друг", "kk": "дос"}},
        {"word": "Schule", "def": {"en": "school", "ru": "школа", "kk": "мектеп"}},
        {"word": "Familie", "def": {"en": "family", "ru": "семья", "kk": "отбасы"}},
        {"word": "Wetter", "def": {"en": "weather", "ru": "погода", "kk": "ауа райы"}},
        {"word": "Buch", "def": {"en": "book", "ru": "книга", "kk": "кітап"}},
        {"word": "Musik", "def": {"en": "music", "ru": "музыка", "kk": "музыка"}},
        {"word": "Tier", "def": {"en": "animal", "ru": "животное", "kk": "жануар"}},
        {"word": "Farbe", "def": {"en": "color", "ru": "цвет", "kk": "түс"}},
        {"word": "Müde", "def": {"en": "tired", "ru": "уставший", "kk": "шаршаған"}},
    ],
    "B1-B2": [
        {"word": "Zwiespältig", "def": {"en": "conflicting, mixed feelings about something.", "ru": "противоречивый, двойственный.", "kk": "қарама-қайшы, екіұдай сезім тудыратын."}},
        {"word": "Pragmatisch", "def": {"en": "practical and realistic.", "ru": "практичный, реалистичный.", "kk": "тәжірибелік әрі шынайы."}},
        {"word": "Allgegenwärtig", "def": {"en": "present everywhere.", "ru": "вездесущий, повсеместный.", "kk": "барлық жерде бар."}},
        {"word": "Plausibel", "def": {"en": "believable, reasonable.", "ru": "правдоподобный, обоснованный.", "kk": "сенімді, нанымды."}},
        {"word": "Akribisch", "def": {"en": "extremely careful and precise.", "ru": "очень тщательный, скрупулёзный.", "kk": "аса мұқият әрі дәл."}},
        {"word": "Aufrichtig", "def": {"en": "honest and direct.", "ru": "честный и прямой.", "kk": "адал әрі турашыл."}},
        {"word": "Widerstandsfähig", "def": {"en": "able to recover quickly from difficulty.", "ru": "способный быстро восстанавливаться после трудностей.", "kk": "қиындықтан тез қалпына келе алатын."}},
        {"word": "Oberflächlich", "def": {"en": "shallow, not thorough.", "ru": "поверхностный, неглубокий.", "kk": "беткейлі, терең емес."}},
        {"word": "Vielseitig", "def": {"en": "versatile, adaptable.", "ru": "разносторонний, гибкий.", "kk": "көп қырлы, бейімделгіш."}},
        {"word": "Skeptisch", "def": {"en": "doubtful, questioning.", "ru": "скептический, сомневающийся.", "kk": "күмәнмен қарайтын."}},
    ],
    "C1-C2": [
        {"word": "Unwiderruflich", "def": {"en": "irrevocable, cannot be undone.", "ru": "безвозвратный, необратимый.", "kk": "қайтарымсыз, өзгертілмейтін."}},
        {"word": "Ambivalent", "def": {"en": "having mixed, contradictory feelings.", "ru": "амбивалентный, двойственный.", "kk": "қарама-қайшы сезімдер тудыратын."}},
        {"word": "Nuanciert", "def": {"en": "showing subtle shades of meaning.", "ru": "нюансированный, тонко проработанный.", "kk": "нәзік реңктермен ерекшеленетін."}},
        {"word": "Kontrovers", "def": {"en": "controversial, causing disagreement.", "ru": "спорный, вызывающий разногласия.", "kk": "пікірталас тудыратын, даулы."}},
        {"word": "Facettenreich", "def": {"en": "multifaceted, having many sides.", "ru": "многогранный.", "kk": "көп қырлы."}},
        {"word": "Rätselhaft", "def": {"en": "mysterious, hard to understand.", "ru": "загадочный.", "kk": "жұмбақ."}},
        {"word": "Paradox", "def": {"en": "seemingly contradictory yet possibly true.", "ru": "парадоксальный.", "kk": "қайшылықты көрінетін, бірақ шындыққа сай болуы мүмкін."}},
        {"word": "Überflüssig", "def": {"en": "unnecessary, superfluous.", "ru": "излишний, ненужный.", "kk": "артық, қажетсіз."}},
        {"word": "Vielschichtig", "def": {"en": "complex, having many layers.", "ru": "многослойный, сложный.", "kk": "көп қабатты, күрделі."}},
        {"word": "Zerrissen", "def": {"en": "torn, internally conflicted.", "ru": "внутренне раздираемый противоречиями.", "kk": "ішкі қайшылықтан жырылған."}},
    ],
}

WORDS_RU = [
    {"word": "Двусмысленный", "def": {"en": "having more than one possible meaning.", "ru": "имеющий более одного значения; неясный.", "kk": "бірнеше мағынасы бар, түсініксіз."}},
    {"word": "Красноречивый", "def": {"en": "eloquent, fluent and persuasive in speech.", "ru": "умеющий говорить выразительно и убедительно.", "kk": "сөйлеуде шешен әрі сендіре білетін."}},
    {"word": "Практичный", "def": {"en": "practical, dealing with things realistically.", "ru": "реалистично подходящий к делу.", "kk": "іске шынайы қарайтын."}},
    {"word": "Повсеместный", "def": {"en": "found everywhere.", "ru": "встречающийся повсюду.", "kk": "барлық жерде кездесетін."}},
    {"word": "Скрупулёзный", "def": {"en": "extremely careful about details.", "ru": "крайне внимательный к деталям.", "kk": "егжей-тегжейіне аса ұқыпты қарайтын."}},
    {"word": "Категоричный", "def": {"en": "stated firmly, without exceptions.", "ru": "твёрдо и безоговорочно высказанный.", "kk": "қатаң, ешбір ерекшеліксіз айтылған."}},
    {"word": "Проницательный", "def": {"en": "having sharp insight or understanding.", "ru": "обладающий острой наблюдательностью и пониманием.", "kk": "өткір байқампаздыққа ие."}},
    {"word": "Изощрённый", "def": {"en": "highly refined or elaborate.", "ru": "утончённый или сложный.", "kk": "өте нәзік немесе күрделі."}},
    {"word": "Многогранный", "def": {"en": "having many different aspects.", "ru": "имеющий много различных сторон.", "kk": "көптеген түрлі қырлары бар."}},
    {"word": "Убедительный", "def": {"en": "persuasive, able to convince.", "ru": "способный убедить, весомый.", "kk": "сендіре алатын, салмақты."}},
]

WORDS_KK = [
    {"word": "Абстрактілі", "def": {"kk": "нақты емес, тек ойша қабылданатын.", "ru": "абстрактный, воспринимаемый лишь мысленно.", "en": "abstract, existing only as an idea."}},
    {"word": "Талғампаз", "def": {"kk": "талғамы биік, талапшыл.", "ru": "привередливый, разборчивый во вкусах.", "en": "having refined, discerning taste."}},
    {"word": "Ұтымды", "def": {"kk": "тиімді әрі орынды.", "ru": "эффективный и уместный.", "en": "efficient and apt."}},
    {"word": "Кең тараған", "def": {"kk": "барлық жерде кездесетін.", "ru": "распространённый повсюду.", "en": "widespread, found everywhere."}},
    {"word": "Сенімді", "def": {"kk": "нанымды, шындыққа жанасымды.", "ru": "правдоподобный, заслуживающий доверия.", "en": "plausible, credible."}},
    {"word": "Байыпты", "def": {"kk": "асықпайтын, байсалды.", "ru": "неторопливый, рассудительный.", "en": "calm and measured in manner."}},
    {"word": "Ұғымтал", "def": {"kk": "тез түсінетін, аңғарымпаз.", "ru": "быстро понимающий, проницательный.", "en": "quick to understand, perceptive."}},
    {"word": "Қайшылықты", "def": {"kk": "өзара сәйкес келмейтін.", "ru": "противоречивый.", "en": "contradictory, conflicting."}},
    {"word": "Ерекше", "def": {"kk": "басқалардан бөлек, айрықша.", "ru": "особенный, отличающийся от других.", "en": "unique, distinct from others."}},
    {"word": "Салмақты", "def": {"kk": "маңызды әрі байсалды.", "ru": "весомый и рассудительный.", "en": "significant and composed."}},
]

WORDS_ES = {
    "A1-A2": [
        {"word": "Casa", "def": {"en": "house", "ru": "дом", "kk": "үй"}},
        {"word": "Amigo", "def": {"en": "friend", "ru": "друг", "kk": "дос"}},
        {"word": "Escuela", "def": {"en": "school", "ru": "школа", "kk": "мектеп"}},
        {"word": "Familia", "def": {"en": "family", "ru": "семья", "kk": "отбасы"}},
        {"word": "Clima", "def": {"en": "weather", "ru": "погода", "kk": "ауа райы"}},
        {"word": "Libro", "def": {"en": "book", "ru": "книга", "kk": "кітап"}},
        {"word": "Música", "def": {"en": "music", "ru": "музыка", "kk": "музыка"}},
        {"word": "Animal", "def": {"en": "animal", "ru": "животное", "kk": "жануар"}},
        {"word": "Color", "def": {"en": "color", "ru": "цвет", "kk": "түс"}},
        {"word": "Cansado", "def": {"en": "tired", "ru": "уставший", "kk": "шаршаған"}},
    ],
    "B1-B2": [
        {"word": "Ambiguo", "def": {"en": "having more than one meaning; unclear.", "ru": "неоднозначный, неясный.", "kk": "бірнеше мағынасы бар, түсініксіз."}},
        {"word": "Elocuente", "def": {"en": "fluent and persuasive in speech.", "ru": "красноречивый.", "kk": "шешен, сендіре білетін."}},
        {"word": "Pragmático", "def": {"en": "practical and realistic.", "ru": "практичный, реалистичный.", "kk": "тәжірибелік әрі шынайы."}},
        {"word": "Omnipresente", "def": {"en": "present everywhere.", "ru": "вездесущий.", "kk": "барлық жерде бар."}},
        {"word": "Meticuloso", "def": {"en": "extremely careful and precise.", "ru": "очень тщательный.", "kk": "аса мұқият әрі дәл."}},
        {"word": "Sincero", "def": {"en": "honest and direct.", "ru": "честный и прямой.", "kk": "адал әрі турашыл."}},
        {"word": "Resiliente", "def": {"en": "able to recover quickly from difficulty.", "ru": "способный быстро восстанавливаться.", "kk": "қиындықтан тез қалпына келе алатын."}},
        {"word": "Superficial", "def": {"en": "shallow, not thorough.", "ru": "поверхностный.", "kk": "беткейлі, терең емес."}},
        {"word": "Versátil", "def": {"en": "versatile, adaptable.", "ru": "разносторонний, гибкий.", "kk": "көп қырлы, бейімделгіш."}},
        {"word": "Escéptico", "def": {"en": "doubtful, questioning.", "ru": "скептический.", "kk": "күмәнмен қарайтын."}},
    ],
    "C1-C2": [
        {"word": "Efímero", "def": {"en": "lasting for a very short time.", "ru": "мимолётный.", "kk": "өте қысқа мерзімге созылатын."}},
        {"word": "Inefable", "def": {"en": "too great to be expressed in words.", "ru": "невыразимый словами.", "kk": "сөзбен айтып жеткізе алмайтын."}},
        {"word": "Perspicaz", "def": {"en": "having keen insight or judgment.", "ru": "проницательный.", "kk": "өткір пайымды, зерек."}},
        {"word": "Ostensible", "def": {"en": "apparent, seemingly true.", "ru": "кажущийся, показной.", "kk": "сырт көрінісінде дұрыс болып көрінетін."}},
        {"word": "Ambivalente", "def": {"en": "having mixed, contradictory feelings.", "ru": "амбивалентный, двойственный.", "kk": "қарама-қайшы сезімдер тудыратын."}},
        {"word": "Enigmático", "def": {"en": "mysterious, hard to understand.", "ru": "загадочный.", "kk": "жұмбақ."}},
        {"word": "Paradójico", "def": {"en": "seemingly contradictory yet possibly true.", "ru": "парадоксальный.", "kk": "қайшылықты көрінетін."}},
        {"word": "Controvertido", "def": {"en": "controversial, causing disagreement.", "ru": "спорный, вызывающий разногласия.", "kk": "пікірталас тудыратын, даулы."}},
        {"word": "Superfluo", "def": {"en": "unnecessary, superfluous.", "ru": "излишний, ненужный.", "kk": "артық, қажетсіз."}},
        {"word": "Polifacético", "def": {"en": "multifaceted, having many sides.", "ru": "многогранный.", "kk": "көп қырлы."}},
    ],
}

WORDS_IT = {
    "A1-A2": [
        {"word": "Casa", "def": {"en": "house", "ru": "дом", "kk": "үй"}},
        {"word": "Amico", "def": {"en": "friend", "ru": "друг", "kk": "дос"}},
        {"word": "Scuola", "def": {"en": "school", "ru": "школа", "kk": "мектеп"}},
        {"word": "Famiglia", "def": {"en": "family", "ru": "семья", "kk": "отбасы"}},
        {"word": "Meteo", "def": {"en": "weather", "ru": "погода", "kk": "ауа райы"}},
        {"word": "Libro", "def": {"en": "book", "ru": "книга", "kk": "кітап"}},
        {"word": "Musica", "def": {"en": "music", "ru": "музыка", "kk": "музыка"}},
        {"word": "Animale", "def": {"en": "animal", "ru": "животное", "kk": "жануар"}},
        {"word": "Colore", "def": {"en": "color", "ru": "цвет", "kk": "түс"}},
        {"word": "Stanco", "def": {"en": "tired", "ru": "уставший", "kk": "шаршаған"}},
    ],
    "B1-B2": [
        {"word": "Ambiguo", "def": {"en": "having more than one meaning; unclear.", "ru": "неоднозначный.", "kk": "бірнеше мағынасы бар."}},
        {"word": "Eloquente", "def": {"en": "fluent and persuasive in speech.", "ru": "красноречивый.", "kk": "шешен."}},
        {"word": "Pragmatico", "def": {"en": "practical and realistic.", "ru": "практичный.", "kk": "тәжірибелік әрі шынайы."}},
        {"word": "Onnipresente", "def": {"en": "present everywhere.", "ru": "вездесущий.", "kk": "барлық жерде бар."}},
        {"word": "Meticoloso", "def": {"en": "extremely careful and precise.", "ru": "очень тщательный.", "kk": "аса мұқият."}},
        {"word": "Sincero", "def": {"en": "honest and direct.", "ru": "честный и прямой.", "kk": "адал әрі турашыл."}},
        {"word": "Resiliente", "def": {"en": "able to recover quickly from difficulty.", "ru": "способный быстро восстанавливаться.", "kk": "қиындықтан тез қалпына келе алатын."}},
        {"word": "Superficiale", "def": {"en": "shallow, not thorough.", "ru": "поверхностный.", "kk": "беткейлі, терең емес."}},
        {"word": "Versatile", "def": {"en": "versatile, adaptable.", "ru": "разносторонний, гибкий.", "kk": "көп қырлы, бейімделгіш."}},
        {"word": "Scettico", "def": {"en": "doubtful, questioning.", "ru": "скептический.", "kk": "күмәнмен қарайтын."}},
    ],
    "C1-C2": [
        {"word": "Effimero", "def": {"en": "lasting for a very short time.", "ru": "мимолётный.", "kk": "өте қысқа мерзімге созылатын."}},
        {"word": "Ineffabile", "def": {"en": "too great to be expressed in words.", "ru": "невыразимый.", "kk": "сөзбен жеткізе алмайтын."}},
        {"word": "Perspicace", "def": {"en": "having keen insight.", "ru": "проницательный.", "kk": "зерек, өткір пайымды."}},
        {"word": "Apparente", "def": {"en": "apparent, seemingly true.", "ru": "кажущийся.", "kk": "сырт көрінісінде дұрыс болып көрінетін."}},
        {"word": "Ambivalente", "def": {"en": "having mixed feelings.", "ru": "двойственный.", "kk": "қарама-қайшы сезімдер тудыратын."}},
        {"word": "Enigmatico", "def": {"en": "mysterious, hard to understand.", "ru": "загадочный.", "kk": "жұмбақ."}},
        {"word": "Paradossale", "def": {"en": "seemingly contradictory yet possibly true.", "ru": "парадоксальный.", "kk": "қайшылықты көрінетін."}},
        {"word": "Controverso", "def": {"en": "controversial, causing disagreement.", "ru": "спорный, вызывающий разногласия.", "kk": "пікірталас тудыратын, даулы."}},
        {"word": "Superfluo", "def": {"en": "unnecessary, superfluous.", "ru": "излишний, ненужный.", "kk": "артық, қажетсіз."}},
        {"word": "Poliedrico", "def": {"en": "multifaceted, having many sides.", "ru": "многогранный.", "kk": "көп қырлы."}},
    ],
}

WORDS_FR = {
    "A1-A2": [
        {"word": "Maison", "def": {"en": "house", "ru": "дом", "kk": "үй"}},
        {"word": "Ami", "def": {"en": "friend", "ru": "друг", "kk": "дос"}},
        {"word": "École", "def": {"en": "school", "ru": "школа", "kk": "мектеп"}},
        {"word": "Famille", "def": {"en": "family", "ru": "семья", "kk": "отбасы"}},
        {"word": "Météo", "def": {"en": "weather", "ru": "погода", "kk": "ауа райы"}},
        {"word": "Livre", "def": {"en": "book", "ru": "книга", "kk": "кітап"}},
        {"word": "Musique", "def": {"en": "music", "ru": "музыка", "kk": "музыка"}},
        {"word": "Animal", "def": {"en": "animal", "ru": "животное", "kk": "жануар"}},
        {"word": "Couleur", "def": {"en": "color", "ru": "цвет", "kk": "түс"}},
        {"word": "Fatigué", "def": {"en": "tired", "ru": "уставший", "kk": "шаршаған"}},
    ],
    "B1-B2": [
        {"word": "Ambigu", "def": {"en": "having more than one meaning; unclear.", "ru": "неоднозначный.", "kk": "бірнеше мағынасы бар."}},
        {"word": "Éloquent", "def": {"en": "fluent and persuasive in speech.", "ru": "красноречивый.", "kk": "шешен."}},
        {"word": "Pragmatique", "def": {"en": "practical and realistic.", "ru": "практичный.", "kk": "тәжірибелік әрі шынайы."}},
        {"word": "Omniprésent", "def": {"en": "present everywhere.", "ru": "вездесущий.", "kk": "барлық жерде бар."}},
        {"word": "Méticuleux", "def": {"en": "extremely careful and precise.", "ru": "очень тщательный.", "kk": "аса мұқият."}},
        {"word": "Sincère", "def": {"en": "honest and direct.", "ru": "честный и прямой.", "kk": "адал әрі турашыл."}},
        {"word": "Résilient", "def": {"en": "able to recover quickly from difficulty.", "ru": "способный быстро восстанавливаться.", "kk": "қиындықтан тез қалпына келе алатын."}},
        {"word": "Superficiel", "def": {"en": "shallow, not thorough.", "ru": "поверхностный.", "kk": "беткейлі, терең емес."}},
        {"word": "Polyvalent", "def": {"en": "versatile, adaptable.", "ru": "разносторонний, гибкий.", "kk": "көп қырлы, бейімделгіш."}},
        {"word": "Sceptique", "def": {"en": "doubtful, questioning.", "ru": "скептический.", "kk": "күмәнмен қарайтын."}},
    ],
    "C1-C2": [
        {"word": "Éphémère", "def": {"en": "lasting for a very short time.", "ru": "мимолётный.", "kk": "өте қысқа мерзімге созылатын."}},
        {"word": "Ineffable", "def": {"en": "too great to be expressed in words.", "ru": "невыразимый.", "kk": "сөзбен жеткізе алмайтын."}},
        {"word": "Perspicace", "def": {"en": "having keen insight.", "ru": "проницательный.", "kk": "зерек, өткір пайымды."}},
        {"word": "Ostensible", "def": {"en": "apparent, seemingly true.", "ru": "кажущийся.", "kk": "сырт көрінісінде дұрыс болып көрінетін."}},
        {"word": "Ambivalent", "def": {"en": "having mixed feelings.", "ru": "двойственный.", "kk": "қарама-қайшы сезімдер тудыратын."}},
        {"word": "Énigmatique", "def": {"en": "mysterious, hard to understand.", "ru": "загадочный.", "kk": "жұмбақ."}},
        {"word": "Paradoxal", "def": {"en": "seemingly contradictory yet possibly true.", "ru": "парадоксальный.", "kk": "қайшылықты көрінетін."}},
        {"word": "Controversé", "def": {"en": "controversial, causing disagreement.", "ru": "спорный, вызывающий разногласия.", "kk": "пікірталас тудыратын, даулы."}},
        {"word": "Superflu", "def": {"en": "unnecessary, superfluous.", "ru": "излишний, ненужный.", "kk": "артық, қажетсіз."}},
        {"word": "Multiforme", "def": {"en": "multifaceted, having many sides.", "ru": "многогранный.", "kk": "көп қырлы."}},
    ],
}

WORDS_ZH = {
    "HSK 1-3": [
        {"word": "家 (jiā)", "def": {"en": "home / family.", "ru": "дом / семья.", "kk": "үй / отбасы."}},
        {"word": "朋友 (péngyǒu)", "def": {"en": "friend.", "ru": "друг.", "kk": "дос."}},
        {"word": "学校 (xuéxiào)", "def": {"en": "school.", "ru": "школа.", "kk": "мектеп."}},
        {"word": "天气 (tiānqì)", "def": {"en": "weather.", "ru": "погода.", "kk": "ауа райы."}},
        {"word": "高兴 (gāoxìng)", "def": {"en": "happy.", "ru": "счастливый, довольный.", "kk": "қуанышты."}},
    ],
    "HSK 4-6": [
        {"word": "矛盾 (máodùn)", "def": {"en": "conflicting, contradictory.", "ru": "противоречивый.", "kk": "қарама-қайшы."}},
        {"word": "实际 (shíjì)", "def": {"en": "practical, realistic.", "ru": "практичный, реалистичный.", "kk": "тәжірибелік, шынайы."}},
        {"word": "普遍 (pǔbiàn)", "def": {"en": "widespread, universal.", "ru": "повсеместный.", "kk": "кең тараған."}},
        {"word": "合理 (hélǐ)", "def": {"en": "reasonable, plausible.", "ru": "разумный, обоснованный.", "kk": "негізді, сенімді."}},
        {"word": "细致 (xìzhì)", "def": {"en": "meticulous, detailed.", "ru": "скрупулёзный, детальный.", "kk": "мұқият, егжей-тегжейлі."}},
    ],
    "HSK 7-9": [
        {"word": "短暂 (duǎnzàn)", "def": {"en": "ephemeral, short-lived.", "ru": "мимолётный.", "kk": "қысқа мерзімді."}},
        {"word": "难以言喻 (nányǐyányù)", "def": {"en": "ineffable, hard to put into words.", "ru": "невыразимый словами.", "kk": "сөзбен жеткізе алмайтын."}},
        {"word": "敏锐 (mǐnruì)", "def": {"en": "perspicacious, sharp insight.", "ru": "проницательный.", "kk": "зерек, өткір пайымды."}},
        {"word": "有争议 (yǒuzhēngyì)", "def": {"en": "controversial.", "ru": "спорный.", "kk": "даулы."}},
        {"word": "多面性 (duōmiànxìng)", "def": {"en": "multifaceted nature.", "ru": "многогранность.", "kk": "көп қырлылық."}},
    ],
}

WORDS_JA = {
    "N5-N4": [
        {"word": "家 (ie)", "def": {"en": "house.", "ru": "дом.", "kk": "үй."}},
        {"word": "友達 (tomodachi)", "def": {"en": "friend.", "ru": "друг.", "kk": "дос."}},
        {"word": "学校 (gakkō)", "def": {"en": "school.", "ru": "школа.", "kk": "мектеп."}},
        {"word": "天気 (tenki)", "def": {"en": "weather.", "ru": "погода.", "kk": "ауа райы."}},
        {"word": "嬉しい (ureshii)", "def": {"en": "happy, glad.", "ru": "счастливый, радостный.", "kk": "қуанышты."}},
    ],
    "N3-N2": [
        {"word": "矛盾 (mujun)", "def": {"en": "contradiction, conflicting.", "ru": "противоречие.", "kk": "қайшылық."}},
        {"word": "現実的 (genjitsuteki)", "def": {"en": "practical, realistic.", "ru": "практичный, реалистичный.", "kk": "тәжірибелік, шынайы."}},
        {"word": "普遍的 (fuhenteki)", "def": {"en": "universal, widespread.", "ru": "универсальный.", "kk": "жалпыға ортақ."}},
        {"word": "妥当 (datō)", "def": {"en": "reasonable, appropriate.", "ru": "разумный, уместный.", "kk": "негізді, орынды."}},
        {"word": "几帳面 (kichōmen)", "def": {"en": "meticulous, precise.", "ru": "скрупулёзный, педантичный.", "kk": "мұқият, дәл."}},
    ],
    "N1": [
        {"word": "儚い (hakanai)", "def": {"en": "ephemeral, fleeting.", "ru": "мимолётный, эфемерный.", "kk": "қысқа мерзімді, өткінші."}},
        {"word": "言葉にできない (kotoba ni dekinai)", "def": {"en": "ineffable, cannot be put into words.", "ru": "невыразимый словами.", "kk": "сөзбен жеткізе алмайтын."}},
        {"word": "洞察力がある (dōsatsuryoku ga aru)", "def": {"en": "perspicacious, insightful.", "ru": "проницательный.", "kk": "зерек, өткір пайымды."}},
        {"word": "物議を醸す (butsugi o kamosu)", "def": {"en": "controversial, causing debate.", "ru": "спорный, вызывающий споры.", "kk": "пікірталас тудыратын."}},
        {"word": "多面的 (tamenteki)", "def": {"en": "multifaceted.", "ru": "многогранный.", "kk": "көп қырлы."}},
    ],
}

WORDS_KO = {
    "TOPIK 1-2": [
        {"word": "집 (jip)", "def": {"en": "house.", "ru": "дом.", "kk": "үй."}},
        {"word": "친구 (chingu)", "def": {"en": "friend.", "ru": "друг.", "kk": "дос."}},
        {"word": "학교 (hakgyo)", "def": {"en": "school.", "ru": "школа.", "kk": "мектеп."}},
        {"word": "날씨 (nalssi)", "def": {"en": "weather.", "ru": "погода.", "kk": "ауа райы."}},
        {"word": "기쁘다 (gippeuda)", "def": {"en": "to be happy, glad.", "ru": "быть счастливым, радостным.", "kk": "қуанышты болу."}},
    ],
    "TOPIK 3-4": [
        {"word": "모순되다 (mosundoeda)", "def": {"en": "to be contradictory.", "ru": "быть противоречивым.", "kk": "қайшылықты болу."}},
        {"word": "실용적 (silyongjeok)", "def": {"en": "practical, realistic.", "ru": "практичный, реалистичный.", "kk": "тәжірибелік, шынайы."}},
        {"word": "보편적 (bopyeonjeok)", "def": {"en": "universal, widespread.", "ru": "универсальный.", "kk": "жалпыға ортақ."}},
        {"word": "타당하다 (tadanghada)", "def": {"en": "to be reasonable, valid.", "ru": "быть разумным, обоснованным.", "kk": "негізді болу."}},
        {"word": "꼼꼼하다 (kkomkkomhada)", "def": {"en": "to be meticulous, thorough.", "ru": "быть скрупулёзным.", "kk": "мұқият, ұқыпты болу."}},
    ],
    "TOPIK 5-6": [
        {"word": "덧없다 (deodeopda)", "def": {"en": "ephemeral, fleeting.", "ru": "мимолётный, эфемерный.", "kk": "қысқа мерзімді, өткінші."}},
        {"word": "형언할 수 없다 (hyeongeonhal su eopda)", "def": {"en": "ineffable, indescribable.", "ru": "невыразимый словами.", "kk": "сөзбен жеткізе алмайтын."}},
        {"word": "통찰력 있다 (tongchallyeok itda)", "def": {"en": "perspicacious, insightful.", "ru": "проницательный.", "kk": "зерек, өткір пайымды."}},
        {"word": "논란이 되다 (nollani doeda)", "def": {"en": "to be controversial.", "ru": "быть спорным.", "kk": "пікірталас тудыру."}},
        {"word": "다면적 (damyeonjeok)", "def": {"en": "multifaceted.", "ru": "многогранный.", "kk": "көп қырлы."}},
    ],
}


IDIOMS_EN = {
    "A1-A2": [
        {"idiom": "Nice to meet you", "meaning": {"en": "a polite greeting when meeting someone new.", "ru": "вежливое приветствие при знакомстве.", "kk": "танысу кезіндегі сыпайы сәлемдесу."}},
        {"idiom": "No worries", "meaning": {"en": "it's okay, don't worry.", "ru": "всё в порядке, не переживай.", "kk": "бәрі жақсы, алаңдама."}},
        {"idiom": "See you later", "meaning": {"en": "a casual way to say goodbye.", "ru": "неформальное прощание.", "kk": "бейресми қоштасу тіркесі."}},
        {"idiom": "Good job!", "meaning": {"en": "well done, praise for good work.", "ru": "молодец, похвала за хорошую работу.", "kk": "жарайсың, жақсы жұмыс үшін мақтау."}},
        {"idiom": "Take it easy", "meaning": {"en": "relax, don't stress.", "ru": "не напрягайся, расслабься.", "kk": "қобалжыма, тыныш бол."}},
        {"idiom": "Thank you very much", "meaning": {"en": "a polite way to show gratitude.", "ru": "вежливая форма благодарности.", "kk": "алғысты сыпайы білдіру тәсілі."}},
        {"idiom": "Excuse me", "meaning": {"en": "a polite way to get attention or apologize.", "ru": "вежливая фраза для привлечения внимания или извинения.", "kk": "назар аудару немесе кешірім сұрау үшін сыпайы тіркес."}},
        {"idiom": "I'm sorry", "meaning": {"en": "an expression of apology.", "ru": "выражение извинения.", "kk": "кешірім білдіру сөзі."}},
        {"idiom": "Have a nice day", "meaning": {"en": "a friendly farewell wish.", "ru": "дружелюбное пожелание при прощании.", "kk": "қоштасқанда айтылатын жылы тілек."}},
        {"idiom": "It's up to you", "meaning": {"en": "the decision is yours to make.", "ru": "решение за тобой.", "kk": "шешім өзіңе байланысты."}},
    ],
    "B1-B2": [
        {"idiom": "A double-edged sword", "meaning": {"en": "something with both good and bad consequences.", "ru": "нечто имеющее и хорошие, и плохие последствия.", "kk": "жақсы да, жаман да салдары бар нәрсе."}},
        {"idiom": "To play devil's advocate", "meaning": {"en": "to argue against an idea to test it.", "ru": "спорить против идеи, чтобы проверить её.", "kk": "идеяны тексеру үшін оған қарсы дәлел айту."}},
        {"idiom": "The tip of the iceberg", "meaning": {"en": "a small visible part of a much bigger problem.", "ru": "малая видимая часть гораздо большей проблемы.", "kk": "үлкен мәселенің көрінетін кішкене бөлігі."}},
        {"idiom": "To hit the nail on the head", "meaning": {"en": "to describe exactly what is causing something.", "ru": "точно определить суть дела.", "kk": "мәселенің нақ өзін дәл айту."}},
        {"idiom": "Once in a blue moon", "meaning": {"en": "something that happens very rarely.", "ru": "то, что случается очень редко.", "kk": "өте сирек болатын нәрсе."}},
        {"idiom": "To break the ice", "meaning": {"en": "to ease tension at the start of a conversation.", "ru": "снять напряжение в начале разговора.", "kk": "әңгіме басында алаңдаушылықты жеңілдету."}},
        {"idiom": "A piece of cake", "meaning": {"en": "something very easy to do.", "ru": "что-то очень простое.", "kk": "өте оңай нәрсе."}},
        {"idiom": "Under the weather", "meaning": {"en": "feeling slightly ill.", "ru": "чувствовать себя немного нездоровым.", "kk": "сәл сырқаттанып тұру."}},
        {"idiom": "To cost an arm and a leg", "meaning": {"en": "to be very expensive.", "ru": "быть очень дорогим.", "kk": "өте қымбат болу."}},
        {"idiom": "To let the cat out of the bag", "meaning": {"en": "to accidentally reveal a secret.", "ru": "случайно выдать секрет.", "kk": "құпияны байқаусызда ашып алу."}},
    ],
    "C1-C2": [
        {"idiom": "To read between the lines", "meaning": {"en": "to understand a hidden meaning.", "ru": "читать между строк.", "kk": "жасырын мағынаны түсіну."}},
        {"idiom": "A blessing in disguise", "meaning": {"en": "something good that seemed bad at first.", "ru": "нет худа без добра.", "kk": "алғашында жаман көрінген, кейін пайдалы болған нәрсе."}},
        {"idiom": "To bite the bullet", "meaning": {"en": "to face a difficult situation bravely.", "ru": "стиснуть зубы и терпеть.", "kk": "қиындықты батыл қабылдау."}},
        {"idiom": "To go the extra mile", "meaning": {"en": "to make more effort than expected.", "ru": "приложить больше усилий, чем требуется.", "kk": "қажеттіден артық күш салу."}},
        {"idiom": "Actions speak louder than words", "meaning": {"en": "what you do matters more than what you say.", "ru": "дела важнее слов.", "kk": "істің сөзден маңыздылығы."}},
        {"idiom": "The elephant in the room", "meaning": {"en": "an obvious problem no one wants to discuss.", "ru": "очевидная проблема, которую все избегают обсуждать.", "kk": "бәрі көріп тұрған, бірақ талқыламайтын мәселе."}},
        {"idiom": "To take something with a grain of salt", "meaning": {"en": "to not fully believe something.", "ru": "относиться к чему-то скептически.", "kk": "бір нәрсеге толық сенбеу."}},
        {"idiom": "To be on the same page", "meaning": {"en": "to have the same understanding as someone else.", "ru": "иметь одинаковое понимание с кем-то.", "kk": "біреумен бірдей түсінікте болу."}},
        {"idiom": "To throw caution to the wind", "meaning": {"en": "to act boldly without worrying about risk.", "ru": "действовать смело, не думая о риске.", "kk": "тәуекелді ойламай батыл әрекет ету."}},
        {"idiom": "The ball is in your court", "meaning": {"en": "it's your turn to act or decide.", "ru": "теперь твоя очередь действовать.", "kk": "енді әрекет ету кезегі сенде."}},
    ],
}

IDIOMS_DE = {
    "A1-A2": [
        {"idiom": "Wie geht's?", "meaning": {"en": "How are you? (greeting)", "ru": "Как дела? (приветствие)", "kk": "Қалың қалай? (сәлемдесу тіркесі)"}},
        {"idiom": "Kein Problem", "meaning": {"en": "No problem.", "ru": "Без проблем.", "kk": "Ешбір мәселе жоқ."}},
        {"idiom": "Viel Spaß!", "meaning": {"en": "Have fun!", "ru": "Удачи, веселись!", "kk": "Сәттілік, көңілді өткіз!"}},
        {"idiom": "Alles klar!", "meaning": {"en": "Got it! All clear!", "ru": "Всё ясно!", "kk": "Бәрі түсінікті!"}},
        {"idiom": "Ich verstehe nicht.", "meaning": {"en": "I don't understand.", "ru": "Я не понимаю.", "kk": "Мен түсінбеймін."}},
        {"idiom": "Danke schön", "meaning": {"en": "Thank you very much.", "ru": "Большое спасибо.", "kk": "Көп рахмет."}},
        {"idiom": "Entschuldigung", "meaning": {"en": "Excuse me / sorry.", "ru": "Извините.", "kk": "Кешіріңіз."}},
        {"idiom": "Es tut mir leid.", "meaning": {"en": "I'm sorry.", "ru": "Мне жаль.", "kk": "Кешірім сұраймын."}},
        {"idiom": "Schönen Tag noch!", "meaning": {"en": "Have a nice day!", "ru": "Хорошего дня!", "kk": "Күніңіз сәтті өтсін!"}},
        {"idiom": "Wie du willst.", "meaning": {"en": "As you wish, it's up to you.", "ru": "Как хочешь, решать тебе.", "kk": "Қалауың бойынша, шешім өзіңде."}},
    ],
    "B1-B2": [
        {"idiom": "Da liegt der Hund begraben", "meaning": {"en": "that's the real core of the problem.", "ru": "вот где собака зарыта (суть проблемы).", "kk": "мәселенің түйіні дәл осында."}},
        {"idiom": "Die Katze im Sack kaufen", "meaning": {"en": "to accept something without checking it first.", "ru": "купить кота в мешке.", "kk": "тексермей-ақ бірдеңені алу."}},
        {"idiom": "Den Nagel auf den Kopf treffen", "meaning": {"en": "to describe exactly what's essential.", "ru": "попасть в самую точку.", "kk": "мәселенің дәл өзін айту."}},
        {"idiom": "Um den heißen Brei reden", "meaning": {"en": "to avoid the main topic.", "ru": "ходить вокруг да около.", "kk": "негізгі тақырыпты айналып өту."}},
        {"idiom": "Die Nase voll haben", "meaning": {"en": "to have had enough of something.", "ru": "быть сытым по горло чем-то.", "kk": "бір нәрседен түңілу, жалығу."}},
        {"idiom": "Das Eis brechen", "meaning": {"en": "to break the ice.", "ru": "растопить лёд, снять напряжение.", "kk": "мұзды еріту, шиеленісті бәсеңдету."}},
        {"idiom": "Ein Kinderspiel", "meaning": {"en": "something very easy (child's play).", "ru": "проще простого.", "kk": "өте оңай нәрсе."}},
        {"idiom": "Nicht ganz auf der Höhe sein", "meaning": {"en": "to feel slightly unwell.", "ru": "чувствовать себя не очень хорошо.", "kk": "сәл сырқаттанып тұру."}},
        {"idiom": "Ein Vermögen kosten", "meaning": {"en": "to be very expensive.", "ru": "стоить целое состояние.", "kk": "өте қымбат тұру."}},
        {"idiom": "Die Katze aus dem Sack lassen", "meaning": {"en": "to accidentally reveal a secret.", "ru": "случайно выдать секрет.", "kk": "құпияны байқаусызда ашып алу."}},
    ],
    "C1-C2": [
        {"idiom": "Jemandem einen Bären aufbinden", "meaning": {"en": "to trick or deceive someone.", "ru": "обмануть, разыграть кого-то.", "kk": "біреуді алдау, ойнату."}},
        {"idiom": "Auf Wolke sieben schweben", "meaning": {"en": "to be extremely happy (on cloud nine).", "ru": "быть на седьмом небе от счастья.", "kk": "бақыттан ұшып жүру."}},
        {"idiom": "Etwas auf die lange Bank schieben", "meaning": {"en": "to postpone something indefinitely.", "ru": "откладывать в долгий ящик.", "kk": "бір нәрсені созбалаңға салу."}},
        {"idiom": "Den Wald vor lauter Bäumen nicht sehen", "meaning": {"en": "can't see the big picture for the details.", "ru": "за деревьями не видеть леса.", "kk": "ұсақ-түйекке бола үлкен суретті көрмеу."}},
        {"idiom": "Sich etwas zu Herzen nehmen", "meaning": {"en": "to take something to heart.", "ru": "принимать что-то близко к сердцу.", "kk": "бір нәрсені жүрекке жақын алу."}},
        {"idiom": "Der Elefant im Raum", "meaning": {"en": "the elephant in the room, an obvious unspoken problem.", "ru": "слон в комнате, очевидная, но замалчиваемая проблема.", "kk": "бәрі көріп тұрған, бірақ айтылмайтын мәселе."}},
        {"idiom": "Mit Vorsicht genießen", "meaning": {"en": "to take something with a grain of salt.", "ru": "относиться к чему-то скептически.", "kk": "бір нәрсеге толық сенбеу."}},
        {"idiom": "Auf einer Wellenlänge sein", "meaning": {"en": "to be on the same wavelength as someone.", "ru": "быть на одной волне с кем-то.", "kk": "біреумен бір толқында болу."}},
        {"idiom": "Alles auf eine Karte setzen", "meaning": {"en": "to risk everything on one option.", "ru": "поставить всё на одну карту.", "kk": "бәрін бір нәрсеге тәуекел ету."}},
        {"idiom": "Der Ball liegt bei dir", "meaning": {"en": "the ball is in your court.", "ru": "теперь твоя очередь действовать.", "kk": "енді әрекет ету кезегі сенде."}},
    ],
}

IDIOMS_RU = [
    {"idiom": "Сесть в лужу", "meaning": {"en": "to end up in an embarrassing situation.", "ru": "оказаться в неловком положении.", "kk": "ыңғайсыз жағдайға тап болу."}},
    {"idiom": "Водить за нос", "meaning": {"en": "to deceive someone.", "ru": "обманывать кого-то.", "kk": "біреуді алдау."}},
    {"idiom": "Бить баклуши", "meaning": {"en": "to be idle, waste time doing nothing.", "ru": "бездельничать.", "kk": "бос уақыт өткізу, еш нәрсе істемеу."}},
    {"idiom": "Держать язык за зубами", "meaning": {"en": "to keep quiet about something.", "ru": "молчать о чём-то, не выдавать секрет.", "kk": "бір нәрсе жайлы үндемеу, құпияны сақтау."}},
    {"idiom": "Как две капли воды", "meaning": {"en": "to look exactly alike.", "ru": "быть очень похожими друг на друга.", "kk": "бір-біріне өте ұқсас болу."}},
    {"idiom": "Заварить кашу", "meaning": {"en": "to start a complicated or troublesome situation.", "ru": "затеять сложное, хлопотное дело.", "kk": "күрделі, бас ауыртатын іс бастау."}},
    {"idiom": "Делать из мухи слона", "meaning": {"en": "to exaggerate a small problem.", "ru": "преувеличивать незначительную проблему.", "kk": "кішкентай мәселені үлкейтіп жіберу."}},
    {"idiom": "Зарубить на носу", "meaning": {"en": "to remember something firmly.", "ru": "твёрдо запомнить что-то.", "kk": "бір нәрсені мықтап есте сақтау."}},
    {"idiom": "Пускать пыль в глаза", "meaning": {"en": "to show off or create a false impression.", "ru": "создавать ложное впечатление, хвастаться.", "kk": "жалған әсер қалдыру, көзбояушылық жасау."}},
    {"idiom": "Не в своей тарелке", "meaning": {"en": "to feel uncomfortable or out of place.", "ru": "чувствовать себя неловко, не в своей стихии.", "kk": "өзін ыңғайсыз, бейтаныс жерде сезіну."}},
]

IDIOMS_KK = [
    {"idiom": "Тілі байланды", "meaning": {"kk": "сөйлей алмай, есінен танғандай халге түсу.", "ru": "лишиться дара речи от неожиданности.", "en": "to become speechless with shock."}},
    {"idiom": "Көзінің қарасындай көру", "meaning": {"kk": "біреуді немесе бірдеңені қатты қастерлеу.", "ru": "беречь кого-то как зеницу ока.", "en": "to cherish someone like the apple of one's eye."}},
    {"idiom": "Мұрнын көкке көтеру", "meaning": {"kk": "тым тәкаппар, паң болу.", "ru": "задирать нос, важничать.", "en": "to become arrogant."}},
    {"idiom": "Екі езуі құлағында", "meaning": {"kk": "өте қуанышты, риза болу.", "ru": "улыбаться до ушей от радости.", "en": "to be grinning from ear to ear."}},
    {"idiom": "Ит арқасы қияда", "meaning": {"kk": "істің оңға басып, сәті түсуі.", "ru": "дела идут в гору, всё складывается удачно.", "en": "things are going smoothly."}},
    {"idiom": "Қой аузынан шөп алмас", "meaning": {"kk": "өте момын, зиянсыз адам.", "ru": "чрезвычайно кроткий, безобидный человек.", "en": "an extremely gentle, harmless person."}},
    {"idiom": "Тас бауыр", "meaning": {"kk": "қатал, мейірімсіз адам.", "ru": "бессердечный, холодный человек.", "en": "a cold, heartless person."}},
    {"idiom": "Өз бетімен кету", "meaning": {"kk": "өз бетінше әрекет ету.", "ru": "действовать самостоятельно, по-своему.", "en": "to act independently, go one's own way."}},
    {"idiom": "Ит өлген жерде", "meaning": {"kk": "қашық, адам аяғы баспаған жер.", "ru": "глухое, забытое богом место.", "en": "a remote, godforsaken place."}},
    {"idiom": "Көңілі қалу", "meaning": {"kk": "көңілі қалу, ренжу.", "ru": "чувствовать разочарование, обиду.", "en": "to feel disappointed or hurt."}},
]

IDIOMS_ES = {
    "A1-A2": [
        {"idiom": "Mucho gusto", "meaning": {"en": "nice to meet you.", "ru": "приятно познакомиться.", "kk": "танысқаныма қуаныштымын."}},
        {"idiom": "No pasa nada", "meaning": {"en": "no worries, it's fine.", "ru": "ничего страшного.", "kk": "ештеңе етпейді."}},
        {"idiom": "Hasta luego", "meaning": {"en": "see you later.", "ru": "до скорого.", "kk": "кездескенше."}},
        {"idiom": "¡Buen trabajo!", "meaning": {"en": "good job!", "ru": "хорошая работа!", "kk": "жарайсың!"}},
        {"idiom": "Tranquilo/a", "meaning": {"en": "take it easy, relax.", "ru": "не переживай, расслабься.", "kk": "алаңдама, тыныш бол."}},
        {"idiom": "Muchas gracias", "meaning": {"en": "thank you very much.", "ru": "большое спасибо.", "kk": "көп рахмет."}},
        {"idiom": "Perdón", "meaning": {"en": "excuse me / sorry.", "ru": "извините.", "kk": "кешіріңіз."}},
        {"idiom": "Lo siento", "meaning": {"en": "I'm sorry.", "ru": "мне жаль.", "kk": "кешірім сұраймын."}},
        {"idiom": "Que tengas un buen día", "meaning": {"en": "have a nice day.", "ru": "хорошего дня.", "kk": "күніңіз сәтті өтсін."}},
        {"idiom": "Como quieras", "meaning": {"en": "as you wish, it's up to you.", "ru": "как хочешь, решать тебе.", "kk": "қалауың бойынша, шешім өзіңде."}},
    ],
    "B1-B2": [
        {"idiom": "Estar en las nubes", "meaning": {"en": "to be daydreaming, absent-minded.", "ru": "витать в облаках.", "kk": "ойға шомып кету."}},
        {"idiom": "Costar un ojo de la cara", "meaning": {"en": "to cost a fortune.", "ru": "стоить целое состояние.", "kk": "өте қымбатқа түсу."}},
        {"idiom": "Meter la pata", "meaning": {"en": "to make a blunder.", "ru": "сделать промах.", "kk": "қателік жіберу."}},
        {"idiom": "No tener pelos en la lengua", "meaning": {"en": "to speak bluntly, without holding back.", "ru": "говорить без обиняков.", "kk": "тіке, ашық сөйлеу."}},
        {"idiom": "Ser pan comido", "meaning": {"en": "to be very easy (a piece of cake).", "ru": "быть проще простого.", "kk": "өте оңай болу."}},
        {"idiom": "Romper el hielo", "meaning": {"en": "to break the ice.", "ru": "растопить лёд, снять напряжение.", "kk": "мұзды еріту, шиеленісті бәсеңдету."}},
        {"idiom": "Estar pachucho/a", "meaning": {"en": "to feel slightly unwell.", "ru": "чувствовать себя не очень хорошо.", "kk": "сәл сырқаттанып тұру."}},
        {"idiom": "Írsele la lengua", "meaning": {"en": "to accidentally reveal something.", "ru": "случайно проговориться.", "kk": "байқаусызда құпияны айтып қою."}},
        {"idiom": "Dar la lata", "meaning": {"en": "to be a nuisance, bother someone.", "ru": "надоедать, докучать.", "kk": "мазалау, жалықтыру."}},
        {"idiom": "Ponerse las pilas", "meaning": {"en": "to get one's act together.", "ru": "взяться за дело, собраться.", "kk": "іске кірісу, жиналу."}},
    ],
    "C1-C2": [
        {"idiom": "Tirar la casa por la ventana", "meaning": {"en": "to spare no expense.", "ru": "не жалеть денег, шиковать.", "kk": "шығынды аямай жұмсау."}},
        {"idiom": "Hablar por los codos", "meaning": {"en": "to talk nonstop.", "ru": "говорить без умолку.", "kk": "тоқтаусыз сөйлеу."}},
        {"idiom": "Dar en el clavo", "meaning": {"en": "to hit the nail on the head.", "ru": "попасть в самую точку.", "kk": "мәселенің дәл өзін айту."}},
        {"idiom": "Irse por las ramas", "meaning": {"en": "to beat around the bush.", "ru": "ходить вокруг да около.", "kk": "негізгі тақырыпты айналып өту."}},
        {"idiom": "Poner los puntos sobre las íes", "meaning": {"en": "to clarify something precisely.", "ru": "расставить все точки над и.", "kk": "бәрін нақтылап түсіндіру."}},
        {"idiom": "El elefante en la habitación", "meaning": {"en": "the elephant in the room.", "ru": "слон в комнате, очевидная замалчиваемая проблема.", "kk": "бәрі көріп тұрған, бірақ айтылмайтын мәселе."}},
        {"idiom": "Tomarlo con pinzas", "meaning": {"en": "to take something with a grain of salt.", "ru": "относиться к чему-то скептически.", "kk": "бір нәрсеге толық сенбеу."}},
        {"idiom": "Estar en la misma sintonía", "meaning": {"en": "to be on the same wavelength.", "ru": "быть на одной волне с кем-то.", "kk": "біреумен бір толқында болу."}},
        {"idiom": "Jugárselo todo a una carta", "meaning": {"en": "to risk everything on one option.", "ru": "поставить всё на одну карту.", "kk": "бәрін бір нәрсеге тәуекел ету."}},
        {"idiom": "La pelota está en tu tejado", "meaning": {"en": "the ball is in your court.", "ru": "теперь твоя очередь действовать.", "kk": "енді әрекет ету кезегі сенде."}},
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

IDIOMS_ZH = {
    "HSK 1-3": [
        {"idiom": "你好吗? (nǐ hǎo ma?)", "meaning": {"en": "How are you? (greeting)", "ru": "Как дела? (приветствие)", "kk": "Қалың қалай? (сәлемдесу)"}},
        {"idiom": "没关系 (méi guānxi)", "meaning": {"en": "No problem, it's okay.", "ru": "Ничего страшного.", "kk": "Ештеңе етпейді."}},
        {"idiom": "再见 (zàijiàn)", "meaning": {"en": "Goodbye.", "ru": "До свидания.", "kk": "Сау бол."}},
        {"idiom": "做得好! (zuò de hǎo!)", "meaning": {"en": "Well done!", "ru": "Молодец!", "kk": "Жарайсың!"}},
        {"idiom": "别担心 (bié dānxīn)", "meaning": {"en": "Don't worry.", "ru": "Не волнуйся.", "kk": "Алаңдама."}},
    ],
    "HSK 4-6": [
        {"idiom": "马马虎虎 (mǎmǎhūhū)", "meaning": {"en": "careless, so-so, mediocre.", "ru": "так себе, небрежно.", "kk": "бей-жай, ортача."}},
        {"idiom": "半途而废 (bàntú'érfèi)", "meaning": {"en": "to give up halfway.", "ru": "бросить на полпути.", "kk": "істі жартылай тастау."}},
        {"idiom": "入乡随俗 (rùxiāngsuísú)", "meaning": {"en": "when in Rome, do as the Romans do.", "ru": "в чужой монастырь со своим уставом не ходят.", "kk": "қай жерге барсаң, сол жердің салтын ұста."}},
        {"idiom": "画蛇添足 (huàshétiānzú)", "meaning": {"en": "to ruin something by overdoing it.", "ru": "испортить излишним старанием.", "kk": "артық әрекетпен істі бұзу."}},
        {"idiom": "一举两得 (yìjǔliǎngdé)", "meaning": {"en": "to kill two birds with one stone.", "ru": "убить двух зайцев одним выстрелом.", "kk": "бір оқпен екі қоян ату."}},
    ],
    "HSK 7-9": [
        {"idiom": "塞翁失马 (sàiwēngshīmǎ)", "meaning": {"en": "a blessing in disguise.", "ru": "нет худа без добра.", "kk": "жаманнан жақсылық шығуы."}},
        {"idiom": "破釜沉舟 (pòfǔchénzhōu)", "meaning": {"en": "to commit fully, no retreat (burn one's bridges).", "ru": "сжечь мосты.", "kk": "кемені өртеп, соңына дейін бару."}},
        {"idiom": "画龙点睛 (huàlóngdiǎnjīng)", "meaning": {"en": "to add the crucial finishing touch.", "ru": "добавить решающий штрих.", "kk": "шешуші түпкі штрихты қосу."}},
        {"idiom": "亡羊补牢 (wángyángbǔláo)", "meaning": {"en": "better late than never.", "ru": "лучше поздно, чем никогда.", "kk": "кеш болса да, түк болмағаннан жақсы."}},
        {"idiom": "井底之蛙 (jǐngdǐzhīwā)", "meaning": {"en": "a person with a narrow view of the world.", "ru": "человек с узким кругозором.", "kk": "дүниетанымы тар адам."}},
    ],
}

IDIOMS_JA = {
    "N5-N4": [
        {"idiom": "元気ですか? (Genki desu ka?)", "meaning": {"en": "How are you? (greeting)", "ru": "Как дела? (приветствие)", "kk": "Қалың қалай? (сәлемдесу)"}},
        {"idiom": "大丈夫です (Daijōbu desu.)", "meaning": {"en": "It's okay, no problem.", "ru": "Всё в порядке.", "kk": "Бәрі жақсы."}},
        {"idiom": "またね (Mata ne.)", "meaning": {"en": "See you (casual goodbye).", "ru": "Пока, увидимся.", "kk": "Кездескенше."}},
        {"idiom": "よくできました! (Yoku dekimashita!)", "meaning": {"en": "Well done!", "ru": "Молодец!", "kk": "Жарайсың!"}},
        {"idiom": "心配しないで (Shinpai shinaide.)", "meaning": {"en": "Don't worry.", "ru": "Не волнуйся.", "kk": "Алаңдама."}},
    ],
    "N3-N2": [
        {"idiom": "猫の手も借りたい (Neko no te mo karitai.)", "meaning": {"en": "to be extremely busy.", "ru": "быть очень занятым.", "kk": "өте бос емес болу."}},
        {"idiom": "石の上にも三年 (Ishi no ue ni mo san nen.)", "meaning": {"en": "patience and persistence pay off.", "ru": "терпение и труд всё перетрут.", "kk": "төзімділік пен еңбек жеміс береді."}},
        {"idiom": "馬が合う (Uma ga au.)", "meaning": {"en": "to get along well with someone.", "ru": "хорошо ладить с кем-то.", "kk": "біреумен жақсы тіл табысу."}},
        {"idiom": "頭が固い (Atama ga katai.)", "meaning": {"en": "to be stubborn, inflexible.", "ru": "быть упрямым.", "kk": "ойлауда қасаң болу."}},
        {"idiom": "耳が痛い (Mimi ga itai.)", "meaning": {"en": "a criticism that hits close to home.", "ru": "критика, задевающая за живое.", "kk": "жанға тиетін сын."}},
    ],
    "N1": [
        {"idiom": "背水の陣 (Haisui no jin.)", "meaning": {"en": "to commit fully with no retreat.", "ru": "сжечь мосты.", "kk": "кейін шегінбей, толық берілу."}},
        {"idiom": "灯台下暗し (Tōdai moto kurashi.)", "meaning": {"en": "the obvious is often overlooked.", "ru": "самое очевидное часто остаётся незамеченным.", "kk": "көзге көрінген нәрсе байқалмай қалады."}},
        {"idiom": "覆水盆に返らず (Fukusui bon ni kaerazu.)", "meaning": {"en": "what's done cannot be undone.", "ru": "что сделано, то сделано.", "kk": "болған іс қайтпайды."}},
        {"idiom": "虎穴に入らずんば虎子を得ず (Koketsu ni irazunba koji o ezu.)", "meaning": {"en": "nothing ventured, nothing gained.", "ru": "кто не рискует, тот не выигрывает.", "kk": "тәуекел етпеген жетістікке жетпейді."}},
        {"idiom": "善は急げ (Zen wa isoge.)", "meaning": {"en": "strike while the iron is hot.", "ru": "куй железо, пока горячо.", "kk": "темірді ыстығында соқ."}},
    ],
}

IDIOMS_KO = {
    "TOPIK 1-2": [
        {"idiom": "어떻게 지내요? (Eotteoke jinaeyo?)", "meaning": {"en": "How are you? (greeting)", "ru": "Как дела? (приветствие)", "kk": "Қалың қалай? (сәлемдесу)"}},
        {"idiom": "괜찮아요 (Gwaenchanhayo.)", "meaning": {"en": "It's okay, no problem.", "ru": "Всё в порядке.", "kk": "Бәрі жақсы."}},
        {"idiom": "또 만나요 (Tto mannayo.)", "meaning": {"en": "See you again.", "ru": "До встречи.", "kk": "Тағы кездесеміз."}},
        {"idiom": "잘했어요! (Jalhaesseoyo!)", "meaning": {"en": "Well done!", "ru": "Молодец!", "kk": "Жарайсың!"}},
        {"idiom": "걱정하지 마세요 (Geokjeonghaji maseyo.)", "meaning": {"en": "Don't worry.", "ru": "Не волнуйся.", "kk": "Алаңдама."}},
    ],
    "TOPIK 3-4": [
        {"idiom": "손이 크다 (Soni keuda.)", "meaning": {"en": "to be generous (lit: to have big hands).", "ru": "быть щедрым.", "kk": "жомарт болу."}},
        {"idiom": "발이 넓다 (Bari neolda.)", "meaning": {"en": "to have wide social connections.", "ru": "иметь широкий круг знакомств.", "kk": "кең таныстығы болу."}},
        {"idiom": "눈이 높다 (Nuni nopda.)", "meaning": {"en": "to have high standards.", "ru": "иметь высокие требования.", "kk": "талғамы жоғары болу."}},
        {"idiom": "입이 무겁다 (Ibi mugeopda.)", "meaning": {"en": "to be discreet, able to keep a secret.", "ru": "уметь хранить секреты.", "kk": "құпияны сақтай білу."}},
        {"idiom": "귀가 얇다 (Gwiga yalpda.)", "meaning": {"en": "to be easily persuaded by others.", "ru": "легко поддаваться чужому влиянию.", "kk": "басқаның сөзіне тез көну."}},
    ],
    "TOPIK 5-6": [
        {"idiom": "등잔 밑이 어둡다 (Deungjan michi eodupda.)", "meaning": {"en": "the obvious is often overlooked.", "ru": "самое очевидное часто остаётся незамеченным.", "kk": "көзге көрінген нәрсе байқалмай қалады."}},
        {"idiom": "엎질러진 물 (Eopjilleojin mul.)", "meaning": {"en": "what's done cannot be undone.", "ru": "что сделано, то сделано.", "kk": "болған іс қайтпайды."}},
        {"idiom": "호랑이 굴에 가야 호랑이를 잡는다 (Horangi gure gaya horangireul jamneunda.)", "meaning": {"en": "nothing ventured, nothing gained.", "ru": "кто не рискует, тот не выигрывает.", "kk": "тәуекел етпеген жетістікке жетпейді."}},
        {"idiom": "쇠뿔도 단김에 빼라 (Soebbuldo dangime ppaera.)", "meaning": {"en": "strike while the iron is hot.", "ru": "куй железо, пока горячо.", "kk": "темірді ыстығында соқ."}},
        {"idiom": "우물 안 개구리 (Umul an gaeguri.)", "meaning": {"en": "a person with a narrow view of the world.", "ru": "человек с узким кругозором.", "kk": "дүниетанымы тар адам."}},
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
        {"title": "'Magic Tree House' by Mary Pope Osborne", "tag": "Adventure", "term": "Curious", "meaning": {"en": "wanting to learn or know about something.", "ru": "желающий узнать что-то новое.", "kk": "бір нәрсені білгісі келетін."}},
        {"title": "'Ivy and Bean' by Annie Barrows", "tag": "Friendship", "term": "Mischief", "meaning": {"en": "playful troublemaking.", "ru": "озорное поведение.", "kk": "ойнақы тентектік."}},
    ],
    "B1-B2": [
        {"title": "'Wonder' by R.J. Palacio", "tag": "School Life", "term": "Empathy", "meaning": {"en": "understanding others' feelings.", "ru": "понимание чувств других.", "kk": "басқалардың сезімін түсіну."}},
        {"title": "'The Giver' by Lois Lowry", "tag": "Society", "term": "Utopia", "meaning": {"en": "an imagined perfect place.", "ru": "воображаемое идеальное место.", "kk": "қиялдағы мінсіз орын."}},
        {"title": "'Animal Farm' by George Orwell", "tag": "Politics", "term": "Allegory", "meaning": {"en": "a story with a hidden meaning.", "ru": "история со скрытым смыслом.", "kk": "жасырын мағынасы бар әңгіме."}},
        {"title": "'Holes' by Louis Sachar", "tag": "Adventure", "term": "Injustice", "meaning": {"en": "unfair treatment of someone.", "ru": "несправедливое обращение с кем-то.", "kk": "біреуге әділетсіз қарау."}},
        {"title": "'Chains' by Laurie Halse Anderson", "tag": "History", "term": "Rebellion", "meaning": {"en": "resistance against authority.", "ru": "сопротивление власти.", "kk": "билікке қарсы тұру."}},
        {"title": "'The Outsiders' by S.E. Hinton", "tag": "Identity", "term": "Loyalty", "meaning": {"en": "being faithful to someone.", "ru": "верность кому-то.", "kk": "біреуге адал болу."}},
    ],
    "C1-C2": [
        {"title": "'1984' by George Orwell", "tag": "Freedom", "term": "Totalitarianism", "meaning": {"en": "absolute state control.", "ru": "абсолютный контроль государства.", "kk": "мемлекеттің толық бақылауы."}},
        {"title": "'Fahrenheit 451' by Ray Bradbury", "tag": "Media", "term": "Censorship", "meaning": {"en": "suppressing information.", "ru": "подавление информации.", "kk": "ақпаратты тежеу."}},
        {"title": "'Brave New World' by Aldous Huxley", "tag": "Society", "term": "Conditioning", "meaning": {"en": "training someone to behave a certain way.", "ru": "обучение кого-либо определённому поведению.", "kk": "біреуді белгілі бір тәртіпке үйрету."}},
        {"title": "'Lord of the Flies' by William Golding", "tag": "Human Nature", "term": "Savagery", "meaning": {"en": "extremely cruel or violent behavior.", "ru": "крайне жестокое поведение.", "kk": "өте қатыгез мінез-құлық."}},
        {"title": "'The Catcher in the Rye' by J.D. Salinger", "tag": "Identity", "term": "Alienation", "meaning": {"en": "feeling isolated from others.", "ru": "чувство оторванности от других.", "kk": "басқалардан алшақтау сезімі."}},
        {"title": "'The Handmaid's Tale' by Margaret Atwood", "tag": "Society", "term": "Oppression", "meaning": {"en": "unjust use of power over others.", "ru": "несправедливое использование власти над другими.", "kk": "басқаларға әділетсіз билік жүргізу."}},
    ],
}

BOOKS_DE = {
    "A1-A2": [
        {"title": "«Rico, Oskar und die Tieferschatten» – Andreas Steinhöfel", "tag": "Freundschaft", "term": "Ängstlich", "meaning": {"en": "fearful, anxious.", "ru": "тревожный, боязливый.", "kk": "қорқынышты, үрейлі."}},
        {"title": "«Die Sams» – Paul Maar", "tag": "Fantasie", "term": "Wunsch", "meaning": {"en": "a desire or wish.", "ru": "желание.", "kk": "тілек."}},
        {"title": "«Emil und die Detektive» – Erich Kästner", "tag": "Abenteuer", "term": "Zusammenhalt", "meaning": {"en": "acting together for a goal.", "ru": "совместные действия ради цели.", "kk": "ортақ мақсат үшін бірге әрекет ету."}},
        {"title": "«Das doppelte Lottchen» – Erich Kästner", "tag": "Familie", "term": "Zwilling", "meaning": {"en": "a twin.", "ru": "близнец.", "kk": "егіз."}},
        {"title": "«Der Regenbogenfisch» – Marcus Pfister", "tag": "Freundschaft", "term": "Freundlich", "meaning": {"en": "kind and considerate toward others.", "ru": "добрый и внимательный к другим.", "kk": "басқаларға мейірімді әрі қамқор."}},
        {"title": "«Die kleine Hexe» – Otfried Preußler", "tag": "Fantasie", "term": "Neugierig", "meaning": {"en": "curious, eager to learn.", "ru": "любопытный.", "kk": "қызығушылық танытатын."}},
    ],
    "B1-B2": [
        {"title": "«Die Welle» – Todd Strasser", "tag": "Gesellschaft", "term": "Konformität", "meaning": {"en": "going along with the group.", "ru": "подчинение группе.", "kk": "топқа бағыну."}},
        {"title": "«Tschick» – Wolfgang Herrndorf", "tag": "Freundschaft", "term": "Außenseiter", "meaning": {"en": "someone who doesn't belong.", "ru": "тот, кто не вписывается.", "kk": "топқа сыймайтын адам."}},
        {"title": "«Momo» – Michael Ende", "tag": "Zeit", "term": "Achtsamkeit", "meaning": {"en": "being aware of the present.", "ru": "внимание к настоящему моменту.", "kk": "қазіргі сәтке мән беру."}},
        {"title": "«Krabat» – Otfried Preußler", "tag": "Fantasie", "term": "Macht", "meaning": {"en": "control or power over others.", "ru": "власть, контроль над другими.", "kk": "басқаларға билік жүргізу."}},
        {"title": "«Vorstadtkrokodile» – Max von der Grün", "tag": "Freundschaft", "term": "Vorurteil", "meaning": {"en": "prejudice.", "ru": "предрассудок.", "kk": "жаңсақ пікір."}},
        {"title": "«Damals war es Friedrich» – Hans Peter Richter", "tag": "Geschichte", "term": "Verfolgung", "meaning": {"en": "persecution.", "ru": "преследование.", "kk": "қуғын-сүргін."}},
    ],
    "C1-C2": [
        {"title": "«Die Verwandlung» – Franz Kafka", "tag": "Identität", "term": "Entfremdung", "meaning": {"en": "feeling disconnected from others.", "ru": "чувство оторванности от других.", "kk": "басқалардан алшақтау сезімі."}},
        {"title": "«Der Steppenwolf» – Hermann Hesse", "tag": "Philosophie", "term": "Zerrissenheit", "meaning": {"en": "inner conflict, being torn between two selves.", "ru": "внутренний разлад, раздвоенность.", "kk": "ішкі қайшылық, екіге бөлінген күй."}},
        {"title": "«Der Vorleser» – Bernhard Schlink", "tag": "Geschichte", "term": "Schuld", "meaning": {"en": "guilt, responsibility for wrongdoing.", "ru": "вина, ответственность за проступок.", "kk": "кінә, жасаған қателігі үшін жауапкершілік."}},
        {"title": "«Homo Faber» – Max Frisch", "tag": "Schicksal", "term": "Zufall", "meaning": {"en": "chance, coincidence.", "ru": "случайность.", "kk": "кездейсоқтық."}},
        {"title": "«Siddhartha» – Hermann Hesse", "tag": "Philosophie", "term": "Erleuchtung", "meaning": {"en": "a state of deep spiritual understanding.", "ru": "состояние глубокого духовного прозрения.", "kk": "терең рухани түсінік күйі."}},
        {"title": "«Der Prozess» – Franz Kafka", "tag": "Justiz", "term": "Absurdität", "meaning": {"en": "absurdity.", "ru": "абсурдность.", "kk": "абсурдтық."}},
    ],
}

BOOKS_RU = [
    {"title": "«Мастер и Маргарита» — Михаил Булгаков", "tag": "Философия", "term": "Аллегория", "meaning": {"en": "a story with a hidden meaning.", "ru": "история со скрытым смыслом.", "kk": "жасырын мағынасы бар әңгіме."}},
    {"title": "«Дети подземелья» — Владимир Короленко", "tag": "Общество", "term": "Сострадание", "meaning": {"en": "sympathy for others.", "ru": "сочувствие другим.", "kk": "басқаларға жанашырлық."}},
    {"title": "«Дубровский» — Александр Пушкин", "tag": "Справедливость", "term": "Справедливость", "meaning": {"en": "fairness and moral rightness.", "ru": "нравственная правота.", "kk": "адалдық пен растық."}},
    {"title": "«Судьба человека» — Михаил Шолохов", "tag": "Война", "term": "Стойкость", "meaning": {"en": "the ability to recover from hardship.", "ru": "способность преодолевать трудности.", "kk": "қиындықтан қайта қалпына келу қабілеті."}},
    {"title": "«Капитанская дочка» — Александр Пушкин", "tag": "История", "term": "Честь", "meaning": {"en": "honor, moral integrity.", "ru": "честь, нравственное достоинство.", "kk": "ар-намыс, адамгершілік қасиет."}},
    {"title": "«Отцы и дети» — Иван Тургенев", "tag": "Поколения", "term": "Нигилизм", "meaning": {"en": "rejection of established beliefs and values.", "ru": "отрицание общепринятых убеждений и ценностей.", "kk": "жалпыға қабылданған нанымдар мен құндылықтарды теріске шығару."}},
]

BOOKS_KK = [
    {"title": "«Абай жолы» – Мұхтар Әуезов", "tag": "Тарих", "term": "Тағдыр", "meaning": {"kk": "адам өмірінің бағыты.", "ru": "предопределённый ход жизни человека.", "en": "the predetermined course of one's life."}},
    {"title": "«Менің атым Қожа» – Бердібек Соқпақбаев", "tag": "Мектеп өмірі", "term": "Жауапкершілік", "meaning": {"kk": "өз әрекетің үшін жауап беру.", "ru": "обязанность отвечать за свои поступки.", "en": "being accountable for one's actions."}},
    {"title": "«Көшпенділер» – Ілияс Есенберлин", "tag": "Тарих", "term": "Азаттық", "meaning": {"kk": "тәуелсіздік, еркіндік.", "ru": "независимость.", "en": "independence."}},
    {"title": "«Ұлпан» – Ғабит Мүсірепов", "tag": "Қоғам", "term": "Әділдік", "meaning": {"kk": "растық пен адалдық.", "ru": "правда и честность.", "en": "fairness and honesty."}},
    {"title": "«Қан мен тер» – Әбдіжәміл Нұрпейісов", "tag": "Тарих", "term": "Тартыс", "meaning": {"kk": "қиын жағдайдағы күрес.", "ru": "борьба в тяжёлых условиях.", "en": "struggle under difficult circumstances."}},
    {"title": "«Балалық шаққа саяхат» – Бердібек Соқпақбаев", "tag": "Балалық шақ", "term": "Достық", "meaning": {"kk": "жақын қарым-қатынас пен сенім.", "ru": "близкие отношения и доверие.", "en": "a close, trusting relationship."}},
]

BOOKS_ES = {
    "A1-A2": [
        {"title": "'El Principito' – Antoine de Saint-Exupéry", "tag": "Filosofía", "term": "Esencial", "meaning": {"en": "what truly matters.", "ru": "то, что действительно важно.", "kk": "шынымен мәні бар нәрсе."}},
        {"title": "'Platero y yo' – Juan Ramón Jiménez", "tag": "Naturaleza", "term": "Ternura", "meaning": {"en": "tenderness, gentle affection.", "ru": "нежность.", "kk": "нәзіктік."}},
        {"title": "'Cuentos de la selva' – Horacio Quiroga", "tag": "Aventura", "term": "Selva", "meaning": {"en": "jungle, forest.", "ru": "джунгли, лес.", "kk": "джунгли, орман."}},
        {"title": "'Marcelino Pan y Vino' – José María Sánchez Silva", "tag": "Amistad", "term": "Bondad", "meaning": {"en": "kindness, goodness.", "ru": "доброта.", "kk": "мейірімділік."}},
        {"title": "'Manolito Gafotas' – Elvira Lindo", "tag": "Vida escolar", "term": "Travieso", "meaning": {"en": "mischievous, playfully naughty.", "ru": "озорной, шаловливый.", "kk": "тентек, ойнақы."}},
        {"title": "'Elmer' – David McKee", "tag": "Identidad", "term": "Colorido", "meaning": {"en": "having many bright colors.", "ru": "разноцветный, яркий.", "kk": "түрлі-түсті, жарқын."}},
    ],
    "B1-B2": [
        {"title": "'Como agua para chocolate' – Laura Esquivel", "tag": "Tradición", "term": "Pasión", "meaning": {"en": "intense, powerful emotion.", "ru": "сильное, глубокое чувство.", "kk": "қатты, терең сезім."}},
        {"title": "'El túnel' – Ernesto Sabato", "tag": "Psicología", "term": "Obsesión", "meaning": {"en": "a fixed, intense preoccupation.", "ru": "навязчивая, сильная поглощённость чем-то.", "kk": "бір нәрсеге қатты құмарту."}},
        {"title": "'La casa de los espíritus' – Isabel Allende", "tag": "Familia", "term": "Destino", "meaning": {"en": "the predetermined course of events.", "ru": "предопределённый ход событий.", "kk": "алдын ала белгіленген өмір барысы."}},
        {"title": "'Réquiem por un campesino español' – Ramón J. Sender", "tag": "Guerra", "term": "Traición", "meaning": {"en": "betrayal.", "ru": "предательство.", "kk": "опасыздық."}},
        {"title": "'El diario de Ana Frank' (edición en español)", "tag": "Historia", "term": "Esperanza", "meaning": {"en": "hope.", "ru": "надежда.", "kk": "үміт."}},
        {"title": "'La casa en Mango Street' – Sandra Cisneros", "tag": "Identidad", "term": "Pertenencia", "meaning": {"en": "belonging.", "ru": "принадлежность.", "kk": "тиесілілік."}},
    ],
    "C1-C2": [
        {"title": "'Cien años de soledad' – Gabriel García Márquez", "tag": "Realismo mágico", "term": "Soledad", "meaning": {"en": "the state of being alone.", "ru": "состояние уединения.", "kk": "жалғыз қалу күйі."}},
        {"title": "'Rayuela' – Julio Cortázar", "tag": "Literatura experimental", "term": "Ambigüedad", "meaning": {"en": "ambiguity.", "ru": "двусмысленность.", "kk": "екіұштылық."}},
        {"title": "'Pedro Páramo' – Juan Rulfo", "tag": "Realismo mágico", "term": "Fantasma", "meaning": {"en": "ghost, apparition.", "ru": "призрак.", "kk": "елес, аруақ."}},
        {"title": "'La casa de Bernarda Alba' – Federico García Lorca", "tag": "Teatro", "term": "Represión", "meaning": {"en": "repression.", "ru": "подавление, репрессия.", "kk": "басып-жаншу, репрессия."}},
        {"title": "'La familia de Pascual Duarte' – Camilo José Cela", "tag": "Sociedad", "term": "Violencia", "meaning": {"en": "violence.", "ru": "насилие.", "kk": "зорлық-зомбылық."}},
        {"title": "'Ficciones' – Jorge Luis Borges", "tag": "Filosofía", "term": "Infinito", "meaning": {"en": "infinity.", "ru": "бесконечность.", "kk": "шексіздік."}},
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

BOOKS_ZH = {
    "HSK 1-3": [
        {"title": "《不一样的卡梅拉》系列", "tag": "儿童故事", "term": "勇敢 (yǒnggǎn)", "meaning": {"en": "brave, having courage.", "ru": "смелый, храбрый.", "kk": "батыл, ержүрек."}},
        {"title": "《猜猜我有多爱你》", "tag": "家庭", "term": "爱 (ài)", "meaning": {"en": "love, deep affection.", "ru": "любовь, глубокая привязанность.", "kk": "сүйіспеншілік."}},
    ],
    "HSK 4-6": [
        {"title": "《小王子》– 圣埃克苏佩里", "tag": "哲学", "term": "本质 (běnzhì)", "meaning": {"en": "essence, what truly matters.", "ru": "суть, то, что действительно важно.", "kk": "мән, шынымен маңызды нәрсе."}},
        {"title": "《活着》– 余华", "tag": "人生", "term": "命运 (mìngyùn)", "meaning": {"en": "fate, the course of events beyond one's control.", "ru": "судьба.", "kk": "тағдыр."}},
    ],
    "HSK 7-9": [
        {"title": "《红楼梦》– 曹雪芹", "tag": "经典文学", "term": "情缘 (qíngyuán)", "meaning": {"en": "a destined emotional bond between people.", "ru": "предначертанная эмоциональная связь между людьми.", "kk": "адамдар арасындағы тағдырлы сезімдік байланыс."}},
        {"title": "《围城》– 钱钟书", "tag": "社会讽刺", "term": "讽刺 (fěngcì)", "meaning": {"en": "satire, using irony to criticize.", "ru": "сатира.", "kk": "сатира, мысқылмен сынау."}},
    ],
}

BOOKS_JA = {
    "N5-N4": [
        {"title": "『ぐりとぐら』– 中川李枝子", "tag": "児童文学", "term": "友情 (yūjō)", "meaning": {"en": "friendship.", "ru": "дружба.", "kk": "достық."}},
        {"title": "『はらぺこあおむし』– エリック・カール", "tag": "児童文学", "term": "空腹 (kūfuku)", "meaning": {"en": "hunger, being hungry.", "ru": "голод.", "kk": "аштық."}},
    ],
    "N3-N2": [
        {"title": "『キッチン』– 吉本ばなな", "tag": "現代文学", "term": "喪失 (sōshitsu)", "meaning": {"en": "loss, the state of losing something.", "ru": "утрата, потеря чего-либо.", "kk": "жоғалту, айырылу."}},
        {"title": "『魔女の宅急便』– 角野栄子", "tag": "成長物語", "term": "自立 (jiritsu)", "meaning": {"en": "independence, standing on one's own.", "ru": "самостоятельность.", "kk": "дербестік."}},
    ],
    "N1": [
        {"title": "『人間失格』– 太宰治", "tag": "文学", "term": "疎外感 (sogaikan)", "meaning": {"en": "a sense of alienation.", "ru": "чувство отчуждения.", "kk": "оқшаулану сезімі."}},
        {"title": "『こころ』– 夏目漱石", "tag": "文学", "term": "孤独 (kodoku)", "meaning": {"en": "solitude, loneliness.", "ru": "одиночество.", "kk": "жалғыздық."}},
    ],
}

BOOKS_KO = {
    "TOPIK 1-2": [
        {"title": "『구름빵』– 백희나", "tag": "동화", "term": "상상력 (sangsangnyeok)", "meaning": {"en": "imagination.", "ru": "воображение.", "kk": "қиял, елестету қабілеті."}},
        {"title": "『강아지똥』– 권정생", "tag": "동화", "term": "소중함 (sojungham)", "meaning": {"en": "preciousness, being valuable.", "ru": "ценность, значимость.", "kk": "құндылық, маңыздылық."}},
    ],
    "TOPIK 3-4": [
        {"title": "『완득이』– 김려령", "tag": "청소년 소설", "term": "편견 (pyeongyeon)", "meaning": {"en": "prejudice, a preconceived opinion.", "ru": "предрассудок, предвзятое мнение.", "kk": "жаңсақ пікір."}},
        {"title": "『나미야 잡화점의 기적』– 히가시노 게이고", "tag": "소설", "term": "인연 (inyeon)", "meaning": {"en": "fated connection between people.", "ru": "предопределённая связь между людьми.", "kk": "адамдар арасындағы тағдырлы байланыс."}},
    ],
    "TOPIK 5-6": [
        {"title": "『채식주의자』– 한강", "tag": "현대 문학", "term": "소외감 (so-oe-gam)", "meaning": {"en": "a sense of alienation.", "ru": "чувство отчуждения.", "kk": "оқшаулану сезімі."}},
        {"title": "『토지』– 박경리", "tag": "대하소설", "term": "운명 (unmyeong)", "meaning": {"en": "fate, destiny.", "ru": "судьба.", "kk": "тағдыр."}},
    ],
}

BOOKS = {"en": BOOKS_EN, "de": BOOKS_DE, "ru": BOOKS_RU, "kk": BOOKS_KK, "es": BOOKS_ES, "it": BOOKS_IT, "fr": BOOKS_FR,
         "zh": BOOKS_ZH, "ja": BOOKS_JA, "ko": BOOKS_KO}

def get_books_pool(p_lang, lvl):
    if p_lang in LEVELED_LANGS:
        return BOOKS[p_lang][lvl]
    return BOOKS[p_lang]

# --- helpers to fetch the right pool ---
def get_word_pool(p_lang, lvl):
    if p_lang in LEVELED_LANGS:
        return {"en": WORDS_EN, "de": WORDS_DE, "es": WORDS_ES, "it": WORDS_IT, "fr": WORDS_FR,
                "zh": WORDS_ZH, "ja": WORDS_JA, "ko": WORDS_KO}[p_lang][lvl]
    return {"ru": WORDS_RU, "kk": WORDS_KK}[p_lang]

def get_idiom_pool(p_lang, lvl):
    if p_lang in LEVELED_LANGS:
        return {"en": IDIOMS_EN, "de": IDIOMS_DE, "es": IDIOMS_ES, "it": IDIOMS_IT, "fr": IDIOMS_FR,
                "zh": IDIOMS_ZH, "ja": IDIOMS_JA, "ko": IDIOMS_KO}[p_lang][lvl]
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
        "zh": {
            "HSK 1-3": [("HSKStory (free graded stories)", "https://hskstory.com/"),
                        ("Chinese Graded Reader", "https://chinesegradedreader.com/")],
            "HSK 4-6": [("HSKReading.com (free)", "https://hskreading.com/"),
                        ("HSK Course Reading", "https://www.hskcourse.com/chinese-reading/")],
            "HSK 7-9": [("HSK Course Reading", "https://www.hskcourse.com/chinese-reading/"),
                        ("HSKReading.com (advanced)", "https://hskreading.com/")],
        },
        "ja": {
            "N5-N4": [("Hanabira Japanese Reading (free)", "https://www.hanabira.org/japanese/reading"),
                      ("Japanesetest4you", "https://japanesetest4you.com/")],
            "N3-N2": [("Hanabira Japanese Reading", "https://www.hanabira.org/japanese/reading"),
                      ("NPO Tadoku Supporters (free)", "https://tadoku.org/")],
            "N1": [("Japanesetest4you", "https://japanesetest4you.com/"),
                   ("Hanabira Japanese Reading", "https://www.hanabira.org/japanese/reading")],
        },
        "ko": {
            "TOPIK 1-2": [("Hanabira Korean Reading (free)", "https://hanabira.org/korean/reading"),
                          ("Korean Graded Readers", "https://koreangradedreaders.com/gr/")],
            "TOPIK 3-4": [("Korean Graded Readers", "https://koreangradedreaders.com/"),
                          ("Hanabira Korean Reading", "https://hanabira.org/korean/reading")],
            "TOPIK 5-6": [("Korean Graded Readers", "https://koreangradedreaders.com/"),
                          ("TOPIK Mock Test (free)", "https://learning-korean.com/topik/")],
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
    weekly_selection = random.sample(books_pool, min(3, len(books_pool)))

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

TOPICS_ZH = {
    "HSK 1-3": [
        ("说说你的家人。", "Shuōshuo nǐ de jiārén."),
        ("你周末喜欢做什么?", "Nǐ zhōumò xǐhuan zuò shénme?"),
        ("描述一下你的房间。", "Miáoshù yíxià nǐ de fángjiān."),
        ("你最喜欢的食物是什么?", "Nǐ zuì xǐhuan de shíwù shì shénme?"),
        ("说说你最好的朋友。", "Shuōshuo nǐ zuì hǎo de péngyou."),
        ("你最喜欢哪个季节?", "Nǐ zuì xǐhuan nǎge jìjié?"),
        ("描述你的学校。", "Miáoshù nǐ de xuéxiào."),
        ("你喜欢什么颜色?", "Nǐ xǐhuan shénme yánsè?"),
    ],
    "HSK 4-6": [
        ("社交媒体让我们更亲近还是更孤独?", "Shèjiāo méitǐ ràng wǒmen gèng qīnjìn háishi gèng gūdú?"),
        ("青少年应该在上学期间打工吗?", "Qīngshàonián yīnggāi zài shàngxué qījiān dǎgōng ma?"),
        ("生活在大城市好还是小城市好?", "Shēnghuó zài dà chéngshì hǎo háishi xiǎo chéngshì hǎo?"),
        ("学校应该禁止使用手机吗?", "Xuéxiào yīnggāi jìnzhǐ shǐyòng shǒujī ma?"),
        ("传统习俗应该保留还是应该现代化?", "Chuántǒng xísú yīnggāi bǎoliú háishi yīnggāi xiàndàihuà?"),
        ("网络名气算是真正的成功吗?", "Wǎngluò míngqì suàn shì zhēnzhèng de chénggōng ma?"),
        ("旅游业对当地社区是利大于弊还是弊大于利?", "Lǚyóuyè duì dāngdì shèqū shì lì dàyú bì háishi bì dàyú lì?"),
        ("青少年应该有更多的独立性吗?", "Qīngshàonián yīnggāi yǒu gèngduō de dúlìxìng ma?"),
    ],
    "HSK 7-9": [
        ("一种语言会随着最后一个使用者的消失而真正消亡吗?", "Yì zhǒng yǔyán huì suízhe zuìhòu yí gè shǐyòngzhě de xiāoshī ér zhēnzhèng xiāowáng ma?"),
        ("文化身份是继承来的,还是自己选择的?", "Wénhuà shēnfèn shì jìchéng lái de, háishi zìjǐ xuǎnzé de?"),
        ("全球化究竟是丰富了本土文化,还是抹去了它们?", "Quánqiúhuà jiūjìng shì fēngfùle běntǔ wénhuà, háishi mǒqùle tāmen?"),
        ("艺术必须具有社会意义吗,还是单纯的美就足够了?", "Yìshù bìxū jùyǒu shèhuì yìyì ma, háishi dānchún de měi jiù zúgòule?"),
        ("我们能完全信任一个民族的集体记忆吗?", "Wǒmen néng wánquán xìnrèn yí gè mínzú de jítǐ jìyì ma?"),
        ("个人自由应该在多大程度上让位于集体利益?", "Gèrén zìyóu yīnggāi zài duōdà chéngdù shàng ràngwèi yú jítǐ lìyì?"),
        ("真正的精英制度存在吗,还是只是一种方便的幻觉?", "Zhēnzhèng de jīngyīng zhìdù cúnzài ma, háishi zhǐshì yì zhǒng fāngbiàn de huànjué?"),
    ],
}

TOPICS_JA = {
    "N5-N4": [
        ("家族について話してください。", "Kazoku ni tsuite hanashite kudasai."),
        ("週末は何をするのが好きですか?", "Shūmatsu wa nani o suru no ga suki desu ka?"),
        ("自分の部屋を説明してください。", "Jibun no heya o setsumei shite kudasai."),
        ("好きな食べ物は何ですか?", "Suki na tabemono wa nan desu ka?"),
        ("親友について話してください。", "Shin'yū ni tsuite hanashite kudasai."),
        ("好きな季節はいつですか?", "Suki na kisetsu wa itsu desu ka?"),
        ("学校について説明してください。", "Gakkō ni tsuite setsumei shite kudasai."),
        ("好きな色は何ですか?", "Suki na iro wa nan desu ka?"),
    ],
    "N3-N2": [
        ("SNSは人と人を近づけますか、それとも孤立させますか?", "SNS wa hito to hito o chikazukemasu ka, soretomo koritsu sasemasu ka?"),
        ("学生は勉強しながらアルバイトをするべきですか?", "Gakusei wa benkyō shinagara arubaito o suru beki desu ka?"),
        ("大都市と田舎、どちらに住む方がいいですか?", "Daitoshi to inaka, dochira ni sumu hō ga ii desu ka?"),
        ("学校で携帯電話を禁止するべきですか?", "Gakkō de keitai denwa o kinshi suru beki desu ka?"),
        ("伝統は守るべきですか、それとも現代化するべきですか?", "Dentō wa mamoru beki desu ka, soretomo gendaika suru beki desu ka?"),
        ("SNSでの人気は本当の成功と言えますか?", "SNS de no ninki wa hontō no seikō to iemasu ka?"),
        ("観光は地元の社会に良い影響を与えますか?", "Kankō wa jimoto no shakai ni yoi eikyō o ataemasu ka?"),
        ("若者はもっと自立するべきですか?", "Wakamono wa motto jiritsu suru beki desu ka?"),
    ],
    "N1": [
        ("言語は最後の話者と共に本当に消えるのでしょうか、それとも別の形で生き続けるのでしょうか?", "Gengo wa saigo no washa to tomo ni hontō ni kieru no deshō ka, soretomo betsu no katachi de ikitsuzukeru no deshō ka?"),
        ("文化的アイデンティティは受け継ぐものでしょうか、それとも自ら選ぶものでしょうか?", "Bunkateki aidentiti wa uketsugu mono deshō ka, soretomo mizukara erabu mono deshō ka?"),
        ("グローバル化は地域文化を豊かにするのでしょうか、それとも消し去るのでしょうか?", "Gurōbaruka wa chiiki bunka o yutaka ni suru no deshō ka, soretomo keshisaru no deshō ka?"),
        ("芸術には社会的な目的が必要でしょうか、それとも美しさだけで十分でしょうか?", "Geijutsu ni wa shakaiteki na mokuteki ga hitsuyō deshō ka, soretomo utsukushisa dake de jūbun deshō ka?"),
        ("私たちは民族の集合的記憶を完全に信頼できるのでしょうか?", "Watashitachi wa minzoku no shūgōteki kioku o kanzen ni shinrai dekiru no deshō ka?"),
        ("個人の自由は、どこまで集団の利益に譲るべきでしょうか?", "Kojin no jiyū wa, dokomade shūdan no rieki ni yuzuru beki deshō ka?"),
        ("真の実力主義は存在するのでしょうか、それとも都合の良い幻想に過ぎないのでしょうか?", "Shin no jitsuryoku shugi wa sonzai suru no deshō ka, soretomo tsugō no yoi gensō ni suginai no deshō ka?"),
    ],
}

TOPICS_KO = {
    "TOPIK 1-2": [
        ("가족에 대해 이야기해 주세요.", "Gajoge daehae iyagihae juseyo."),
        ("주말에 무엇을 하는 것을 좋아해요?", "Jumare mueoseul haneun geoseul joahaeyo?"),
        ("당신의 방을 묘사해 보세요.", "Dangsinui bangeul myosahae boseyo."),
        ("가장 좋아하는 음식은 무엇이에요?", "Gajang joahaneun eumsigeun mueosieyo?"),
        ("가장 친한 친구에 대해 말해 주세요.", "Gajang chinhan chingue daehae malhae juseyo."),
        ("어떤 계절을 가장 좋아해요?", "Eotteon gyejeoreul gajang joahaeyo?"),
        ("학교에 대해 설명해 주세요.", "Hakgyoe daehae seolmyeonghae juseyo."),
        ("가장 좋아하는 색깔은 무엇이에요?", "Gajang joahaneun saekkkareun mueosieyo?"),
    ],
    "TOPIK 3-4": [
        ("소셜 미디어는 우리를 더 가깝게 만들까요, 아니면 더 고립시킬까요?", "Sosyeol midieoneun urireul deo gakkapge mandeulkkayo, animyeon deo goripsikilkkayo?"),
        ("학생들은 공부하면서 아르바이트를 해야 할까요?", "Haksaengdeureun gongbuhamyeonseo areubaiteureul haeya halkkayo?"),
        ("대도시와 작은 마을 중 어디에 사는 것이 더 좋을까요?", "Daedosiwa jageun maeul jung eodie saneun geosi deo joeulkkayo?"),
        ("학교에서 휴대폰 사용을 금지해야 할까요?", "Hakgyoeseo hyudaepon sayongeul geumjihaeya halkkayo?"),
        ("전통은 지켜야 할까요, 아니면 현대화해야 할까요?", "Jeontongeun jikyeoya halkkayo, animyeon hyeondaehwahaeya halkkayo?"),
        ("소셜 미디어에서의 인기가 진짜 성공이라고 할 수 있을까요?", "Sosyeol midieoeseoui ingiga jinjja seonggongirago hal su isseulkkayo?"),
        ("관광은 지역 사회에 도움이 될까요, 해가 될까요?", "Gwangwangeun jiyeok sahoee doumi doelkkayo, haega doelkkayo?"),
        ("청소년은 더 많은 독립성을 가져야 할까요?", "Cheongsonyeoneun deo maneun dongnipseongeul gajyeoya halkkayo?"),
    ],
    "TOPIK 5-6": [
        ("언어는 마지막 사용자와 함께 정말로 사라지는 것일까요, 아니면 다른 형태로 살아남는 것일까요?", "Eoneoneun majimak sayongjawa hamkke jeongmallo sarajineun geosilkkayo, animyeon dareun hyeongtaero saranamneun geosilkkayo?"),
        ("문화적 정체성은 물려받는 것일까요, 아니면 스스로 선택하는 것일까요?", "Munhwajeok jeongcheseongeun mullyeobatneun geosilkkayo, animyeon seuseuro seontaekhaneun geosilkkayo?"),
        ("세계화는 지역 문화를 풍요롭게 할까요, 아니면 지워버릴까요?", "Segyehwaneun jiyeok munhwareul pungyoropge halkkayo, animyeon jiwobeorilkkayo?"),
        ("예술은 사회적 목적을 가져야 할까요, 아니면 아름다움만으로 충분할까요?", "Yesureun sahoejeok mokjeogeul gajyeoya halkkayo, animyeon areumdaummaneuro chungbunhalkkayo?"),
        ("우리는 한 민족의 집단 기억을 완전히 신뢰할 수 있을까요?", "Urineun han minjogui jipdan gieogeul wanjeonhi silloehal su isseulkkayo?"),
        ("개인의 자유는 어느 정도까지 공동의 이익에 양보해야 할까요?", "Gaeinui jayuneun eoneu jeongdokkaji gongdongui iige yangbohaeya halkkayo?"),
        ("진정한 능력주의는 존재할까요, 아니면 편리한 환상일 뿐일까요?", "Jinjeonghan neungnyeokjuuineun jonjaehalkkayo, animyeon pyeollihan hwansangil ppunilkkayo?"),
    ],
}

def get_topic_pool(p_lang, lvl):
    if p_lang in LEVELED_LANGS:
        return {"en": TOPICS_EN, "de": TOPICS_DE, "es": TOPICS_ES, "it": TOPICS_IT, "fr": TOPICS_FR,
                 "zh": TOPICS_ZH, "ja": TOPICS_JA, "ko": TOPICS_KO}[p_lang][lvl]
    return {"ru": TOPICS_RU, "kk": TOPICS_KK}[p_lang]

# --- 8. MAIN INTERFACE ---
st.title(t["title"])
st.write(t["subtitle"])

if "topic" not in st.session_state or st.session_state.topic is None:
    st.session_state.topic = t["click_button"]

if st.button(t["get_topic"]):
    random.seed()
    st.session_state.topic = random.choice(get_topic_pool(practice_lang, level))

# topics for zh/ja/ko are (text, reading) tuples; other languages are plain strings
_topic = st.session_state.topic
if isinstance(_topic, tuple):
    topic_text = _topic[0]
    topic_display = f"{_topic[0]} ({_topic[1]})"
else:
    topic_text = _topic
    topic_display = _topic

st.warning(f"**{t['current_topic']}** {topic_display}")

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
            PROMPT_LANG_NAME = {"en": "English", "kk": "Kazakh", "ru": "Russian", "de": "German",
                                 "es": "Spanish", "it": "Italian", "fr": "French",
                                 "zh": "Chinese", "ja": "Japanese", "ko": "Korean"}
            practice_lang_name = PROMPT_LANG_NAME[practice_lang]
            level_note = f" The student's level is {level}." if practice_lang in LEVELED_LANGS else ""

            prompt = (
                f"Topic (spoken in {practice_lang_name}): {topic_text}. "
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
