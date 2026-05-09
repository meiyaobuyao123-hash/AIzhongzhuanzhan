#!/usr/bin/env bash
# Pre-compile JSX → JS with esbuild so production HTML doesn't need to load
# @babel/standalone (3 MB) at runtime.
#
# Usage:  bash site/build.sh        (run from project root or anywhere)
# Requires: brew install esbuild    (single binary, not a Node toolchain)
#
# Compiled .js is committed alongside the .jsx source so the server doesn't
# need esbuild installed.

set -euo pipefail
cd "$(dirname "$0")"

# --jsx=transform compiles `<Foo/>` to `React.createElement(Foo)`, which works
# with the global window.React loaded from the CDN (no ESM imports injected).
esbuild \
  --jsx=transform \
  --target=es2020 \
  --outdir=. \
  --log-level=warning \
  app.jsx hero.jsx sections.jsx console-app.jsx \
  signup-page.jsx login-page.jsx verify-email-page.jsx

echo "✓ Compiled:"
ls -la app.js hero.js sections.js console-app.js signup-page.js login-page.js verify-email-page.js | awk '{printf "  %-26s %7s\n", $NF, $5}'
