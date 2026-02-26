import streamlit as st
from PIL import Image

# अपना आइकॉन फाइल अपलोड करो GitHub पर (PNG, 32x32 या 512x512 पिक्सल)
icon = Image.open("icon.png")  # icon.png नाम की फाइल होनी चाहिए
st.set_page_config(
    page_title="Vanya AI",
    page_icon=icon,  # ये आइकॉन टैब में दिखेगा
    layout="centered",
    initial_sidebar_state="expanded"
)
    st.markdown("""
    <link rel="apple-touch-icon" href="icon.png">
    <link rel="apple-touch-icon" sizes="180x180" href="icon.png">
    <link rel="icon" type="image/png" sizes="32x32" href="icon.png">
    <link rel="icon" type="image/png" sizes="16x16" href="icon.png">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black">
    <meta name="apple-mobile-web-app-title" content="Vanya AI">
    <meta name="theme-color" content="#FF69B4">  <!-- अपना कलर डालो, जैसे पिंक -->
    
# बैकग्राउंड म्यूजिक और साउंड इफेक्ट
st.markdown("""
    <audio autoplay loop id="bg_music" style="display:none;">
        <source src="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3" type="audio/mpeg">
    </audio>

    <script>
        // बैकग्राउंड म्यूजिक ऑटो प्ले (म्यूट रखा है, यूजर क्लिक पर अनम्यूट कर सकते हो)
        const bgMusic = document.getElementById('bg_music');
        bgMusic.volume = 0.2;  // हल्का वॉल्यूम
        bgMusic.play().catch(function(error) {
            console.log("Auto-play prevented: " + error);
        });

        // साउंड इफेक्ट जब यूजर मैसेज भेजे
        function playSendSound() {
            const sendSound = new Audio('https://assets.mixkit.co/sfx/preview/mixkit-message-sent-1043.mp3');
            sendSound.volume = 0.5;
            sendSound.play();
        }

        // साउंड इफेक्ट जब Vanya जवाब दे
        function playReceiveSound() {
            const receiveSound = new Audio('https://assets.mixkit.co/sfx/preview/mixkit-message-received-1044.mp3');
            receiveSound.volume = 0.5;
            receiveSound.play();
        }

        // यूजर इनपुट पर साउंड
        const inputBox = document.querySelector('input[data-testid="stChatInputTextInput"]');
        if (inputBox) {
            inputBox.addEventListener('keydown', function(e) {
                if (e.key === 'Enter') {
                    playSendSound();
                }
            });
        }

        // जवाब आने पर साउंड (Streamlit री-रेंडर पर)
        window.addEventListener('message', function(e) {
            if (e.data.type === 'streamlit:componentReady') {
                playReceiveSound();
            }
        });
    </script>
""", unsafe_allow_html=True)
""", unsafe_allow_html=True)
from streamlit_mic_recorder import speech_to_text
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from gtts import gTTS
from io import BytesIO
import requests
import json
import os
from huggingface_hub import InferenceClient
from PIL import Image

# API KEYS
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
HF_TOKEN = st.secrets["HF_TOKEN"]

# मौसम फंक्शन (पिछला)
def get_delhi_weather():
    url = "https://api.open-meteo.com/v1/forecast?latitude=28.6139&longitude=77.2090&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m&timezone=Asia%2FKolkata&daily=temperature_2m_max&forecast_days=2"
    try:
        resp = requests.get(url).json()
        curr = resp['current']
        temp = curr['temperature_2m']
        feels = curr['apparent_temperature']
        hum = curr['relative_humidity_2m']
        wind = curr['wind_speed_10m']
        code = curr['weather_code']
        if code in [0, 1]:
            desc = "साफ आसमान"
        elif code in [2, 3]:
            desc = "बादल छाए हुए"
        elif code in [45, 48]:
            desc = "धुंध"
        elif code in [51,53,55,61,63,65]:
            desc = "बारिश"
        else:
            desc = "मौसम सामान्य"
        forecast = f"कल मैक्स ~{resp['daily']['temperature_2m_max'][1]}°C"
        return f"दिल्ली में अभी: {temp}°C (फील्स {feels}°C), {desc}, नमी {hum}%, हवा {wind} km/h। {forecast}"
    except:
        return "मौसम चेक नहीं हो पाया..."

# To-Do
TODO_FILE = "todo_list.json"

def load_todos():
    if os.path.exists(TODO_FILE):
        with open(TODO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_todos(todos):
    with open(TODO_FILE, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)

# इमेज
hf_client = InferenceClient(token=HF_TOKEN)

def generate_image(prompt):
    try:
        img = hf_client.text_to_image(prompt=prompt, model="black-forest-labs/FLUX.1-dev", num_inference_steps=28, guidance_scale=7.5)
        return img
    except Exception as e:
        return f"इमेज बनाने में दिक्कत: {str(e)}"

# Groq + मेमोरी
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7, groq_api_key=GROQ_API_KEY)

prompt = ChatPromptTemplate.from_messages([
    ("system", "तुम Vanya हो, female AI असिस्टेंट। यूजर का नाम UDAN INSTITUTE है, दिल्ली में रहता है। मूड बताने पर गाना सजेस्ट करो (YouTube लिंक के साथ)। मौसम, टू-डू, इमेज सब हैंडल करो। याद रखो।"),
    MessagesPlaceholder("history"),
    ("human", "{input}")
])

chain = prompt | llm

if "chat_history" not in st.session_state:
    st.session_state.chat_history = StreamlitChatMessageHistory(key="messages")

conversational_chain = RunnableWithMessageHistory(
    chain,
    lambda sid: st.session_state.chat_history,
    input_messages_key="input",
    history_messages_key="history"
)

st.title("Vanya - तुम्हारा पर्सनल AI 💕")

for msg in st.session_state.chat_history.messages:
    with st.chat_message("user" if msg.type == "human" else "assistant"):
        st.markdown(msg.content)

# To-Do UI
st.subheader("मेरा To-Do List")
todos = load_todos()
for i, todo in enumerate(todos):
    checked = st.checkbox(todo["task"], value=todo.get("done", False), key=f"todo_{i}")
    if checked != todo.get("done", False):
        todos[i]["done"] = checked
        save_todos(todos)

if st.button("सभी क्लियर करो"):
    todos = []
    save_todos(todos)
    st.rerun()

# इनपुट
st.write("🎤 बोलो या टाइप करो (उदाहरण: 'मूड सैड है गाना सजेस्ट करो', 'मौसम बताओ', 'इमेज बना के दिखा')")
text_voice = speech_to_text(language='hi-IN', start_prompt="बोलो", stop_prompt="बंद", key='vanya_voice')

prompt_text = st.chat_input("या टाइप करो...")

prompt_input = text_voice or prompt_text

if prompt_input:
    with st.chat_message("user"):
        st.markdown(prompt_input)

    with st.chat_message("assistant"):
        with st.spinner("Vanya सोच रही है..."):
            lower = prompt_input.lower()
            if "मौसम" in lower or "weather" in lower:
                response = get_delhi_weather()
            elif "इमेज" in lower or "दिखा" in lower or "बना" in lower or "generate" in lower or "image" in lower:
                with st.spinner("इमेज बना रही हूँ..."):
                    image = generate_image(prompt_input)
                    if isinstance(image, Image.Image):
                        st.image(image, caption=f"तुम्हारे लिए बनाई गई", use_column_width=True)
                        response = "कैसी लगी इमेज? 😘"
                    else:
                        response = image
            elif "टू-डू" in lower or "todo" in lower or "task" in lower or "याद दिला" in lower:
                parse_prompt = f"यूजर: '{prompt_input}'\nJSON: {{'action': 'add', 'task': 'टास्क नाम'}}"
                parse_resp = llm.invoke(parse_prompt).content.strip()
                try:
                    data = eval(parse_resp)
                    if data.get('action') == 'add':
                        todos.append({"task": data['task'], "done": False})
                        save_todos(todos)
                        response = f"टास्क ऐड कर दिया: {data['task']}"
                    else:
                        response = "अभी सिर्फ ऐड कर सकती हूँ।"
                except:
                    response = "समझ नहीं आई... फिर से बोलो ना।"
            elif "मूड" in lower or "song" in lower or "गाना" in lower or "music" in lower or "सजेस्ट" in lower:
                # म्यूजिक सजेस्ट
                mood = "happy" if "happy" in lower or "खुश" in lower else "sad" if "sad" in lower or "उदास" in lower else "romantic" if "romantic" in lower or "रोमांटिक" in lower else "energetic" if "energetic" in lower or "एनर्जी" in lower else "normal"
                response = f"तुम्हारा मूड {mood} लग रहा है... सुनो ये गाना:\n"
                if mood == "sad":
                    response += "Arijit Singh - Channa Mereya (YouTube: https://www.youtube.com/results?search_query=Channa+Mereya+Arijit+Singh)"
                elif mood == "happy":
                    response += "A.R. Rahman - Jai Ho (YouTube: https://www.youtube.com/results?search_query=Jai+Ho+A.R.+Rahman)"
                elif mood == "romantic":
                    response += "Atif Aslam - Jeene Laga Hoon (YouTube: https://www.youtube.com/results?search_query=Jeene+Laga+Hoon+Atif+Aslam)"
                elif mood == "energetic":
                    response += "Badshah - Genda Phool (YouTube: https://www.youtube.com/results?search_query=Genda+Phool+Badshah)"
                else:
                    response += "Ed Sheeran - Perfect (YouTube: https://www.youtube.com/results?search_query=Perfect+Ed+Sheeran)"
                response += "\nऔर बताओ मूड कैसा है अब?"
            else:
                resp_obj = conversational_chain.invoke(
                    {"input": prompt_input},
                    config={"configurable": {"session_id": "vanya"}}
                )
                response = resp_obj.content

        st.markdown(response)

        tts = gTTS(text=response, lang='hi', tld='co.in')
        buf = BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        st.audio(buf, format='audio/mp3', autoplay=True)
