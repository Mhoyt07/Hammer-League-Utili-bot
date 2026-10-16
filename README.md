## Installation

### Prerequisites

- macOS with [Homebrew](https://brew.sh/)
- Git
- A Firebase project with Realtime Database enabled

### Install uv (Homebrew)

```zsh
brew install uv
```

Fallback, if you don't use Homebrew:

```zsh
curl -LsSf [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh
```

### Setup

```zsh
git clone https://github.com/Mhoyt07/Hammer-League-Utili-bot.git
cd Hammer-League-Utili-bot.git
uv sync
```

`uv sync` reads `.python-version`, creates `.venv`, and installs the exact versions pinned in `uv.lock`.

### Configuration

```zsh
cp .env.example .env
```

Open `.env` and fill in your Firebase values (for example `[FIREBASE_DATABASE_URL]` and `[FIREBASE_CREDENTIALS_PATH]`). Put your service-account key at the path you set. Never commit it.

## Usage

Launch the GUI:

```zsh
uv run python gui.py
```

Run the league logic from the terminal:

```zsh
uv run python league.py
```

`uv run` uses the project's `.venv` automatically, so you don't need to activate it.