#!/usr/bin/env bash
# Source this file in every terminal used for the hands-on.
# It makes the repository's Golden Thread CLI and disposable demo toolchain
# available without relying on shell state from another terminal.

_gt_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="${_gt_root}/golden-thread-cli/bin:${_gt_root}/.demo/venv/bin:${PATH}"
unset _gt_root
