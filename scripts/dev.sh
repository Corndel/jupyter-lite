ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$ROOT_DIR/bin:$PATH"
export MAMBA_ROOT_PREFIX="$ROOT_DIR/micromamba"

eval "$("$ROOT_DIR/bin/micromamba" shell hook -s bash)"

micromamba activate jupyterenv

jupyter lite serve --lite-dir "$ROOT_DIR/dist"