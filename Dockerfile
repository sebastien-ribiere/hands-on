FROM python:3.12-slim

ARG CLAUDE_CODE_CHANNEL=stable
ARG CLAUDE_CODE_KEY_FINGERPRINT=31DDDE24DDFAB679F42D7BD2BAA929FF1A7ECACE

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore \
    DISABLE_UPDATES=1

# The participant does not run setup scripts on the host. The image is built
# from this Dockerfile and contains the complete toolchain used by the lab.
# Claude Code is installed from Anthropic's signed apt repository; the signing
# key fingerprint is checked explicitly before the repository is trusted.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       bash ca-certificates curl git gnupg \
    && install -d -m 0755 /etc/apt/keyrings \
    && curl -fsSL https://downloads.claude.ai/keys/claude-code.asc \
       -o /etc/apt/keyrings/claude-code.asc \
    && test "$(gpg --show-keys --with-colons /etc/apt/keyrings/claude-code.asc \
         | awk -F: '$1 == "fpr" {print $10; exit}')" = "${CLAUDE_CODE_KEY_FINGERPRINT}" \
    && echo "deb [signed-by=/etc/apt/keyrings/claude-code.asc] https://downloads.claude.ai/claude-code/apt/${CLAUDE_CODE_CHANNEL} ${CLAUDE_CODE_CHANNEL} main" \
       > /etc/apt/sources.list.d/claude-code.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends claude-code \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash apprentice \
    && install -d -o apprentice -g apprentice /home/apprentice/.claude

COPY --chown=apprentice:apprentice . /workspace

# Golden Thread itself stays stdlib-only. pytest, bandit and PyYAML are the
# toolchain of this hands-on: tests, the real security analyser and the small
# local GitLab job reader respectively.
RUN python3 -m pip install --no-cache-dir \
      /workspace/golden-thread-cli \
      bandit==1.9.4 \
      pytest==8.3.4 \
      PyYAML==6.0.2

# Réglages du shell installés hors du volume workspace persistant.
COPY --chown=apprentice:apprentice demo/lab.bashrc /home/apprentice/.bashrc

USER apprentice

# The corporate source normally already exists on a forge. For the standalone
# lab image we publish its three tagged demo versions once, while building the
# image. No participant executes this script on their workstation.
RUN cd /workspace && ./demo/publish-source.sh

# The image must behave like a fresh clone: it has a clean project history but
# none of the disposable Golden Thread evidence is committed (.demo is ignored).
RUN git -C /workspace init -q -b main \
    && git -C /workspace config user.name "Aurelis Apprentice" \
    && git -C /workspace config user.email "apprentice@aurelis.invalid" \
    && git -C /workspace add -A \
    && git -C /workspace commit -q -m "Hands-on baseline"

ENV HOME=/home/apprentice \
    GOLDEN_THREAD_LAB=1

WORKDIR /workspace/demo-spellbook

CMD ["bash"]
