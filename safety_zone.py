import streamlit as st
from streamlit_mic_recorder import mic_recorder
import google.generativeai as genai
import random
import datetime

# --- 1. CONFIG ---
API_KEY = st.secrets["GEMINI_KEY"]
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="The Safety Zone", page_icon="🎙️", layout="wide")

# --- 2. SIDEBAR: READING & VOCAB LIBRARY ---
with st.sidebar:
    st.header("📚 Study Materials (B1-B2+)")
    
    # --- DAILY WORD & IDIOM ---
    words_of_the_day = [
        {"word": "Ambiguous", "def": "having more than one possible meaning; unclear."},
        {"word": "Eloquent", "def": "fluent or persuasive in speaking or writing."},
        {"word": "Pragmatic", "def": "dealing with things sensibly and realistically."},
        {"word": "Ubiquitous", "def": "present, appearing, or found everywhere."},
        {"word": "Plausible", "def": "seeming reasonable or probable."},
        {"word": "Vivid", "def": "producing powerful feelings or strong, clear images."},
        {"word": "Meticulous", "def": "showing great attention to detail; very careful."}
    ]
    idioms_of_the_day = [
        {"idiom": "A double-edged sword", "meaning": "something that has both favorable and unfavorable consequences."},
        {"idiom": "To play devil's advocate", "meaning": "to argue against an idea to test its quality."},
        {"idiom": "The tip of the iceberg", "meaning": "a small part of a much larger problem."},
        {"idiom": "To hit the nail on the head", "meaning": "to describe exactly what is causing a situation."},
        {"idiom": "Burn the midnight oil", "meaning": "to stay up late working or studying."},
        {"idiom": "Beat around the bush", "meaning": "to avoid talking about the main topic."},
        {"idiom": "Once in a blue moon", "meaning": "something that happens very rarely."}
    ]

    day_of_year = datetime.date.today().timetuple().tm_yday
    today_word = words_of_the_day[day_of_year % len(words_of_the_day)]
    today_idiom = idioms_of_the_day[day_of_year % len(idioms_of_the_day)]

    st.success(f"🌟 **Word of the Day:**\n\n**{today_word['word']}** — {today_word['def']}")
    st.info(f"🗣️ **Idiom of the Day:**\n\n**'{today_idiom['idiom']}'** — {today_idiom['meaning']}")
    st.write("---")
    
    st.subheader("📰 Recommended Articles & News")
    st.markdown("""
    * **[News in Levels](https://www.newsinlevels.com/)** — World news by levels.
    * **[BBC Learning English](https://www.bbc.co.uk/learningenglish/english/features/6-minute-english)** — Perfect for B1-B2.
    * **[Teen Vogue - Politics](https://www.teenvogue.com/politics)** — High-quality articles for teens.
    """)

    # --- WEEKLY BOOKS ---
    all_books = [
        {"title": "'Animal Farm' by George Orwell", "tag": "Politics", "vocab": "Corruption (dishonest conduct), Allegory (a story with a hidden meaning)"},
        {"title": "'The Giver' by Lois Lowry", "tag": "Society", "vocab": "Conformity (following rules/trends), Utopia (an imagined perfect place)"},
        {"title": "'Fahrenheit 451' by Ray Bradbury", "tag": "Media", "vocab": "Distraction (something that takes focus), Censorship (suppressing info)"},
        {"title": "'Brave New World' by Aldous Huxley", "tag": "Science", "vocab": "Conditioning (training to behave a certain way), Stability (being steady)"},
        {"title": "'Wonder' by R.J. Palacio", "tag": "School Life", "vocab": "Empathy (understanding others' feelings), Resilience (recovering quickly)"},
        {"title": "'The Hunger Games' by Suzanne Collins", "tag": "Survival", "vocab": "Defiance (open resistance), Sacrifice (giving up value)"},
        {"title": "'1984' by George Orwell", "tag": "Freedom", "vocab": "Totalitarianism (absolute control), Thoughtcrime (illegal thoughts)"},
        {"title": "'The Little Prince' by A. de Saint-Exupéry", "tag": "Philosophy", "vocab": "Essential (very important), Paradox (contradictory statement)"},
        {"title": "'Lord of the Flies' by William Golding", "tag": "Order", "vocab": "Savagery (being fierce/cruel), Leadership (leading a group)"},
        {"title": "'To Kill a Mockingbird' by Harper Lee", "tag": "Justice", "vocab": "Integrity (being honest/moral), Compassion (sympathy)"}
    ]

    week_num = datetime.date.today().isocalendar()[1]
    random.seed(week_num) 
    weekly_selection = random.sample(all_books, 5)

    st.subheader(f"📖 Weekly Recommendations (Week {week_num})")
    for book in weekly_selection:
        st.markdown(f"* **{book['title']}** ({book['tag']})")

    st.write("---")
    st.subheader("✨ Vocab from these sources")
    for book in weekly_selection:
        short_name = book['title'].split(' by ')[0]
        st.info(f"**From {short_name}:**\n\n{book['vocab']}")

# --- 3. MAIN INTERFACE ---
st.title("🎙️ The Safety Zone")
st.write("Read the materials in the sidebar, pick a topic, and record your speech!")

if 'topic' not in st.session_state:
    st.session_state.topic = "Click the button below!"

topics = [
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
    "The Main Character: Is it healthy to view your life as a movie starring you?"
]

if st.button("🎲 Get a Topic"):
    random.seed() 
    st.session_state.topic = random.choice(topics)

st.warning(f"**Current Topic:** {st.session_state.topic}")

# --- 4. THE RECORDER ---
st.subheader("Step 1: Record your answer")
audio = mic_recorder(
    start_prompt="🔴 Start Recording",
    stop_prompt="⏹️ Stop & Send",
    key='recorder'
)

if audio:
    st.audio(audio['bytes'])
    st.subheader("Step 2: AI Analysis")
    with st.spinner("Analyzing..."):
        try:
            audio_data = {"mime_type": "audio/wav", "data": audio['bytes']}
            prompt = f"Topic: {st.session_state.topic}. Evaluate grammar, vocab and give 3 tips to improve. Speak as a supportive tutor for an 8th grader."
            response = model.generate_content([prompt, audio_data])
            st.success("Feedback ready!")
            st.markdown(response.text)
        except Exception as e:
            st.error(f"Error: {e}")
