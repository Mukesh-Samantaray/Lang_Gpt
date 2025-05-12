import os
import sqlite3
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain, SequentialChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain_google_genai import ChatGoogleGenerativeAI

from dotenv import load_dotenv

# I have setup two API keys, one for OpenAI and one for Google Generative AI because when i was doing the project the chatgpt one was not working
os.environ["OPENAI_API_KEY"] = "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"
os.environ["GOOGLE_API_KEY"] = "AIzaSyAzQ0HPOfbWQcJY5nKHJJgfO2P-pNmlaok"

MODEL = "GEMINI" # or "OPENAI"

load_dotenv()

def init_db():
    conn = sqlite3.connect('language_learning.db')
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        native_language TEXT,
        learning_language TEXT,
        proficiency_level TEXT,
        created_at TIMESTAMP
    )
    ''')

    # Create sessions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sessions (
        session_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        scene TEXT,
        start_time TIMESTAMP,
        end_time TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    ''')

    # Create mistakes table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS mistakes (
        mistake_id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        user_message TEXT,
        mistake_text TEXT,
        correction TEXT,
        mistake_type TEXT,
        explanation TEXT,
        created_at TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES sessions (session_id)
    )
    ''')

    conn.commit()
    conn.close()

def create_user(native_language, learning_language, proficiency_level):
    conn = sqlite3.connect('language_learning.db')
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO users (native_language, learning_language, proficiency_level, created_at)
    VALUES (?, ?, ?, ?)
    ''', (native_language, learning_language, proficiency_level, datetime.now()))

    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return user_id

def start_session(user_id, scene):
    conn = sqlite3.connect('language_learning.db')
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO sessions (user_id, scene, start_time)
    VALUES (?, ?, ?)
    ''', (user_id, scene, datetime.now()))

    session_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return session_id

def end_session(session_id):
    conn = sqlite3.connect('language_learning.db')
    cursor = conn.cursor()

    cursor.execute('''
    UPDATE sessions SET end_time = ? WHERE session_id = ?
    ''', (datetime.now(), session_id))

    conn.commit()
    conn.close()

def record_mistake(session_id, user_message, mistake_text, correction, mistake_type, explanation):
    conn = sqlite3.connect('language_learning.db')
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO mistakes (session_id, user_message, mistake_text, correction, mistake_type, explanation, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (session_id, user_message, mistake_text, correction, mistake_type, explanation, datetime.now()))

    conn.commit()
    conn.close()

def get_session_mistakes(session_id):
    conn = sqlite3.connect('language_learning.db')
    cursor = conn.cursor()

    cursor.execute('''
    SELECT mistake_text, correction, mistake_type, explanation
    FROM mistakes
    WHERE session_id = ?
    ''', (session_id,))

    mistakes = cursor.fetchall()
    conn.close()

    return mistakes

def get_user_info(user_id):
    conn = sqlite3.connect('language_learning.db')
    cursor = conn.cursor()

    cursor.execute('''
    SELECT native_language, learning_language, proficiency_level
    FROM users
    WHERE user_id = ?
    ''', (user_id,))

    user_info = cursor.fetchone()
    conn.close()

    return user_info

SCENES = {
    "restaurant": "You are at a restaurant and need to order food.",
    "hotel": "You are checking into a hotel and discussing your reservation.",
    "shopping": "You are shopping for clothes and asking for help.",
    "doctor": "You are at a doctor's appointment describing symptoms.",
    "transport": "You are asking for directions and transportation information.",
    "none": "Free conversation with no specific scene - talk about any topic."
}

def get_language_model():
    if MODEL == "GEMINI":
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            temperature=0.5,
            api_key=os.getenv("GOOGLE_API_KEY")
        )
    else:
        return ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.7,
            api_key=os.getenv("OPENAI_API_KEY")
        )

def init_conversation_agent(native_language, learning_language, proficiency_level, scene):
    memory = ConversationBufferMemory(memory_key="chat_history",input_key="input", return_messages=True)

    conversation_prompt = PromptTemplate(
        input_variables=["native_language", "learning_language", "proficiency_level", "scene", "chat_history", "input"],
        template="""
        You are a language learning assistant helping someone learn {learning_language}.
        The student's native language is {native_language} and their proficiency level in {learning_language} is {proficiency_level}.

        Current scene: {scene}

        Previous conversation:
        {chat_history}

        Rules:
        1. Primarily use {learning_language} in your responses, but adjust complexity based on the proficiency level
        2. For beginners, use simple phrases and include translations to {native_language} in parentheses
        3. For intermediate learners, use more complex sentences and only translate difficult phrases
        4. For advanced learners, use natural speech with idioms and colloquialisms
        5. Stay in character for the scene
        6. If the user makes a language mistake, gently correct it and explain the correction
        7. Keep responses concise and focused on the conversation

        User's message: {input}

        Your response in {learning_language} (with appropriate help based on their level):
        """
    )

    conversation_chain = LLMChain(
        llm=get_language_model(),
        prompt=conversation_prompt,
        memory=memory,
        verbose=True
    )

    return conversation_chain

def init_error_detection_agent(native_language, learning_language, proficiency_level):
    error_prompt = PromptTemplate(
        input_variables=["native_language", "learning_language", "proficiency_level", "user_message"],
        template="""
        Analyze the following message from a {learning_language} language learner whose native language is {native_language} and proficiency level is {proficiency_level}.

        User's message: {user_message}

        Identify any language mistakes in the JSON format below. If there are no mistakes, return an empty array.

        ```json
        [
            {{
                "mistake_text": "the incorrect text",
                "correction": "the corrected text",
                "mistake_type": "grammar|vocabulary|spelling|pronunciation|structure",
                "explanation": "Brief explanation of the error and why the correction is better"
            }}
        ]
        ```

        Only return the JSON, nothing else.
        """
    )

    error_chain = LLMChain(
        llm=get_language_model(),
        prompt=error_prompt,
        verbose=True
    )

    return error_chain

def init_review_agent(native_language, learning_language):
    review_prompt = PromptTemplate(
        input_variables=["native_language", "learning_language", "mistakes"],
        template="""
        Based on the following mistakes made during a {learning_language} learning session by a {native_language} speaker, provide:

        1. A summary of the key areas needing improvement
        2. Patterns in the mistakes
        3. 3-5 specific practice recommendations
        4. Encouragement on what was done well

        Mistakes:
        {mistakes}

        Provide your analysis in both {learning_language} and {native_language}.
        """
    )

    review_chain = LLMChain(
        llm=get_language_model(),
        prompt=review_prompt,
        verbose=True
    )

    return review_chain

class LanguageLearningChatbot:
    def __init__(self):
        init_db()
        self.user_id = None
        self.session_id = None
        self.conversation_agent = None
        self.error_detection_agent = None
        self.review_agent = None
        self.user_info = None

    def start_onboarding(self):
        print("Welcome to the Language Learning Chatbot!")
        print("Let's set up your profile.")

        native_language = input("What is your native language? ")
        learning_language = input("What language would you like to learn? ")

        print("\nWhat is your current level in {}?".format(learning_language))
        print("1. Beginner")
        print("2. Intermediate")
        print("3. Advanced")
        level_choice = input("Enter the number (1-3): ")

        level_map = {
            "1": "beginner",
            "2": "intermediate",
            "3": "advanced"
        }
        proficiency_level = level_map.get(level_choice, "beginner")

        self.user_id = create_user(native_language, learning_language, proficiency_level)
        self.user_info = (native_language, learning_language, proficiency_level)

        self.error_detection_agent = init_error_detection_agent(
            native_language, learning_language, proficiency_level
        )

        print("\nGreat! Profile created. Now let's choose a conversation scene.")
        self.select_scene()

    def select_scene(self):
        print("\nAvailable conversation scenes:")
        for i, (scene_key, scene_desc) in enumerate(SCENES.items(), 1):
            print(f"{i}. {scene_key.title()}: {scene_desc}")

        scene_choice = input("\nEnter the number of your chosen scene (1-5): ")
        try:
            scene_index = int(scene_choice) - 1
            scene_key = list(SCENES.keys())[scene_index]
            scene_desc = SCENES[scene_key]
        except (ValueError, IndexError):
            print("Invalid choice. Selecting 'restaurant' as default.")
            scene_key = "restaurant"
            scene_desc = SCENES[scene_key]

        self.session_id = start_session(self.user_id, scene_key)

        native_language, learning_language, proficiency_level = self.user_info
        self.conversation_agent = init_conversation_agent(
            native_language, learning_language, proficiency_level, scene_desc
        )

        print(f"\nScene set: {scene_key.title()} - {scene_desc}")
        print("Let's start the conversation. Type 'exit' at any time to end the session.")

        initial_response = self.conversation_agent.run(
            native_language=native_language,
            learning_language=learning_language,
            proficiency_level=proficiency_level,
            scene=scene_desc,
            input="Hello! Start the conversation in this scene."
        )

        print(f"\nBot: {initial_response}")
        self.chat_loop()

    def chat_loop(self):
        while True:
            user_message = input("\nYou: ")

            if user_message.lower() == 'exit':
                self.end_session()
                break

            native_language, learning_language, proficiency_level = self.user_info
            error_analysis = self.error_detection_agent.run(
                native_language=native_language,
                learning_language=learning_language,
                proficiency_level=proficiency_level,
                user_message=user_message
            )

            try:
                import json
                errors = json.loads(error_analysis)
                for error in errors:
                    record_mistake(
                        self.session_id,
                        user_message,
                        error["mistake_text"],
                        error["correction"],
                        error["mistake_type"],
                        error["explanation"]
                    )
            except Exception as e:
                print(f"Error processing mistakes: {e}")

            bot_response = self.conversation_agent.run(
                native_language=native_language,
                learning_language=learning_language,
                proficiency_level=proficiency_level,
                scene=SCENES[self.get_current_scene()],
                input=user_message
            )

            print(f"\nBot: {bot_response}")

    def get_current_scene(self):
        conn = sqlite3.connect('language_learning.db')
        cursor = conn.cursor()

        cursor.execute('''
        SELECT scene FROM sessions WHERE session_id = ?
        ''', (self.session_id,))

        scene = cursor.fetchone()[0]
        conn.close()

        return scene

    def end_session(self):
        end_session(self.session_id)

        mistakes = get_session_mistakes(self.session_id)

        if not mistakes:
            print("\nSession complete! You made no mistakes in this session. Great job!")
            return

        mistakes_formatted = "\n".join([
            f"- Mistake: '{mistake[0]}', Correction: '{mistake[1]}', Type: {mistake[2]}, Explanation: {mistake[3]}"
            for mistake in mistakes
        ])

        if not self.review_agent:
            native_language, learning_language, _ = self.user_info
            self.review_agent = init_review_agent(native_language, learning_language)

        native_language, learning_language, _ = self.user_info
        review = self.review_agent.run(
            native_language=native_language,
            learning_language=learning_language,
            mistakes=mistakes_formatted
        )

        print("\n----- SESSION REVIEW -----")
        print(review)
        print("-------------------------")

chatbot = LanguageLearningChatbot()
chatbot.start_onboarding()
