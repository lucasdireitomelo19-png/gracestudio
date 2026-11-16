#!/usr/bin/env python3
"""Grace Studio — widgets animados vetoriais (eventos ASS), nas cores e fonte de cada marca.

Widgets:
  etiqueta_preco   pílula com "a partir de" + preço grande, entra deslizando com "pop"
  selo             círculo girando levemente com texto curto ("TAXA 0%", "3 ANOS DE GARANTIA")
  faixa_oferta     faixa diagonal de canto ("SUPER SALES", "BLACK NOVEMBER")
  lower_third      barra que cresce + nome/título (apresentador, loja)
  cta              botão com borda que pulsa ("Visite a IESA", "Agende seu test drive")
  seta             seta que se desenha apontando para um ponto
  circulo_destaque círculo que se desenha em volta de um detalhe (ex.: farol, roda)
  barra_progresso  barra fina no topo que acompanha a duração do vídeo
  contagem         número que conta de 0 até o valor ("100 MIL", "R$ 23 MIL")
Uso: eventos = widget(nome, t0, t1, W, H, K, marca, **params)
"""
import math


def _ts(x):
    x = max(0.0, x)
    return f"{int(x // 3600)}:{int(x % 3600 // 60):02d}:{x % 60:05.2f}"


def _c(hexrgb, a=0):
    h = hexrgb.lstrip("#")
    return f"&H{a:02X}{h[4:6]}{h[2:4]}{h[0:2]}&".upper()


def _ev(layer, t0, t1, tags, text, style="GS_W"):
    return f"Dialogue: {layer},{_ts(t0)},{_ts(t1)},{style},,0,0,0,,{{{tags}}}{text}\n"


def _rrect(w, h, r):
    """Retângulo de cantos arredondados (desenho ASS) com origem no canto superior esquerdo."""
    k = 0.55 * r
    return (f"m {r} 0 l {w-r} 0 b {w-r+k} 0 {w} {r-k} {w} {r} l {w} {h-r} b {w} {h-r+k} {w-r+k} {h} {w-r} {h} "
            f"l {r} {h} b {r-k} {h} 0 {h-r+k} 0 {h-r} l 0 {r} b 0 {r-k} {r-k} 0 {r} 0")


def _circ(r, cx=0, cy=0):
    k = 0.5523 * r
    return (f"m {cx} {cy-r} b {cx+k} {cy-r} {cx+r} {cy-k} {cx+r} {cy} b {cx+r} {cy+k} {cx+k} {cy+r} {cx} {cy+r} "
            f"b {cx-k} {cy+r} {cx-r} {cy+k} {cx-r} {cy} b {cx-r} {cy-k} {cx-k} {cy-r} {cx} {cy-r}")


def estilo_ass(fonte, fonte_bold, K):
    return (f"Style: GS_W,{fonte},{round(60*K)},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1\n"
            f"Style: GS_WB,{fonte_bold},{round(60*K)},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1\n")


def widget(nome, t0, t1, W, H, K, marca, **p):
    cor = marca.get("cor", "#00A3E0")
    cor2 = marca.get("cor_texto", "#FFFFFF")
    fade_out = f"\\t({int((t1-t0)*1000)-200},{int((t1-t0)*1000)},\\alpha&HFF&)"
    out = ""

    if nome == "etiqueta_preco":
        x, y = p.get("x", round(0.07 * W)), p.get("y", round(0.70 * H))
        topo, preco = p.get("topo", "a partir de"), p.get("preco", "R$ 0")
        w = round(max(len(preco) * 52, len(topo) * 26 + 40) * K)
        h, pad, dx = round(200 * K), round(36 * K), round(80 * K)

        def anim(yy, xx):
            return (f"\\move({xx-dx},{yy},{xx},{yy},0,260)\\fscx92\\fscy92\\t(0,260,\\fscx100\\fscy100)"
                    f"\\alpha&HFF&\\t(0,160,\\alpha&H00&){fade_out}")
        out += _ev(5, t0, t1, f"\\an7\\p1\\1c{_c(cor)}{anim(y, x)}", _rrect(w, h, round(28 * K)))
        out += _ev(6, t0, t1, f"\\an7\\fs{round(40*K)}\\1c{_c(cor2)}{anim(y+round(24*K), x+pad)}", topo)
        out += _ev(6, t0, t1, f"\\an7\\fs{round(92*K)}\\1c{_c(cor2)}{anim(y+round(72*K), x+pad)}", preco, "GS_WB")
        return out, [t0]

    if nome == "selo":
        x, y, r = p.get("x", round(0.80 * W)), p.get("y", round(0.30 * H)), round(p.get("raio", 150) * K)
        linhas = p.get("texto", "TAXA\\N0%")
        anim = f"\\pos({x},{y})\\frz-12\\fscx0\\fscy0\\t(0,280,\\fscx110\\fscy110)\\t(280,380,\\fscx100\\fscy100){fade_out}"
        out += _ev(5, t0, t1, f"\\an5\\p1\\1c{_c(cor)}\\3c{_c(cor2)}\\bord{round(5*K)}{anim}", _circ(r, r, r))
        out += _ev(6, t0, t1, f"\\an5\\fs{round(r*0.42)}\\1c{_c(cor2)}{anim}", linhas, "GS_WB")
        return out, [t0]

    if nome == "faixa_oferta":
        texto = p.get("texto", "SUPER SALES")
        larg, alt = round(1100 * K), round(110 * K)
        x, y = p.get("x", W - round(210 * K)), p.get("y", round(210 * K))
        anim = f"\\pos({x},{y})\\frz-45\\clip(0,0,0,{H})\\t(0,350,\\clip(0,0,{W},{H})){fade_out}"
        out += _ev(5, t0, t1, f"\\an5\\p1\\1c{_c(cor)}{anim}", f"m {-larg//2} {-alt//2} l {larg//2} {-alt//2} l {larg//2} {alt//2} l {-larg//2} {alt//2}")
        out += _ev(6, t0, t1, f"\\an5\\fs{round(64*K)}\\1c{_c(cor2)}\\fsp{round(6*K)}{anim}", texto, "GS_WB")
        return out, [t0]

    if nome == "lower_third":
        x, y = p.get("x", round(0.07 * W)), p.get("y", round(0.78 * H))
        titulo, sub = p.get("titulo", "Nome"), p.get("sub", "Cargo")
        w = round(max(len(titulo) * 40, len(sub) * 26) * K + 80 * K)
        out += _ev(5, t0, t1, f"\\an7\\pos({x},{y})\\p1\\1c{_c(cor)}\\fscx0\\t(0,300,\\fscx100){fade_out}", _rrect(round(14*K), round(150*K), round(7*K)))
        out += _ev(5, t0, t1, f"\\an7\\pos({x+round(28*K)},{y})\\p1\\1c&H000000&\\alpha&H60&\\fscx0\\t(80,420,\\fscx100){fade_out}", _rrect(w, round(150*K), round(10*K)))
        out += _ev(6, t0, t1, f"\\an7\\pos({x+round(56*K)},{y+round(18*K)})\\fs{round(64*K)}\\alpha&HFF&\\t(260,460,\\alpha&H00&){fade_out}", titulo, "GS_WB")
        out += _ev(6, t0, t1, f"\\an7\\pos({x+round(56*K)},{y+round(90*K)})\\fs{round(40*K)}\\1c{_c(cor)}\\alpha&HFF&\\t(380,580,\\alpha&H00&){fade_out}", sub)
        return out, [t0]

    if nome == "cta":
        texto = p.get("texto", "Visite a IESA")
        x, y = p.get("x", W // 2), p.get("y", round(0.70 * H))
        w, h = round(len(texto) * 34 * K + 120 * K), round(130 * K)
        pulso = "".join(f"\\t({600+i*900},{1050+i*900},\\fscx106\\fscy106)\\t({1050+i*900},{1500+i*900},\\fscx100\\fscy100)" for i in range(int((t1-t0)/0.9)))
        anim = f"\\pos({x},{y})\\fscx60\\fscy60\\t(0,220,\\fscx100\\fscy100)\\alpha&HFF&\\t(0,150,\\alpha&H00&){pulso}{fade_out}"
        out += _ev(5, t0, t1, f"\\an5\\p1\\1c{_c(cor)}\\3c{_c(cor2)}\\bord{round(4*K)}{anim}", _rrect(w, h, h // 2))
        out += _ev(6, t0, t1, f"\\an5\\fs{round(58*K)}\\1c{_c(cor2)}{anim}", texto, "GS_WB")
        return out, [t0]

    if nome == "seta":
        x0, y0 = p.get("de", (round(0.25 * W), round(0.35 * H)))
        x1, y1 = p.get("para", (round(0.55 * W), round(0.55 * H)))
        ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
        L = math.hypot(x1 - x0, y1 - y0)
        esp, cab = round(14 * K), round(60 * K)
        corpo = f"m 0 {-esp//2} l {L-cab} {-esp//2} l {L-cab} {-cab//1.4} l {L} 0 l {L-cab} {cab//1.4} l {L-cab} {esp//2} l 0 {esp//2}"
        out += _ev(5, t0, t1, f"\\an7\\pos({x0},{y0})\\org({x0},{y0})\\frz{-ang:.1f}\\p1\\1c{_c(cor)}\\3c&H000000&\\bord{round(3*K)}"
                              f"\\clip({x0-round(L)},{y0-round(L)},{x0},{y0+round(L)})\\t(0,350,\\clip({x0-round(L)},{y0-round(L)},{x0+round(L)+cab},{y0+round(L)})){fade_out}", corpo)
        return out, [t0]

    if nome == "circulo_destaque":
        x, y, r = p.get("x", W // 2), p.get("y", H // 2), round(p.get("raio", 180) * K)
        fo = fade_out.replace("\\alpha", "\\3a")
        anim = f"\\pos({x},{y})\\fscx130\\fscy130\\3a&HFF&\\t(0,260,\\fscx100\\fscy100\\3a&H00&){fo}"
        out += _ev(5, t0, t1, f"\\an5\\p1\\1a&HFF&\\3c{_c(cor)}\\bord{round(10*K)}\\shad0{anim}", _circ(r, r, r))
        return out, [t0]

    if nome == "barra_progresso":
        h = round(10 * K)
        out += _ev(7, t0, t1, f"\\an7\\pos(0,0)\\p1\\1c{_c(cor)}\\clip(0,0,0,{h})\\t(0,{int((t1-t0)*1000)},\\clip(0,0,{W},{h}))", f"m 0 0 l {W} 0 l {W} {h} l 0 {h}")
        return out, []

    if nome == "contagem":
        x, y = p.get("x", W // 2), p.get("y", round(0.45 * H))
        alvo, prefixo, sufixo = int(p.get("valor", 100)), p.get("prefixo", ""), p.get("sufixo", "")
        dur, n = min(1.2, (t1 - t0) * 0.6), 18
        for i in range(n + 1):
            a = t0 + dur * (i / n) ** 0.6
            b = t0 + dur * ((i + 1) / n) ** 0.6 if i < n else t1
            v = round(alvo * i / n)
            out += _ev(6, a, b, f"\\an5\\pos({x},{y})\\fs{round(150*K)}\\1c{_c(cor2)}\\3c{_c(cor)}\\bord{round(6*K)}", f"{prefixo}{v}{sufixo}", "GS_WB")
        return out, [t0]

    raise ValueError(f"widget desconhecido: {nome}")


WIDGETS = ["etiqueta_preco", "selo", "faixa_oferta", "lower_third", "cta", "seta", "circulo_destaque", "barra_progresso", "contagem"]
