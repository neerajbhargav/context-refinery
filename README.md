# ContextRefinery

A desktop app that turns a goal plus the source files you drop in into one token-budgeted LLM prompt.

## Status

This is a parked research prototype. It is not under active development, and no accuracy or retrieval numbers are claimed because none have been measured. Known limitations: the app uses only files you drop in, because folder indexing exists in the API but the UI never calls it. Every request adds chunks to one shared, persistent collection, so an edited file can return its old content and files from earlier requests can leak into later prompts. Two dropped files with the same name raise an error and leave the context empty. The line ranges given to the model are wrong, because the indexer computes them as if each token were one line. The refinement loop is a retry: it gives the writer the same inputs each time, with no eval feedback, and it returns the last attempt, not the best one. The local eval gate weights n-gram overlap with the retrieved context at 50% and budget fill at 25%, so a verbatim copy of the context can pass it, and an evaluator error counts as a pass. The streaming view drops most agent messages after the first step. The local API allows any origin (CORS `*` with credentials), so run it only on a machine you trust. Tests cover only the optional DeepEval adapter, and there is no test CI. Pre-built binaries exist for Windows x64 only, and each installer is about 273 MB because the sidecar bundles PyTorch.

## Install

### Windows (one command)

```powershell
irm https://raw.githubusercontent.com/neerajbhargav/context-refinery/master/install.ps1 | iex
```

### Mac / Linux (source installer)

```bash
curl -fsSL https://raw.githubusercontent.com/neerajbhargav/context-refinery/master/install.sh | bash
```

These scripts install from source after checking prerequisites, create a desktop shortcut (Windows) or app entry (Mac/Linux), and launch the setup wizard.

### Desktop App (pre-built)

The published `v0.1.0` release provides **Windows x64 only**: `.exe` and `.msi` installers in [Releases](https://github.com/neerajbhargav/context-refinery/releases) (checked October 21, 2026). No macOS or Linux binaries are published; use the source installer or manual setup on those platforms. The release workflow lists macOS and Linux runners, but the Tauri bundle targets are Windows only (NSIS and MSI), and the workflow's only run was cancelled.

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
- **Rust** >= 1.77 (only for `tauri build`, not needed for dev mode)
- **Ollama** (optional, for local models): [ollama.com](https://ollama.com)

## First Run

On first launch, a **setup wizard** walks you through:

1. **Choose your AI provider**: Ollama (local, recommended), Google Gemini, OpenAI, or Anthropic
2. **Configure**: pull an Ollama model or enter your API key
3. **Test connection**: verify everything works
4. **Launch**: start using ContextRefinery

You can change providers anytime in Settings.

## Features

- **Hybrid Retrieval**: ChromaDB vector search + BM25 lexical search + Reciprocal Rank Fusion
- **Cross-Encoder Reranking**: `ms-marco-MiniLM-L-6-v2` reorders the fused candidates
- **LangGraph Pipeline**: A state machine with intent analysis, retrieval, prompt writing and evaluation steps
- **Retry Loop**: Re-runs the prompt writer if the eval score is below 0.75 (up to 3 iterations). The writer gets the same inputs on each run. Local metrics (n-gram grounding, information density, budget utilization) always run for non-empty prompts. The optional evaluator uses the libraries' default OpenAI-backed configuration: set `OPENAI_API_KEY` and install `deepeval>=2.9` and/or `ragas>=0.2` (RAGAS also requires `datasets`). DeepEval is tried first; RAGAS is tried when DeepEval is unavailable, not after a DeepEval runtime failure. Missing dependencies or runtime failures leave local scoring in place. The activation gate accepts any configured cloud key, but this path does not configure Google or Anthropic evaluator models.
- **Token Budget Control**: Logarithmic slider from 512 to 32K tokens
- **Multi-Provider**: Google Gemini, OpenAI GPT-4o, Anthropic Claude, Ollama (local)
- **Local Model Manager**: Pull/delete Ollama models from the UI with streaming progress
- **Multi-Format Export**: Markdown, XML, JSON
- **Keyboard Shortcuts**: `Ctrl+Enter` (refine), `Ctrl+B` (toggle sidebar)

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
| `GOOGLE_API_KEY` | none | Required if using Google Gemini |
| `OPENAI_API_KEY` | none | Required if using OpenAI |
| `ANTHROPIC_API_KEY` | none | Required if using Anthropic |
| `EMBEDDING_PROVIDER` | `google` | `google` / `ollama` / `sentence-transformers` |
| `OLLAMA_MODEL` | `gemma3` | Default Ollama model |

## License

MIT. See [LICENSE](LICENSE).
