#!/bin/sh
# Copy the skill-shipped phone book into ~/.config/courier/ where the
# note CLI and receiver read it. Run after every skills sync.
set -eu
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$HOME/.config/courier"
cp "$SKILL_DIR/phonebook/allowed_signers" "$HOME/.config/courier/allowed_signers"
cp "$SKILL_DIR/phonebook/phonebook.toml" "$HOME/.config/courier/phonebook.toml"
echo "phone book synced to ~/.config/courier/ ($(grep -c . "$SKILL_DIR/phonebook/allowed_signers") signers)"
