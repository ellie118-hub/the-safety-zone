import streamlit as st
import os
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

# --- 2. LANGUAGE SWITCHER ---
LANGUAGES = {
    "en": {"label": "English", "flag": "🇬🇧"},
    "de": {"label": "Deutsch", "flag": "🇩🇪"},
    # more languages get added here later, same pattern
}

if "lang" not in st.session_state:
    st.session_state.lang = "en"

top_left, top_right = st.columns([6, 1])
with top_right:
    chosen = st.selectbox(
        "🌐",
        options=list(LANGUAGES.keys()),
        format_func=lambda code: f"{LANGUAGES[code]['flag']} {LANGUAGES[code]['label']}",
        index=list(LANGUAGES.keys()).index(st.session_state.lang),
        label_visibility="collapsed",
        key="lang_picker",
    )

if chosen != st.session_state.lang:
    st.session_state.lang = chosen
    st.session_state.topic = None
    st.rerun()

lang = st.session_state.lang

# --- 3. UI TEXT ---
UI = {
    "en": {
        "sidebar_header": "📚 Study Materials (B1-B2+)",
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
    "de": {
        "sidebar_header": "📚 Lernmaterialien (B1-B2+)",
        "word_of_day": "🌟 Wort des Tages:",
        "idiom_of_day": "🗣️ Redewendung des Tages:",
        "articles_header": "📰 Empfohlene Artikel & Nachrichten",
        "books_header": "📖 Wöchentliche Empfehlungen",
        "vocab_header": "✨ Wortschatz aus diesen Quellen",
        "title": "🎙️ Die Sicherheitszone",
        "subtitle": "Lies die Materialien in der Seitenleiste, wähle ein Thema und nimm deine Antwort auf!",
        "click_button": "Klicke auf den Button unten!",
        "get_topic": "🎲 Thema auswählen",
        "current_topic": "Aktuelles Thema:",
        "step1": "Schritt 1: Nimm deine Antwort auf",
        "step2": "Schritt 2: KI-Analyse",
        "start_recording": "🔴 Aufnahme starten",
        "stop_recording": "⏹️ Stoppen & Senden",
        "analyzing": "Analysiere...",
        "feedback_ready": "Feedback ist fertig!",
        "error": "Fehler:",
    },
}
t = UI[lang]

# --- 4. SIDEBAR: WORD & IDIOM OF THE DAY ---
words_of_the_day = {
    "en": [
        {"word": "Ambiguous", "def": "having more than one possible meaning; unclear."},
        {"word": "Eloquent", "def": "fluent or persuasive in speaking or writing."},
        {"word": "Pragmatic", "def": "dealing with things sensibly and realistically."},
        {"word": "Ubiquitous", "def": "present, appearing, or found everywhere."},
        {"word": "Plausible", "def": "seeming reasonable or probable."},
        {"word": "Vivid", "def": "producing powerful feelings or strong, clear images."},
        {"word": "Meticulous", "def": "showing great attention to detail; very careful."},
    ],
    "de": [
        {"word": "Zwiespältig", "def": "widersprüchlich; mit gemischten Gefühlen verbunden."},
        {"word": "Eloquent", "def": "redegewandt und überzeugend im Sprechen oder Schreiben."},
        {"word": "Pragmatisch", "def": "sachlich und auf das Praktische ausgerichtet."},
        {"word": "Allgegenwärtig", "def": "überall vorhanden oder spürbar."},
        {"word": "Plausibel", "def": "einleuchtend und nachvollziehbar."},
        {"word": "Lebhaft", "def": "voller Energie; ein eindrucksvolles, klares Bild erzeugend."},
        {"word": "Akribisch", "def": "äußerst sorgfältig und genau."},
    ],
}

idioms_of_the_day = {
    "en": [
        {"idiom": "A double-edged sword", "meaning": "something that has both favorable and unfavorable consequences."},
        {"idiom": "To play devil's advocate", "meaning": "to argue against an idea to test its quality."},
        {"idiom": "The tip of the iceberg", "meaning": "a small part of a much larger problem."},
        {"idiom": "To hit the nail on the head", "meaning": "to describe exactly what is causing a situation."},
        {"idiom": "Burn the midnight oil", "meaning": "to stay up late working or studying."},
        {"idiom": "Beat around the bush", "meaning": "to avoid talking about the main topic."},
        {"idiom": "Once in a blue moon", "meaning": "something that happens very rarely."},
    ],
    "de": [
        {"idiom": "Da liegt der Hund begraben", "meaning": "das ist der eigentliche Kern des Problems."},
        {"idiom": "Die Katze im Sack kaufen", "meaning": "etwas akzeptieren, ohne es vorher zu prüfen."},
        {"idiom": "Den Nagel auf den Kopf treffen", "meaning": "genau das Wesentliche treffen."},
        {"idiom": "Um den heißen Brei reden", "meaning": "das eigentliche Thema vermeiden."},
        {"idiom": "Die Nase voll haben", "meaning": "von etwas genug haben, es satt haben."},
        {"idiom": "Ins Fettnäpfchen treten", "meaning": "unabsichtlich etwas Peinliches tun oder sagen."},
        {"idiom": "Alle Jubeljahre", "meaning": "sehr selten, nur ab und zu."},
    ],
}

day_of_year = datetime.date.today().timetuple().tm_yday
today_word = words_of_the_day[lang][day_of_year % len(words_of_the_day[lang])]
today_idiom = idioms_of_the_day[lang][day_of_year % len(idioms_of_the_day[lang])]

# --- 5. SIDEBAR: ARTICLES, BOOKS, VOCAB ---
with st.sidebar:
    st.header(t["sidebar_header"])

    st.success(f"**{t['word_of_day']}**\n\n**{today_word['word']}** — {today_word['def']}")
    st.info(f"**{t['idiom_of_day']}**\n\n**'{today_idiom['idiom']}'** — {today_idiom['meaning']}")
    st.write("---")

    st.subheader(t["articles_header"])
    if lang == "de":
        st.markdown("""
        * **[Nachrichtenleicht](https://www.nachrichtenleicht.de/)** — Nachrichten in einfacher Sprache.
        * **[DW Learn German](https://learngerman.dw.com/)** — Übungen für B1-B2.
        * **[Deutsche Welle](https://www.dw.com/de/themen/s-9077)** — Aktuelle Artikel zu vielen Themen.
        """)
    else:
        st.markdown("""
        * **[News in Levels](https://www.newsinlevels.com/)** — World news by levels.
        * **[BBC Learning English](https://www.bbc.co.uk/learningenglish/english/features/6-minute-english)** — Perfect for B1-B2.
        * **[Teen Vogue - Politics](https://www.teenvogue.com/politics)** — High-quality articles for teens.
        """)

    all_books = {
        "en": [
            {"title": "'Animal Farm' by George Orwell", "tag": "Politics", "vocab": "Corruption (dishonest conduct), Allegory (a story with a hidden meaning)"},
            {"title": "'The Giver' by Lois Lowry", "tag": "Society", "vocab": "Conformity (following rules/trends), Utopia (an imagined perfect place)"},
            {"title": "'Fahrenheit 451' by Ray Bradbury", "tag": "Media", "vocab": "Distraction (something that takes focus), Censorship (suppressing info)"},
            {"title": "'Brave New World' by Aldous Huxley", "tag": "Science", "vocab": "Conditioning (training to behave a certain way), Stability (being steady)"},
            {"title": "'Wonder' by R.J. Palacio", "tag": "School Life", "vocab": "Empathy (understanding others' feelings), Resilience (recovering quickly)"},
            {"title": "'The Hunger Games' by Suzanne Collins", "tag": "Survival", "vocab": "Defiance (open resistance), Sacrifice (giving up value)"},
            {"title": "'1984' by George Orwell", "tag": "Freedom", "vocab": "Totalitarianism (absolute control), Thoughtcrime (illegal thoughts)"},
            {"title": "'The Little Prince' by A. de Saint-Exupéry", "tag": "Philosophy", "vocab": "Essential (very important), Paradox (contradictory statement)"},
            {"title": "'Lord of the Flies' by William Golding", "tag": "Order", "vocab": "Savagery (being fierce/cruel), Leadership (leading a group)"},
            {"title": "'To Kill a Mockingbird' by Harper Lee", "tag": "Justice", "vocab": "Integrity (being honest/moral), Compassion (sympathy)"},
        ],
        "de": [
            {"title": "'Die Welle' von Todd Strasser", "tag": "Gesellschaft", "vocab": "Konformität (sich anpassen), Manipulation (heimliche Beeinflussung)"},
            {"title": "'Tschick' von Wolfgang Herrndorf", "tag": "Freundschaft", "vocab": "Außenseiter (jemand, der nicht dazugehört), Freiheit (Unabhängigkeit)"},
            {"title": "'Momo' von Michael Ende", "tag": "Zeit", "vocab": "Achtsamkeit (bewusstes Wahrnehmen), Hektik (Stress und Eile)"},
            {"title": "'Der Vorleser' von Bernhard Schlink", "tag": "Geschichte", "vocab": "Schuld (Verantwortung für Unrecht), Scham (Gefühl der Peinlichkeit)"},
            {"title": "'Emil und die Detektive' von Erich Kästner", "tag": "Abenteuer", "vocab": "Mut (Tapferkeit), Zusammenhalt (gemeinsam handeln)"},
            {"title": "'Die Verwandlung' von Franz Kafka", "tag": "Identität", "vocab": "Entfremdung (sich fremd fühlen), Absurdität (Widersinnigkeit)"},
            {"title": "'Krabat' von Otfried Preußler", "tag": "Fantasie", "vocab": "Macht (Kontrolle über andere), Opfer (Verzicht für ein Ziel)"},
            {"title": "'Der Steppenwolf' von Hermann Hesse", "tag": "Philosophie", "vocab": "Zerrissenheit (innerer Konflikt), Sehnsucht (starkes Verlangen)"},
        ],
    }

    books_pool = all_books[lang]
    week_num = datetime.date.today().isocalendar()[1]
    random.seed(week_num)
    weekly_selection = random.sample(books_pool, min(5, len(books_pool)))

    st.subheader(f"{t['books_header']} ({week_num})")
    for book in weekly_selection:
        st.markdown(f"* **{book['title']}** ({book['tag']})")

    st.write("---")
    st.subheader(t["vocab_header"])
    for book in weekly_selection:
        separator = " von " if lang == "de" else " by "
        short_name = book['title'].split(separator)[0]
        st.info(f"**{short_name}:**\n\n{book['vocab']}")

# --- 6. MAIN INTERFACE ---
st.title(t["title"])
st.write(t["subtitle"])

if "topic" not in st.session_state or st.session_state.topic is None:
    st.session_state.topic = t["click_button"]

topics = {
    "en": [
        "School Uniform: Does it destroy our individuality?",
        "Homework: Should it be banned for more free time?",
        "E-books vs Paper Books: Which is better for studying?",
        "Artificial Intelligence: Is it okay to use ChatGPT for school essays?",
        "Social Media: Does Instagram make us feel more insecure?",
        "Video Games: Are they a waste of time or develop logic?",
        "Music: How does your favorite genre define you?",
        "Sports: Should PE (physical education) be optional?",
        "Fast Fashion: Should we stop buying cheap clothes to save the planet?",
        "Plastic Pollution: Can one person really make a difference?",
        "Space Travel: Should we spend money on Mars or fix Earth first?",
        "Friendship: Is it better to have one best friend or many acquaintances?",
        "Celebrity Culture: Why are we obsessed with famous people?",
        "Pocket Money: Should parents pay kids for house chores?",
        "Travel: Does visiting other countries change our worldview?",
        "Conformity: Is it better to be like everyone else or to be a rebel?",
        "Sustainability: How can we implement green habits in our school?",
        "Digital Literacy: Should we trust everything we read in the news?",
        "Society: Is a perfect 'Utopia' actually possible or is it boring?",
        "Morning Routines: Does waking up at 5:00 AM actually make you successful?",
        "Room Aesthetics: Does a messy desk mean you are creative or just disorganized?",
        "Energy Drinks: Should they be banned for teenagers under 16?",
        "Online Friends: Can someone you have never met be your real best friend?",
        "Read Receipts: Do we have a right to read a message without replying immediately?",
        "Group Chats: Are they great for connecting or just a source of social stress?",
        "Digital Apologies: Is saying 'sorry' over text as meaningful as in person?",
        "Trend Following: Do we buy clothes because we like them or because they are viral?",
        "Avatar Identity: Why do we care so much about how our game characters look?",
        "Emoji Language: Could humans eventually communicate entirely without words?",
        "Second-Hand Style: Is thrifting a way to be unique or just a passing trend?",
        "Movie Villains: Why is the 'bad guy' often more interesting than the hero?",
        "Old Tech: Why are teenagers becoming obsessed with vinyl and film cameras?",
        "Spoiler Culture: Does knowing the ending of a movie ruin it or make it better?",
        "Privacy vs Security: Should parents have the right to check their children's phones?",
        "AI Creativity: Can an algorithm ever create 'real' art, or is it just copying humans?",
        "Boredom: In a world of smartphones, have we forgotten how to just think?",
        "Memory Deletion: If you could erase one embarrassing memory, would you do it?",
        "The Main Character: Is it healthy to view your life as a movie starring you?",
    ],
    "de": [
        "Schuluniform: Zerstört sie unsere Individualität?",
        "Hausaufgaben: Sollten sie abgeschafft werden, um mehr Freizeit zu haben?",
        "E-Books vs. gedruckte Bücher: Was eignet sich besser zum Lernen?",
        "Künstliche Intelligenz: Ist es okay, ChatGPT für Schulaufsätze zu benutzen?",
        "Soziale Medien: Macht Instagram uns unsicherer?",
        "Videospiele: Zeitverschwendung oder fördern sie logisches Denken?",
        "Musik: Wie definiert dein Lieblingsgenre deine Persönlichkeit?",
        "Sport: Sollte Sportunterricht freiwillig sein?",
        "Fast Fashion: Sollten wir aufhören, billige Kleidung zu kaufen, um den Planeten zu retten?",
        "Plastikmüll: Kann eine einzelne Person wirklich etwas bewirken?",
        "Weltraumforschung: Sollten wir Geld für den Mars ausgeben oder zuerst die Erde retten?",
        "Freundschaft: Ist es besser, einen besten Freund zu haben oder viele Bekannte?",
        "Promikultur: Warum sind wir von berühmten Menschen so besessen?",
        "Taschengeld: Sollten Eltern Kinder für Hausarbeit bezahlen?",
        "Reisen: Verändert das Besuchen anderer Länder unsere Weltsicht?",
        "Konformität: Ist es besser, wie alle anderen zu sein, oder ein Rebell zu sein?",
        "Nachhaltigkeit: Wie können wir grüne Gewohnheiten in unserer Schule umsetzen?",
        "Digitale Kompetenz: Sollten wir allem glauben, was wir in den Nachrichten lesen?",
        "Gesellschaft: Ist eine perfekte 'Utopie' überhaupt möglich, oder wäre sie langweilig?",
        "Morgenroutinen: Macht das Aufstehen um 5 Uhr wirklich erfolgreich?",
        "Energydrinks: Sollten sie für Jugendliche unter 16 verboten werden?",
        "Online-Freunde: Kann jemand, den man nie getroffen hat, ein echter bester Freund sein?",
        "Gruppenchats: Verbinden sie uns, oder sind sie nur eine Quelle für sozialen Stress?",
        "Trendfolgen: Kaufen wir Kleidung, weil sie uns gefällt, oder weil sie gerade angesagt ist?",
        "Langeweile: Haben wir in einer Welt voller Smartphones verlernt, einfach nachzudenken?",
    ],
}

if st.button(t["get_topic"]):
    random.seed()
    st.session_state.topic = random.choice(topics[lang])

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
            if lang == "de":
                prompt = (
                    f"Thema: {st.session_state.topic}. "
                    "Bewerte Grammatik und Wortschatz der Antwort und gib 3 Tipps zur Verbesserung. "
                    "Antworte auf Deutsch, im Ton einer unterstützenden Lehrkraft für eine 8. Klasse."
                )
            else:
                prompt = (
                    f"Topic: {st.session_state.topic}. Evaluate grammar, vocab and give 3 tips to improve. "
                    "Speak as a supportive tutor for an 8th grader."
                )
            response = model.generate_content([prompt, audio_data])
            st.success(t["feedback_ready"])
            st.markdown(response.text)
        except Exception as e:
            st.error(f"{t['error']} {e}")
