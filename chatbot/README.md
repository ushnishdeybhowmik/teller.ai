# Teller.ai - Banking Assistant Chatbot

A secure and intelligent banking assistant that handles user complaints and queries through both text and voice interactions.

## Features

- 🤖 Multi-modal interaction (Text & Voice)
- 🔒 Secure user authentication
- 📊 Analytics dashboard
- 🗣️ Voice input/output support
- 📍 User location tracking
- ⭐ User feedback system
- 🔄 Multiple LLM support (Mistral, TinyLlama, ChatGPT)

## Prerequisites

- Python 3.11+
- pipenv
- GPU support (optional, for faster inference)

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pipenv install
```

3. For GPU support (optional):
```bash
install_gpu.bat
```

4. Set up environment variables:
Create a `.env` file with:
```
OPENAI_API_KEY=your_key_here
```

## Usage

1. Start the application:
```bash
pipenv run streamlit run main.py
```

2. Access the application at `http://localhost:8501`

## Project Structure

- `/core` - Core functionality modules
  - `/agent` - LLM integration
  - `/db` - Database management
  - `/processing` - Security and data processing
  - `/stt` - Speech-to-text processing
- `/models` - LLM model files
- `/assets` - Static assets
- `/temp` - Temporary files

## Security

- Password hashing
- Session management
- Input sanitization
- Rate limiting

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License
