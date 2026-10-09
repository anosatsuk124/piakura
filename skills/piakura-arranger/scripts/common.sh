#!/usr/bin/env bash
set -euo pipefail
# cd -P resolves a skill directory reached through an installer's symlink.
piakura_skill_dir=$(cd -P "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)

# Tools come from, in order: PIAKURA_BIN, PIAKURA_ROOT/bin, the bin/ of the
# development checkout that contains this skill, or the release that the
# installed skill's VERSION names (see the piakura skill's install.sh).
piakura_bin_dir() {
  local root version data
  if [[ -n ${PIAKURA_BIN:-} ]]; then
    printf '%s\n' "$PIAKURA_BIN"
    return
  fi
  if [[ -n ${PIAKURA_ROOT:-} ]]; then
    printf '%s/bin\n' "$PIAKURA_ROOT"
    return
  fi
  root=$(cd -P "$piakura_skill_dir/../.." && pwd -P)
  if [[ -f "$root/go.mod" ]] && grep -qx 'module sakura-midi-arranger' "$root/go.mod"; then
    printf '%s/bin\n' "$root"
    return
  fi
  if [[ -f "$piakura_skill_dir/VERSION" ]]; then
    version=$(<"$piakura_skill_dir/VERSION")
    # As in XDG (and piakura's Go code), a relative XDG_DATA_HOME is ignored.
    case ${XDG_DATA_HOME:-} in
    /*) data=$XDG_DATA_HOME ;;
    *) data=$HOME/.local/share ;;
    esac
    printf '%s/piakura/releases/%s/bin\n' "$data" "$version"
    return
  fi
  printf 'Cannot locate the piakura tools; run the piakura skill to install them\n' >&2
  return 2
}

# Portable stand-ins for GNU-only tools (macOS ships bash 3.2 and BSD tools).
# readlink -m: an absolute path with symlinks resolved; missing parts allowed.
piakura_abspath() {
  python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$1"
}

piakura_sha256() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$@"
  else
    shasum -a 256 "$@"
  fi
}

# Verify a SHA256SUMS file quietly; the exit status reports the result.
piakura_sha256_check() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum --check --status "$@"
  else
    shasum -a 256 --check --status "$@"
  fi
}

# mv -T: rename to a path that must not exist, so a directory is never moved
# into an existing one.
piakura_rename() {
  if [[ -e $2 || -L $2 ]]; then
    printf 'Refusing to replace existing %s\n' "$2" >&2
    return 2
  fi
  mv -- "$1" "$2"
}

arranger_tool() {
  local tool=$1 dir
  shift
  dir=$(piakura_bin_dir) || return 2
  if [[ ! -x "$dir/$tool" ]]; then
    printf 'Missing %s in %s; run the piakura skill to install the tools (a development checkout builds them into bin/)\n' "$tool" "$dir" >&2
    return 2
  fi
  "$dir/$tool" "$@"
}
