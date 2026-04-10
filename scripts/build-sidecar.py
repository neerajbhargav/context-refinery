"""
Build the FastAPI sidecar binary using PyInstaller.

Usage:
    cd src-backend
    python ../scripts/build-sidecar.py

This creates a single-file executable that Tauri will bundle as an external binary.
The output is placed in src-tauri/binaries/ with the correct platform-specific name.
"""

import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
BACKEND_DIR = ROOT / "src-backend"
BINARIES_DIR = ROOT / "src-tauri" / "binaries"


def get_target_triple() -> str:
    """Get the Rust-style target triple for the current platform."""
    machine = platform.machine().lower()
    system = platform.system().lower()

    arch_map = {
        "x86_64": "x86_64",
        "amd64": "x86_64",
        "aarch64": "aarch64",
        "arm64": "aarch64",
    }
    arch = arch_map.get(machine, machine)

    if system == "windows":
        return f"{arch}-pc-windows-msvc"
    elif system == "darwin":
        return f"{arch}-apple-darwin"
    elif system == "linux":
        return f"{arch}-unknown-linux-gnu"
    else:
        raise RuntimeError(f"Unsupported platform: {system} {machine}")


def main():
    BINARIES_DIR.mkdir(parents=True, exist_ok=True)
    target_triple = get_target_triple()
    ext = ".exe" if platform.system() == "Windows" else ""
    output_name = f"context-refinery-api-{target_triple}{ext}"

    print(f"Building sidecar for: {target_triple}")
    print(f"Output: {BINARIES_DIR / output_name}")

    # Run PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", f"context-refinery-api-{target_triple}",
        "--distpath", str(BINARIES_DIR),
        "--workpath", str(BACKEND_DIR / "build"),
        "--specpath", str(BACKEND_DIR),
        "--clean",
        # Hidden imports for dynamic LLM provider loading
        "--hidden-import", "langchain_openai",
        "--hidden-import", "langchain_anthropic",
        "--hidden-import", "langchain_google_genai",
        "--hidden-import", "langchain_ollama",
        "--hidden-import", "chromadb",
        "--hidden-import", "sentence_transformers",
        "--hidden-import", "tiktoken",
        "--hidden-import", "tiktoken_ext",
        "--hidden-import", "tiktoken_ext.openai_public",
        # Collect data files needed at runtime
        "--collect-data", "chromadb",
        "--collect-data", "tiktoken_ext",
        "--collect-data", "sentence_transformers",
        str(BACKEND_DIR / "main.py"),
    ]

    print(f"\nRunning: {' '.join(cmd[:6])}...")
    result = subprocess.run(cmd, cwd=str(BACKEND_DIR))

    if result.returncode != 0:
        print("\nPyInstaller build failed!", file=sys.stderr)
        sys.exit(1)

    output_path = BINARIES_DIR / output_name
    if output_path.exists():
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"\nSidecar built successfully: {output_path}")
        print(f"Size: {size_mb:.1f} MB")
    else:
        print(f"\nExpected output not found: {output_path}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
