# ContextRefinery

> **AI-powered context orchestration engine** — transforms codebases into LLM-optimized prompts.

## Install

### Windows (one command)

```powershell
irm https://raw.githubusercontent.com/neerajbhargav/context-refinery/master/install.ps1 | iex
```

### Mac / Linux (one command)

```bash
curl -fsSL https://raw.githubusercontent.com/neerajbhargav/context-refinery/master/install.sh | bash
```

This installs everything, creates a desktop shortcut (Windows) or app entry (Mac/Linux), and launches the setup wizard.

### Desktop App (pre-built)

Download the latest `.exe` / `.dmg` / `.AppImage` from [Releases](https://github.com/neerajbhargav/context-refinery/releases).

### Manual

```bash
git clone https://github.com/neerajbhargav/context-refinery.git
cd context-refinery

# Backend
cd src-backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python main.py              # Starts on :8741

# Frontend (new terminal)
cd ..
pnpm install
pnpm dev                    # Opens on :1420
```

### Requirements

- **Python** >= 3.11
- **Node.js** >= 18 (with pnpm)
- **Rust** >= 1.77 (only for `tauri build` — not needed for dev mode)
- **Ollama** (optional, for local models) — [ollama.com](https://ollama.com)

## First Run

On first launch, a **setup wizard** walks you through:

1. **Choose your AI provider** — Ollama (local, recommended), Google Gemini, OpenAI, or Anthropic
2. **Configure** — pull an Ollama model or enter your API key
3. **Test connection** — verify everything works
4. **Launch** — start using ContextRefinery

You can change providers anytime in Settings.

## Features

- **Hybrid Retrieval**: ChromaDB vector search + BM25 lexical search + Reciprocal Rank Fusion
- **Cross-Encoder Reranking**: `ms-marco-MiniLM-L-6-v2` for high-precision context selection
- **LangGraph Pipeline**: Multi-agent orchestration (intent analysis, retrieval, refinement, evaluation)
- **Iterative Refinement**: Automatically re-refines if eval score < threshold (up to 3 iterations)
- **Token Budget Control**: Logarithmic slider from 512 to 32K tokens
- **Multi-Provider**: Google Gemini, OpenAI GPT-4o, Anthropic Claude, Ollama (local)
- **Local Model Manager**: Pull/delete Ollama models from the UI with streaming progress
- **Multi-Format Export**: Markdown, XML, JSON
- **Keyboard Shortcuts**: `Ctrl+Enter` (refine), `Ctrl+B` (toggle sidebar), `Ctrl+S` (settings)

## Architecture

```
Vue 3 + Tailwind ──► FastAPI Sidecar ──► LangGraph Pipeline
  (Tauri shell)         :8741              Intent → Retrieve → Refine → Eval
                          │
                    ┌─────┼─────┐
                 ChromaDB  BM25  Cross-Encoder
                 (dense)  (sparse) (reranker)
```

## Environment Variables

In `src-backend/.env` (auto-configured by setup wizard):

| Variable | Default | Description |
|----------|---------|-------------|
| `DEFAULT_LLM_PROVIDER` | `google` | `ollama` / `google` / `openai` / `anthropic` |
| `GOOGLE_API_KEY` | — | Required if using Google Gemini |
| `OPENAI_API_KEY` | — | Required if using OpenAI |
| `ANTHROPIC_API_KEY` | — | Required if using Anthropic |
| `EMBEDDING_PROVIDER` | `google` | `google` / `ollama` / `sentence-transformers` |
| `OLLAMA_MODEL` | `gemma3` | Default Ollama model |

## License

MIT
