# RoboFriend

RoboFriend is a Dockerized AI-powered penpal application. It uses an AI model to generate engaging email responses and a mailer service to send and receive emails. The application is composed of three main services:

1. **AI Service**: Uses an AI model to generate email responses and summarize discussions.
2. **Mailer Service**: Sends and receives emails, managing the communication with your penpal.
3. **MongoDB service**: Stores the email exchanges and current summary between RoboFriend and the user.

## Project Structure

Here's an overview of the project structure:

```
docker
├── df
│   ├── Dockerfile.ai              # Dockerfile for the AI service
│   ├── Dockerfile.mailer          # Dockerfile for the mailer service
│   ├── ai_data
│   │   ├── ai_penpal.py           # AI penpal logic
│   │   ├── discussion_summary.py  # Discussion summarization logic
│   │   ├── maildb.py              # Database interaction module for AI service
│   │   ├── openai.key             # API key for OpenAI GPT-4 model
│   │   └── requirements.txt       # Python dependencies for the AI service
│   └── mailer_data
│       ├── maildb.py              # Database interaction module for mailer service
│       ├── penpal_mailer.py       # Email sending and receiving logic
│       ├── requirements.txt       # Python dependencies for the mailer service
│       └── token.json             # OAuth2 token for Google API
├── docker-compose.yaml            # Docker Compose configuration file
└── init-mongo.sh                  # Initialization script for MongoDB
```

## Requirements

- Docker
- Docker Compose

## Setup

1. Clone this repository:

   ```
   git clone https://github.com/tznurmin/robofriend.git
   cd robofriend/docker
   ```

2. Add your OpenAI API key to `df/ai_data/openai.key`.

3. Add your Google API OAuth2 token to `df/mailer_data/token.json`. Follow [these instructions](https://developers.google.com/identity/protocols/oauth2) to obtain an OAuth2 token.

4. Edit the `docker-compose.yaml` file to configure the project details.

5. Build and run the application using Docker Compose:

   ```
   docker-compose up -d
   ```

6. Your RoboFriend is now up and running! The AI service will start generating email responses and the mailer service will send and receive emails.

## Usage

Once the application is running, simply send an email to the configured email address. In the email address's local part (the part before the '@' symbol), include a plus sign (+) followed by a user ID to uniquely identify the user. This helps the AI service to differentiate between different users and maintain separate conversation histories for each user. The AI service will generate a response based on the summary stored in the MongoDB service, and the mailer service will send the email to the recipient.

For example, if your configured email address is robofriend@example.com and the user ID is john123, the email should be sent to robofriend+john123@example.com.

## Stopping the Application

To stop the running containers and remove the associated resources, execute the following command in the project directory:

```
docker-compose down
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
