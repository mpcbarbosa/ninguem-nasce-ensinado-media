#!/usr/bin/env python3
"""Motor de produção @ninguem_nasce_ensinado.

Lê content/<mês>/*.json (ver SCHEMA.md), gera:
  media/<mês>/<ID>/01.jpg…   carrosséis, imagens, stories
  media/<mês>/<ID>/reel.mp4  reels (4 cenas, ~12 s, faixa de áudio silenciosa)
  media/<mês>/N<nn>/story.jpg  story «novo post» para cada post P<nn>
  media/<mês>/calendario.csv  linhas prontas para a folha do Make
  media/<mês>/preview.html     pré-visualização do mês

Uso: python engine/render.py 2026-11 [--base-url URL]
"""
import json, os, re, sys, glob, csv, html, shutil, subprocess, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_BASE = "https://raw.githubusercontent.com/mpcbarbosa/ninguem-nasce-ensinado-media/main/"

TH = {
 "L": dict(bg="#F3EDE2", ink="#1C1A17", muted="#5E574D", acc="#B8322A", line="#D6CCBC", margin="#E2A59C", card="#FFFFFF", cardink="#1C1A17", cardlab="#2D6A47", hand="#B8322A", ok="#2D6A47", pill="#1C1A17", pillink="#F3EDE2"),
 "K": dict(bg="#1C1A17", ink="#F3EDE2", muted="#B5AC9E", acc="#E0503F", line="#3A3631", margin="#5A2A24", card="#2A2723", cardink="#F3EDE2", cardlab="#E0503F", hand="#E0503F", ok="#F3EDE2", pill="#F3EDE2", pillink="#1C1A17"),
 "R": dict(bg="#B8322A", ink="#FFFFFF", muted="#F6DCD7", acc="#1C1A17", line="#CC5A4F", margin="#D9776C", card="#FFFFFF", cardink="#1C1A17", cardlab="#B8322A", hand="#1C1A17", ok="#FFFFFF", pill="#1C1A17", pillink="#FFFFFF"),
}
SERIF = "font-family: Fraunces, Georgia, serif;"


def fonts_css():
    """Fontes locais (fonts/*.woff2) se existirem; senão Google Fonts."""
    F = os.path.join(ROOT, "fonts")
    if os.path.isdir(F) and glob.glob(F + "/**/*.woff2", recursive=True):
        def f(p): return "file://" + os.path.join(F, p)
        css = (f"@font-face{{font-family:Fraunces;font-style:normal;font-weight:100 900;src:url({f('fraunces-latin-opsz-normal.woff2')});}}"
               f"@font-face{{font-family:Fraunces;font-style:italic;font-weight:100 900;src:url({f('fraunces-latin-opsz-italic.woff2')});}}")
        css += "".join(f"@font-face{{font-family:'Instrument Sans';font-weight:{w};src:url({f(f'instrument-sans-latin-{w}-normal.woff2')});}}" for w in (400, 500, 600, 700))
        css += "".join(f"@font-face{{font-family:Caveat;font-weight:{w};src:url({f(f'caveat-latin-{w}-normal.woff2')});}}" for w in (600, 700))
        return "<style>" + css + "</style>"
    return ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;0,9..144,800;'
            '1,9..144,400;1,9..144,600&family=Instrument+Sans:wght@400;500;600;700&family=Caveat:wght@600;700&display=swap">')


def fx(n):  # tamanho de letra escalável pelo auto-ajuste
    return f"calc(var(--k) * {n}px)"


def md(t, T):
    t = html.escape(str(t), quote=False)
    t = re.sub(r"\[\[(.+?)\]\]", lambda m: f'<span style="color:{T["acc"]}">{m.group(1)}</span>', t)
    t = re.sub(r"~~(.+?)~~", lambda m: f'<s style="text-decoration-color:{T["hand"]};text-decoration-thickness:0.08em">{m.group(1)}</s>', t)
    return t.replace("\n", "<br>")


def caret(w, col, sw=20):
    return (f'<svg width="{w}" height="{int(w*1.05)}" viewBox="0 0 124 130" fill="none" stroke="{col}" stroke-width="{sw}" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 118 C 30 80, 48 40, 60 12 C 72 44, 90 84, 112 116"></path></svg>')


def block(b, T, story=False):
    t = b.get("t")
    if t == "label":
        return f'<div style="font-size:{fx(26 if story else 24)};font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:{T["acc"]}">{md(b["text"],T)}</div>'
    if t == "h":
        it = "font-style:italic;font-weight:600;" if b.get("italic") else "font-weight:800;"
        return f'<h2 style="margin:0;{SERIF}{it}font-size:{fx(b.get("size",96))};line-height:1.04;letter-spacing:-0.02em;color:{T["ink"]};text-wrap:balance">{md(b["text"],T)}</h2>'
    if t == "q":
        return f'<div style="{SERIF}font-style:italic;font-weight:600;font-size:{fx(b.get("size",100))};line-height:1.06;letter-spacing:-0.02em;color:{T["ink"]};text-wrap:balance">{md(b["text"],T)}</div>'
    if t == "p":
        col = T["muted"] if b.get("muted") else T["ink"]
        return f'<p style="margin:0;font-size:{fx(b.get("size",40 if story else 34))};line-height:1.45;color:{col}">{md(b["text"],T)}</p>'
    if t == "hand":
        return f'<div style="font-family:Caveat,cursive;font-weight:700;font-size:{fx(b.get("size",58 if story else 54))};line-height:1.15;color:{T["hand"]};transform:rotate(-2deg);transform-origin:left">{md(b["text"],T)}</div>'
    if t == "big":
        return f'<div style="{SERIF}font-weight:800;font-size:{fx(b.get("size",230))};line-height:0.95;letter-spacing:-0.03em;color:{T["ink"]}">{md(b["text"],T)}</div>'
    if t == "pairs":
        rows = ""
        for w, r in b["rows"]:
            rows += (f'<div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px;padding:{fx(20)} 0;border-bottom:2px solid {T["line"]}">'
                     f'<div style="display:flex;align-items:center;gap:16px;font-size:{fx(36)};color:{T["muted"]}"><span style="font-family:Caveat,cursive;font-weight:700;font-size:{fx(48)};color:{T["hand"]}">✗</span><s style="text-decoration-color:{T["hand"]};text-decoration-thickness:3px">{md(w,T)}</s></div>'
                     f'<div style="display:flex;align-items:center;gap:16px;font-size:{fx(36)};font-weight:600;color:{T["ink"]}"><span style="font-family:Caveat,cursive;font-weight:700;font-size:{fx(48)};color:{T["ok"]}">✓</span><span>{md(r,T)}</span></div></div>')
        return f'<div style="display:flex;flex-direction:column">{rows}</div>'
    if t == "items":
        out = ""
        for n, h, tx in b["rows"]:
            out += (f'<div style="display:flex;gap:28px;align-items:flex-start">'
                    f'<div style="flex-shrink:0;width:{fx(64)};height:{fx(64)};box-sizing:border-box;border-radius:50%;border:3px solid {T["acc"]};display:flex;align-items:center;justify-content:center;font-family:Caveat,cursive;font-weight:700;color:{T["acc"]};font-size:{fx(40)}">{md(n,T)}</div>'
                    f'<div style="display:flex;flex-direction:column;gap:6px;min-width:0"><div style="{SERIF}font-weight:800;font-size:{fx(42)};line-height:1.15;color:{T["ink"]}">{md(h,T)}</div>'
                    f'<div style="font-size:{fx(30)};line-height:1.42;color:{T["muted"]}">{md(tx,T)}</div></div></div>')
        return f'<div style="display:flex;flex-direction:column;gap:{fx(32)}">{out}</div>'
    if t == "card":
        return (f'<div style="padding:{fx(34)} {fx(38)};background:{T["card"]};border-radius:20px;display:flex;flex-direction:column;gap:12px">'
                f'<div style="font-size:{fx(22)};font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:{T["cardlab"]}">{md(b.get("label",""),T)}</div>'
                f'<div style="{SERIF}font-style:italic;font-weight:600;font-size:{fx(b.get("size",44))};line-height:1.2;color:{T["cardink"]}">{md(b["text"],T)}</div></div>')
    if t == "bubble":
        al = "flex-end" if b.get("align") == "right" else "flex-start"
        bd = T["ink"]
        return (f'<div style="align-self:{al};max-width:88%;padding:{fx(28)} {fx(42)};background:{T["card"]};border:2px solid {bd};border-radius:44px;'
                f'{SERIF}font-style:italic;font-weight:600;font-size:{fx(b.get("size",56))};line-height:1.15;color:{T["cardink"]}">{md(b["text"],T)}</div>')
    if t == "tenframe":
        n1, n2 = int(b.get("ink", 0)), int(b.get("red", 0)); cells = ""
        for i in range(10):
            col = T["ink"] if i < n1 else (T["acc"] if i < n1 + n2 else None)
            dot = f'<div style="width:84px;height:84px;border-radius:42px;background:{col}"></div>' if col else ""
            cells += f'<div style="height:130px;display:flex;align-items:center;justify-content:center;border:4px solid {T["ink"]};margin:-2px">{dot}</div>'
        return f'<div style="display:grid;grid-template-columns:repeat(5,minmax(0,1fr));width:690px;max-width:100%">{cells}</div>'
    if t == "sabias":
        return f'<div style="display:flex;align-items:center;gap:24px">{caret(90,T["hand"])}<div style="font-family:Caveat,cursive;font-weight:700;font-size:{fx(80)};color:{T["hand"]};transform:rotate(-3deg)">Sabias que…?</div></div>'
    if t == "swipe":
        c = T["acc"] if T is not TH["R"] else "#FFFFFF"
        return (f'<div style="display:flex;align-items:center;gap:12px;font-size:{fx(30)};font-weight:700;color:{c}">Desliza '
                f'<svg width="36" height="24" viewBox="0 0 36 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 12h30M22 3l10 9-10 9"></path></svg></div>')
    if t == "cta":
        return (f'<div style="display:flex;gap:20px;flex-wrap:wrap">'
                f'<div style="padding:{fx(22)} {fx(32)};border-radius:40px;background:{T["pill"]};color:{T["pillink"]};font-size:{fx(28)};font-weight:700">Guarda este post</div>'
                f'<div style="padding:{fx(22)} {fx(32)};border-radius:40px;border:2px solid {T["ink"]};color:{T["ink"]};font-size:{fx(28)};font-weight:700">Partilha com quem educa</div></div>')
    if t == "cta_reel":
        c = T["acc"] if T is not TH["R"] else "#1C1A17"
        return (block({"t": "h", "text": "Guarda e envia", "size": 120}, T) +
                f'<h2 style="margin:0;{SERIF}font-style:italic;font-weight:600;font-size:{fx(120)};line-height:1.04;color:{c}">a quem precisa.</h2>' +
                block({"t": "p", "text": b.get("text", "Ninguém nasce ensinado."), "size": 42, "muted": True}, T))
    if t == "ref":
        return f'<div style="font-size:{fx(22 if not story else 26)};line-height:1.4;color:{T["muted"]};border-top:2px solid {T["line"]};padding-top:14px">{md(b["text"],T)}</div>'
    if t == "img":
        return f'<img src="{b["src"]}" alt="{html.escape(b.get("alt",""))}" style="width:{b.get("w",600)}px;height:{b.get("h",750)}px;object-fit:cover;border-radius:24px;border:3px solid {T["ink"]};transform:rotate(-2deg)">'
    raise ValueError(f"bloco desconhecido: {t}")


def page(Tk, w, h, kicker, idx, total, inner, kind):
    T = TH[Tk]
    if kind == "post":
        pad = "96px 96px 88px 140px"
        head = f'<div style="display:flex;justify-content:space-between;align-items:center;font-size:22px;font-weight:600;letter-spacing:0.14em;text-transform:uppercase;color:{T["muted"]}"><div>{html.escape(kicker)}</div><div>{idx:02d} / {total:02d}</div></div>' if total > 1 else \
               f'<div style="font-size:22px;font-weight:600;letter-spacing:0.14em;text-transform:uppercase;color:{T["muted"]}">{html.escape(kicker)}</div>'
        segs = "".join(f'<div style="width:36px;height:5px;border-radius:3px;background:{T["ink"] if i==idx else T["line"]}"></div>' for i in range(1, total + 1)) if total > 1 else ""
        foot = f'<div style="display:flex;justify-content:space-between;align-items:center;font-size:24px;font-weight:600;color:{T["muted"]}"><div>@ninguem_nasce_ensinado</div><div style="display:flex;gap:8px">{segs}</div></div>'
        gap = 44
    else:  # reel / story 9:16 — margens seguras da interface do Instagram
        pad = "250px 110px 360px 150px"
        right = "".join(f'<div style="width:34px;height:6px;border-radius:3px;background:{T["ink"] if i==idx else T["line"]}"></div>' for i in range(1, total + 1)) if total > 1 else ""
        head = f'<div style="display:flex;justify-content:space-between;align-items:center;font-size:28px;font-weight:600;letter-spacing:0.14em;text-transform:uppercase;color:{T["muted"]}"><div>{html.escape(kicker)}</div><div style="display:flex;gap:8px">{right}</div></div>'
        foot = f'<div style="font-size:30px;font-weight:600;color:{T["muted"]}">@ninguem_nasce_ensinado</div>'
        gap = 48
    body = (f'<div id="pg" style="--k:1;position:relative;width:{w}px;height:{h}px;box-sizing:border-box;padding:{pad};display:flex;flex-direction:column;gap:40px;background:{T["bg"]};overflow:hidden">'
            f'<div style="position:absolute;left:96px;top:0;width:2px;height:{h}px;background:{T["margin"]}"></div>{head}'
            f'<div id="c" style="flex-grow:1;min-height:0;display:flex;flex-direction:column;justify-content:center;gap:{fx(gap)}">{inner}</div>{foot}</div>')
    return (f'<!doctype html><html lang="pt"><head><meta charset="utf-8">{fonts_css()}'
            f'<style>body{{margin:0;font-family:"Instrument Sans",system-ui,sans-serif;color:{T["ink"]};background:{T["bg"]}}}</style></head><body>{body}</body></html>')


class Renderer:
    def __init__(self):
        from playwright.sync_api import sync_playwright
        self._p = sync_playwright().start()
        exe = os.environ.get("CHROMIUM_PATH")
        self.b = self._p.chromium.launch(executable_path=exe) if exe else self._p.chromium.launch()
        self.warn = []

    def shot(self, doc, w, h, out_png, label):
        tmp = out_png + ".html"
        open(tmp, "w").write(doc)
        pg = self.b.new_page(viewport={"width": w, "height": h})
        pg.goto("file://" + tmp)
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(250)
        k = pg.evaluate("""() => { const pg=document.getElementById('pg'), c=document.getElementById('c');
            let k=1; const over=()=>c.scrollHeight>c.clientHeight+1||c.scrollWidth>c.clientWidth+1;
            const used=()=>{const a=c.firstElementChild,b=c.lastElementChild; if(!a) return 0;
                return b.getBoundingClientRect().bottom-a.getBoundingClientRect().top;};
            const set=v=>{k=Math.round(v*100)/100; pg.style.setProperty('--k',k);};
            while(over() && k>0.55) set(k-0.04);
            // aumentar a letra quando o slide fica demasiado vazio
            while(!over() && used()<c.clientHeight*TARGET && k<MAXK) set(k+0.04);
            while(over() && k>0.55) set(k-0.02);
            return [k, over()]; }""".replace("TARGET", "0.62" if h > 1400 else "0.55").replace("MAXK", "1.7" if h > 1400 else "1.3"))
        if k[0] < 1: self.warn.append(f"{label}: letra reduzida para {int(k[0]*100)}%")
        if k[1]: self.warn.append(f"{label}: AINDA NÃO CABE — rever texto")
        pg.screenshot(path=out_png)
        pg.close(); os.remove(tmp)

    def close(self):
        self.b.close(); self._p.stop()


def to_jpg(png, jpg):
    from PIL import Image
    Image.open(png).convert("RGB").save(jpg, quality=90, optimize=True)
    os.remove(png)


def make_reel(pngs, out):
    d, x = 3.4, 0.4
    args = ["ffmpeg", "-y", "-loglevel", "error"]
    for p in pngs: args += ["-loop", "1", "-t", str(d), "-i", p]
    args += ["-f", "lavfi", "-t", str(len(pngs) * d - (len(pngs) - 1) * x), "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]
    fl, prev = [], "[0:v]"
    for i in range(1, len(pngs)):
        off = round(i * (d - x), 2)
        lab = f"[v{i}]"
        fl.append(f"{prev}[{i}:v]xfade=transition=fade:duration={x}:offset={off}{lab}")
        prev = lab
    fl.append(f"{prev}fps=30,format=yuv420p[vo]")
    args += ["-filter_complex", ";".join(fl), "-map", "[vo]", "-map", f"{len(pngs)}:a",
             "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-profile:v", "high", "-level", "4.1",
             "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out]
    subprocess.run(args, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mes")
    ap.add_argument("--base-url", default=os.environ.get("NNE_BASE_URL", DEFAULT_BASE))
    a = ap.parse_args()
    src = os.path.join(ROOT, "content", a.mes)
    dst = os.path.join(ROOT, "media", a.mes)
    os.makedirs(dst, exist_ok=True)
    items = [json.load(open(f)) for f in sorted(glob.glob(src + "/*.json"))]
    R = Renderer()
    rows, prev = [], []
    url = lambda rel: a.base_url + rel.replace(os.sep, "/")
    for it in items:
        iid, tipo = it["id"], it["tipo"]
        od = os.path.join(dst, iid); shutil.rmtree(od, ignore_errors=True); os.makedirs(od)
        slides = it["slides"]; n = len(slides)
        post = tipo in ("CARROSSEL", "IMAGEM")
        w, h = (1080, 1350) if post else (1080, 1920)
        files = []
        for i, s in enumerate(slides, 1):
            T = TH[s["T"]]
            inner = "".join(block(b, T, story=not post) for b in s["blocks"])
            doc = page(s["T"], w, h, it.get("kicker", ""), i, n if tipo != "STORY" else 1, inner, "post" if post else "tall")
            png = os.path.join(od, f"{i:02d}.png")
            R.shot(doc, w, h, png, f"{iid} slide {i}")
            files.append(png)
        if tipo == "REEL":
            mp4 = os.path.join(od, "reel.mp4"); make_reel(files, mp4)
            cover = os.path.join(od, "capa.jpg"); to_jpg(files[0], cover)
            for f in files[1:]: to_jpg(f, f[:-4] + ".jpg")
            media = [url(os.path.relpath(mp4, ROOT))]
            thumbs = [cover] + [f[:-4] + ".jpg" for f in files[1:]]
        else:
            jpgs = []
            for f in files: j = f[:-4] + ".jpg"; to_jpg(f, j); jpgs.append(j)
            media = [url(os.path.relpath(j, ROOT)) for j in jpgs]
            thumbs = jpgs
        notas = {"STORY": ("Dica do dia" if iid.startswith("SD") else "Sabias que…?")}.get(tipo, "")
        rows.append(dict(ID=iid, Quando=it["quando"], Tipo=tipo, Imagens=",".join(media), Legenda=it.get("legenda", ""),
                         Estado="Aprovado", Notas=notas, Resultado="", Pasta=f"media/{a.mes}/{iid}"))
        prev.append((it, thumbs))
        # story «novo post» para cada post de feed
        if post:
            num = re.sub(r"\D", "", iid)
            sid = f"N{num}"
            sd = os.path.join(dst, sid); shutil.rmtree(sd, ignore_errors=True); os.makedirs(sd)
            Tk = "K" if slides[0]["T"] == "L" else "L"
            T = TH[Tk]
            inner = (block({"t": "h", "text": it.get("titulo", ""), "size": 84}, T) +
                     block({"t": "img", "src": "file://" + thumbs[0], "w": 600, "h": 750, "alt": "Capa do post"}, T) +
                     block({"t": "hand", "text": "Novo no feed — vai espreitar!", "size": 58}, T))
            doc = page(Tk, 1080, 1920, "Novo post no feed", 1, 1, inner, "tall")
            png = os.path.join(sd, "01.png"); R.shot(doc, 1080, 1920, png, f"{sid} story"); j = png[:-4] + ".jpg"; to_jpg(png, j)
            hh, mm = it["quando"][-5:].split(":")
            q = it["quando"][:-5] + f"{hh}:{int(mm)+15:02d}"
            rows.append(dict(ID=sid, Quando=q, Tipo="STORY", Imagens=url(os.path.relpath(j, ROOT)), Legenda="",
                             Estado="Aprovado", Notas=f"Story «novo post» — sai depois do post {iid}", Resultado="", Pasta=f"media/{a.mes}/{sid}"))
            prev.append(({"id": sid, "tipo": "STORY", "quando": q, "titulo": "Novo post: " + it.get("titulo", ""), "legenda": ""}, [j]))
    R.close()
    rows.sort(key=lambda r: (r["Quando"], r["ID"]))
    with open(os.path.join(dst, "calendario.csv"), "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=["ID", "Quando", "Tipo", "Imagens", "Legenda", "Estado", "Notas", "Resultado", "Pasta"])
        wr.writeheader(); wr.writerows(rows)
    write_preview(dst, prev, a.mes)
    open(os.path.join(dst, "avisos.txt"), "w").write("\n".join(R.warn) + "\n")
    print(f"{len(items)} peças, {len(rows)} linhas de calendário; avisos: {len(R.warn)}")
    for w_ in R.warn: print(" -", w_)


def write_preview(dst, prev, mes):
    cards = ""
    for it, thumbs in sorted(prev, key=lambda x: x[0]["quando"]):
        imgs = "".join(f'<img loading="lazy" src="{os.path.relpath(t, dst)}" alt="">' for t in thumbs)
        cap = html.escape(it.get("legenda", "")).replace("\n", "<br>")
        cards += (f'<article><header><b>{html.escape(it["quando"])}</b> · {it["tipo"]} · {it["id"]}<h3>{html.escape(it.get("titulo",""))}</h3></header>'
                  f'<div class="strip">{imgs}</div>{"<details><summary>Legenda</summary><p>"+cap+"</p></details>" if cap else ""}</article>')
    open(os.path.join(dst, "preview.html"), "w").write(
        f'<!doctype html><html lang="pt"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Pré-visualização {mes}</title>'
        '<style>body{margin:0;padding:16px;background:#F3EDE2;color:#1C1A17;font-family:system-ui,sans-serif}article{background:#fff;border-radius:12px;padding:14px;margin:0 0 16px}'
        'h3{margin:4px 0 10px;font-family:Georgia,serif}.strip{display:flex;gap:8px;overflow-x:auto}.strip img{height:260px;border-radius:6px}</style></head>'
        f'<body><h1>@ninguem_nasce_ensinado · {mes}</h1>{cards}</body></html>')


if __name__ == "__main__":
    main()
