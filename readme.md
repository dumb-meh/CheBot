# 🚩 CheBot - Revolutionary Motivational Chatbot

A chat bot for one of my comrade.

## Overview

CheBot is a motivational chatbot inspired by the revolutionary spirit of Che Guevara. It provides encouragement, inspiration, and guidance with the passionate determination of a revolutionary leader, while focusing on personal growth and positive change.

## Features

- 🔐 **Secure Authentication**: Only authorized users can access the chat
- 🎭 **Che Guevara Personality**: Motivational responses with revolutionary spirit
- 💬 **Real-time Chat**: Interactive web interface with conversation history
- 🌟 **Personal Welcome**: Personalized greeting with user ID
- 📱 **Responsive Design**: Works on desktop and mobile devices
- 🚀 **Docker Ready**: Easy deployment with Docker Compose

## Setup

### Prerequisites

- Docker and Docker Compose
- Groq API key ([Get one here](https://console.groq.com/keys))

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd chebot
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   ```

3. **Configure environment variables**
   Edit `.env` file:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   USER_ID=your_authorized_username
   ```

4. **Start the application**
   ```bash
   docker-compose up --build
   ```

5. **Access the application**
   Open your browser and go to `http://localhost:8031`

## Usage

1. **Authentication**: Enter your authorized user ID on the login page
2. **Chat**: Start conversing with CheBot about your struggles, dreams, or goals
3. **Motivation**: Receive revolutionary inspiration and guidance
4. **Logout**: Use the logout button to end your session

## API Endpoints

- `GET /` - Login page
- `POST /login` - Authentication endpoint
- `GET /chat` - Chat interface (requires authentication)
- `POST /api/chat` - Chat API endpoint (requires authentication)
- `POST /logout` - Logout endpoint
- `GET /health` - Health check endpoint

## Configuration

### Environment Variables

- `GROQ_API_KEY`: Your Groq API key for AI responses
- `USER_ID`: The authorized user ID that can access the chatbot

### Groq Model

The chatbot uses the `mixtral-8x7b-32768` model by default. You can modify this in the `get_che_response()` function in `main.py`.

## Security Features

- Session-based authentication
- HTTP-only cookies for session management
- Single authorized user access
- Automatic session cleanup on logout

## Docker Deployment

The application is containerized and can be deployed using Docker Compose:

```bash
# Build and start
docker-compose up --build

# Run in background
docker-compose up -d

# Stop services
docker-compose down
```

## Development

### Local Development

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables**
   ```bash
   export GROQ_API_KEY=your_api_key
   export USER_ID=your_username
   ```

3. **Run the application**
   ```bash
   python main.py
   ```

### File Structure

```
chebot/
├── main.py              # Main application file
├── requirements.txt     # Python dependencies
├── Dockerfile          # Docker configuration
├── docker-compose.yml  # Docker Compose configuration
├── .dockerignore       # Docker ignore rules
├── .gitignore         # Git ignore rules
├── .env               # Environment variables (create this)
└── README.md          # This file
```

## Customization

### Personality Modification

Edit the `CHE_SYSTEM_PROMPT` in `main.py` to modify the chatbot's personality and responses.

### UI Customization

The HTML template in the `get_chat_interface()` function contains all the styling and can be modified to change the appearance.

### Model Configuration

Change the model in the `get_che_response()` function:
```python
model="mixtral-8x7b-32768",  # Change this to other available models
```

## Troubleshooting

### Common Issues

1. **Authentication Failed**: Check that your `USER_ID` in `.env` matches your login input
2. **API Errors**: Verify your `GROQ_API_KEY` is valid and has sufficient credits
3. **Connection Issues**: Ensure Docker is running and ports are available

### Logs

View application logs:
```bash
docker-compose logs -f app
```

## Contributing

This is a personal project for a specific comrade. Modifications should align with the revolutionary spirit and motivational purpose.

## License

This project is for personal use. All rights reserved.

---

*"The revolution is not an apple that falls when it is ripe. You have to make it fall." - Che Guevara*