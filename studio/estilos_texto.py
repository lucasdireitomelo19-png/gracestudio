#!/usr/bin/env python3
"""Grace Studio — estilos de texto/legenda animados (gera eventos ASS para o libass/ffmpeg).

Cada estilo recebe um bloco: linhas de palavras [(palavra, t_ini, t_fim, destaque)] em segundos da timeline,
posição (x, y, alinhamento), tamanho, fontes e cor da marca, e devolve linhas "Dialogue:" prontas.

Estilos:
  referencia     texto fino, destaques em negrito, cada palavra entra com fade (referência BMW X2)
  karaoke        linha inteira visível, a palavra falada acende na cor da marca
  hormozi        2–3 palavras por vez, MAIÚSCULAS, negrito com contorno, "pop" de escala, destaque colorido
  caixa          texto sobre caixa de cor sólida (estilo CapCut), entra deslizando
  marcador       palavra de destaque com marca-texto colorido passando por trás
  maquina        letra por letra (máquina de escrever)
  subindo        cada palavra sobe e aparece (slide up)
  neon           brilho colorido em volta do texto, pulsando
  impacto        uma palavra gigante por vez no centro, com tremor
  minimal        pequeno, discreto, fade da linha inteira
"""


def _ts(x):
    x = max(0.0, x)
    return f"{int(x // 3600)}:{int(x % 3600 // 60):02d}:{x % 60:05.2f}"


def cor_ass(hexrgb, alpha=0):
    """'#RRGGBB' -> '&HAABBGGRR' do ASS."""
    h = hexrgb.lstrip("#")
    r, g, b = h[0:2], h[2:4], h[4:6]
    return f"&H{alpha:02X}{b}{g}{r}".upper().replace("&H", "&H")


def _ev(layer, st, en, style, tags, text):
    return f"Dialogue: {layer},{_ts(st)},{_ts(en)},{style},,0,0,0,,{{{tags}}}{text}\n"


def estilos_ass(fonte, fonte_bold, tam, cor_marca="#FFFFFF", K=1.0):
    """Estilos base (cabeçalho [V4+ Styles]) usados pelos geradores."""
    c = cor_ass(cor_marca)
    return "\n".join([
        f"Style: GS_Reg,{fonte},{tam},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1",
        f"Style: GS_Bold,{fonte_bold},{tam},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1",
        f"Style: GS_Hz,{fonte_bold},{round(tam*1.6)},&H00FFFFFF,{c},&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,{round(6*K)},{round(3*K)},5,0,0,0,1",
        f"Style: GS_Box,{fonte_bold},{tam},&H00FFFFFF,&H00FFFFFF,{c},{c},1,0,0,0,100,100,0,0,3,{round(16*K)},0,7,0,0,0,1",
        f"Style: GS_Big,{fonte_bold},{round(tam*3)},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1",
    ]) + "\n"


def _sombra(text):
    return text.replace("\\alpha&H00&", "\\alpha&H90&")


def gerar(estilo, linhas, x, y, tam, an=7, cor_marca="#FFFFFF", fim=None, K=1.0, lh=1.22):
    """linhas: [[(palavra, t_ini, t_fim, destaque)]]; retorna (eventos_ass, tempos_de_pop)."""
    out, pops = "", []
    cm = cor_ass(cor_marca)
    blur = round(10 * K)
    todas = [w for ln in linhas for w in ln]
    t0 = todas[0][1] - 0.04
    t1 = fim if fim is not None else todas[-1][2] + 0.6
    passo = round(tam * lh)

    def com_sombra(st, en, style, tags, txt, xx, yy, layer=1):
        s = _ev(layer - 1, st, en, style, f"\\pos({xx+round(4*K)},{yy+round(5*K)})\\an{an}\\1c&H000000&\\blur{blur}{tags}", _sombra(txt))
        return s + _ev(layer, st, en, style, f"\\pos({xx},{yy})\\an{an}{tags}", txt)

    if estilo in ("referencia", "subindo", "marcador", "minimal", "maquina", "neon", "karaoke", "caixa"):
        yy = y
        for ln in linhas:
            l0 = ln[0][1] - 0.04
            txt = ""
            for w, a, b, e in ln:
                ms = max(0, int((a - l0) * 1000))
                if estilo == "referencia":
                    txt += f"{{\\b{1 if e else 0}\\alpha&HFF&\\t({ms},{ms+220},\\alpha&H00&)}}{w} "
                elif estilo == "subindo":
                    txt += (f"{{\\b{1 if e else 0}\\alpha&HFF&\\fscy60\\t({ms},{ms+180},\\alpha&H00&\\fscy100)}}{w} ")
                elif estilo == "marcador":
                    txt += f"{{\\b{1 if e else 0}\\alpha&HFF&\\t({ms},{ms+150},\\alpha&H00&)}}{w} "
                elif estilo == "karaoke":
                    mb = max(0, int((b - l0) * 1000))
                    txt += (f"{{\\b{1 if e else 0}\\1c&HFFFFFF&\\t({ms},{ms+80},\\1c{cm}\\fscx108\\fscy108)"
                            f"\\t({mb},{mb+120},\\1c&HFFFFFF&\\fscx100\\fscy100)}}{w} ")
                elif estilo == "maquina":
                    letras = list(w)
                    dur = max(0.05, (b - a) / max(1, len(letras)))
                    txt += "".join(f"{{\\alpha&HFF&\\t({int(ms+i*dur*1000)},{int(ms+i*dur*1000)+1},\\alpha&H00&)}}{ch}"
                                   for i, ch in enumerate(letras)) + " "
                else:  # minimal, neon, caixa: palavras normais (linha entra inteira)
                    txt += f"{{\\b{1 if e else 0}}}{w} "
                if e:
                    pops.append(a)
            txt = txt.strip()
            if estilo == "minimal":
                out += com_sombra(l0, t1, "GS_Reg", "\\fscx80\\fscy80\\alpha&HFF&\\t(0,250,\\alpha&H00&)", txt, x, yy)
                yy += round(passo * 0.82)
                continue
            if estilo == "neon":
                glow = f"\\1c{cm}\\3c{cm}\\bord{round(4*K)}\\blur{round(14*K)}\\alpha&H30&\\t(0,600,\\alpha&H00&)\\t(600,1200,\\alpha&H50&)"
                out += _ev(0, l0, t1, "GS_Bold", f"\\pos({x},{yy})\\an{an}{glow}", txt)
                out += _ev(1, l0, t1, "GS_Bold", f"\\pos({x},{yy})\\an{an}\\alpha&HFF&\\t(0,200,\\alpha&H00&)", txt)
                yy += passo
                continue
            if estilo == "caixa":
                out += _ev(1, l0, t1, "GS_Box", f"\\move({x-round(60*K)},{yy},{x},{yy},0,220)\\an{an}\\alpha&HFF&\\t(0,180,\\alpha&H00&)", txt)
                yy += round(passo * 1.25)
                continue
            out += com_sombra(l0, t1, "GS_Reg", "", txt, x, yy)
            if estilo == "marcador":
                # marca-texto só atrás da palavra de destaque, crescendo da esquerda p/ direita
                pref = 0
                for w, a, b, e in ln:
                    larg = round(len(w) * tam * 0.56)
                    if e:
                        ms = max(0, int((a - l0) * 1000))
                        out += _ev(0, l0, t1, "GS_Reg",
                                   f"\\pos({x + pref - round(6*K)},{yy + round(tam*0.12)})\\an7\\p1\\1c{cm}\\alpha&H30&"
                                   f"\\fscx0\\t({ms},{ms+260},\\fscx100)",
                                   f"m 0 0 l {larg + round(12*K)} 0 l {larg + round(12*K)} {round(tam*0.92)} l 0 {round(tam*0.92)}")
                    pref += larg + round(tam * 0.28)
            yy += passo
        return out, pops

    if estilo == "hormozi":
        # 2–3 palavras por vez, centralizado
        grupo = []
        for w in todas:
            grupo.append(w)
            if len(grupo) == 3 or w[0].endswith((",", ".", "!", "?")):
                gs, ge = grupo[0][1], grupo[-1][2] + 0.05
                txt = " ".join((f"{{\\1c{cm}}}{p.upper()}{{\\1c&HFFFFFF&}}" if e else p.upper()) for p, _, _, e in grupo)
                out += _ev(2, gs, ge, "GS_Hz", f"\\pos({x},{y})\\an5\\fscx70\\fscy70\\t(0,120,\\fscx108\\fscy108)\\t(120,200,\\fscx100\\fscy100)", txt)
                pops.append(gs)
                grupo = []
        if grupo:
            gs, ge = grupo[0][1], grupo[-1][2] + 0.3
            txt = " ".join(p.upper() for p, _, _, _ in grupo)
            out += _ev(2, gs, ge, "GS_Hz", f"\\pos({x},{y})\\an5\\fscx70\\fscy70\\t(0,120,\\fscx108\\fscy108)\\t(120,200,\\fscx100\\fscy100)", txt)
        return out, pops

    if estilo == "impacto":
        # palavras de destaque seguidas viram uma frase só, gigante no centro
        grupos, g = [], []
        for w in todas:
            if w[3]:
                g.append(w)
            elif g:
                grupos.append(g); g = []
        if g:
            grupos.append(g)
        for g in grupos:
            a, b = g[0][1], g[-1][2]
            txt = " ".join(p.upper() for p, _, _, _ in g)
            esc = min(100, int(100 * 7 / max(4, len(txt))))
            out += _ev(3, a, b + 0.35, "GS_Big",
                       f"\\pos({x},{y})\\an5\\fscx{int(esc*1.4)}\\fscy{int(esc*1.4)}\\t(0,120,\\fscx{esc}\\fscy{esc})\\alpha&H40&\\t(0,90,\\alpha&H00&)",
                       txt)
            pops.append(a)
        return out, pops

    raise ValueError(f"estilo desconhecido: {estilo}")


ESTILOS = ["referencia", "karaoke", "hormozi", "caixa", "marcador", "maquina", "subindo", "neon", "impacto", "minimal"]
