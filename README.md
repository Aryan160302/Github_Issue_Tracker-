# Ollama GitHub Issue Assistant

Small project: given a public GitHub repo URL and issue number, the app:

1. Fetches the issue details (title, body, comments) via the GitHub API.
2. Sends the data to a **local Ollama model** (e.g. `llama3`).
3. Returns a structured JSON analysis:
   - `summary`
   - `type`
   - `priority_score`
   - `suggested_labels`
   - `potential_impact`
4. Displays the result in a minimal web UI with a "Copy JSON" button.

The idea is to rely entirely on your local Ollama instance, no external LLM API keys.

## 1. Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/) installed on your machine
- At least one chat model pulled in Ollama, e.g.:

```bash
ollama pull llama3
```

You should be able to run a quick test in your terminal:

```bash
ollama run llama3 "Say hello in one sentence."
```

If that works, you're ready.

## 2. Install Python dependencies

From the project root:

```bash
pip install -r requirements.txt
```

(If you prefer a virtualenv, you can create one, but it's not required.)

## 3. Environment variables

You can copy the example file and tweak it if you like:

```bash
cp .env.example .env
```

For this project the backend reads these environment variables:

- `OLLAMA_MODEL` – name of the model you've pulled in Ollama (default: `llama3`)
- `OLLAMA_BASE_URL` – base URL for Ollama (default: `http://127.0.0.1:11434`)
- `GITHUB_TOKEN` – optional GitHub personal access token

On Linux/macOS/WSL you can set them like this:

```bash
export OLLAMA_MODEL="llama3"
# optional:
# export OLLAMA_BASE_URL="http://127.0.0.1:11434"
# export GITHUB_TOKEN="ghp_your_github_token_here"
```

On Windows PowerShell:

```powershell
$env:OLLAMA_MODEL="llama3"
# optional:
# $env:OLLAMA_BASE_URL="http://127.0.0.1:11434"
# $env:GITHUB_TOKEN="ghp_your_github_token_here"
```

## 4. Run Ollama

Make sure the Ollama server is running. Usually starting any Ollama command will launch it,
but to be explicit you can do:

```bash
ollama serve
```

Leave this running in a background terminal.

## 5. Run the backend (FastAPI)

In a new terminal, from the project root:

```bash
uvicorn backend.main:app --reload
```

You should see something like:

```text
Uvicorn running on http://127.0.0.1:8000
```

Quick test:

```bash
curl http://127.0.0.1:8000/
# -> {"status":"ok"}
```

## 6. Run the frontend

From a second terminal:

```bash
cd frontend
python -m http.server 5500
```

Open the UI:

- http://127.0.0.1:5500/

## 7. Using the app

1. Enter a public GitHub repository URL (e.g. `https://github.com/facebook/react`).
2. Enter an existing issue number.
3. Click **"Analyze Issue"**.

The backend will:

- fetch the issue + comments from GitHub,
- send a prompt to your local Ollama model,
- parse JSON from the model output,
- and return a structured analysis.

The frontend shows both a human-friendly view and the raw JSON.

## 8. Notes

- If Ollama is not running or the model isn't pulled, you'll see a clear error message.
- Very long issue bodies/comments are truncated before hitting the model.
- The JSON parsing is defensive: it tries to slice out the JSON part if the model adds extra text.
