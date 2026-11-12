#!/usr/bin/env bash
# Baixa os brutos de uma pasta (ids.txt: "<drive_id> <nome>"), extrai áudio, miniaturas e transcreve.
set -u
P=$1
HERE=$(cd "$(dirname "$0")" && pwd)
cd "$P/raw" || exit 1
while read -r id name; do
  [ -s "$name.MOV" ] && continue
  curl -sS -L --retry 3 -o "$name.MOV" "https://drive.usercontent.google.com/download?id=$id&export=download&confirm=t" || echo "FALHOU $name"
done < ../ids.txt
for f in *.MOV; do
  n=${f%.MOV}
  [ -s ../audio/$n.wav ] || ffmpeg -v error -y -i "$f" -vn -ac 1 -ar 16000 ../audio/$n.wav
  [ -s ../thumbs/$n.jpg ] || ffmpeg -v error -y -i "$f" -vf "fps=1.5,scale=-1:200,tile=8x1" -frames:v 1 ../thumbs/$n.jpg
done
cd .. && python3 "$HERE/transcrever.py" .
