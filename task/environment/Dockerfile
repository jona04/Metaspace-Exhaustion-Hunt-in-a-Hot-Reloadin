FROM ubuntu:24.04

SHELL ["/bin/bash", "-lc"]

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends curl ca-certificates ripgrep tmux asciinema git python3 python3-pip openjdk-17-jdk-headless \
    && curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.2/install.sh | bash \
    && . "$HOME/.nvm/nvm.sh" && nvm install 22 \
    && npm install -g @openai/codex@latest \
    && ln -sf "$(which node)" /usr/local/bin/node \
    && ln -sf "$(which codex)" /usr/local/bin/codex \
    && rm -rf /var/lib/apt/lists/*

COPY textd /workspace/textd

RUN chmod +x /workspace/textd/bin/*

WORKDIR /workspace/textd
