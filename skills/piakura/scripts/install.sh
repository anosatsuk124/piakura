#!/usr/bin/env bash
# Install the piakura tools that match this skill's VERSION, verified against
# the release's SHA256SUMS, into $XDG_DATA_HOME/piakura/releases/<version>.
# Nothing outside that directory changes, except the one link --link-bin makes
# when the user asked for it; shell profiles are never edited.
#
# Usage: install.sh --terms-version ID [--version vX.Y.Z] [--link-bin]
#                                       install if needed; --link-bin also links
#                                       ${XDG_BIN_HOME:-~/.local/bin}/piakura
#        install.sh --check             exit 0 when installed
#        install.sh --unlink-bin        remove that link
# The last line printed is the tool directory. PIAKURA_RELEASE_URL replaces the
# download location (a mirror, or file:///dir for tests).
set -euo pipefail
here=$(cd -P "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)
repo=anosatsuk124/piakura
terms_version='' version='' check='' link='' unlink=''
while [[ $# -gt 0 ]]; do
  case $1 in
  --terms-version) terms_version=$2 && shift 2 ;;
  --version) version=$2 && shift 2 ;;
  --check) check=1 && shift ;;
  --link-bin) link=1 && shift ;;
  --unlink-bin) unlink=1 && shift ;;
  *)
    printf 'Unknown option %s\n' "$1" >&2
    exit 2
    ;;
  esac
done
die() {
  printf '%s\n' "$*" >&2
  exit 1
}
case ${XDG_DATA_HOME:-} in
/*) data=$XDG_DATA_HOME/piakura ;;
*) data=$HOME/.local/share/piakura ;;
esac
case ${XDG_BIN_HOME:-} in
/*) bindir=$XDG_BIN_HOME ;;
*) bindir=$HOME/.local/bin ;;
esac
link_path=$bindir/piakura

# The link points at current/, so that it follows updates. Only a link into
# piakura's data directory is piakura's: anything else at that path is the
# user's and stays.
ours() { [[ -L "$link_path" ]] && case $(readlink "$link_path") in "$data"/*) true ;; *) false ;; esac }
link_bin() {
  if [[ -e "$link_path" || -L "$link_path" ]] && ! ours; then
    printf 'Not linking: %s already exists and is not the link piakura made\n' "$link_path" >&2
    return 0
  fi
  mkdir -p "$bindir"
  ln -sfn "$data/current/bin/piakura" "$link_path"
  printf 'Linked %s\n' "$link_path" >&2
  case ":$PATH:" in
  *":$bindir:"*) ;;
  *) printf '%s is not on your PATH; add it in your shell profile to run piakura by name\n' "$bindir" >&2 ;;
  esac
}
if [[ -n "$unlink" ]]; then
  if ours; then
    rm -f -- "$link_path"
    printf 'Removed %s\n' "$link_path" >&2
  elif [[ -e "$link_path" || -L "$link_path" ]]; then
    printf 'Left %s alone: it is not the link piakura made\n' "$link_path" >&2
  fi
  exit 0
fi

# A development checkout builds its own tools into bin/ (mise run build).
root=$(cd -P "$here/../.." && pwd -P)
if [[ ! -f "$here/VERSION" ]] && [[ -f "$root/go.mod" ]] && grep -qx 'module sakura-midi-arranger' "$root/go.mod"; then
  [[ -x "$root/bin/piakura" ]] || die "Development checkout: run 'mise run bootstrap && mise run build' in $root"
  [[ -z "$link" ]] || printf 'Development checkout: not linking piakura onto your PATH; use %s/bin\n' "$root" >&2
  printf '%s/bin\n' "$root"
  exit 0
fi

[[ -n "$version" ]] || version=$(cat "$here/VERSION" 2>/dev/null) || die "No VERSION in $here; reinstall the skills"
case $version in v[0-9]*) ;; *) die "Invalid version: $version" ;; esac
target=$data/releases/$version
installed() { [[ -x "$target/bin/piakura" ]] && [[ "$("$target/bin/piakura" version 2>/dev/null)" == "$version" ]]; }

if [[ -n "$check" ]]; then
  installed || exit 1
  printf '%s/bin\n' "$target"
  exit 0
fi
# Installing is part of the consented workflow: the caller passes the version
# of the terms the user accepted, which must be the one this skill ships.
expected=$(sed -n 's/^TERMS_VERSION: *//p' "$here/references/terms.md")
[[ -n "$terms_version" && "$terms_version" == "$expected" ]] ||
  die "Pass --terms-version $expected after the user accepts references/terms.md"
if installed; then
  [[ -e "$data/current" ]] || ln -sfn "releases/$version" "$data/current"
  [[ -z "$link" ]] || link_bin
  printf '%s/bin\n' "$target"
  exit 0
fi

case $(uname -s) in
Linux) os=linux ;;
Darwin) os=darwin ;;
*) die "Unsupported system: $(uname -s) (Linux and macOS are supported)" ;;
esac
case $(uname -m) in
x86_64 | amd64) arch=amd64 ;;
arm64 | aarch64) arch=arm64 ;;
*) die "Unsupported processor: $(uname -m)" ;;
esac
[[ "$os/$arch" != darwin/amd64 ]] || die "Intel Macs are not supported; use an Apple silicon Mac or Linux"
asset=piakura_${version}_${os}_${arch}.tar.gz

mkdir -p "$data/releases"
tmp=$(mktemp -d "$data/releases/.download-XXXXXX")
trap 'rm -rf -- "$tmp"' EXIT
if [[ -n ${PIAKURA_RELEASE_URL:-} ]]; then
  for file in "$asset" SHA256SUMS; do
    curl -fsSL -o "$tmp/$file" "$PIAKURA_RELEASE_URL/$file" || die "Cannot download $PIAKURA_RELEASE_URL/$file"
  done
elif command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  gh release download "$version" -R "$repo" -p "$asset" -p SHA256SUMS -D "$tmp" ||
    die "Cannot download $version from $repo; check that your GitHub account can read it"
else
  base=https://github.com/$repo/releases/download/$version
  for file in "$asset" SHA256SUMS; do
    curl -fsSL -o "$tmp/$file" "$base/$file" ||
      die "Cannot download $base/$file. While the repository is private, install the GitHub CLI and run 'gh auth login'."
  done
fi

want=$(awk -v f="$asset" '$2 == f || $2 == "*" f {print $1}' "$tmp/SHA256SUMS")
[[ -n "$want" ]] || die "SHA256SUMS does not list $asset"
if command -v sha256sum >/dev/null 2>&1; then
  got=$(sha256sum "$tmp/$asset" | cut -d ' ' -f 1)
else
  got=$(shasum -a 256 "$tmp/$asset" | cut -d ' ' -f 1)
fi
[[ "$got" == "$want" ]] || die "Checksum mismatch for $asset; nothing was installed"

mkdir "$tmp/extract"
tar -xzf "$tmp/$asset" -C "$tmp/extract"
[[ -x "$tmp/extract/bin/piakura" ]] || die "$asset has no bin/piakura"
[[ "$("$tmp/extract/bin/piakura" version)" == "$version" ]] || die "$asset is not version $version"
rm -rf -- "$target"
mv -- "$tmp/extract" "$target"
ln -sfn "releases/$version" "$data/current"
printf 'Installed piakura %s\n' "$version" >&2
[[ -z "$link" ]] || link_bin
printf '%s/bin\n' "$target"
