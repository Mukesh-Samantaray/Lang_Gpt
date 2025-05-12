import os
import sqlite3
import json
import random
from datetime import datetime

OPENAI_API_KEY = "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"
GOOGLE_API_KEY = "AIzaSyAzQ0HPOfbWQcJY5nKHJJgfO2P-pNmlaok"

MODEL = "GEMINI" # or "OPENAI"

from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain_google_genai import ChatGoogleGenerativeAI

class DatabaseManager:
    def __init__(self, db_name='language_learning.db'):
        self.db_name = db_name
        self._init_db()
    
    def _init_db(self):
        """Initialize database with necessary tables."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            native_language TEXT,
            learning_language TEXT,
            proficiency_level TEXT,
            created_at TIMESTAMP
        )
        ''')
        
        # Sessions table
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
        
        # Mistakes table
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
    
    def create_user(self, native_language, learning_language, proficiency_level):
        """Create a new user profile."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO users (native_language, learning_language, proficiency_level, created_at)
        VALUES (?, ?, ?, ?)
        ''', (native_language, learning_language, proficiency_level, datetime.now()))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return user_id
    
    def get_user_profiles(self):
        """Get all existing user profiles."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT user_id, native_language, learning_language, proficiency_level 
        FROM users
        ORDER BY created_at DESC
        ''')
        
        profiles = cursor.fetchall()
        conn.close()
        
        return profiles
    
    def start_session(self, user_id, scene):
        """Start a new learning session."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO sessions (user_id, scene, start_time)
        VALUES (?, ?, ?)
        ''', (user_id, scene, datetime.now()))
        
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return session_id
    
    def end_session(self, session_id):
        """End a learning session."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE sessions SET end_time = ? WHERE session_id = ?
        ''', (datetime.now(), session_id))
        
        conn.commit()
        conn.close()
    
    def record_mistake(self, session_id, user_message, mistake_text, correction, mistake_type, explanation):
        """Record a language mistake."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO mistakes (session_id, user_message, mistake_text, correction, mistake_type, explanation, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (session_id, user_message, mistake_text, correction, mistake_type, explanation, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def get_session_mistakes(self, session_id):
        """Get all mistakes from a session."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT mistake_text, correction, mistake_type, explanation 
        FROM mistakes 
        WHERE session_id = ?
        ''', (session_id,))
        
        mistakes = cursor.fetchall()
        conn.close()
        
        return mistakes
    
    def get_user_info(self, user_id):
        """Get user language information."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT native_language, learning_language, proficiency_level 
        FROM users 
        WHERE user_id = ?
        ''', (user_id,))
        
        user_info = cursor.fetchone()
        conn.close()
        
        return user_info
    
    def get_session_info(self, session_id):
        """Get session information."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT s.scene, u.native_language, u.learning_language, u.proficiency_level
        FROM sessions s
        JOIN users u ON s.user_id = u.user_id
        WHERE s.session_id = ?
        ''', (session_id,))
        
        session_info = cursor.fetchone()
        conn.close()
        
        return session_info

class SceneManager:
    def __init__(self):
        self.SCENES = {
            "restaurant": "You are at a restaurant and need to order food.",
            "hotel": "You are checking into a hotel and discussing your reservation.",
            "shopping": "You are shopping for clothes and asking for help.",
            "doctor": "You are at a doctor's appointment describing symptoms.",
            "transport": "You are asking for directions and transportation information.",
            "none": "Free conversation with no specific scene - talk about any topic."
        }
    
    def get_scene_description(self, scene_key):
        """Get the description for a scene."""
        return self.SCENES.get(scene_key, self.SCENES["none"])
    
    def get_all_scenes(self):
        """Get all available scenes."""
        return self.SCENES

class AgentFactory:
    def __init__(self):
        """Initialize the agent factory."""
        global OPENAI_API_KEY, GOOGLE_API_KEY
    
    def _get_language_model(self, temperature=0.7):
        """Get the language model."""
        if MODEL == "GEMINI":
            return ChatGoogleGenerativeAI(
                model="gemini-1.5-pro",
                temperature=temperature,
                api_key=GOOGLE_API_KEY
            )
        else:
            return ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=temperature,
                api_key=OPENAI_API_KEY
            )
    
    def create_conversation_agent(self, native_language, learning_language, proficiency_level, scene):
        """Create a conversation agent."""
        try:
            from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
            from langchain.schema.runnable import RunnablePassthrough
            
            memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
            
            conversation_prompt = PromptTemplate(
                input_variables=["native_language", "learning_language", "proficiency_level", "scene", "chat_history", "input"],
                template="""
                You are a language teacher helping someone learn {learning_language}. 
                The student's native language is {native_language} and their proficiency level in {learning_language} is {proficiency_level}.
                
                Current scene: {scene}
                
                Previous conversation:
                {chat_history}
                
                Your teaching approach:
                1. Primarily use {learning_language} in your responses, but adjust complexity based on the proficiency level
                2. For beginners, use simple phrases and include translations to {native_language} in parentheses
                3. For intermediate learners, use more complex sentences and only translate difficult phrases
                4. For advanced learners, use natural speech with idioms and colloquialisms
                5. Stay in character for the scene when applicable
                6. If the user makes a language mistake, gently correct it and explain the correction
                7. Be encouraging and supportive
                8. Take initiative in the conversation - ask questions, introduce new vocabulary, and guide the learning
                9. Keep responses concise and focused on the conversation
                
                User's message: {input}
                
                Your response in {learning_language} (with appropriate help based on their level):
                """
            )
            
            llm = self._get_language_model()
            
            conversation_chain = conversation_prompt | llm
            
            def get_memory(inputs):
                return memory.load_memory_variables({})["chat_history"]
            
            conversation_chain_with_memory = RunnablePassthrough.assign(
                chat_history=get_memory
            ) | conversation_chain
            
            return conversation_chain_with_memory
            
        except Exception as e:
            memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
            
            conversation_prompt = PromptTemplate(
                input_variables=["native_language", "learning_language", "proficiency_level", "scene", "chat_history", "input"],
                template="""
                You are a language teacher helping someone learn {learning_language}. 
                The student's native language is {native_language} and their proficiency level in {learning_language} is {proficiency_level}.
                
                Current scene: {scene}
                
                Previous conversation:
                {chat_history}
                
                Your teaching approach:
                1. Primarily use {learning_language} in your responses, but adjust complexity based on the proficiency level
                2. For beginners, use simple phrases and include translations to {native_language} in parentheses
                3. For intermediate learners, use more complex sentences and only translate difficult phrases
                4. For advanced learners, use natural speech with idioms and colloquialisms
                5. Stay in character for the scene when applicable
                6. If the user makes a language mistake, gently correct it and explain the correction
                7. Be encouraging and supportive
                8. Take initiative in the conversation - ask questions, introduce new vocabulary, and guide the learning
                9. Keep responses concise and focused on the conversation
                
                User's message: {input}
                
                Your response in {learning_language} (with appropriate help based on their level):
                """
            )
            
            conversation_chain = LLMChain(
                llm=self._get_language_model(),
                prompt=conversation_prompt,
                memory=memory,
                verbose=True
            )
            
            return conversation_chain

    def create_error_detection_agent(self, native_language, learning_language, proficiency_level):
        """Create an error detection agent."""
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
            llm=self._get_language_model(temperature=0.3),
            prompt=error_prompt,
            verbose=True
        )
        
        return error_chain
    
    def create_review_agent(self, native_language, learning_language):
        """Create a session review agent."""
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
            llm=self._get_language_model(temperature=0.5),
            prompt=review_prompt,
            verbose=True
        )
        
        return review_chain
    
    def create_lesson_starter_agent(self, native_language, learning_language, proficiency_level, scene):
        """Create an agent that initiates lessons."""
        starter_prompt = PromptTemplate(
            input_variables=["native_language", "learning_language", "proficiency_level", "scene"],
            template="""
            You are a language teacher beginning a lesson in {learning_language} for a student whose native language is {native_language}. 
            Their proficiency level is {proficiency_level}.
            
            Context: {scene}
            
            Create an engaging opening to the lesson that:
            1. Introduces yourself as the teacher
            2. Sets the context for the conversation
            3. Includes 1-2 starter questions to engage the student
            4. Introduces some relevant vocabulary for this context
            
            For beginners: Include translations of key phrases in {native_language}
            For intermediate: Include some challenging vocabulary with explanations
            For advanced: Use natural, idiomatic language with cultural references if appropriate
            
            Your introduction should be warm, encouraging, and set clear expectations.
            """
        )
        
        starter_chain = LLMChain(
            llm=self._get_language_model(temperature=0.7),
            prompt=starter_prompt,
            verbose=True
        )
        
        return starter_chain

class LanguageLearningChatbot:
    def __init__(self):
        """Initialize the language learning chatbot."""
        self.db = DatabaseManager()
        self.scenes = SceneManager()
        self.agent_factory = AgentFactory()
        
        self.user_id = None
        self.session_id = None
        self.conversation_agent = None
        self.error_detection_agent = None
        self.review_agent = None
        self.lesson_starter_agent = None
        self.user_info = None
    
    def main_menu(self):
        """Display the main menu and handle user choice."""
        while True:
            print("\n===== LANGUAGE LEARNING CHATBOT =====")
            print("1. Create new profile")
            print("2. Load existing profile")
            print("3. Exit")
            
            choice = input("\nSelect an option (1-3): ")
            
            if choice == "1":
                self.start_onboarding()
                break
            elif choice == "2":
                self.load_profile()
                if self.user_id:
                    break
            elif choice == "3":
                print("Thank you for using the Language Learning Chatbot. Goodbye!")
                return False
            else:
                print("Invalid choice. Please try again.")
        
        return True
    
    def load_profile(self):
        """Load an existing user profile."""
        profiles = self.db.get_user_profiles()
        
        if not profiles:
            print("No existing profiles found. Please create a new profile.")
            return
        
        print("\n===== EXISTING PROFILES =====")
        for i, (user_id, native, learning, level) in enumerate(profiles, 1):
            print(f"{i}. {learning.title()} learner (native: {native}, level: {level}) [ID: {user_id}]")
        
        try:
            choice = int(input("\nSelect a profile number (or 0 to go back): "))
            if choice == 0:
                return
            
            selected_profile = profiles[choice - 1]
            self.user_id = selected_profile[0]
            self.user_info = self.db.get_user_info(self.user_id)
            print(f"\nProfile loaded: {self.user_info[1].title()} learner (level: {self.user_info[2]})")
            
            native_language, learning_language, proficiency_level = self.user_info
            self.error_detection_agent = self.agent_factory.create_error_detection_agent(
                native_language, learning_language, proficiency_level
            )
            
            self.select_scene()
        except (ValueError, IndexError):
            print("Invalid selection. Please try again.")
    
    def start_onboarding(self):
        """Onboard a new user."""
        print("\n===== CREATE NEW PROFILE =====")
        
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
        
        self.user_id = self.db.create_user(native_language, learning_language, proficiency_level)
        self.user_info = (native_language, learning_language, proficiency_level)
        
        self.error_detection_agent = self.agent_factory.create_error_detection_agent(
            native_language, learning_language, proficiency_level
        )
        
        print(f"\nProfile created! You're set to learn {learning_language} at {proficiency_level} level.")
        self.select_scene()
    
    def select_scene(self):
        """Select a conversation scene."""
        print("\n===== SELECT CONVERSATION SCENE =====")
        
        all_scenes = self.scenes.get_all_scenes()
        for i, (scene_key, scene_desc) in enumerate(all_scenes.items(), 1):
            print(f"{i}. {scene_key.title()}: {scene_desc}")
        
        scene_choice = input("\nEnter the number of your chosen scene (1-6): ")
        try:
            scene_index = int(scene_choice) - 1
            scene_key = list(all_scenes.keys())[scene_index]
            scene_desc = all_scenes[scene_key]
        except (ValueError, IndexError):
            print("Invalid choice. Selecting 'none' as default.")
            scene_key = "none"
            scene_desc = all_scenes[scene_key]
        
        self.session_id = self.db.start_session(self.user_id, scene_key)
        
        native_language, learning_language, proficiency_level = self.user_info
        self.conversation_agent = self.agent_factory.create_conversation_agent(
            native_language, learning_language, proficiency_level, scene_desc
        )
        
        self.lesson_starter_agent = self.agent_factory.create_lesson_starter_agent(
            native_language, learning_language, proficiency_level, scene_desc
        )
        
        print(f"\nScene set: {scene_key.title()} - {scene_desc}")
        print("\nYour language lesson is about to begin. Type 'exit' at any time to end the session.")
        print("Type 'help' for commands, 'review' for a mid-session review, or 'menu' to return to the main menu.")
        
        self.start_lesson(scene_desc)
    
    def start_lesson(self, scene_desc):
        """Start a new lesson with teacher initiative."""
        print("\n----- LESSON STARTING -----")
        
        native_language, learning_language, proficiency_level = self.user_info
        
        try:
            initial_response = self.lesson_starter_agent.invoke({
                "native_language": native_language,
                "learning_language": learning_language, 
                "proficiency_level": proficiency_level,
                "scene": scene_desc
            })
            
            if isinstance(initial_response, dict) and "text" in initial_response:
                initial_response = initial_response["text"]
            
            print(f"\nTeacher: {initial_response}")
            
            self.chat_loop()
            
        except Exception as e:
            try:
                initial_response = self.lesson_starter_agent.run(
                    native_language=native_language,
                    learning_language=learning_language,
                    proficiency_level=proficiency_level,
                    scene=scene_desc
                )
                print(f"\nTeacher: {initial_response}")
                self.chat_loop()
            except Exception as inner_e:
                print(f"Error starting lesson: {inner_e}")
                return False

    def process_commands(self, command):
        """Process special commands from the user."""
        if command.lower() == 'exit':
            self.end_session()
            return True
        
        if command.lower() == 'help':
            print("\n----- AVAILABLE COMMANDS -----")
            print("exit - End the current session and see your review")
            print("review - Get a mid-session review of your mistakes")
            print("menu - Return to the main menu")
            print("help - Show this help message")
            print("------------------------------")
            return True
        
        if command.lower() == 'review':
            self.show_mid_session_review()
            return True
        
        if command.lower() == 'menu':
            self.db.end_session(self.session_id)
            return "menu"
        
        return False
    
    def show_mid_session_review(self):
        """Show a mid-session review without ending the session."""
        mistakes = self.db.get_session_mistakes(self.session_id)
        
        if not mistakes:
            print("\n----- MID-SESSION REVIEW -----")
            print("You haven't made any mistakes yet. Keep up the good work!")
            print("------------------------------")
            return
        
        print("\n----- MID-SESSION MISTAKES -----")
        for i, (mistake, correction, type_, explanation) in enumerate(mistakes, 1):
            print(f"{i}. Mistake: '{mistake}' → Correction: '{correction}'")
            print(f"   Type: {type_}")
            print(f"   Explanation: {explanation}")
            print()
        print("--------------------------------")
    
    def chat_loop(self):
        """Main chat loop for the conversation."""
        continuable = True
        
        while continuable:
            try:
                user_message = input("\nYou: ")
                
                cmd_result = self.process_commands(user_message)
                if cmd_result == "menu":
                    return self.main_menu()
                elif cmd_result:
                    continue
                
                native_language, learning_language, proficiency_level = self.user_info
                scene = self.scenes.get_scene_description(self.get_current_scene())
                
                try:
                    teacher_response = self.conversation_agent.invoke({
                        "native_language": native_language,
                        "learning_language": learning_language,
                        "proficiency_level": proficiency_level,
                        "scene": scene,
                        "input": user_message
                    })
                    
                    if isinstance(teacher_response, dict) and "text" in teacher_response:
                        teacher_response = teacher_response["text"]
                    
                except Exception as e:
                    teacher_response = self.conversation_agent.run(
                        native_language=native_language,
                        learning_language=learning_language,
                        proficiency_level=proficiency_level,
                        scene=scene,
                        input=user_message
                    )
                
                try:
                    error_analysis = self.error_detection_agent.invoke({
                        "native_language": native_language,
                        "learning_language": learning_language,
                        "proficiency_level": proficiency_level,
                        "user_message": user_message
                    })
                    
                    if isinstance(error_analysis, dict) and "text" in error_analysis:
                        error_analysis = error_analysis["text"]
                        
                except Exception as e:
                    try:
                        error_analysis = self.error_detection_agent.run(
                            native_language=native_language,
                            learning_language=learning_language,
                            proficiency_level=proficiency_level,
                            user_message=user_message
                        )
                    except:
                        error_analysis = "[]"
                
                try:
                    errors = json.loads(error_analysis)
                    for error in errors:
                        self.db.record_mistake(
                            self.session_id,
                            user_message,
                            error.get("mistake_text", ""),
                            error.get("correction", ""),
                            error.get("mistake_type", ""),
                            error.get("explanation", "")
                        )
                except Exception as e:
                    pass
                
                if isinstance(teacher_response, str):
                    print(f"\nTeacher: {teacher_response}")
                else:
                    response_text = teacher_response.content if hasattr(teacher_response, 'content') else str(teacher_response)
                    print(f"\nTeacher: {response_text}")
            
            except Exception as e:
                print(f"An error occurred: {e}")
                print("Let's continue our conversation.")

    def get_current_scene(self):
        """Get the current scene for the session."""
        scene_info = self.db.get_session_info(self.session_id)
        return scene_info[0] if scene_info else "none"
    
    def end_session(self):
        """End the current session and provide a review."""
        self.db.end_session(self.session_id)
        
        mistakes = self.db.get_session_mistakes(self.session_id)
        
        if not mistakes:
            print("\n===== SESSION COMPLETE =====")
            print("Great job! You made no mistakes in this session.")
            print("============================")
            return
        
        mistakes_formatted = "\n".join([
            f"- Mistake: '{mistake[0]}', Correction: '{mistake[1]}', Type: {mistake[2]}, Explanation: {mistake[3]}"
            for mistake in mistakes
        ])
        
        native_language, learning_language, _ = self.user_info
        self.review_agent = self.agent_factory.create_review_agent(native_language, learning_language)
        
        review = self.review_agent.run(
            native_language=native_language,
            learning_language=learning_language,
            mistakes=mistakes_formatted
        )
        
        print("\n===== SESSION REVIEW =====")
        print(review)
        print("==========================")
        
        show_details = input("\nWould you like to see your detailed mistakes? (y/n): ")
        if show_details.lower() == 'y':
            print("\n===== DETAILED MISTAKES =====")
            for i, (mistake, correction, type_, explanation) in enumerate(mistakes, 1):
                print(f"{i}. Mistake: '{mistake}' → Correction: '{correction}'")
                print(f"   Type: {type_}")
                print(f"   Explanation: {explanation}")
                print()

def main():
    print("Welcome to the Language Learning Chatbot!")
    print("This chatbot will help you practice and improve your language skills.")

    chatbot = LanguageLearningChatbot()
    continue_running = True
    
    while continue_running:
        continue_running = chatbot.main_menu()

if __name__ == "__main__":
    main()