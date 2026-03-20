#!/usr/bin/env python3
"""
Content Research MCP - Interactive Setup Wizard
Configures API keys and registers the MCP server with Claude Desktop.
"""

import json
import os
import platform
import shutil
import sys
from pathlib import Path


def get_project_dir() -> Path:
    """Return the directory where this script lives."""
    return Path(__file__).resolve().parent


def get_claude_config_path() -> Path | None:
    """Auto-detect Claude Desktop config path based on OS."""
    system = platform.system()
    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "Claude" / "claude_desktop_config.json"
    elif system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    elif system == "Linux":
        return Path.home() / ".config" / "claude" / "claude_desktop_config.json"
    return None


def ensure_env_file(project_dir: Path) -> Path:
    """Check for .env file; copy from .env.example if missing."""
    env_path = project_dir / ".env"
    example_path = project_dir / ".env.example"

    if env_path.exists():
        print("[INFO] .env file already exists.")
    else:
        if example_path.exists():
            shutil.copy(example_path, env_path)
            print("[OK] Created .env from .env.example")
        else:
            env_path.touch()
            print("[OK] Created empty .env file")

    return env_path


def prompt_api_keys() -> dict:
    """Interactively ask user for API keys."""
    print()
    print("=" * 60)
    print("  Content Research MCP - Setup Wizard")
    print("=" * 60)
    print()

    # --- Naver ---
    print("[1/2] Naver Developer API")
    print("  Get your keys at: https://developers.naver.com")
    print("  (Create an application -> select 'Search' API)")
    print()
    naver_id = input("  Naver Client ID: ").strip()
    naver_secret = input("  Naver Client Secret: ").strip()
    print()

    # --- Unsplash ---
    print("[2/2] Unsplash API")
    print("  Get your key at: https://unsplash.com/developers")
    print("  (Create an application -> copy Access Key)")
    print()
    unsplash_key = input("  Unsplash Access Key: ").strip()
    print()

    return {
        "NAVER_CLIENT_ID": naver_id,
        "NAVER_CLIENT_SECRET": naver_secret,
        "UNSPLASH_ACCESS_KEY": unsplash_key,
    }


def write_env(env_path: Path, keys: dict) -> None:
    """Write API keys to the .env file."""
    lines = []
    lines.append("# Naver Developer API (https://developers.naver.com)")
    lines.append(f"NAVER_CLIENT_ID={keys['NAVER_CLIENT_ID']}")
    lines.append(f"NAVER_CLIENT_SECRET={keys['NAVER_CLIENT_SECRET']}")
    lines.append("")
    lines.append("# Unsplash API (https://unsplash.com/developers)")
    lines.append(f"UNSPLASH_ACCESS_KEY={keys['UNSPLASH_ACCESS_KEY']}")
    lines.append("")

    env_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] API keys saved to {env_path}")


def register_claude_desktop(project_dir: Path, env_path: Path) -> None:
    """Add content-research MCP entry to Claude Desktop config."""
    config_path = get_claude_config_path()

    if config_path is None:
        print("[!!] Could not detect Claude Desktop config path for this OS.")
        print("     You will need to manually add the MCP entry.")
        print_manual_config(project_dir, env_path)
        return

    print(f"[INFO] Claude Desktop config: {config_path}")

    # Load existing config or start fresh
    config = {}
    if config_path.exists():
        # Backup existing config
        backup_path = config_path.with_suffix(".json.bak")
        shutil.copy(config_path, backup_path)
        print(f"[OK] Backed up existing config to {backup_path}")

        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            print("[!!] Existing config could not be parsed. Starting with empty config.")
            config = {}
    else:
        # Ensure parent directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure mcpServers key exists
    if "mcpServers" not in config:
        config["mcpServers"] = {}

    server_py = str(project_dir / "server.py")
    env_str = str(env_path)

    config["mcpServers"]["content-research"] = {
        "command": sys.executable,
        "args": [server_py, "--env", env_str],
    }

    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] Registered 'content-research' MCP in Claude Desktop config.")


def print_manual_config(project_dir: Path, env_path: Path) -> None:
    """Print the config snippet for manual setup."""
    server_py = str(project_dir / "server.py")
    env_str = str(env_path)

    print()
    print("  Add this to your Claude Desktop config (mcpServers section):")
    print()
    snippet = {
        "content-research": {
            "command": sys.executable,
            "args": [server_py, "--env", env_str],
        }
    }
    print(f"  {json.dumps(snippet, indent=4, ensure_ascii=False)}")
    print()


def print_success() -> None:
    """Print final success message with usage examples."""
    print()
    print("=" * 60)
    print("  Setup Complete!")
    print("=" * 60)
    print()
    print("[OK] Content Research MCP is ready to use.")
    print()
    print("Usage examples (in Claude Desktop):")
    print()
    print('  - "Search Naver blogs about AI trends"')
    print('  - "Find free images of coffee shops on Unsplash"')
    print('  - "Translate this paragraph to English"')
    print('  - "What are the trending topics on Naver right now?"')
    print()
    print("Note: Restart Claude Desktop to load the new MCP server.")
    print()


def main() -> None:
    project_dir = get_project_dir()

    # Step 1: Ensure .env exists
    env_path = ensure_env_file(project_dir)

    # Step 2-3: Prompt for API keys
    keys = prompt_api_keys()

    # Step 4: Write .env
    write_env(env_path, keys)

    # Step 5-6: Register with Claude Desktop
    register_claude_desktop(project_dir, env_path)

    # Step 7: Success message
    print_success()


if __name__ == "__main__":
    main()
