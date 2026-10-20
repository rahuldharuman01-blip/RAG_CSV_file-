# CSV-Based RAG Chatbot

## About the Project

This project is a chatbot that answers questions using information stored in CSV files. It uses Retrieval-Augmented Generation (RAG) to find relevant information from the uploaded data and generate answers based on the retrieved content.

The application provides a simple web interface where users can ask questions about the information available in the CSV files. Instead of searching through rows manually, users can interact with the data using natural language.

The project is developed using Python and Flask, with HTML, CSS, and JavaScript for the frontend. Ollama can be used to run a language model locally for generating responses without requiring an external AI API.

## Technologies Used

- Python
- Flask
- Retrieval-Augmented Generation (RAG)
- CSV for storing data
- Ollama for local language model integration
- HTML
- CSS
- JavaScript

## Project Structure

```text
CSV-RAG-Chatbot/
├── app.py
├── templates/
│   └── index.html
├── static/
│   ├── style.css
│   └── script.js
├── data/
│   └── home_data.csv
├── requirements.txt
└── README.md
```

The folder structure and filenames may differ depending on your implementation.

## Features

- Answers questions using information from CSV files.
- Retrieves relevant information based on the user's query.
- Provides a chat-based interface.
- Uses a local language model through Ollama, if configured.
- Displays responses through a web application.
- Organizes information in an easy-to-use format.

## Installation

### 1. Clone the Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd CSV-RAG-Chatbot
```

Replace `YOUR_GITHUB_REPOSITORY_URL` with your GitHub repository URL.

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows using PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Install the Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Ollama

Install Ollama if it is not already installed. Download the language model required by your application.

For example, to use Llama 3.2:

```bash
ollama pull llama3.2
```

Make sure Ollama is running before starting the chatbot. If your project uses a different model, use that model's name instead.

### 5. Run the Application

```bash
python app.py
```

Open the local URL displayed in the terminal, usually:

```text
http://127.0.0.1:5000
```

## How It Works

1. The application reads information from a CSV file.
2. The user's question is processed by the application.
3. The system retrieves information relevant to the question.
4. The retrieved content is provided to the language model.
5. The model generates a response based on the available information.
6. The answer is displayed in the chatbot interface.

## Use Cases

This project can be used to search and understand information stored in CSV files. For example, a home-related dataset could contain information about rooms, furniture, appliances, maintenance, and other household topics.

## Future Improvements

- Support for multiple CSV files.
- Improved retrieval accuracy.
- Chat history support.
- Better handling of large datasets.
- More options for selecting local language models.

