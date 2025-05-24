# PsyRA - Psychological Response Assistant

PsyRA is a web-based application that provides psychological support through an AI-powered conversational agent. The application uses advanced language models and retrieval-augmented generation (RAG) to deliver contextually relevant and empathetic responses based on clinical psychology knowledge.

## Features

- **User Authentication System**
  - Secure signup and login functionality
  - Password hashing using SHA-256
  - User profile management

- **Interactive Chat Interface**
  - Real-time conversation with AI assistant
  - Chat history management
  - Session-based conversations
  - Ability to rename and organize chat sessions

- **Advanced AI Capabilities**
  - Integration with Groq's LLaMA language model
  - Context-aware responses using RAG
  - Clinical psychology knowledge base integration
  - Automatic relevance assessment of retrieved information

- **User Settings**
  - Profile management
  - Password update functionality
  - Personalization options

## Technical Stack

- **Backend**
  - FastAPI (Python web framework)
  - MongoDB (Database)
  - Groq API (LLM provider)
  - FAISS (Vector store for RAG)
  - Jina Embeddings for semantic search

- **Frontend**
  - HTML/CSS
  - JavaScript
  - Jinja2 Templates

## Environment Requirements

The application requires several environment variables to be set:

```plaintext
GROQ_API_KEY=your_groq_api_key
DATABASE_URI=your_mongodb_uri
DATABASE_NAME=your_database_name
JINA_API_KEY=your_jina_api_key
```

## Project Structure

```
├── assets/           # Static assets
├── core/            # Core functionality
│   ├── agent.py     # AI agent implementation
│   └── database.py  # Database configuration
├── handlers/        # API route handlers
│   ├── app/         # Application routes
│   ├── auth/        # Authentication routes
│   └── home/        # Home page routes
├── modules/         # Additional modules
├── utils/           # Utility functions
│   └── code_files/  # Helper code files
└── views/           # HTML templates
```

## Running the Application

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Set up the environment variables in a `.env` file

3. Start the server:
```bash
<!-- - python server.py -->
fastapi dev server.py
```

The application will be available at `http://localhost:8000`

## Features in Detail

### Authentication System
- User registration with email and password
- Secure password storage using SHA-256 hashing
- Session management and user identification

### Chat System
- Real-time conversation with AI assistant
- Context-aware responses using clinical psychology knowledge
- Chat history persistence
- Session management and organization

### RAG Implementation
- Integration with clinical psychology resources
- Semantic search using Jina Embeddings
- Hybrid retrieval combining embedding and keyword-based search
- Automatic relevance assessment of retrieved information

### User Interface
- Clean and intuitive chat interface
- Responsive design
- Easy navigation between chat sessions
- User settings management
