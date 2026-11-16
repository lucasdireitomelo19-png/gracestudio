#!/usr/bin/env bash
# Grace Studio — instala as skills de edição de vídeo (versões fixadas, já revisadas) em ~/.claude/skills
# e as ferramentas que elas usam. Rodar de novo em cada sessão nova (a máquina da nuvem é temporária).
set -euo pipefail

SRC=${SKILLS_SRC:-/home/user/tools/skills-src}
DST=${SKILLS_DST:-$HOME/.claude/skills}
TOOLS=${TOOLS_DIR:-/home/user/tools}
mkdir -p "$SRC" "$DST" "$TOOLS"

# repo  commit(revisado)  pasta-da-skill-dentro-do-repo
REPOS=(
  "remotion-dev/skills 3e20ac75161bc34468845df714701cc9bf6075f4 skills/*"
  "Moessif/code-video-showcase decd75d0aaaf19f81a50b52d0d02e605178916e0 ."
  "MakeMyClip/editor e090b420f2f0c2c5fd4b16d3b741348fdd6d8671 ."
  "kmilo93sd/agent-video-editor 8e32c0aff64c445ef1e2b87bc04408a34d68c973 skills/editing-videos"
)

for entry in "${REPOS[@]}"; do
  read -r repo commit sub <<<"$entry"
  dir="$SRC/${repo//\//_}"
  if [ ! -d "$dir/.git" ]; then
    git clone -q "https://github.com/$repo.git" "$dir"
  fi
  git -C "$dir" fetch -q --depth 1 origin "$commit" 2>/dev/null || true
  git -C "$dir" checkout -q "$commit"
  for s in $dir/$sub; do
    [ -f "$s/SKILL.md" ] || continue
    name=$(sed -n 's/^name:[[:space:]]*//p' "$s/SKILL.md" | head -1 | tr -d '"')
    rm -rf "$DST/$name"
    mkdir -p "$DST/$name" && (cd "$s" && tar --exclude=.git --exclude=node_modules -cf - .) | tar -xf - -C "$DST/$name"
    echo "skill instalada: $name  ($repo@${commit:0:7})"
  done
done

# MakeMyClip: CLI fixado (0.5.2) + Node 24 local; a skill passa a chamar o wrapper `clip`
if [ ! -x "$TOOLS/makemyclip/clip" ]; then
  mkdir -p "$TOOLS/makemyclip" && cd "$TOOLS/makemyclip"
  npm init -y >/dev/null
  npm install --silent --no-audit --no-fund node@24 @makemyclip/editor@0.5.2 2>/dev/null
  cat > clip <<'EOF'
#!/usr/bin/env bash
D=$(cd "$(dirname "$0")" && pwd)
export MAKEMYCLIP_FFMPEG_PATH=${MAKEMYCLIP_FFMPEG_PATH:-/usr/bin/ffmpeg}
exec "$D/node_modules/node/bin/node" "$D/node_modules/@makemyclip/editor/dist/cli.js" "$@"
EOF
  chmod +x clip
fi
ln -sf "$TOOLS/makemyclip/clip" /usr/local/bin/clip 2>/dev/null || true
sed -i 's#npx -y @makemyclip/editor#clip#g' "$DST/editor/SKILL.md" 2>/dev/null || true

# sons CC0 do agent-video-editor -> biblioteca do Grace Studio
LIB=/home/user/gracestudio/work/biblioteca/sfx_cc0
mkdir -p "$LIB" && cp -r "$DST/editing-videos/library/." "$LIB/" 2>/dev/null || true
echo "pronto: $(ls "$DST" | wc -l) skills em $DST"
