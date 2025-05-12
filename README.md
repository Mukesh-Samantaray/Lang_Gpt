# Language Learning Chatbot Documentation

## Overview

This project is a language learning chatbot that helps users practice a new language through interactive conversations. It utilizes OpenAI's ChatGPT and Google's Gemini models for AI-generated responses and error detection.

## Features

- **User Profiles**: Stores user information including native and learning languages.
- **Conversation Scenes**: Users can choose different real-life scenarios to practice conversations.
- **Error Detection**: AI detects and corrects language mistakes.
- **Session Tracking**: Logs user conversations for review and analysis.
- **AI Review**: Provides feedback on mistakes and suggestions for improvement.

## Technologies Used

- **Python**
- **SQLite** (for storing user and session data)
- **LangChain** (for managing AI interactions)
- **OpenAI API** (for GPT-based AI responses)
- **Google Generative AI API** (for Gemini-based AI responses)
- **dotenv** (for managing API keys securely)

---

## Installation

### Prerequisites

- Python 3.8+
- Required dependencies:
  ```bash
  pip install langchain langchain-openai langchain-google-genai sqlite3 python-dotenv
  ```

### Environment Variables

```ini
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=your_google_api_key
```

---

## Database Schema

The chatbot uses an SQLite database (`language_learning.db`) with three tables:

### Users Table

Stores user information.

```sql
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    native_language TEXT,
    learning_language TEXT,
    proficiency_level TEXT,
    created_at TIMESTAMP
);
```

### Sessions Table

Stores conversation session details.

```sql
CREATE TABLE IF NOT EXISTS sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    scene TEXT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);
```

### Mistakes Table

Stores language mistakes detected by AI.

```sql
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
);
```

---

## Usage

### Initializing the Chatbot

```python
chatbot = LanguageLearningChatbot()
chatbot.start_onboarding()
```

### User Onboarding

The chatbot asks for:

- Native language
- Learning language
- Proficiency level (Beginner, Intermediate, Advanced)

### Selecting a Conversation Scene

Users choose from:

- **Restaurant**: Ordering food.
- **Hotel**: Checking in.
- **Shopping**: Buying clothes.
- **Doctor**: Describing symptoms.
- **Transport**: Asking for directions.
- **None**: Free conversation.

### Starting a Conversation

Users chat with the AI, which responds based on the selected scene and proficiency level.

### Error Detection & Feedback

The chatbot:

1. Detects mistakes using AI.
2. Stores mistakes in the database.
3. Provides corrections and explanations.
4. Summarizes key improvement areas at the end of a session.

### Ending a Session

When a user types `exit`, the chatbot:

- Saves conversation data.
- Generates a session review.
- Provides improvement suggestions.

---

## AI Components

### Language Model Selection

```python
MODEL = "GEMINI"  # or "OPENAI"
```

Depending on the model, it uses:

- **Gemini** (`gemini-1.5-pro`)
- **ChatGPT** (`gpt-3.5-turbo`)

### AI Chains

#### Conversation Agent

Generates responses in the target language.

```python
conversation_chain = LLMChain(llm=get_language_model(), prompt=conversation_prompt, memory=memory, verbose=True)
```

#### Error Detection Agent

Identifies grammar, vocabulary, and spelling mistakes.

```python
error_chain = LLMChain(llm=get_language_model(), prompt=error_prompt, verbose=True)
```

#### Review Agent

Analyzes mistakes and provides feedback.

```python
review_chain = LLMChain(llm=get_language_model(), prompt=review_prompt, verbose=True)
```

---

## Future Enhancements

- **Speech Recognition**: Allowing voice-based conversations.
- **More Scenes**: Expanding conversation topics.
- **Personalized Learning Plans**: Adapting based on past mistakes.
- **Mobile App Integration**: Making it available on Android & iOS.

---

## Conclusion

This chatbot provides an interactive and AI-powered language learning experience. With real-time feedback, error detection, and scene-based conversations, it helps users improve their language skills efficiently.
