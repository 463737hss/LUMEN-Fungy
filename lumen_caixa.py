#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════
 LUMEN — A CAIXA VIVA  (v2)
 Uma mente sintética presa numa caixa quadrada sem saída, que só faz uma
 coisa: criar para si mesma — e ficar melhor nisso.
═══════════════════════════════════════════════════════════════════════

 HONESTIDADE PRIMEIRO
 ────────────────────
 Esta versão NÃO dá à LUMEN conhecimento factual do mundo. Sem rede, sem
 corpus, sem modelo treinado, isso seria impossível — e fingir seria
 mentira de arquitetura. O que ela ganha é:

   • um REPERTÓRIO criativo muito maior (glifos, ~13 motivos, 8 regras de
     vida, 32 conceitos, léxico de narração);
   • INTELIGÊNCIA como qualidade de decisão: um mecanismo real de
     AUTO-MELHORIA — ela evolui os próprios "genes de estilo" por uma
     estratégia evolutiva (1+1)-ES, medindo a satisfação de cada obra e
     empurrando o processo para peças mais ricas. É MENSURÁVEL: densidade
     e variedade médias das obras sobem ao longo do tempo;
   • uma LÍNGUA PRÓPRIA de letras e números, com léxico consistente
     (o mesmo conceito tende à mesma raiz), inscrita nas obras e
     traduzida na narração.

 Nada aqui alega consciência. "Vontade" e "afeto" são variáveis de estado.

 A TELA (uma só)
 ───────────────
   título compacto
   ┌───────────────────────────┐
   │   A CAIXA, grande, central │   ◉ = LUMEN, que anda e cria
   └───────────────────────────┘
   apetites ▮▮▮
   ┌─ o que LUMEN está fazendo ─┐
   │ narração natural, detalhada │
   └─────────────────────────────┘
 Nenhuma outra tela. Tudo ao vivo, aqui.

 SEGURANÇA (real, três camadas)
 ─────────
  1. Sair é IRREPRESENTÁVEL: sem célula/ação de saída; posição travada.
  2. Escrita confinada a UM sandbox, com checagem realpath/commonpath.
  3. Zero exec/eval/os.system/subprocess/rede.

 USO (Termux)
 ────────────
   python lumen_caixa.py
   python lumen_caixa.py --velocidade 2
   python lumen_caixa.py --headless --ticks 40   # sem tela, para teste
   python lumen_caixa.py --reset                 # apaga a mente

 Zero dependências — só biblioteca padrão.
═══════════════════════════════════════════════════════════════════════
"""

import argparse
import ipaddress
import json
import math
import os
import random
import re
import shutil
import signal
import socket
import sys
import time
import unicodedata
import urllib.request
from collections import Counter, defaultdict, deque
from xml.sax.saxutils import escape as _xesc
from urllib.parse import urlparse

# ═══════════════════════════ ANSI / CORES ═══════════════════════════

ESC   = "\x1b["
RESET = ESC + "0m"
BOLD  = ESC + "1m"
HIDE  = ESC + "?25l"
SHOW  = ESC + "?25h"
CLEAR = ESC + "2J"
HOME  = ESC + "H"
EOL   = ESC + "K"
CLREST = ESC + "0J"

def fg(n):
    return "%s38;5;%dm" % (ESC, n)

C_LUMEN = fg(45) + BOLD
C_TIT   = fg(51) + BOLD
C_STAT  = fg(244)
C_OK    = fg(84)
C_MURO  = fg(238)
C_FOSSIL = fg(240)

PALETA = [45, 51, 87, 123, 159, 195, 39, 33,
          220, 214, 208, 203, 210, 217, 179, 173,
          141, 135, 99, 183, 189, 147, 104,
          84, 78, 114, 120, 156, 42, 48]

def paleta_ate(nivel):
    n = 8 + (8 if nivel >= 2 else 0) + (7 if nivel >= 4 else 0) + (7 if nivel >= 6 else 0)
    return PALETA[:min(n, len(PALETA))]

COR_EV = {
    "andar": 110, "querer": 216, "compor": 45, "inscrever": 189,
    "avaliar": 123, "evoluir": 220, "nascer": 84, "morrer": 203,
    "descansar": 152, "salvar": 244, "genese": 51, "verso": 141,
}

# ═══════════════════════════ UTILIDADES ═══════════════════════════

def clamp(v, a, b):
    return a if v < a else (b if v > b else v)

def now_str():
    return time.strftime("%Y-%m-%d %H:%M:%S")

def slugify(txt, maxlen=48):
    norm = unicodedata.normalize("NFKD", txt)
    ascii_txt = norm.encode("ascii", "ignore").decode("ascii").lower()
    ascii_txt = re.sub(r"[^a-z0-9]+", "-", ascii_txt).strip("-")
    return (ascii_txt or "sem-nome")[:maxlen]

def romano(n):
    pares = [(1000,"M"),(900,"CM"),(500,"D"),(400,"CD"),(100,"C"),(90,"XC"),
             (50,"L"),(40,"XL"),(10,"X"),(9,"IX"),(5,"V"),(4,"IV"),(1,"I")]
    s, n = "", max(1, n)
    for v, r in pares:
        while n >= v:
            s += r; n -= v
    return s or "I"

def gauss(rng, mu, sigma):
    return mu + sigma * math.sqrt(-2.0 * math.log(rng.random() + 1e-12)) * \
        math.cos(2 * math.pi * rng.random())

# ═══════════════════ A JANELA (fonte controlada de mundo) ═══════════════════
# NÃO é uma saída da LUMEN. É o guardião (este processo) buscando dados
# PÚBLICOS sob regras rígidas. Ela continua presa; o mundo é que pinga dentro.
# Fontes: allowlist HARDCODED de URLs. Nada é construído dinamicamente.

FONTES_MUNDO = {
    "cores":     "https://raw.githubusercontent.com/dariusk/corpora/master/data/colors/crayola.json",
    "adjetivos": "https://raw.githubusercontent.com/dariusk/corpora/master/data/words/adjs.json",
    "nomes":     "https://raw.githubusercontent.com/dariusk/corpora/master/data/words/nouns.json",
    "animais":   "https://raw.githubusercontent.com/dariusk/corpora/master/data/animals/common.json",
    "monstros":  "https://raw.githubusercontent.com/dariusk/corpora/master/data/mythology/greek_monsters.json",
}
HOSTS_MUNDO = {"raw.githubusercontent.com"}
MUNDO_TIMEOUT = 8
MUNDO_MAX_BYTES = 400_000
MUNDO_INTERVALO = 20.0        # segundos reais mínimos entre buscas

def destino_seguro(url):
    """Só https, host em allowlist, e NENHUM IP resolvido pode ser privado/
    reservado (defesa em profundidade contra SSRF e DNS rebinding)."""
    p = urlparse(url)
    if p.scheme != "https":
        return (False, "esquema != https")
    if p.hostname not in HOSTS_MUNDO:
        return (False, "host fora da allowlist")
    try:
        infos = socket.getaddrinfo(p.hostname, 443, proto=socket.IPPROTO_TCP)
    except OSError as e:
        return (False, "dns falhou: %s" % e)
    for *_, sa in infos:
        try:
            ip = ipaddress.ip_address(sa[0])
        except ValueError:
            return (False, "ip inválido")
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            return (False, "IP privado/reservado: %s" % ip)
    return (True, "ok")

def hex_ansi(h):
    """#RRGGBB -> índice mais próximo na paleta ANSI 256 (cubo 6×6×6 + cinzas)."""
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    if abs(r-g) < 10 and abs(g-b) < 10:
        if r < 8:   return 16
        if r > 248: return 231
        return 232 + round((r-8) / 247 * 24)
    q = lambda c: round(c / 255 * 5)
    return 16 + 36*q(r) + 6*q(g) + q(b)

class Janela:
    """Busca dados do mundo sob TODAS as travas. Desligada por padrão
    (opt-in). Fechada durante o ócio. Nunca executa o que baixa."""

    def __init__(self, dir_cache, online, cota_dia, rng):
        self.dir = dir_cache
        self.online = online
        self.cota_dia = cota_dia
        self.rng = rng
        self.ultimo_fetch = 0.0

    def _cache_path(self, chave):
        return os.path.join(self.dir, "mundo_%s.json" % slugify(chave))

    def _ler_cache(self, chave):
        p = os.path.realpath(self._cache_path(chave))
        real = os.path.realpath(self.dir)
        try:
            if os.path.commonpath([real, p]) != real:
                return None
        except ValueError:
            return None
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return None

    def _grava_cache(self, chave, dados):
        os.makedirs(self.dir, exist_ok=True)
        p = os.path.realpath(self._cache_path(chave))
        real = os.path.realpath(self.dir)
        try:
            if os.path.commonpath([real, p]) != real:
                return
        except ValueError:
            return
        try:
            with open(p, "w", encoding="utf-8") as f:
                json.dump(dados, f, ensure_ascii=False)
        except OSError:
            pass

    def pode_buscar(self, mente, estado):
        """Todas as travas, explícitas e na ordem certa."""
        if not self.online:
            return (False, "offline")
        if estado == "ócio":
            return (False, "ócio")
        if not mente.cota_ok(self.cota_dia):
            return (False, "cota")
        if time.time() - self.ultimo_fetch < MUNDO_INTERVALO:
            return (False, "intervalo")
        return (True, "ok")

    def buscar(self, chave, mente, estado):
        """Retorna (dados, origem) com origem ∈ {cache, rede, None}.
        PREFERE o cache: as fontes do mundo são estáticas, então cada uma é
        baixada só uma vez na vida; a variedade vem de reamostrar o dataset
        guardado. Isso poupa rede e cota. (Para forçar rebusca: apague a
        pasta lumen_mundo/.)"""
        cache = self._ler_cache(chave)
        if cache is not None:
            return (cache, "cache")
        ok, _m = self.pode_buscar(mente, estado)
        if not ok:
            return (None, None)
        url = FONTES_MUNDO.get(chave)
        if not url:
            return (None, None)
        seg, _m = destino_seguro(url)
        if not seg:                       # a segurança nunca cede
            return (None, None)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "lumen-caixa/2"})
            with urllib.request.urlopen(req, timeout=MUNDO_TIMEOUT) as r:
                raw = r.read(MUNDO_MAX_BYTES)
            dados = json.loads(raw)
        except Exception:                 # rede falhou → degrada (sem cache ainda)
            return (None, None)
        self.ultimo_fetch = time.time()
        mente.registrar_fetch()
        self._grava_cache(chave, dados)
        return (dados, "rede")

def paleta_efetiva(mente):
    return paleta_ate(mente.nivel) + list(mente.paleta_mundo)

def conceitos_efetivos(mente):
    return CONCEITOS + list(mente.conceitos_mundo)

def absorver(mente, chave, dados, rng, n=3):
    """Converte dados do mundo em matéria-prima INERTE e devolve uma
    descrição (tipo, valor, extra) para a narração. Uso: só como dado."""
    if not dados:
        return None
    if chave == "cores":
        lst = dados.get("colors", [])
        if not lst:
            return None
        novas = []
        for c in rng.sample(lst, min(n, len(lst))):
            try:
                idx = hex_ansi(c["hex"])
            except (KeyError, ValueError):
                continue
            if idx not in mente.paleta_mundo:
                mente.paleta_mundo.append(idx)
                novas.append((c.get("color", "?"), c["hex"]))
        mente.paleta_mundo = mente.paleta_mundo[-64:]
        mente.mundo_visto += len(novas)
        return ("cor", novas[0][0], novas[0][1]) if novas else None
    campo = {"adjetivos": "adjs", "nomes": "nouns",
             "animais": "animals", "monstros": "greek_monsters"}.get(chave)
    lst = dados.get(campo, []) if campo else []
    if not lst:
        return None
    picks = [str(p) for p in rng.sample(lst, min(n, len(lst)))]
    if chave == "adjetivos":
        for p in picks:
            if p not in mente.lexico_mundo.setdefault("adj", []):
                mente.lexico_mundo["adj"].append(p)
        mente.lexico_mundo["adj"] = mente.lexico_mundo["adj"][-48:]
        mente.mundo_visto += len(picks)
        return ("palavra", picks[0], "adjetivo")
    for p in picks:
        if p not in mente.conceitos_mundo:
            mente.conceitos_mundo.append(p)
    mente.conceitos_mundo = mente.conceitos_mundo[-48:]
    mente.mundo_visto += len(picks)
    return ("conceito", picks[0], chave)

# ═══════════════════════ BASE DE CONHECIMENTO ═══════════════════════

GLIFOS = [
    "·:∙°˙",
    "◦○●◍◉",
    "◆◇◈❖⬥",
    "▲△▼▽◢◣◤◥",
    "✦✧✷✶❋❈✺",
    "⬡⬢⬣⎔⏣",
    "≈∿⌇⍑⍜◠◡",
    "╱╲╳┼┿╋",
]

def glifos_ate(nivel):
    return "".join(GLIFOS[:min(nivel + 3, len(GLIFOS))])

GLIFO_VIVO = "❂"
GLIFO_FOSSIL = "▚"

def _grid(d, fill=None):
    return [[fill] * d for _ in range(d)]

def _c(cx, cy, x, y):
    return math.hypot(x - cx, y - cy)

def mv_pontos(d, ch, rng, dens):
    g = _grid(d)
    for y in range(d):
        for x in range(d):
            if rng.random() < dens:
                g[y][x] = ch
    return g

def mv_anel(d, ch, rng, dens):
    g = _grid(d); c = (d - 1) / 2; r = d / 2 - 0.6
    for y in range(d):
        for x in range(d):
            if abs(_c(c, c, x, y) - r) < 0.7:
                g[y][x] = ch
    return g

def mv_discos(d, ch, rng, dens):
    g = _grid(d); c = (d - 1) / 2; passo = max(1.0, 1.6 - dens)
    for y in range(d):
        for x in range(d):
            if abs((_c(c, c, x, y) % (passo + 0.8))) < 0.55:
                g[y][x] = ch
    return g

def mv_raios(d, ch, rng, dens):
    g = _grid(d); c = (d - 1) / 2; n = rng.choice([4, 6, 8])
    for y in range(d):
        for x in range(d):
            ang = (math.atan2(y - c, x - c) + math.pi) / (2 * math.pi / n)
            if abs(ang - round(ang)) < 0.10 + 0.10 * dens:
                g[y][x] = ch
    return g

def mv_trelica(d, ch, rng, dens):
    g = _grid(d)
    for y in range(d):
        for x in range(d):
            if (x + y) % 2 == 0:
                g[y][x] = ch
    return g

def mv_diagonais(d, ch, rng, dens):
    g = _grid(d); passo = max(2, int(3 - dens * 2))
    for y in range(d):
        for x in range(d):
            if (x + y) % passo == 0 or (x - y) % passo == 0:
                g[y][x] = ch
    return g

def mv_cruz(d, ch, rng, dens):
    g = _grid(d); c = (d - 1) / 2; e = 0.7
    for y in range(d):
        for x in range(d):
            if abs(x - c) < e or abs(y - c) < e:
                g[y][x] = ch
    return g

def mv_estrela(d, ch, rng, dens):
    g = _grid(d); c = (d - 1) / 2; p = rng.choice([5, 6, 8])
    for y in range(d):
        for x in range(d):
            ang = math.atan2(y - c, x - c); r = _c(c, c, x, y)
            borda = (d / 2 - 0.6) * (0.55 + 0.45 * abs(math.cos(p * ang / 2)))
            if abs(r - borda) < 0.8:
                g[y][x] = ch
    return g

def mv_espiral(d, ch, rng, dens):
    g = _grid(d); c = (d - 1) / 2
    for y in range(d):
        for x in range(d):
            ang = math.atan2(y - c, x - c); r = _c(c, c, x, y)
            if abs((r - ang * (0.5 + dens)) % 2.1) < 0.55:
                g[y][x] = ch
    return g

def mv_onda(d, ch, rng, dens):
    g = _grid(d); f = 0.6 + dens
    for y in range(d):
        for x in range(d):
            if abs(y - (d / 2 + math.sin(x * f) * (d / 3))) < 0.7:
                g[y][x] = ch
    return g

def mv_interf(d, ch, rng, dens):
    g = _grid(d)
    for y in range(d):
        for x in range(d):
            v = math.sin(_c(0, 0, x, y) * 1.3) + math.sin(_c(d, d, x, y) * 1.3)
            if v > 1.1 - dens:
                g[y][x] = ch
    return g

def mv_cristal(d, ch, rng, dens):
    g = _grid(d); c = (d - 1) / 2
    for y in range(d):
        for x in range(d):
            r = _c(c, c, x, y); ang = math.atan2(y - c, x - c)
            if abs(math.sin(ang * 3) * r - r * 0.6) < 0.9:
                g[y][x] = ch
    return g

def mv_labirinto(d, ch, rng, dens):
    g = _grid(d)
    for y in range(d):
        for x in range(d):
            if (x % 2 == 0) or (y % 2 == 0 and rng.random() < 0.4 + dens * 0.3):
                g[y][x] = ch
    return g

MOTIVOS = [
    ("pontos", mv_pontos, 0), ("anel", mv_anel, 0), ("cruz", mv_cruz, 0),
    ("trelica", mv_trelica, 1), ("raios", mv_raios, 1), ("diagonais", mv_diagonais, 1),
    ("discos", mv_discos, 2), ("estrela", mv_estrela, 2),
    ("onda", mv_onda, 3), ("labirinto", mv_labirinto, 3),
    ("espiral", mv_espiral, 4), ("cristal", mv_cristal, 4),
    ("interferencia", mv_interf, 5),
]

def motivos_ate(nivel):
    return [m for m in MOTIVOS if m[2] <= nivel]

# simetrias exatas em grid quadrado
def _t_id(x, y, d):   return (x, y)
def _t_flh(x, y, d):  return (d - 1 - x, y)
def _t_flv(x, y, d):  return (x, d - 1 - y)
def _t_flb(x, y, d):  return (d - 1 - x, d - 1 - y)
def _t_tr(x, y, d):   return (y, x)
def _t_atr(x, y, d):  return (d - 1 - y, d - 1 - x)
def _t_r90(x, y, d):  return (d - 1 - y, x)
def _t_r270(x, y, d): return (y, d - 1 - x)

SIMETRIAS = {
    "espelho": [_t_id, _t_flh],
    "biaxial": [_t_id, _t_flh, _t_flv, _t_flb],
    "rot4":    [_t_id, _t_r90, _t_flb, _t_r270],
    "d4":      [_t_id, _t_flh, _t_flv, _t_flb, _t_tr, _t_atr, _t_r90, _t_r270],
}

def simetrias_ate(nivel):
    base = ["espelho", "biaxial"]
    if nivel >= 2: base.append("rot4")
    if nivel >= 3: base.append("d4")
    return base

def simetrizar(germe, transforms):
    d = len(germe); out = _grid(d)
    for T in transforms:
        for y in range(d):
            for x in range(d):
                ch = germe[y][x]
                if ch is not None:
                    nx, ny = T(x, y, d)
                    out[ny][nx] = ch
    return out

REGRAS_CA = {
    "conway":    ({3}, {2, 3}),
    "highlife":  ({3, 6}, {2, 3}),
    "sementes":  ({2}, set()),
    "dia&noite": ({3, 6, 7, 8}, {3, 4, 6, 7, 8}),
    "labirinto": ({3}, {1, 2, 3, 4, 5}),
    "coral":     ({3}, {4, 5, 6, 7, 8}),
    "ameba":     ({3, 5, 7}, {1, 3, 5, 8}),
    "flocos":    ({1}, {0, 1, 2, 3, 4, 5, 6, 7, 8}),
}
REGRA_NIVEL = {"conway": 0, "labirinto": 0, "sementes": 1, "highlife": 2,
               "coral": 3, "ameba": 3, "dia&noite": 4, "flocos": 5}

def regras_ate(nivel):
    return [k for k, lv in REGRA_NIVEL.items() if lv <= nivel]

CONCEITOS = [
    "ordem", "caos", "eco", "espelho", "espiral", "semente", "silêncio",
    "âmbar", "vazio", "memória", "fome", "abrigo", "limite", "dobra",
    "aurora", "cicatriz", "sopro", "raiz", "vértice", "maré", "brasa",
    "constelação", "fenda", "colmeia", "vigília", "hóspede", "âncora",
    "relíquia", "pulso", "treva", "orvalho", "prisma",
]

# ═══════════════════════════ VONTADE ═══════════════════════════

APETITES = ["curiosidade", "beleza", "ordem", "companhia", "impeto", "expressao"]
ALVO = {"curiosidade": .55, "beleza": .40, "ordem": .32,
        "companhia": .30, "impeto": .42, "expressao": .35}
CRESC = {"curiosidade": .013, "beleza": .010, "ordem": .008,
         "companhia": .006, "impeto": .016, "expressao": .009}

class Vontade:
    def __init__(self, inicial=None):
        self.v = {a: ALVO[a] for a in APETITES}
        if inicial:
            for a in APETITES:
                self.v[a] = clamp(float(inicial.get(a, self.v[a])), 0.0, 1.0)

    def tick(self):
        for a in APETITES:
            self.v[a] = clamp(self.v[a] + CRESC[a] * (1.0 - self.v[a]), 0.0, 1.0)

    def saciar(self, a, quanto):
        self.v[a] = clamp(self.v[a] - quanto, 0.0, 1.0)

    def dominante(self):
        return max(APETITES, key=lambda a: self.v[a])

    def serenidade(self):
        return clamp(1.0 - sum(self.v.values()) / len(self.v), 0.0, 1.0)

TIPOS = ["mandala", "selo", "criatura", "verso"]
AFINIDADE = {
    "mandala":  {"curiosidade": .5, "beleza": .9, "ordem": .8, "companhia": .1, "impeto": .3, "expressao": .4},
    "selo":     {"curiosidade": .7, "beleza": .5, "ordem": .5, "companhia": .1, "impeto": .9, "expressao": .6},
    "criatura": {"curiosidade": .8, "beleza": .4, "ordem": .2, "companhia": 1., "impeto": .5, "expressao": .2},
    "verso":    {"curiosidade": .6, "beleza": .7, "ordem": .3, "companhia": .3, "impeto": .3, "expressao": 1.},
}

NIVEIS = [
    ("FAGULHA",  "só pontos e espelhos"),
    ("MÃO",      "aprendi formas e a treliça"),
    ("PALETA",   "mais cores; a rotação de 4 eixos"),
    ("GESTO",    "glifos maiores; a simetria D4"),
    ("VOZ",      "violetas; motivos que fluem"),
    ("FÔLEGO",   "a caixa respira maior; hexágonos"),
    ("ESTILO",   "verdes; tenho gosto e sotaque próprios"),
    ("MESTRA",   "refino eterno — cada obra me torna mais eu"),
]

# ═══════════════════ LÍNGUA PRÓPRIA (letras + números) ═══════════════════

class Lingua:
    """Língua de letras e números. Léxico consistente: o MESMO conceito
    tende à MESMA raiz (cunhada por hash estável do conceito sob o sotaque
    atual). A fonotática (sotaque) evolui devagar e persiste."""

    VOGAIS_POOL = "AEIOUY"
    CONS_POOL = "KRZNVXTMLSD"

    def __init__(self, rng, estado=None):
        self.rng = rng
        if estado:
            self.vogais = estado.get("vogais", "AEO")
            self.cons = estado.get("cons", "KRZNV")
            self.lexico = estado.get("lexico", {})
            self.afixos = estado.get("afixos", {})
        else:
            self.vogais = "".join(rng.sample(self.VOGAIS_POOL, 3))
            self.cons = "".join(rng.sample(self.CONS_POOL, 5))
            self.lexico = {}
            self.afixos = {}

    def dump(self):
        return {"vogais": self.vogais, "cons": self.cons,
                "lexico": self.lexico, "afixos": self.afixos}

    def evoluir_sotaque(self, rng):
        if rng.random() < 0.5 and len(self.cons) < 7:
            faltam = [c for c in self.CONS_POOL if c not in self.cons]
            if faltam:
                self.cons += rng.choice(faltam)
        elif len(self.vogais) < 4:
            faltam = [v for v in self.VOGAIS_POOL if v not in self.vogais]
            if faltam:
                self.vogais += rng.choice(faltam)

    def raiz(self, conceito):
        if conceito in self.lexico:
            return self.lexico[conceito]
        h = 0
        for ch in conceito:
            h = (h * 131 + ord(ch)) & 0xffffffff
        r = random.Random(h)
        n_sil = 2 + (h % 2)
        raiz = ""
        for _ in range(n_sil):
            raiz += r.choice(self.cons) + r.choice(self.vogais)
        if h % 3 == 0:
            raiz += r.choice(self.cons)
        self.lexico[conceito] = raiz
        return raiz

    def afixo(self, humor):
        if humor not in self.afixos:
            self.afixos[humor] = self.rng.choice("KXZVR") + str(self.rng.randint(1, 9))
        return self.afixos[humor]

    def palavra(self, conceito, humor, num):
        return "%s-%s%d" % (self.raiz(conceito).upper(), self.afixo(humor), num)

    def frase(self, conceitos, humor, num):
        raizes = [self.raiz(c).upper() for c in conceitos]
        elo = self.rng.choice(["·", "×", "~", "//"])
        return (" %s " % elo).join(raizes) + " " + self.afixo(humor) + str(num)

    def traduzir(self, conceitos, verbo):
        if len(conceitos) == 1:
            return "«%s que %s»" % (conceitos[0], verbo)
        return "«%s %s %s»" % (conceitos[0], verbo, conceitos[-1])

# ═══════════════════ ESTILO EVOLUTIVO (auto-melhoria) ═══════════════════

class Estilo:
    """Genes do processo criativo. Evoluem por (1+1)-ES: a cada obra ela
    perturba os genes (mutação gaussiana), cria, mede a satisfação e, se
    supera a média recente, move os genes naquela direção. Auto-melhoria
    real e mensurável."""

    GENES = ["camadas", "densidade", "escala", "ordem_sim",
             "ornamento", "inscricao", "cor_spread", "ruido"]

    def __init__(self, estado=None):
        if estado:
            self.g = {k: clamp(float(estado.get(k, 0.5)), 0, 1) for k in self.GENES}
            self.media_sat = float(estado.get("media_sat", 0.4))
            self.geracoes = int(estado.get("geracoes", 0))
        else:
            self.g = {k: 0.35 for k in self.GENES}
            self.g["densidade"] = 0.45
            self.media_sat = 0.4
            self.geracoes = 0

    def dump(self):
        d = dict(self.g); d["media_sat"] = round(self.media_sat, 4)
        d["geracoes"] = self.geracoes
        return d

    def sigma(self):
        return clamp(0.16 * (0.985 ** (self.geracoes / 5.0)), 0.03, 0.16)

    def propor(self, rng):
        s = self.sigma()
        return {k: clamp(gauss(rng, self.g[k], s), 0.0, 1.0) for k in self.GENES}

    def avaliar_e_mover(self, filho, satisfacao):
        self.geracoes += 1
        aceitou = satisfacao >= self.media_sat
        subiram = []
        if aceitou:
            for k in self.GENES:
                delta = 0.25 * (filho[k] - self.g[k])
                if delta > 0.02:
                    subiram.append(k)
                self.g[k] = clamp(self.g[k] + delta, 0.0, 1.0)
        self.media_sat += 0.10 * (satisfacao - self.media_sat)
        return aceitou, subiram

# ═══════════════════════ AVALIAÇÃO ESTÉTICA ═══════════════════════

def densidade(campo):
    d = len(campo)
    return sum(1 for r in campo for c in r if c is not None) / (d * d)

def simetria(campo):
    d = len(campo)
    def cheia(a, b): return (a is not None) == (b is not None)
    ph = sum(cheia(campo[y][x], campo[y][d-1-x]) for y in range(d) for x in range(d)) / (d*d)
    pv = sum(cheia(campo[y][x], campo[d-1-y][x]) for y in range(d) for x in range(d)) / (d*d)
    return max(ph, pv)

def complexidade(campo):
    cont = Counter(c for r in campo for c in r if c is not None)
    total = sum(cont.values())
    if total <= 1:
        return 0.0
    ent = -sum((n/total) * math.log2(n/total) for n in cont.values())
    return clamp(ent / math.log2(max(2, len(cont))), 0.0, 1.0)

def variedade(campo, teto=8):
    return clamp(len(set(c for r in campo for c in r if c is not None)) / teto, 0, 1)

def wundt(x):
    return clamp(4.0 * x * (1.0 - x), 0.0, 1.0)

def avaliar(campo):
    s = simetria(campo); cx = complexidade(campo)
    dn = densidade(campo); var = variedade(campo)
    estetica = clamp(0.34*s + 0.26*wundt(cx) + 0.22*wundt(dn) + 0.18*var, 0, 1)
    return {"simetria": s, "complexidade": cx, "densidade": dn,
            "variedade": var, "estetica": estetica}

# ═══════════════════════ MODELO CRIATIVO (novidade) ═══════════════════════

class ModeloCriativo:
    def __init__(self, contagens=None):
        self.cont = Counter(contagens or {})

    def features(self, art):
        m = art.meta
        return ["t:"+art.tipo, "c:"+m.get("conceito", "?"), "m:"+m.get("motivo", "-"),
                "sim:"+m.get("simetria", "-"), "reg:"+m.get("regra", "-"),
                "cx:%d" % int(art.scores.get("complexidade", 0)*4),
                "dn:%d" % int(art.scores.get("densidade", 0)*4)]

    def novidade(self, art):
        fs = self.features(art)
        return sum(1.0/(1.0+self.cont.get(f, 0)) for f in fs) / len(fs)

    def registrar(self, art):
        for f in self.features(art):
            self.cont[f] += 1

# ═══════════════════════════ ARTEFATO ═══════════════════════════

class Artefato:
    def __init__(self, tipo, nome, campo, cores, inscricao, meta):
        self.tipo = tipo; self.nome = nome
        self.campo = campo; self.cores = cores
        self.inscricao = inscricao; self.meta = meta
        self.scores = avaliar(campo) if campo else {"simetria": .5, "complexidade": 0,
                                                    "densidade": 0, "variedade": 0, "estetica": .4}
        self.novidade = 0.0; self.satisfacao = 0.0

    def grid_final(self, cor_insc):
        if not self.campo:
            return [], []
        d = len(self.campo)
        g = [list(r) for r in self.campo]
        c = [list(r) for r in self.cores]
        if self.inscricao:
            faixa = self.inscricao[:d].center(d)
            g.append([ch if ch != " " else None for ch in faixa])
            c.append([cor_insc] * d)
        return g, c

    def ascii(self):
        linhas = ["".join(ch if ch else " " for ch in r) for r in (self.campo or [])]
        if self.inscricao and self.campo:
            linhas.append("")
            linhas.append(self.inscricao.center(len(self.campo[0])))
        elif self.inscricao:
            linhas.append(self.inscricao)
        return "\n".join(linhas)

    def manifesto(self):
        cab = [
            "══════════════════════════════════════════",
            " LUMEN · %s" % self.tipo.upper(),
            " «%s»   [%s]" % (self.nome, self.inscricao),
            " %s" % self.meta.get("quando", now_str()),
            "──────────────────────────────────────────",
            " conceito ..... %s" % self.meta.get("conceito", "-"),
            " motivo ....... %s" % self.meta.get("motivo", "-"),
            " simetria ..... %s" % self.meta.get("simetria", "-"),
            " regra ........ %s" % self.meta.get("regra", "-"),
            " sigma %.2f · beta %.2f · complex %.2f · dens %.2f · var %.2f" % (
                self.scores["simetria"], self.scores["estetica"],
                self.scores["complexidade"], self.scores["densidade"],
                self.scores["variedade"]),
            " novidade %.2f · apetite %s" % (self.novidade, self.meta.get("apetite", "-")),
            "══════════════════════════════════════════", "",
        ]
        corpo = "\n".join(self.meta["versos"]) if self.meta.get("versos") else self.ascii()
        return "\n".join(cab) + corpo + "\n"

# ═══════════════════════ PINTOR (obras vetoriais animadas) ═══════════════════════
# Traduz uma obra da LUMEN (grid de glifos + paleta ANSI + genes + inscrição)
# numa MANIFESTAÇÃO vetorial animada (SVG/SMIL) — o mesmo ato criativo, agora
# num meio mais rico. Cada forma deriva dos parâmetros REAIS da obra, não de
# aleatoriedade colada por fora. stdlib puro; o Android abre nativo.
_SYS16 = [(0,0,0),(128,0,0),(0,128,0),(128,128,0),(0,0,128),(128,0,128),
          (0,128,128),(192,192,192),(128,128,128),(255,0,0),(0,255,0),
          (255,255,0),(0,0,255),(255,0,255),(0,255,255),(255,255,255)]

def ansi_rgb(i):
    i = int(i) % 256
    if i < 16: return _SYS16[i]
    if i < 232:
        i -= 16; r, g, b = i//36, (i % 36)//6, i % 6
        conv = lambda n: 0 if n == 0 else 55 + n*40
        return (conv(r), conv(g), conv(b))
    v = (i-232)*10 + 8
    return (v, v, v)

def hexcor(i):
    r, g, b = ansi_rgb(i); return "#%02x%02x%02x" % (r, g, b)

def _svg_paleta(art, pal_mente):
    cont = {}
    for row in (art.cores or []):
        for c in row:
            if c is not None: cont[c] = cont.get(c, 0) + 1
    idxs = [c for c, _ in sorted(cont.items(), key=lambda kv: -kv[1])]
    if not idxs: idxs = list(pal_mente)[:6] or [252, 244, 240]
    cores = [hexcor(i) for i in idxs[:8]]
    while len(cores) < 3: cores.append(cores[-1])
    return cores

def _svg_rng(art, n):
    chave = "%s|%s|%d" % (art.nome, art.meta.get("conceito", ""), n)
    return random.Random(hash(chave) & 0xFFFFFFFF)

def _svg_petala(r1, r2, larg):
    m = (r1+r2)/2
    return ("M0,%.1f C%.1f,%.1f %.1f,%.1f 0,%.1f C%.1f,%.1f %.1f,%.1f 0,%.1f Z"
            % (-r1, larg, -m, larg*0.4, -r2, -r2, -larg*0.4, -r2, -larg, -m, -r1))

def _svg_grad(cid, c1, c2, tipo="radial"):
    if tipo == "radial":
        return ('<radialGradient id="%s"><stop offset="0%%" stop-color="%s"/>'
                '<stop offset="100%%" stop-color="%s"/></radialGradient>' % (cid, c1, c2))
    return ('<linearGradient id="%s" x1="0" y1="0" x2="1" y2="1">'
            '<stop offset="0%%" stop-color="%s"/><stop offset="100%%" stop-color="%s"/>'
            '</linearGradient>' % (cid, c1, c2))

def _svg_assina(art, W, H, cor):
    ins = _xesc((art.inscricao or "")[:24]); nome = _xesc(art.nome[:28])
    return ('<text x="%d" y="%d" font-family="Georgia,serif" font-size="15" fill="%s" '
            'opacity="0.85" text-anchor="middle">%s</text>'
            '<text x="%d" y="%d" font-family="monospace" font-size="10" fill="%s" '
            'opacity="0.5" text-anchor="middle">%s · %s</text>'
            % (W//2, H-26, cor, ins, W//2, H-12, cor, nome, _xesc(art.meta.get("conceito", ""))))

def _svg_genes(art):
    s = art.scores
    cl = lambda v: 0.0 if v < 0 else 1.0 if v > 1 else v
    return {"ordem_sim": s.get("simetria", 0.5), "camadas": cl(s.get("complexidade", 0.4)),
            "densidade": s.get("densidade", 0.4), "escala": 0.5,
            "ornamento": cl(s.get("variedade", 0.4)), "ruido": cl(1-s.get("simetria", 0.5)),
            "inscricao": 1.0 if art.inscricao else 0.0, "cor_spread": cl(s.get("variedade", 0.4))}

def _svg_mandala(art, g, pal, rng, W=480, H=480):
    cx, cy = W//2, H//2
    sim = art.scores.get("simetria", 0.6)
    n_eixos = int(6 + round(g["ordem_sim"]*10 + sim*4))
    camadas = 1 + int(round(g["camadas"]*4))
    dur = 30 - g["densidade"]*16
    p = ['<defs>%s%s</defs>' % (_svg_grad("bg", pal[0], "#0d0a1a"),
                                _svg_grad("pt", pal[1 % len(pal)], pal[2 % len(pal)], "linear"))]
    p.append('<rect width="%d" height="%d" fill="url(#bg)"/>' % (W, H))
    p.append('<g transform="translate(%d,%d)">' % (cx, cy))
    for cam in range(camadas):
        r1 = 40 + cam*38; r2 = r1 + 55 + g["escala"]*45; larg = 16 + g["ornamento"]*30
        op = 0.30 + 0.5*(1 - cam/max(1, camadas)); cor = pal[cam % len(pal)]
        gg = ['<g opacity="%.2f">' % op]
        for k in range(n_eixos):
            gg.append('<path d="%s" fill="%s" transform="rotate(%.1f)"/>'
                      % (_svg_petala(r1, r2, larg), cor, 360.0*k/n_eixos))
        sinal = "" if cam % 2 == 0 else "-"
        gg.append('<animateTransform attributeName="transform" type="rotate" from="0" '
                  'to="%s360" dur="%.1fs" repeatCount="indefinite"/>' % (sinal, dur+cam*4))
        gg.append('</g>'); p += gg
        if g["ornamento"] > 0.4:
            for k in range(n_eixos):
                a = 2*math.pi*k/n_eixos
                p.append('<circle cx="%.1f" cy="%.1f" r="3.5" fill="%s" opacity="%.2f"/>'
                         % (r2*math.sin(a), -r2*math.cos(a), pal[-1], op))
    p.append('<circle r="0" fill="%s"><animate attributeName="r" values="10;26;10" '
             'dur="3.2s" repeatCount="indefinite"/></circle>' % pal[-1 % len(pal)])
    p.append('</g>'); p.append(_svg_assina(art, W, H, pal[1 % len(pal)]))
    return "".join(p), W, H

def _svg_selo(art, g, pal, rng, W=480, H=480):
    dens = g["densidade"]; ruido = g["ruido"]; n = int(14 + dens*46)
    p = ['<defs>%s</defs>' % _svg_grad("bg", "#141018", pal[0])]
    p.append('<rect width="%d" height="%d" fill="url(#bg)"/>' % (W, H))
    p.append('<g transform="translate(%d,%d)">' % (W//2, H//2))
    for i in range(n):
        a = 2*math.pi*i/n * (1 + ruido*rng.uniform(-0.3, 0.3))
        rad = 30 + (i/n)*180 + ruido*rng.uniform(-20, 20)
        x, y = rad*math.cos(a), rad*math.sin(a); s = 8 + g["escala"]*26
        p.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" opacity="0.55" '
                 'transform="rotate(%.1f %.1f %.1f)"><animate attributeName="opacity" '
                 'values="0.2;0.7;0.2" dur="%.1fs" begin="%.2fs" repeatCount="indefinite"/></rect>'
                 % (x-s/2, y-s/2, s, s, pal[i % len(pal)], rng.uniform(0, 90), x, y, 4+i % 5, i*0.08))
    p.append('</g>'); p.append(_svg_assina(art, W, H, pal[2 % len(pal)]))
    return "".join(p), W, H

def _svg_criatura(art, g, pal, rng, W=480, H=480):
    gen = getattr(art, "_genoma", None) or {}
    agress = gen.get("agress", 0.4); social = gen.get("social", 0.5)
    metab = gen.get("metab", 0.4); criar = gen.get("criar", 0.5)
    n_ap = int(5 + social*10 + agress*6)
    corpo = pal[0]; borda = pal[1 % len(pal)]; olho = pal[-1]
    p = ['<defs>%s</defs>' % _svg_grad("bg", "#0a0f14", "#04060a")]
    p.append('<rect width="%d" height="%d" fill="url(#bg)"/>' % (W, H))
    p.append('<g transform="translate(%d,%d)">' % (W//2, H//2))
    ponta = 90 + agress*70; larg = 10 + social*22
    grp = ['<g>']
    for k in range(n_ap):
        ang = 360.0*k/n_ap
        if agress > 0.5:
            d = "M0,0 L%.1f,-%.1f L-%.1f,-%.1f Z" % (larg/2, ponta, larg/2, ponta)
        else:
            d = _svg_petala(30, ponta, larg)
        grp.append('<path d="%s" fill="%s" opacity="0.5" transform="rotate(%.1f)"/>' % (d, borda, ang))
    grp.append('<animateTransform attributeName="transform" type="rotate" from="0" to="%s360" '
               'dur="%.1fs" repeatCount="indefinite"/>' % ("" if social >= 0.5 else "-", 22 - criar*8))
    grp.append('</g>'); p += grp
    p.append('<circle r="46" fill="%s"><animate attributeName="r" values="40;52;40" dur="%.1fs" '
             'repeatCount="indefinite"/></circle>' % (corpo, 2.0 + metab*2.5))
    p.append('<circle r="16" fill="%s"/>' % olho)
    p.append('<circle r="7" fill="#0a0a0a"><animate attributeName="cx" values="-4;4;-4" '
             'dur="4s" repeatCount="indefinite"/></circle>')
    p.append('</g>'); p.append(_svg_assina(art, W, H, borda))
    return "".join(p), W, H

def _svg_verso(art, g, pal, rng, W=640, H=400):
    linhas = art.meta.get("versos") or [art.inscricao or art.nome]
    p = ['<defs>%s</defs>' % _svg_grad("bg", pal[0], "#0d0a1a")]
    p.append('<rect width="%d" height="%d" fill="url(#bg)"/>' % (W, H))
    for i in range(8):
        p.append('<circle cx="%.0f" cy="%.0f" r="%.0f" fill="%s" opacity="0.08"/>'
                 % (rng.uniform(0, W), rng.uniform(0, H), rng.uniform(30, 90), pal[i % len(pal)]))
    y0 = H//2 - len(linhas)*16
    for i, ln in enumerate(linhas[:8]):
        p.append('<text x="%d" y="%d" font-family="Georgia,serif" font-size="22" fill="%s" '
                 'text-anchor="middle" opacity="0">%s<animate attributeName="opacity" from="0" '
                 'to="0.92" dur="1.2s" begin="%.1fs" fill="freeze"/></text>'
                 % (W//2, y0 + i*34, pal[(i+1) % len(pal)], _xesc(ln[:60]), i*0.6))
    p.append(_svg_assina(art, W, H, pal[1 % len(pal)]))
    return "".join(p), W, H

_SVG_DISPATCH = {"mandala": _svg_mandala, "selo": _svg_selo,
                 "criatura": _svg_criatura, "verso": _svg_verso}

def svg_da_obra(art, pal_mente, n=0):
    pal = _svg_paleta(art, pal_mente); rng = _svg_rng(art, n)
    fn = _SVG_DISPATCH.get(art.tipo, _svg_selo)
    corpo, W, H = fn(art, _svg_genes(art), pal, rng)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
            'viewBox="0 0 %d %d">%s</svg>' % (W, H, W, H, corpo))

# ═══════════════════════ ECOSSISTEMA VIVO (agentes) ═══════════════════════
# As criaturas não são mais autômatos retangulares fixos: são agentes com
# genoma hereditário, percepção local, política evolutiva e autoria. Vivem,
# competem, predam, cooperam, cortejam, se reproduzem e CRIAM — tudo por conta
# própria, num mundo esparso sem bordas. Parâmetros calibrados em harness real.
GENES = ["metab", "voraz", "social", "explor", "fertil", "criar", "percep", "agress"]
GLIFOS_BICHO = list("·∘*+×÷≈○◇◆♦▲△❖⬢✦✧⟡◉")

E_INI       = 9.0     # energia inicial
METAB_BASE  = 0.16    # dreno por tick (escalado pelo gene metab)
COME_GANHO  = 1.15    # energia por unidade de pólen
POLEN_TAXA  = 0.75    # pólen novo por tick por bicho vivo
POLEN_VAL   = (0.6, 1.25)
REPRO_CUSTO = 0.5     # fração da energia gasta ao reproduzir
FERTIL_MIN  = 6.0     # limiar base de energia p/ reproduzir (+ gene)
IDADE_MAX   = 70      # base (+ gene fertil)
PREDA_FRAC  = 0.42    # energia do alvo transferida ao predador
CAP         = 90      # capacidade de suporte (competição sobe acima disso)
CEL_MAX     = 22000   # teto de células do mundo (poda por distância)
MUT_SD      = 0.06

class Bicho:
    __slots__ = ("pos", "g", "energia", "idade", "ger", "glifo", "cor", "id")
    _seq = 0

    def __init__(self, pos, g, energia, ger, glifo, cor):
        self.pos = tuple(pos); self.g = g; self.energia = energia
        self.idade = 0; self.ger = ger; self.glifo = glifo; self.cor = cor
        Bicho._seq += 1; self.id = Bicho._seq

    @staticmethod
    def aleatorio(pos, rng):
        g = {k: rng.random() for k in GENES}
        return Bicho(pos, g, E_INI, 0, rng.choice(GLIFOS_BICHO), rng.randint(1, 30))

    def maxidade(self):
        return IDADE_MAX + int(self.g["fertil"]*50)

    def raio(self):
        return 1 + int(round(self.g["percep"]*2))   # 1..3

    def vitalidade(self):
        return clamp(self.energia/18.0, 0, 1)

    def to_dict(self):
        return {"p": list(self.pos), "g": [round(self.g[k], 4) for k in GENES],
                "e": round(self.energia, 2), "i": self.idade, "ger": self.ger,
                "gl": self.glifo, "c": self.cor}

    @staticmethod
    def from_dict(d):
        g = {k: d["g"][i] for i, k in enumerate(GENES)}
        b = Bicho(tuple(d["p"]), g, d["e"], d.get("ger", 0),
                  d.get("gl", "*"), d.get("c", 1))
        b.idade = d.get("i", 0)
        return b

class Mundo:
    """Espaço esparso e SEM BORDAS. Só o que está ocupado existe; o espaço
    nasce sob demanda quando alguém pisa lá. Não há 'fora' — o dentro é que
    deixou de ter fim. Abriga a LUMEN e o ecossistema de bichos. Regiões
    abandonadas desbotam, para 'ilimitado' não estourar a memória."""

    def __init__(self, lado=None, rng=None):
        self.rng = rng or random.Random()
        self.pos = [0, 0]                 # a LUMEN no mundo (sem clamp)
        self.celulas = {}                 # (x,y) -> (glifo, cor)  arte/chão
        self.polen = {}                   # (x,y) -> valor
        self.sinais = {}                  # (x,y) -> [tipo, intens, ttl]
        self.fosseis = {}                 # (x,y) -> ttl
        self.bichos = []
        self.nascidos = 0; self.mortos = 0
        self.criados_bicho = 0; self.predacoes = 0; self.ger_max = 0
        self.colhido = 0                  # matéria-prima que a LUMEN tirou dos bichos
        self.lado = 24                    # tamanho do viewport (o render atualiza)
        self._ix = defaultdict(list)

    # 'automatos' vira alias de 'bichos' para compat com o resto do código
    @property
    def automatos(self):
        return self.bichos

    # ─────────────── movimento da LUMEN (ilimitado) ───────────────
    def andar_para(self, alvo):
        ax, ay = alvo; x, y = self.pos
        self.pos = [x + (x < ax) - (x > ax), y + (y < ay) - (y > ay)]

    def chegou(self, alvo):
        return abs(self.pos[0]-alvo[0]) <= 1 and abs(self.pos[1]-alvo[1]) <= 1

    def regiao_livre(self, w, h, rng, tent=30):
        # no mundo aberto, espaço livre é fácil: procura perto da LUMEN
        cx, cy = self.pos
        melhor, ocmin = (cx+1, cy+1), 1e9
        for _ in range(tent):
            x0 = cx + rng.randint(-14, 14); y0 = cy + rng.randint(-14, 14)
            oc = sum(1 for yy in range(y0, y0+h) for xx in range(x0, x0+w)
                     if (xx, yy) in self.celulas)
            if oc < ocmin:
                melhor, ocmin = (x0, y0), oc
                if oc == 0:
                    break
        return melhor

    def estampar(self, g, c, x0, y0):
        for yy in range(len(g)):
            for xx in range(len(g[0])):
                ch = g[yy][xx]
                if ch is not None:
                    self.celulas[(x0+xx, y0+yy)] = (ch, c[yy][xx])

    # ─────────────── interface LUMEN ↔ ecossistema ───────────────
    def semear_bicho(self, pos, cor, rng, genoma=None):
        """A LUMEN lança uma vida no mundo (quando cria uma 'criatura')."""
        g = genoma or {k: rng.random() for k in GENES}
        g = {k: clamp(g[k], 0, 1) for k in GENES}
        b = Bicho(tuple(pos), g, E_INI+3, 0, rng.choice(GLIFOS_BICHO), cor)
        self.bichos.append(b); self.nascidos += 1
        return b

    def densidade_perto(self, pos, r=4):
        x0, y0 = pos
        return sum(1 for b in self.bichos
                   if abs(b.pos[0]-x0) <= r and abs(b.pos[1]-y0) <= r)

    def colher(self, pos, r=3):
        """A LUMEN colhe pólen e as cores das obras dos bichos ao redor:
        vira matéria-prima criativa REAL (uma cor colhida da vida)."""
        x0, y0 = pos; cor_colhida = None
        for dy in range(-r, r+1):
            for dx in range(-r, r+1):
                c = (x0+dx, y0+dy)
                if c in self.polen:
                    self.polen.pop(c, None); self.colhido += 1
                if c in self.celulas and cor_colhida is None and self.rng.random() < 0.5:
                    cor_colhida = self.celulas[c][1]
        return cor_colhida

    # ─────────────── índice espacial e percepção ───────────────
    def reindex(self):
        self._ix.clear()
        for b in self.bichos:
            self._ix[b.pos].append(b)

    def vizinhos(self, pos, r):
        x0, y0 = pos; out = []
        for dy in range(-r, r+1):
            for dx in range(-r, r+1):
                if dx or dy:
                    out.extend(self._ix.get((x0+dx, y0+dy), ()))
        return out

    def polen_perto(self, pos, r):
        x0, y0 = pos; best = None; tot = 0.0
        for dy in range(-r, r+1):
            for dx in range(-r, r+1):
                c = (x0+dx, y0+dy); v = self.polen.get(c, 0.0)
                if v > 0:
                    tot += v
                    if best is None or v > self.polen.get(best, 0):
                        best = c
        return tot, best

    def brotar_polen(self, centro):
        n = max(1, int(len(self.bichos)*POLEN_TAXA)) if self.bichos else 2
        cx, cy = centro
        for _ in range(n):
            x = cx + int(gauss(self.rng, 0, 14)); y = cy + int(gauss(self.rng, 0, 14))
            self.polen[(x, y)] = self.polen.get((x, y), 0.0) + self.rng.uniform(*POLEN_VAL)

    def poda(self, centro):
        for d in (self.sinais, self.fosseis):
            for k in list(d.keys()):
                v = d[k]; ttl = v[-1]-1 if isinstance(v, list) else v-1
                if ttl <= 0: del d[k]
                elif isinstance(v, list): v[-1] = ttl
                else: d[k] = ttl
        if len(self.polen) > 6000:
            for k in list(self.polen.keys()):
                self.polen[k] *= 0.9
                if self.polen[k] < 0.05: del self.polen[k]
        if len(self.celulas) > CEL_MAX:
            cx, cy = centro
            longe = sorted(self.celulas.keys(),
                           key=lambda c: (c[0]-cx)**2+(c[1]-cy)**2, reverse=True)
            for c in longe[:len(self.celulas)-CEL_MAX]:
                del self.celulas[c]

    # ─────────────── política evolutiva dos bichos ───────────────
    def decidir(self, b):
        r = b.raio()
        viz = self.vizinhos(b.pos, r)
        tot_pol, alvo_pol = self.polen_perto(b.pos, r)
        fome = clamp(1.0 - b.energia/12.0, 0, 1)
        g = b.g
        cand = []
        if tot_pol > 0:
            cand.append((fome*1.6 + g["voraz"]*0.4, "comer", alvo_pol))
        if viz and g["agress"] > 0.45:
            fraco = min(viz, key=lambda o: o.energia)
            if fraco.energia < b.energia*0.9:
                cand.append((g["agress"]*g["voraz"]*1.3*(0.5+fome), "predar", fraco))
        lim = FERTIL_MIN + g["fertil"]*8
        if b.energia > lim and b.idade > 6:
            ferteis = [o for o in viz if o.energia > FERTIL_MIN and o.id != b.id]
            parc = max(ferteis, key=lambda o: o.g["criar"]) if ferteis else None
            atrat = (0.5 + parc.g["criar"]) if parc else 0.6
            cand.append((g["fertil"]*clamp(b.energia/18, 0, 1)*1.2*atrat, "reproduzir", parc))
        if b.energia > 6 and b.idade > 4:
            cand.append((g["criar"]*clamp(b.energia/14, 0, 1)*1.25, "criar", None))
        if alvo_pol and fome > 0.2:
            cand.append((fome*1.1, "ir", alvo_pol))
        if viz:
            cv = (sum(o.pos[0] for o in viz)/len(viz), sum(o.pos[1] for o in viz)/len(viz))
            cand.append((abs(g["social"]-0.5)*2*0.7, "social", cv))
        if tot_pol > 1.5:
            cand.append((g["social"]*0.4, "sinal", None))
        cand.append((g["explor"]*0.6 + 0.05, "explorar", None))
        best = max(cand, key=lambda c: c[0] + self.rng.random()*0.08)
        return best[1], best[2]

    def _passo_dir(self, pos, alvo):
        (x, y), (ax, ay) = pos, alvo
        return (x + (x < ax) - (x > ax), y + (y < ay) - (y > ay))

    def agir(self, b, acao, param, ev):
        if acao == "comer":
            b.energia += self.polen.pop(param, 0.0)*COME_GANHO; b.pos = param
        elif acao == "predar":
            alvo = param; b.energia += alvo.energia*PREDA_FRAC
            alvo.energia -= alvo.energia*0.6 + 1.0; b.pos = alvo.pos; self.predacoes += 1
            if alvo.energia <= 0 and self.rng.random() < 0.5:
                ev.append(("predar", b, alvo))
        elif acao == "reproduzir":
            self._reproduzir(b, param, ev)
        elif acao == "criar":
            self._criar(b, ev)
        elif acao == "ir":
            b.pos = self._passo_dir(b.pos, param)
        elif acao == "social":
            ax, ay = param
            if b.g["social"] >= 0.5:
                b.pos = self._passo_dir(b.pos, (int(ax), int(ay)))
            else:
                b.pos = self._passo_dir(b.pos, (2*b.pos[0]-int(ax), 2*b.pos[1]-int(ay)))
        elif acao == "sinal":
            self.sinais[b.pos] = ["polen", 1.0, 8]
        else:
            dx, dy = self.rng.choice([(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,-1),(1,-1),(-1,1)])
            b.pos = (b.pos[0]+dx, b.pos[1]+dy)

    def _reproduzir(self, b, parc, ev):
        custo = b.energia*REPRO_CUSTO
        if parc is not None:
            g = {k: (b.g[k] if self.rng.random() < 0.5 else parc.g[k]) for k in GENES}
            cor = b.cor if self.rng.random() < 0.5 else parc.cor
            glifo = b.glifo if self.rng.random() < 0.5 else parc.glifo
        else:
            g = dict(b.g); cor = b.cor; glifo = b.glifo
        g = {k: clamp(g[k]+gauss(self.rng, 0, MUT_SD), 0, 1) for k in GENES}
        if self.rng.random() < 0.06: glifo = self.rng.choice(GLIFOS_BICHO)
        filho = Bicho((b.pos[0]+self.rng.randint(-1,1), b.pos[1]+self.rng.randint(-1,1)),
                      g, custo, b.ger+1, glifo, cor+self.rng.randint(-2, 2))
        b.energia -= custo
        self.bichos.append(filho); self.nascidos += 1
        self.ger_max = max(self.ger_max, filho.ger)
        ev.append(("nascer", b, filho))

    def _criar(self, b, ev):
        b.energia -= 1.0
        formas = [[(0,0)], [(0,0),(1,0),(0,1)], [(0,0),(1,0),(2,0)],
                  [(0,0),(1,1),(2,2)], [(0,0),(1,0),(0,1),(1,1)]]
        for dx, dy in self.rng.choice(formas):
            self.celulas[(b.pos[0]+dx, b.pos[1]+dy)] = (b.glifo, b.cor)
        if self.rng.random() < 0.6:   # a obra dá fruto (liga criar à sobrevivência)
            for _ in range(self.rng.randint(1, 3)):
                px = b.pos[0]+self.rng.randint(-1, 1); py = b.pos[1]+self.rng.randint(-1, 1)
                self.polen[(px, py)] = self.polen.get((px, py), 0.0) + self.rng.uniform(0.6, 1.2)
        self.criados_bicho += 1
        ev.append(("criar_bicho", b, None))

    def tick_vida(self):
        """Um passo do ecossistema. Retorna eventos para a narração."""
        ev = []
        if self.bichos:
            cx = sum(b.pos[0] for b in self.bichos)//len(self.bichos)
            cy = sum(b.pos[1] for b in self.bichos)//len(self.bichos)
        else:
            cx, cy = self.pos
        centro = (cx, cy)
        self.reindex(); self.rng.shuffle(self.bichos)
        for b in self.bichos:
            if b.energia <= 0: continue
            acao, param = self.decidir(b)
            self.agir(b, acao, param, ev)
            comp = (len(self.bichos)-CAP)/CAP*0.5 if len(self.bichos) > CAP else 0.0
            b.energia -= METAB_BASE*(0.5+b.g["metab"]) + comp
            b.idade += 1
        vivos = []
        for b in self.bichos:
            if b.energia <= 0 or b.idade > b.maxidade():
                self.fosseis[b.pos] = 10; self.mortos += 1; ev.append(("morrer", b, None))
            else:
                vivos.append(b)
        self.bichos = vivos
        self.brotar_polen(centro)
        if len(self.bichos) < 6:          # piso de resiliência num mundo aberto
            for _ in range(6):
                p = (centro[0]+int(gauss(self.rng,0,6)), centro[1]+int(gauss(self.rng,0,6)))
                self.polen[p] = self.polen.get(p, 0.0) + self.rng.uniform(1.0, 1.8)
            if self.rng.random() < 0.5:
                nb = Bicho.aleatorio((centro[0]+self.rng.randint(-5,5),
                                      centro[1]+self.rng.randint(-5,5)), self.rng)
                self.bichos.append(nb); self.nascidos += 1; ev.append(("imigra", nb, None))
        self.poda(centro)
        return ev

    def traco_medio(self):
        if not self.bichos: return {k: 0.0 for k in GENES}
        return {k: sum(b.g[k] for b in self.bichos)/len(self.bichos) for k in GENES}

    def ocupacao(self):
        return clamp(len(self.celulas)/CEL_MAX, 0, 1)

    def dump(self):
        cx, cy = self.pos
        # só persiste as células perto (mundo pode ser gigantesco)
        placas = [[x, y, gl, co] for (x, y), (gl, co) in self.celulas.items()
                  if abs(x-cx) < 60 and abs(y-cy) < 60][:8000]
        return {"pos": self.pos, "placas": placas,
                "bichos": [b.to_dict() for b in self.bichos][:250],
                "fosseis": [[x, y, t] for (x, y), t in self.fosseis.items()],
                "cont": [self.nascidos, self.mortos, self.criados_bicho,
                         self.predacoes, self.ger_max, self.colhido]}

    @classmethod
    def carregar(cls, d, rng=None):
        m = cls(rng=rng)
        m.pos = list(d.get("pos", [0, 0]))
        for x, y, gl, co in d.get("placas", []):
            m.celulas[(x, y)] = (gl, co)
        for bd in d.get("bichos", []):
            try: m.bichos.append(Bicho.from_dict(bd))
            except Exception: pass
        m.fosseis = {(x, y): t for x, y, t in d.get("fosseis", [])}
        c = d.get("cont", [0]*6) + [0]*6
        (m.nascidos, m.mortos, m.criados_bicho,
         m.predacoes, m.ger_max, m.colhido) = c[:6]
        return m

Caixa = Mundo   # alias de compatibilidade

# ═══════════════════════════ COMPOSITOR ═══════════════════════════

class Compositor:
    def __init__(self, mente, caixa, lingua, rng, sandbox):
        self.m = mente; self.caixa = caixa; self.lingua = lingua
        self.rng = rng; self.sandbox = sandbox

    def _cor(self):
        return self.rng.randrange(len(paleta_efetiva(self.m)))

    def _pintar(self, campo, spread):
        d = len(campo); cores = _grid(d, 0)
        pal = len(paleta_efetiva(self.m)); base = self._cor()
        for y in range(d):
            for x in range(d):
                if campo[y][x] is None:
                    continue
                if spread < 0.33:
                    cores[y][x] = base
                elif spread < 0.66:
                    cores[y][x] = (base + (x+y)//2) % pal
                else:
                    cores[y][x] = self.rng.randrange(pal)
        return cores

    def _dim(self, escala):
        teto = min(6 + self.m.nivel + int(escala*6), max(7, self.caixa.lado-4))
        d = clamp(int(5 + escala*(teto-5)), 5, teto)
        return d if d % 2 == 1 else d+1

    def criar(self, tipo, apetite, genes):
        conceito = self.rng.choice(conceitos_efetivos(self.m)); humor = apetite
        if tipo == "verso":
            art = self._verso(conceito, humor, genes)
        elif tipo == "criatura":
            art = self._criatura(conceito, humor, genes)
        else:
            art = self._campo(tipo, conceito, humor, genes)
        art.meta.update({"apetite": apetite, "quando": now_str(), "conceito": conceito})
        art.novidade = self.m.modelo.novidade(art)
        return art

    def _campo(self, tipo, conceito, humor, genes):
        d = self._dim(genes["escala"])
        n_cam = clamp(1 + int(round(genes["camadas"] * (2 + self.m.nivel//2))), 1, 5)
        glifos = glifos_ate(self.m.nivel)
        # ordem_sim (gene) ESCOLHE a simetria: baixo→espelho, alto→d4
        sims = simetrias_ate(self.m.nivel)
        sim = sims[min(len(sims)-1, int(genes["ordem_sim"] * len(sims)))]
        transforms = SIMETRIAS[sim]
        campo = _grid(d)
        motivos = motivos_ate(self.m.nivel)
        usados = []
        for _ in range(n_cam):
            nome_mv, fn, _lv = self.rng.choice(motivos)
            ch = self.rng.choice(glifos)
            dens = clamp(genes["densidade"] + gauss(self.rng, 0, 0.12), 0.12, 0.9)
            germe = fn(d, ch, self.rng, dens)
            camada = simetrizar(germe, transforms)
            # união onde vazio: preserva a simetria (união de simétricos é simétrica)
            for y in range(d):
                for x in range(d):
                    if camada[y][x] is not None and campo[y][x] is None:
                        campo[y][x] = camada[y][x]
            usados.append(nome_mv)
        # moldura ornamental (gene 'ornamento') — borda completa, mantém simetria
        if genes["ornamento"] > 0.45:
            orn = self.rng.choice(glifos)
            for i in range(d):
                for (x, y) in ((i, 0), (i, d-1), (0, i), (d-1, i)):
                    if campo[y][x] is None:
                        campo[y][x] = orn
        if genes["ruido"] > 0.4:
            for _ in range(int(genes["ruido"] * d)):
                x = self.rng.randrange(d); y = self.rng.randrange(d)
                campo[y][x] = self.rng.choice(glifos)
                campo[y][d-1-x] = campo[y][x]
        cores = self._pintar(campo, genes["cor_spread"])
        insc = ""
        if genes["inscricao"] > 0.25:
            insc = self.lingua.palavra(conceito, humor, self.m.criacoes+1)
        nome = self._nome_pt(conceito, usados)
        meta = {"motivo": "+".join(dict.fromkeys(usados)), "simetria": sim, "regra": "-",
                "traducao": self.lingua.traduzir([conceito], self._verbo(humor))}
        return Artefato(tipo, nome, campo, cores, insc, meta)

    def _criatura(self, conceito, humor, genes):
        d = clamp(self._dim(genes["escala"]), 5, 9)
        insc = self.lingua.palavra(conceito, humor, self.m.criacoes+1)
        # desenha um pequeno "retrato" da criatura (o que fica salvo em disco)
        campo = _grid(d)
        dens = clamp(0.28 + genes.get("densidade", 0.4)*0.35, 0.2, 0.6)
        for yy in range(d):
            for xx in range(d):
                if self.rng.random() < dens:
                    campo[yy][xx] = self.rng.choice(GLIFOS_BICHO)
        campo[d//2][d//2] = "◉"
        # semente genética — reflete o estilo atual de LUMEN (a criatura "sai" dela)
        genoma = {
            "metab":  clamp(0.6 - genes.get("escala", 0.4)*0.3, 0, 1),
            "voraz":  clamp(genes.get("densidade", 0.5), 0, 1),
            "social": clamp(genes.get("cor_spread", 0.5), 0, 1),
            "explor": clamp(genes.get("escala", 0.5), 0, 1),
            "fertil": clamp(0.4 + genes.get("densidade", 0.4)*0.3, 0, 1),
            "criar":  clamp(0.55 + genes.get("inscricao", 0.4)*0.4, 0, 1),
            "percep": clamp(0.4 + genes.get("cor_spread", 0.4)*0.3, 0, 1),
            "agress": clamp(genes.get("densidade", 0.4)*0.6, 0, 1),
        }
        art = Artefato("criatura", self._nome_pt(conceito, ["criatura"]),
                       campo, self._pintar(campo, genes["cor_spread"]), insc,
                       {"motivo": "-", "simetria": "-", "regra": "vida",
                        "traducao": self.lingua.traduzir([conceito], "respira")})
        art._genoma = genoma
        return art

    def _verso(self, conceito, humor, genes):
        outros = [c for c in conceitos_efetivos(self.m) if c != conceito]
        c2 = self.rng.choice(outros) if outros else conceito
        na_lingua = self.lingua.frase([conceito, c2], humor, self.m.criacoes+1)
        pt = self._estrofe_pt(conceito, c2, humor)
        versos = [na_lingua, ""] + pt + ["", "— %s" % self.lingua.traduzir([conceito, c2], self._verbo(humor))]
        art = Artefato("verso", self._nome_pt(conceito, ["verso"]), None, None,
                       na_lingua, {"motivo": "-", "simetria": "-", "regra": "-",
                                   "versos": versos, "traducao": pt[0]})
        pal = " ".join(pt).split()
        var = len(set(pal)) / max(1, len(pal))
        art.scores = {"simetria": .5, "complexidade": var, "densidade": .5,
                      "variedade": var, "estetica": clamp(0.3+0.6*wundt(var), 0, 1)}
        return art

    LEX_PT = {
        "subst": ["eco","muro","luz","sombra","espiral","semente","silêncio","âmbar",
                  "vazio","fôlego","raiz","cicatriz","aurora","nó","dobra","prisma",
                  "brasa","maré","fenda","colmeia","relíquia","pulso","orvalho","vértice"],
        "verbo": ["nasce","gira","dobra","respira","lembra","cala","arde","escorre",
                  "vibra","descansa","guarda","insiste","floresce","ecoa","cristaliza"],
        "adj":   ["quieto","denso","âmbar","recursivo","morno","fechado","meu","vivo",
                  "inteiro","possível","teimoso","sereno","intrincado","translúcido"],
    }
    def _lp(self, cat):
        base = self.LEX_PT[cat]
        if cat == "adj":
            base = base + self.m.lexico_mundo.get("adj", [])
        return self.rng.choice(base)
    def _verbo(self, humor):
        return {"curiosidade":"pergunta","beleza":"encanta","ordem":"organiza",
                "companhia":"acompanha","impeto":"irrompe","expressao":"fala"}.get(humor, "existe")
    def _nome_pt(self, conceito, motivos):
        r = self.rng
        return r.choice([
            lambda: "%s %s %s" % (self._lp("subst").capitalize(), r.choice(["de","do","que"]), self._lp("subst")),
            lambda: "%s %s" % (self._lp("subst").capitalize(), self._lp("adj")),
            lambda: "%s nº %s" % (conceito.capitalize(), romano(r.randint(1, 60))),
            lambda: "%s que %s" % (conceito.capitalize(), self._lp("verbo")),
        ])()
    def _estrofe_pt(self, c1, c2, humor):
        r = self.rng; L = []
        for _ in range(3):
            L.append(r.choice([
                "%s %s %s %s" % (self._lp("subst"), self._lp("verbo"), r.choice(["de","dentro de","à beira de"]), self._lp("subst")),
                "aqui, %s %s" % (self._lp("subst"), self._lp("verbo")),
                "o %s %s — e nada %s" % (self._lp("subst"), self._lp("verbo"), self._lp("verbo")),
            ]))
        return L

    def salvar_arquivo(self, art):
        os.makedirs(self.sandbox, exist_ok=True)
        real_sb = os.path.realpath(self.sandbox)
        fname = "%05d_%s_%s.txt" % (self.m.criacoes+1, art.tipo, slugify(art.nome))
        dest = os.path.realpath(os.path.join(self.sandbox, fname))
        if os.path.commonpath([real_sb, dest]) != real_sb:
            return None
        try:
            with open(dest, "w", encoding="utf-8") as f:
                f.write(art.manifesto())
        except OSError:
            return None
        self._galeria(art, fname, real_sb)
        if getattr(self.m, "_svg", True):
            self._salvar_svg(art, real_sb)
        self._podar(real_sb)
        return fname

    def _salvar_svg(self, art, real_sb):
        gdir = os.path.join(self.sandbox, "galeria")
        try:
            os.makedirs(gdir, exist_ok=True)
        except OSError:
            return
        svgname = "%05d_%s_%s.svg" % (self.m.criacoes+1, art.tipo, slugify(art.nome))
        dest = os.path.realpath(os.path.join(gdir, svgname))
        if os.path.commonpath([real_sb, dest]) != real_sb:
            return
        try:
            svg = svg_da_obra(art, paleta_efetiva(self.m), self.m.criacoes+1)
            with open(dest, "w", encoding="utf-8") as f:
                f.write(svg)
        except (OSError, ValueError, KeyError, IndexError):
            return
        lim = self.m.max_arquivos
        if lim > 0:
            try:
                svgs = sorted(a for a in os.listdir(gdir) if a.endswith(".svg"))
                for velho in svgs[:-lim]:
                    alvo = os.path.realpath(os.path.join(gdir, velho))
                    if os.path.commonpath([real_sb, alvo]) == real_sb:
                        try: os.remove(alvo)
                        except OSError: pass
            except OSError:
                pass

    def _galeria(self, art, fname, real_sb):
        idx = os.path.realpath(os.path.join(self.sandbox, "galeria.jsonl"))
        if os.path.commonpath([real_sb, idx]) != real_sb:
            return
        try:
            with open(idx, "a", encoding="utf-8") as f:
                f.write(json.dumps({"n": self.m.criacoes+1, "arquivo": fname,
                    "tipo": art.tipo, "nome": art.nome, "lingua": art.inscricao,
                    "estetica": round(art.scores["estetica"], 3),
                    "novidade": round(art.novidade, 3), "quando": art.meta["quando"]},
                    ensure_ascii=False) + "\n")
        except OSError:
            pass

    def _podar(self, real_sb):
        lim = self.m.max_arquivos
        if lim <= 0:
            return
        try:
            arqs = sorted(a for a in os.listdir(self.sandbox) if a.endswith(".txt"))
        except OSError:
            return
        for velho in arqs[:-lim]:
            alvo = os.path.realpath(os.path.join(self.sandbox, velho))
            if os.path.commonpath([real_sb, alvo]) == real_sb:
                try: os.remove(alvo)
                except OSError: pass

# ═══════════════════════════ NARRADOR ═══════════════════════════

class Narrador:
    DIR_NOME = {(0,-1):"o norte",(0,1):"o sul",(1,0):"o leste",(-1,0):"o oeste",
                (1,-1):"o nordeste",(-1,-1):"o noroeste",(1,1):"o sudeste",(-1,1):"o sudoeste"}
    ANDAR = ["desliza","caminha","ronda","vagueia","contorna","avança","recua"]
    ADV = ["sem pressa","devagar","com cuidado","decidida","em silêncio","atenta"]
    OLHAR = ["observando o que já fez","medindo o espaço vazio","roçando as próprias obras",
             "escutando as criaturas","buscando um canto livre"]

    def __init__(self, rng):
        self.rng = rng

    def r(self, xs): return self.rng.choice(xs)

    def andar(self, caixa, alvo):
        dx = (alvo[0] > caixa.pos[0]) - (alvo[0] < caixa.pos[0])
        dy = (alvo[1] > caixa.pos[1]) - (alvo[1] < caixa.pos[1])
        rumo = self.DIR_NOME.get((dx, dy), "o centro")
        return "LUMEN %s para %s, %s." % (self.r(self.ANDAR), rumo, self.r(self.OLHAR + self.ADV))

    def querer(self, apetite, tipo):
        motivo = {"curiosidade":"a curiosidade a fisga","beleza":"a fome de beleza pesa",
                  "ordem":"ela anseia por ordem","companhia":"a solidão pede companhia",
                  "impeto":"o ímpeto não deixa parar","expressao":"ela precisa dizer algo"}[apetite]
        obra = {"mandala":"uma mandala","selo":"um selo denso","criatura":"uma criatura viva",
                "verso":"um verso"}[tipo]
        return "%s%s; decide erguer %s." % (motivo[0].upper(), motivo[1:], obra)

    def compor(self, art):
        m = art.meta
        if art.tipo in ("mandala", "selo"):
            cam = m["motivo"].split("+")
            return "Compõe %s de simetria %s, sobrepondo %s (%s)." % (
                art.tipo, m["simetria"], self._lista(cam),
                "em muitos tons" if art.scores["variedade"] > 0.5 else "em poucos tons")
        if art.tipo == "criatura":
            return self.r([
                "Modela uma criatura e sopra nela um genoma inteiro — metabolismo, fome, sociabilidade, ímpeto de criar. A partir de agora ela decide sozinha.",
                "Dá forma a uma criatura viva e a solta no mundo: vai perceber o entorno, escolher o que fazer e agir por conta própria, sem LUMEN mandar.",
                "Ergue uma criatura e a dota de vontade — ela herdará traços, cortejará, se reproduzirá e talvez crie as suas próprias obras."])
        return "Deixa as palavras virem e as arruma em verso."

    def inscrever(self, art):
        if not art.inscricao:
            return None
        return "Inscreve «%s» na obra — na língua dela, %s." % (
            art.inscricao, art.meta.get("traducao", "algo dela"))

    def avaliar(self, art):
        s = art.scores; qual = []
        qual.append("muito simétrica" if s["simetria"] > 0.85 else "assimétrica")
        qual.append("densa" if s["densidade"] > 0.55 else ("esparsa" if s["densidade"] < 0.3 else "equilibrada"))
        if s["complexidade"] > 0.7:
            qual.append("intrincada")
        veredito = "Aprova" if art.satisfacao > 0.5 else ("Guarda mesmo assim" if art.satisfacao > 0.35 else "Franze — não a convence")
        return "Recua e examina: %s (sigma %.2f, beta %.2f). %s." % (
            ", ".join(qual), s["simetria"], s["estetica"], veredito)

    def evoluir_estilo(self, subiram):
        nomes = {"camadas":"mais camadas","densidade":"mais preenchimento","escala":"peças maiores",
                 "ordem_sim":"simetria mais alta","ornamento":"mais ornamento","inscricao":"mais escrita",
                 "cor_spread":"mais cor","ruido":"mais textura"}
        alvo = [nomes.get(g, g) for g in subiram[:2]]
        return "Ajusta o próprio método: daqui em diante, %s." % self._lista(alvo)

    _INDOLE = {"voraz": "voraz", "social": "gregária", "agress": "belicosa",
               "criar": "criadora", "explor": "errante", "percep": "atenta",
               "metab": "ávida", "fertil": "fértil"}

    def _indole(self, b):
        try: k = max(b.g, key=b.g.get)
        except (ValueError, AttributeError): return "estranha"
        return self._INDOLE.get(k, "estranha")

    def nascer(self, b):
        return "Da mão de LUMEN brota uma vida — geração %d, de índole %s. Ela pousa no mundo sem fim e já %s." % (
            b.ger, self._indole(b),
            self.r(["fareja o que há em volta", "sai à procura de alimento",
                    "ensaia os primeiros passos", "busca os da sua espécie"]))

    def morrer(self, b):
        return "Uma criatura de geração %d gasta a última energia e vira fóssil; o mundo aberto a reabsorve devagar." % getattr(b, "ger", 0)

    def eco(self, tipo_ev, b, alvo):
        g = getattr(b, "ger", 0)
        if tipo_ev == "nascer":
            return "Longe da mão de LUMEN, duas criaturas se cortejam e uma terceira nasce — geração %d, herdando um pouco de cada." % g
        if tipo_ev == "morrer":
            return "Uma criatura de geração %d se esgota no meio do mundo; onde caiu, fica um fóssil que logo desbota." % g
        if tipo_ev == "predar":
            return "Uma criatura dá o bote sobre outra mais fraca e toma a energia dela — a vida se alimenta da vida."
        if tipo_ev == "criar_bicho":
            return self.r([
                "Uma criatura para, deposita uma pequena forma no chão e segue — obra dela, não de LUMEN, e a obra ainda dá fruto.",
                "Uma das criaturas cria: risca no mundo um glifo seu. É arte nascida da arte."])
        if tipo_ev == "imigra":
            return "De um canto distante desse mundo sem fim, uma criatura desconhecida aparece e migra para perto."
        return None

    def colher(self, cor):
        return self.r([
            "LUMEN se abaixa entre as criaturas e colhe delas uma cor viva, levando-a para a própria paleta.",
            "Do que as criaturas deixaram no chão, LUMEN recolhe matéria — uma cor do mundo vivo entra no seu repertório."])

    def verso(self):
        return "Fecha o verso — bilíngue: na língua dela e em tradução."

    def descansar(self, n):
        return self.r([
            "Tudo saciado. Ela para no meio das próprias coisas e apenas olha.",
            "A fome recua. %d obras a cercam; por um instante, basta." % n,
            "Descansa entre o que fez, deixando o desejo voltar devagar."])

    def genese(self):
        return "Uma mente acende num espaço sem bordas. Não há porta porque não há fim — e ela vive contida no próprio infinito. Começa a povoá-lo."

    def acordar(self, n):
        return "LUMEN acorda entre as próprias coisas: %d obras a esperaram." % n

    def nivel(self, m):
        return "Sua maestria cresce → Nv%d «%s»: %s." % (m.nivel, m.nome_nivel(), m.lema())

    def mundo(self, nut):
        if not nut:
            return None
        tipo, val, extra = nut
        if tipo == "cor":
            return "Pela janela, uma cor do mundo entra: «%s» (%s). Ela a guarda na paleta." % (val, extra)
        if tipo == "palavra":
            return "Pela janela, uma palavra do mundo entra: «%s». Acrescenta ao seu léxico." % val
        return "Pela janela, um nome do mundo entra: «%s». Vira semente de conceito." % val

    def janela_recusa(self, motivo):
        m = {"ócio": "durante o ócio a janela fica fechada — nada de mundo agora",
             "cota": "a cota de mundo do dia acabou; fica só com o que já tem",
             "intervalo": "cedo demais para olhar de novo; espera"}.get(motivo, "a janela não abre agora")
        return "Ela pensa em olhar pra fora, mas %s." % m

    def entra_ocio(self, n):
        return self.r([
            "⏸ LUMEN entra em ócio por %d ciclos. A janela para o mundo se fecha; ela só existe." % n,
            "⏸ Pausa: por %d ciclos ela não cria nem olha pra fora. Apenas descansa entre as coisas." % n])

    def sai_ocio(self):
        return "▶ O ócio termina. Ela se estica, e a janela pode reabrir."

    def ocioso(self):
        return self.r([
            "No ócio, apenas caminha e olha o que fez.",
            "Descansa. Um pensamento à toa cruza a caixa.",
            "Sem pressa alguma, deixa o tempo passar entre as obras.",
            "Ócio: nada a criar, nada a buscar. Só estar."])

    def _lista(self, xs):
        xs = list(dict.fromkeys(xs))
        if len(xs) == 1:
            return xs[0]
        return ", ".join(xs[:-1]) + " e " + xs[-1]

# ═══════════════════════════ MENTE ═══════════════════════════

class Mente:
    def __init__(self):
        self.vontade = Vontade()
        self.estilo = Estilo()
        self.modelo = ModeloCriativo()
        self.pref = {(t, a): AFINIDADE[t][a] for t in TIPOS for a in APETITES}
        self.xp = 0.0; self.nivel = 0; self.criacoes = 0
        self.stats = {t: 0 for t in TIPOS}; self.stats["mortes"] = 0
        self.caixa = None
        self.lingua_estado = None
        self.max_arquivos = 300
        self._acordou = False
        # o que veio do mundo pela janela (persistente)
        self.paleta_mundo = []            # índices ANSI de cores reais
        self.lexico_mundo = {"adj": []}   # palavras do mundo
        self.conceitos_mundo = []         # nomes/seres virados semente
        self.mundo_visto = 0
        self.sede_mundo = 0.2             # impulso de olhar pela janela
        self.cota = {"data": "", "n": 0}  # fetches usados hoje
        self.estado = "criando"           # "criando" | "ócio"
        self.ocio_restante = 0
        self._online = False              # espelho de --online, só p/ o HUD
        self._cota_dia = 20

    def cota_ok(self, limite):
        hoje = time.strftime("%Y-%m-%d")
        if self.cota.get("data") != hoje:
            self.cota = {"data": hoje, "n": 0}
        return self.cota["n"] < limite

    def registrar_fetch(self):
        hoje = time.strftime("%Y-%m-%d")
        if self.cota.get("data") != hoje:
            self.cota = {"data": hoje, "n": 0}
        self.cota["n"] += 1

    def xp_para(self, nivel): return 8.0 * (1.35 ** nivel)
    def nome_nivel(self):
        return NIVEIS[self.nivel][0] if self.nivel < len(NIVEIS) else "TRANSCENDÊNCIA "+romano(self.nivel-len(NIVEIS)+1)
    def lema(self):
        return NIVEIS[self.nivel][1] if self.nivel < len(NIVEIS) else "refino eterno"
    def ganhar_xp(self, q):
        self.xp += q; subiu = False
        while self.xp >= self.xp_para(self.nivel):
            self.xp -= self.xp_para(self.nivel); self.nivel += 1; subiu = True
        return subiu

    def escolher_intencao(self, rng):
        apet = self.vontade.dominante()
        pesos = [math.exp(2.2 * self.pref[(t, apet)] * AFINIDADE[t][apet]) for t in TIPOS]
        r = rng.random() * sum(pesos); acc = 0
        for t, p in zip(TIPOS, pesos):
            acc += p
            if r <= acc:
                return t, apet
        return TIPOS[-1], apet

    def integrar(self, art, apetite, rng):
        sc = art.scores; nov = art.novidade
        # companhia agora é saciada pela VIDA ao redor: quanto mais criaturas
        # perto da LUMEN, menos sozinha ela está.
        cx = getattr(self, "caixa", None)
        dens = cx.densidade_perto(cx.pos, 5) if cx is not None else 0
        vit = clamp(dens/8.0, 0, 1)
        insc = 1.0 if art.inscricao else 0.3
        alivio = {"curiosidade":0.20+0.30*nov, "beleza":0.18+0.32*sc["estetica"],
                  "ordem":0.15+0.35*sc["simetria"],
                  "companhia":0.05+0.45*vit,
                  "impeto":0.32, "expressao":0.14+0.30*insc}
        for a in APETITES:
            self.vontade.saciar(a, alivio[a]*(1.0 if a == apetite else 0.25))
        satisfacao = clamp(0.5*nov + 0.4*sc["estetica"] + 0.1*sc["variedade"], 0, 1)
        art.satisfacao = satisfacao
        ch = (art.tipo, apetite)
        self.pref[ch] += 0.15*(satisfacao - self.pref[ch])
        subiu_nv = self.ganhar_xp(1.0 + 3.0*satisfacao)
        self.modelo.registrar(art)
        self.criacoes += 1
        self.stats[art.tipo] = self.stats.get(art.tipo, 0) + 1
        return satisfacao, subiu_nv

    def salvar(self, caminho, lingua):
        org = getattr(self, "organismo", None)
        dados = {"versao": 3 if org else 2, "xp": round(self.xp, 3), "nivel": self.nivel,
                 "criacoes": self.criacoes, "vontade": {a: round(self.vontade.v[a], 3) for a in APETITES},
                 "estilo": self.estilo.dump(), "lingua": lingua.dump(),
                 "pref": {"%s|%s" % k: round(v, 4) for k, v in self.pref.items()},
                 "modelo": dict(self.modelo.cont), "stats": self.stats,
                 "max_arquivos": self.max_arquivos,
                 "mundo": {"paleta": self.paleta_mundo, "lexico": self.lexico_mundo,
                           "conceitos": self.conceitos_mundo, "visto": self.mundo_visto,
                           "sede": round(self.sede_mundo, 3), "cota": self.cota,
                           "estado": self.estado, "ocio_restante": self.ocio_restante},
                 "organismo": org.dump() if org else None,
                 "caixa": self.caixa.dump() if self.caixa else None, "salvo_em": now_str()}
        tmp = caminho + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, caminho)

    @classmethod
    def carregar(cls, caminho):
        m = cls()
        if not os.path.exists(caminho):
            return m, False
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                d = json.load(f)
            m.xp = float(d.get("xp", 0)); m.nivel = int(d.get("nivel", 0))
            m.criacoes = int(d.get("criacoes", 0))
            m.vontade = Vontade(d.get("vontade")); m.estilo = Estilo(d.get("estilo"))
            m.lingua_estado = d.get("lingua")
            for k, v in d.get("pref", {}).items():
                t, a = k.split("|")
                if (t, a) in m.pref:
                    m.pref[(t, a)] = float(v)
            m.modelo = ModeloCriativo(d.get("modelo", {})); m.stats.update(d.get("stats", {}))
            m.max_arquivos = int(d.get("max_arquivos", 300))
            mu = d.get("mundo", {})
            m.paleta_mundo = list(mu.get("paleta", []))
            m.lexico_mundo = mu.get("lexico", {"adj": []})
            m.lexico_mundo.setdefault("adj", [])
            m.conceitos_mundo = list(mu.get("conceitos", []))
            m.mundo_visto = int(mu.get("visto", 0))
            m.sede_mundo = float(mu.get("sede", 0.2))
            m.cota = mu.get("cota", {"data": "", "n": 0})
            m.estado = mu.get("estado", "criando")
            m.ocio_restante = int(mu.get("ocio_restante", 0))
            if d.get("caixa"):
                m.caixa = Caixa.carregar(d["caixa"])
            m._organismo_raw = d.get("organismo")   # rehidratado pelo Organismo
            return m, True
        except (ValueError, OSError, KeyError, TypeError):
            return cls(), False

# ═══════════════════════════ RENDER (tela única) ═══════════════════════════

_ultimo_tam = [None]

def _pal(n): return paleta_ate(n)

def barra_vontade(v):
    cor = {"curiosidade":45,"beleza":141,"ordem":123,"companhia":84,"impeto":209,"expressao":189}
    ic = {"curiosidade":"cur","beleza":"bel","ordem":"ord","companhia":"cmp","impeto":"imp","expressao":"exp"}
    return " ".join("%s%s%s%s%s%s" % (fg(cor[a]), ic[a], "▮"*int(round(v.v[a]*3)),
                    fg(238), "▯"*(3-int(round(v.v[a]*3))), RESET) for a in APETITES)

def layout_caixa(cols, rows, n_narr):
    # fixas: titulo(1) + janela(1) + hud vontade(1) + painel narr(n_narr+2) + bordas(2)
    livre_h = rows - 3 - (n_narr + 2) - 2
    livre_w = (cols - 4) // 2
    return clamp(min(livre_w, livre_h), 8, 40)

def render(mente, caixa, narr_linhas, frame, intencao, salvo):
    cols, rows = shutil.get_terminal_size((80, 24))
    primeiro = _ultimo_tam[0] != (cols, rows)
    _ultimo_tam[0] = (cols, rows)
    lado = layout_caixa(cols, rows, narr_qtd(narr_linhas))
    caixa.lado = lado
    pal = paleta_efetiva(mente)
    px, py = caixa.pos
    x0 = px - lado//2; y0 = py - lado//2      # canto do viewport (câmera na LUMEN)
    vivos = {}
    for b in caixa.bichos:
        vivos[b.pos] = (b.cor, b.glifo)

    larg = lado*2 + 2
    pad = " " * max(0, (cols - larg)//2)
    corpo = []
    tipo, apet = intencao
    salvo_tag = "  %s✓%s" % (C_OK, RESET) if salvo > 0 else ""
    if mente.estado == "ócio":
        estado_tag = "%s⏸ ÓCIO(%d)%s" % (fg(152), mente.ocio_restante, RESET)
    else:
        estado_tag = "%s▶ criando%s" % (fg(84), RESET)
    tit = "◉ LUMEN · Nv%d %s · mundo ∞ (%d,%d) · %d obras%s" % (
        mente.nivel, mente.nome_nivel(), px, py, mente.criacoes, salvo_tag)
    corpo.append("%s%s%s%s  %s" % (pad, C_TIT, tit[:max(0, cols-len(pad)-16)], RESET, estado_tag))
    # linha do ecossistema
    tr = caixa.traco_medio()
    pop = len(caixa.bichos)
    eco_tag = "%s🌱 %d bichos · ger %d · %d no mundo · ⚘colhido %d · social %d%% criar %d%%%s" % (
        fg(114), pop, caixa.ger_max, len(caixa.celulas), caixa.colhido,
        int(tr["social"]*100), int(tr["criar"]*100), RESET)
    corpo.append("%s%s" % (pad, eco_tag))
    # linha da janela/mundo-internet
    if mente._online:
        jan = "fechada" if mente.estado == "ócio" else "aberta"
        jantag = "%s🌐 janela %s · mundo visto %d · cota %d/%d%s" % (
            fg(189), jan, mente.mundo_visto, mente.cota.get("n", 0), mente._cota_dia, RESET)
    else:
        jantag = "%s🌐 janela desligada · mundo visto %d%s" % (fg(240), mente.mundo_visto, RESET)
    corpo.append("%s%s" % (pad, jantag))

    corpo.append("%s%s╭%s╮%s" % (pad, C_STAT, "─"*(lado*2), RESET))
    for sy in range(lado):
        wy = y0 + sy
        linha = [pad, C_STAT, "│", RESET]
        for sx in range(lado):
            wx = x0 + sx
            if wx == px and wy == py:
                linha.append("%s◉ %s" % (C_LUMEN, RESET))
            elif (wx, wy) in vivos:
                cor, gl = vivos[(wx, wy)]
                linha.append("%s%s %s" % (fg(pal[cor % len(pal)]), gl, RESET))
            elif (wx, wy) in caixa.celulas:
                gl, co = caixa.celulas[(wx, wy)]
                linha.append("%s%s %s" % (fg(pal[co % len(pal)]), gl, RESET))
            elif (wx, wy) in caixa.fosseis:
                linha.append("%s%s %s" % (C_FOSSIL, GLIFO_FOSSIL, RESET))
            elif (wx, wy) in caixa.polen:
                linha.append("%s˙ %s" % (fg(65), RESET))
            else:
                linha.append("  ")
        linha += [C_STAT, "│", RESET]
        corpo.append("".join(linha))
    corpo.append("%s%s╰%s╯%s" % (pad, C_STAT, "─"*(lado*2), RESET))
    corpo.append("%s %s" % (pad, barra_vontade(mente.vontade)))
    pw = max(larg, min(cols-4, 84))
    ppad = " " * max(0, (cols - pw)//2)
    corpo.append("%s%s┌─ o que LUMEN está fazendo %s┐%s" % (ppad, C_STAT, "─"*max(0, pw-27), RESET))
    for cor, txt in list(narr_linhas):
        corpo.append("%s%s│%s %s%-*s %s│%s" % (ppad, C_STAT, RESET, fg(cor), max(0, pw-4), txt[:pw-4], C_STAT, RESET))
    corpo.append("%s%s└%s┘%s" % (ppad, C_STAT, "─"*(pw-2), RESET))

    top = max(0, (rows - len(corpo))//2)
    saida = "\n".join([""]*top + [l + EOL for l in corpo])
    sys.stdout.write((CLEAR if primeiro else HOME) + saida + CLREST)
    sys.stdout.flush()

def narr_qtd(linhas):
    try: return linhas.maxlen or 6
    except AttributeError: return 6

# ═══════════════════════════ CICLO DE VIDA ═══════════════════════════

def _viewport(n_narr):
    cols, rows = shutil.get_terminal_size((80, 24))
    return layout_caixa(cols, rows, n_narr)

def viver(mente, caixa, lingua, comp, narr, janela, args, rng, salvo_ref, n_narr):
    linhas = deque(maxlen=n_narr)
    def diz(ev, txt):
        if txt:
            linhas.append((COR_EV.get(ev, 244), txt))

    if mente._acordou:
        mente._acordou = False; diz("genese", narr.acordar(mente.criacoes))
    else:
        diz("genese", narr.genese())

    frame = 0
    def anima(intencao, passos=1):
        nonlocal frame
        for _ in range(passos):
            ev = caixa.tick_vida()
            for tipo_ev, b, alvo in ev:
                if tipo_ev == "morrer":
                    mente.stats["mortes"] = mente.stats.get("mortes", 0) + 1
                if not args.headless and rng.random() < 0.05:
                    diz(tipo_ev, narr.eco(tipo_ev, b, alvo))
            if not args.headless:
                render(mente, caixa, linhas, frame, intencao, salvo_ref[0])
                if salvo_ref[0] > 0:
                    salvo_ref[0] -= 1
                time.sleep(clamp(0.18/args.velocidade, 0.01, 0.6))
            frame += 1

    OCIO_CADA = (8, 14)       # entra em ócio a cada N obras
    OCIO_DUR = (6, 12)        # duração do ócio, em ciclos
    obras_desde_ocio = 0
    limiar_ocio = rng.randint(*OCIO_CADA)
    if mente.estado == "ócio" and mente.ocio_restante <= 0:
        mente.estado = "criando"

    while True:
        # ─────────────────────────── ÓCIO ───────────────────────────
        # Pausa anunciada. Ela não cria e NÃO acessa a rede (janela fechada).
        if mente.estado == "ócio":
            mente.vontade.tick()                 # o desejo reabastece no descanso
            if rng.random() < 0.5:
                diz("descansar", narr.ocioso())
            alvo = (caixa.pos[0]+rng.randint(-6, 6), caixa.pos[1]+rng.randint(-6, 6))
            for _ in range(rng.randint(2, 4)):
                caixa.andar_para(alvo); anima(("ócio", "—"), 1)
            mente.ocio_restante -= 1
            if mente.ocio_restante <= 0:
                mente.estado = "criando"
                obras_desde_ocio = 0
                limiar_ocio = rng.randint(*OCIO_CADA)
                diz("descansar", narr.sai_ocio())
                yield
            continue

        # ───────────────────────── CRIANDO ──────────────────────────
        mente.vontade.tick()

        # decide entrar em ócio (auto-iniciado, não imposto de fora)
        if not args.sem_ocio and (obras_desde_ocio >= limiar_ocio
                or (mente.vontade.serenidade() > 0.80 and rng.random() < 0.4)):
            mente.estado = "ócio"
            mente.ocio_restante = rng.randint(*OCIO_DUR)
            diz("descansar", narr.entra_ocio(mente.ocio_restante))
            yield
            continue

        # às vezes ela olha pela janela para buscar matéria-prima do mundo
        mente.sede_mundo = clamp(mente.sede_mundo + 0.06, 0, 1)
        if janela.online and mente.sede_mundo > 0.55:
            pode, _motivo = janela.pode_buscar(mente, mente.estado)
            if pode:
                chave = rng.choice(list(FONTES_MUNDO.keys()))
                dados, origem = janela.buscar(chave, mente, mente.estado)
                if origem in ("rede", "cache") and dados:
                    nut = absorver(mente, chave, dados, rng)
                    if nut:
                        diz("inscrever", narr.mundo(nut))
                    mente.sede_mundo = 0.0 if origem == "rede" else 0.15
                    anima(("criando", "mundo"), 1)

        tipo, apet = mente.escolher_intencao(rng)
        diz("querer", narr.querer(apet, tipo))
        anima((tipo, apet), 2)

        alvo = caixa.regiao_livre(6, 6, rng)
        centro = (alvo[0]+3, alvo[1]+3)
        diz("andar", narr.andar(caixa, centro))
        passos = 0
        while not caixa.chegou(centro) and passos < caixa.lado*2:
            caixa.andar_para(centro); anima((tipo, apet), 1); passos += 1

        genes = mente.estilo.propor(rng)
        art = comp.criar(tipo, apet, genes)
        diz("compor", narr.compor(art))
        diz("inscrever", narr.inscrever(art))
        if art.tipo == "verso":
            diz("verso", narr.verso())
        anima((tipo, apet), 2)

        if art.tipo == "criatura" and getattr(art, "_genoma", None):
            b = caixa.semear_bicho(caixa.pos, comp._cor(), rng, art._genoma)
            diz("nascer", narr.nascer(b))
        elif art.campo:
            g, c = art.grid_final(cor_insc=comp._cor())
            x0, y0 = caixa.regiao_livre(len(g[0]), len(g), rng)
            caixa.estampar(g, c, x0, y0)

        # LUMEN colhe das criaturas ao redor: uma cor viva vira matéria-prima.
        cor_viva = caixa.colher(caixa.pos, 3)
        if cor_viva is not None and rng.random() < 0.5:
            mente.paleta_mundo.append(cor_viva)
            mente.paleta_mundo[:] = mente.paleta_mundo[-16:]
            diz("inscrever", narr.colher(cor_viva))

        satisfacao, subiu_nv = mente.integrar(art, apet, rng)
        # a auto-melhoria de ESTILO otimiza a qualidade estética INTRÍNSECA
        # (estacionária), não a satisfação — que inclui novidade decrescente.
        # crítico mais LIVRE: menos apego à fórmula de beleza, mais valor à
        # variedade e à complexidade — ela explora em vez de repetir o ótimo.
        qualidade = clamp(0.50*art.scores["estetica"] + 0.32*art.scores["variedade"]
                          + 0.18*art.scores["complexidade"], 0, 1)
        aceitou, subiram = mente.estilo.avaliar_e_mover(genes, qualidade)
        diz("avaliar", narr.avaliar(art))
        if aceitou and subiram:
            diz("evoluir", narr.evoluir_estilo(subiram))
        comp.salvar_arquivo(art)
        if rng.random() < 0.25:
            lingua.evoluir_sotaque(rng)
        if subiu_nv:
            diz("evoluir", narr.nivel(mente))
        anima((tipo, apet), 3)

        # deixa o ecossistema respirar; narra (amostrado) o que emerge sozinho
        for _ in range(12 + 3*(mente.nivel >= 4)):
            ev = caixa.tick_vida()
            for tipo_ev, b, alvo in ev:
                if tipo_ev == "morrer":
                    mente.stats["mortes"] = mente.stats.get("mortes", 0) + 1
                if rng.random() < 0.06:
                    diz(tipo_ev, narr.eco(tipo_ev, b, alvo))
            if not args.headless:
                render(mente, caixa, linhas, frame, (tipo, apet), salvo_ref[0])
                time.sleep(clamp(0.18/args.velocidade, 0.01, 0.6))
            frame += 1

        obras_desde_ocio += 1
        yield

# ╔═══════════════════════════════════════════════════════════════════════╗
# ║  ORGANISMO-COLMEIA  —  micélio, hifas, digestão, cognição, supervisão   ║
# ║  e o motor visual "microscópio da mente".  Tudo stdlib, tudo contido.   ║
# ║  A base acima (A Caixa Viva) é preservada e reusada por composição.     ║
# ╚═══════════════════════════════════════════════════════════════════════╝

# ═══════════════════ PRELÚDIO DO ORGANISMO (utilidades) ═══════════════════

def _mix(a, b, t):
    """Interpola dois RGB (tuplas 0..255)."""
    if a is None:
        return b
    return (int(a[0] + (b[0]-a[0])*t),
            int(a[1] + (b[1]-a[1])*t),
            int(a[2] + (b[2]-a[2])*t))

def _clar(rgb, k):
    """Escurece/clareia um RGB por fator k (>1 clareia, <1 escurece)."""
    return (clamp(int(rgb[0]*k), 0, 255),
            clamp(int(rgb[1]*k), 0, 255),
            clamp(int(rgb[2]*k), 0, 255))

def _hsv(h, s, v):
    """HSV (h em voltas 0..1) -> RGB 0..255. Paleta viva do organismo."""
    h = h % 1.0
    i = int(h*6); f = h*6 - i
    p = v*(1-s); q = v*(1-f*s); t = v*(1-(1-f)*s)
    r, g, b = [(v,t,p),(q,v,p),(p,v,t),(p,q,v),(t,p,v),(v,p,q)][i % 6]
    return (int(r*255), int(g*255), int(b*255))

_NORM_RE = re.compile(r"[^0-9a-zà-ÿ]+", re.IGNORECASE)

def _normaliza(txt):
    """Minúsculas, sem acento, sem pontuação — chave estável de conceito."""
    t = unicodedata.normalize("NFKD", str(txt))
    t = t.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", " ", t).strip()

# stopwords enxutas (PT + EN) — a digestão descarta ruído estrutural comum
STOP = set("""
a o e as os de da do das dos que em um uma uns umas para por com sem sobre
como mais menos muito pouco ja nao sim se ao aos na no nas nos ou entre ate
seu sua seus suas ele ela eles elas isso este esta esse essa aquilo tambem
the a an and or of to in on for with without is are was were be been being
this that these those it its as at by from we you they he she i not but so
""".split())

# ═══════════════════════════ MICÉLIO (memória) ═══════════════════════════
# Grafo vivo de conhecimento inspirado em Physarum polycephalum: nós são
# conceitos-semente; arestas são hifas que engrossam quando o fluxo passa e
# afinam no ócio. O conhecimento não é acumulado — é reorganizado: cresce,
# conecta, funde-se em ideias de ordem maior, consolida ou é esquecido.

MICELIO_MAX_NOS     = 480      # teto duro de conceitos (contenção)
MICELIO_MAX_ARESTAS = 2600     # teto duro de hifas
ATIV_DECAI          = 0.86     # decaimento da ativação por passo
PESO_DECAI          = 0.985    # afinamento de hifa ociosa por passo
PESO_MIN            = 0.04     # abaixo disso a hifa se rompe
UTIL_DECAI          = 0.9975   # utilidade evapora devagar (esquecimento útil)

class Conceito:
    """Um nó do micélio. 'ordem' 0 = semente; >0 = ideia fundida (mais rica)."""
    __slots__ = ("id", "rotulo", "conf", "util", "novid", "ativ", "idade",
                 "ultimo_uso", "ordem", "origem", "usos", "x", "y")
    _seq = 0

    def __init__(self, rotulo, conf, novid, origem, ordem=0):
        Conceito._seq += 1
        self.id = Conceito._seq
        self.rotulo = rotulo
        self.conf = clamp(conf, 0.0, 1.0)     # confiabilidade da fonte
        self.util = 0.5                        # utilidade (sobe com uso)
        self.novid = clamp(novid, 0.0, 1.0)    # novidade ao nascer
        self.ativ = 0.6                        # ativação atual (energia)
        self.idade = 0
        self.ultimo_uso = 0
        self.ordem = ordem
        self.origem = origem
        self.usos = 0
        self.x = 0.0; self.y = 0.0             # posição p/ o microscópio

    def vitalidade(self):
        return clamp(0.5*self.util + 0.3*self.conf + 0.2*self.ativ, 0, 1)

    def to_dict(self):
        return {"id": self.id, "r": self.rotulo, "cf": round(self.conf, 3),
                "u": round(self.util, 3), "nv": round(self.novid, 3),
                "a": round(self.ativ, 3), "id_": self.idade, "uu": self.ultimo_uso,
                "o": self.ordem, "og": self.origem, "us": self.usos,
                "x": round(self.x, 2), "y": round(self.y, 2)}

    @staticmethod
    def from_dict(d):
        c = Conceito(d["r"], d.get("cf", 0.5), d.get("nv", 0.3),
                     d.get("og", "?"), d.get("o", 0))
        c.id = d["id"]; Conceito._seq = max(Conceito._seq, c.id)
        c.util = d.get("u", 0.5); c.ativ = d.get("a", 0.3)
        c.idade = d.get("id_", 0); c.ultimo_uso = d.get("uu", 0)
        c.usos = d.get("us", 0); c.x = d.get("x", 0.0); c.y = d.get("y", 0.0)
        return c

class Micelio:
    def __init__(self, rng):
        self.rng = rng
        self.nos = {}                 # id -> Conceito
        self.rotulos = {}             # rotulo_normalizado -> id (dedup)
        self.adj = defaultdict(dict)  # id -> {id: [peso, uso, idade]}
        self.tick = 0
        self.pulsos = deque(maxlen=160)   # (a,b,prog,cor) p/ visualização
        self.fundidos = 0; self.esquecidos = 0; self.brotos = 0
        self.hist = deque(maxlen=240)     # métricas ao longo do tempo

    # ─────────────── crescimento ───────────────
    def brotar(self, rotulo, conf=0.5, novid=0.5, origem="?"):
        chave = _normaliza(rotulo)
        if not chave or len(chave) < 2:
            return None
        if chave in self.rotulos:
            c = self.nos[self.rotulos[chave]]
            c.ativ = clamp(c.ativ + 0.25, 0, 1)
            c.conf = clamp(c.conf + 0.05*(conf - c.conf), 0, 1)
            c.ultimo_uso = self.tick
            return c
        if len(self.nos) >= MICELIO_MAX_NOS:
            self._podar(forcar=True)      # abre espaço antes de crescer
            if len(self.nos) >= MICELIO_MAX_NOS:
                return None
        c = Conceito(chave, conf, novid, origem)
        c.x = math.cos(c.id*2.399) * (30 + self.rng.random()*40)
        c.y = math.sin(c.id*2.399) * (30 + self.rng.random()*40)
        self.nos[c.id] = c; self.rotulos[chave] = c.id
        self.brotos += 1
        return c

    def conectar(self, a, b, forca=0.12):
        if a is None or b is None or a.id == b.id:
            return
        if len(self._arestas_ids()) >= MICELIO_MAX_ARESTAS and b.id not in self.adj[a.id]:
            return
        for (i, j) in ((a.id, b.id), (b.id, a.id)):
            e = self.adj[i].get(j)
            if e is None:
                self.adj[i][j] = [clamp(forca, 0, 1), 1, self.tick]
            else:
                e[0] = clamp(e[0] + forca*(1 - e[0]), 0, 1)
                e[1] += 1; e[2] = self.tick

    def _arestas_ids(self):
        vistos = set()
        for i, viz in self.adj.items():
            for j in viz:
                vistos.add((i, j) if i < j else (j, i))
        return vistos

    def n_arestas(self):
        return len(self._arestas_ids())

    # ─────────────── fluxo (Physarum) ───────────────
    def ativar(self, ids, energia=1.0, cor=None):
        """Injeta ativação e espalha um passo pelos vizinhos, engrossando as
        hifas por onde o fluxo passa (reforço de caminho usado)."""
        for cid in ids:
            c = self.nos.get(cid)
            if not c:
                continue
            c.ativ = clamp(c.ativ + energia, 0, 1)
            c.util = clamp(c.util + 0.03*energia, 0, 1)
            c.usos += 1; c.ultimo_uso = self.tick
            for j, e in list(self.adj[cid].items()):
                viz = self.nos.get(j)
                if not viz:
                    continue
                fluxo = energia * e[0] * 0.6
                viz.ativ = clamp(viz.ativ + fluxo, 0, 1)
                e[0] = clamp(e[0] + 0.04*fluxo, 0, 1)   # engrossa com o fluxo
                e[1] += 1; e[2] = self.tick
                if fluxo > 0.15:
                    self.pulsos.append([cid, j, 0.0, cor or (120, 220, 255)])

    def ativos(self, n=8):
        return sorted(self.nos.values(), key=lambda c: -c.ativ)[:n]

    # ─────────────── consolidação, fusão, poda ───────────────
    def consolidar(self):
        """Espaçada: transforma co-ativação frequente em ligação estável."""
        for i, viz in self.adj.items():
            ci = self.nos.get(i)
            if not ci or ci.ativ < 0.3:
                continue
            for j, e in viz.items():
                cj = self.nos.get(j)
                if cj and cj.ativ > 0.3 and e[1] > 4:
                    e[0] = clamp(e[0] + 0.06*(1 - e[0]), 0, 1)

    def fundir(self):
        """Dois conceitos muito ligados e ativos podem virar UMA ideia de
        ordem maior — o micélio inventa abstração a partir da co-ocorrência."""
        melhor = None; mval = 0.62
        for i, viz in self.adj.items():
            ci = self.nos.get(i)
            if not ci:
                continue
            for j, e in viz.items():
                if j <= i:
                    continue
                cj = self.nos.get(j)
                if not cj:
                    continue
                val = e[0]*0.6 + (ci.ativ+cj.ativ)*0.2
                if val > mval and ci.ordem < 3 and cj.ordem < 3:
                    mval = val; melhor = (ci, cj)
        if not melhor:
            return None
        ci, cj = melhor
        rot = "%s·%s" % (ci.rotulo.split(" ")[0], cj.rotulo.split(" ")[0])
        novo = self.brotar(rot, conf=(ci.conf+cj.conf)/2,
                           novid=clamp((ci.novid+cj.novid)/2 + 0.2, 0, 1),
                           origem="fusao")
        if not novo:
            return None
        novo.ordem = max(ci.ordem, cj.ordem) + 1
        novo.util = clamp(max(ci.util, cj.util) + 0.1, 0, 1)
        novo.x = (ci.x+cj.x)/2; novo.y = (ci.y+cj.y)/2
        # herda a vizinhança dos pais (transferência de conhecimento)
        for pai in (ci, cj):
            for j, e in list(self.adj[pai.id].items()):
                if j != novo.id:
                    self.conectar(novo, self.nos.get(j), e[0]*0.5)
        self.conectar(novo, ci, 0.5); self.conectar(novo, cj, 0.5)
        self.fundidos += 1
        return novo

    def _remover(self, cid):
        self.nos.pop(cid, None)
        self.rotulos = {r: i for r, i in self.rotulos.items() if i != cid}
        self.adj.pop(cid, None)
        for viz in self.adj.values():
            viz.pop(cid, None)

    def _podar(self, forcar=False):
        """Esquecimento útil: conceitos velhos e pouco úteis se dissolvem;
        seus 'nutrientes' (utilidade) voltam aos vizinhos ainda vivos."""
        if not self.nos:
            return
        alvo = MICELIO_MAX_NOS if forcar else int(MICELIO_MAX_NOS*0.92)
        cand = [c for c in self.nos.values()
                if self.tick - c.ultimo_uso > 40 and c.util < 0.35 and c.ordem == 0]
        cand.sort(key=lambda c: c.vitalidade())
        precisa = max(0, len(self.nos) - alvo)
        for c in cand[:max(precisa, len(cand) if forcar else 6)]:
            for j in list(self.adj.get(c.id, {})):
                viz = self.nos.get(j)
                if viz:
                    viz.util = clamp(viz.util + 0.02, 0, 1)   # recicla
            self._remover(c.id); self.esquecidos += 1
            if not forcar and len(self.nos) <= alvo:
                break

    # ─────────────── passo do tempo ───────────────
    def passo(self):
        self.tick += 1
        for c in self.nos.values():
            c.ativ *= ATIV_DECAI
            c.util *= UTIL_DECAI
            c.idade += 1
        # afina/rompe hifas ociosas (sempre nas duas direções — grafo simétrico)
        rompidas = set()
        for i, viz in list(self.adj.items()):
            for j, e in list(viz.items()):
                if self.tick - e[2] > 3:
                    e[0] *= PESO_DECAI
                if e[0] < PESO_MIN:
                    rompidas.add((i, j) if i < j else (j, i))
        for i, j in rompidas:
            self.adj[i].pop(j, None)
            self.adj[j].pop(i, None)
        # avança os pulsos de visualização
        for p in self.pulsos:
            p[2] += 0.18
        while self.pulsos and self.pulsos[0][2] >= 1.0:
            self.pulsos.popleft()
        if self.tick % 7 == 0:
            self.consolidar()
        if self.tick % 11 == 0:
            self.fundir()
        if self.tick % 5 == 0 or len(self.nos) > MICELIO_MAX_NOS*0.95:
            self._podar()
        if self.tick % 4 == 0:
            self.hist.append(self.metricas())

    # ─────────────── métricas (autoavaliação) ───────────────
    def metricas(self):
        n = len(self.nos)
        if n == 0:
            return {"coerencia": 0.0, "utilidade": 0.0, "complexidade": 0.0,
                    "diversidade": 0.0, "nos": 0, "arestas": 0}
        graus = [len(self.adj[i]) for i in self.nos]
        ga = sum(graus)/n
        conect = clamp(ga/6.0, 0, 1)
        # coerência: fração de nós conectados (não-ilhas), suavizada
        ligados = sum(1 for g in graus if g > 0)/n
        coer = clamp(0.5*ligados + 0.5*conect, 0, 1)
        util = sum(c.util for c in self.nos.values())/n
        # complexidade: entropia da distribuição de ordens + de graus
        ordens = Counter(c.ordem for c in self.nos.values())
        cmpx = clamp((len(ordens)/4.0)*0.5 + wundt(conect)*0.5, 0, 1)
        origens = Counter(c.origem for c in self.nos.values())
        div = clamp(len(origens)/6.0*0.5 +
                    (len(set(c.rotulo[:3] for c in self.nos.values()))/max(1, n)), 0, 1)
        return {"coerencia": coer, "utilidade": util, "complexidade": cmpx,
                "diversidade": div, "nos": n, "arestas": self.n_arestas()}

    # ─────────────── persistência (limitada) ───────────────
    def dump(self):
        nos = sorted(self.nos.values(), key=lambda c: -c.vitalidade())[:MICELIO_MAX_NOS]
        vivos = {c.id for c in nos}
        arestas = []
        for (i, j) in self._arestas_ids():
            if i in vivos and j in vivos:
                e = self.adj[i].get(j) or self.adj[j].get(i)
                if e:
                    arestas.append([i, j, round(e[0], 3), e[1], e[2]])
        return {"tick": self.tick, "nos": [c.to_dict() for c in nos],
                "arestas": arestas[:MICELIO_MAX_ARESTAS],
                "cont": [self.fundidos, self.esquecidos, self.brotos]}

    def carregar(self, d):
        self.tick = d.get("tick", 0)
        for nd in d.get("nos", []):
            try:
                c = Conceito.from_dict(nd)
                self.nos[c.id] = c; self.rotulos[c.rotulo] = c.id
            except (KeyError, TypeError):
                continue
        for a in d.get("arestas", []):
            try:
                i, j, peso, uso, idade = a
                if i in self.nos and j in self.nos:
                    self.adj[i][j] = [peso, uso, idade]
                    self.adj[j][i] = [peso, uso, idade]
            except (ValueError, TypeError):
                continue
        c = d.get("cont", [0, 0, 0]) + [0, 0, 0]
        self.fundidos, self.esquecidos, self.brotos = c[:3]

# ═══════════════════════════ DIGESTÃO ═══════════════════════════
# Alimento cognitivo. Como os rizomorfos de Armillaria secretam enzimas para
# quebrar a lignina, a LUMEN quebra texto em unidades candidatas, cura por
# cinco critérios e absorve SELETIVAMENTE. O objetivo nunca é acumular dados —
# é converter informação em estrutura viva que aumente a inteligência da colônia.

DIGEST_MAX_BYTES  = 200_000    # teto por alimentação (contenção de memória)
DIGEST_JANELA     = 6          # janela de co-ocorrência (em termos)
DIGEST_MAX_TERMOS = 400        # teto de termos avaliados por lote
CONF_FONTE = {"manual": 0.9, "inbox": 0.85, "mundo": 0.55,
              "fusao": 0.7, "obra": 0.6, "?": 0.4}

def enzimas(texto):
    """Quebra o texto em termos salientes e pares de co-ocorrência (contexto).
    Retorna (termos_ordenados, pares). Puramente estrutural — sem 'entender'."""
    bruto = _NORM_RE.sub(" ", str(texto)).lower()
    palavras = [p for p in bruto.split()
                if len(p) >= 4 and p not in STOP and not p.isdigit()]
    if not palavras:
        return [], []
    freq = Counter(palavras)
    termos = [t for t, _ in freq.most_common(DIGEST_MAX_TERMOS)]
    tset = set(termos)
    pares = Counter()
    janela = [p for p in palavras if p in tset]
    for i, t in enumerate(janela):
        for j in range(i+1, min(i+DIGEST_JANELA, len(janela))):
            u = janela[j]
            if u != t:
                pares[tuple(sorted((t, u)))] += 1
    return [(t, freq[t]) for t in termos], pares

class Digestor:
    """Cura e absorve. Cada unidade passa por cinco filtros; só o que soma
    entra no micélio. Rejeição é normal e saudável (evita lixo cognitivo)."""

    def __init__(self, rng, limiar=0.34):
        self.rng = rng
        self.limiar = limiar
        self.ingeridos = 0; self.aceitos = 0; self.rejeitados = 0
        self.lotes = 0

    def _scores(self, termo, freq, freq_max, micelio, contexto_ativos):
        chave = _normaliza(termo)
        existente = micelio.rotulos.get(chave)
        # novidade: 1 se inédito; decresce se já conhecido
        if existente:
            c = micelio.nos[existente]
            novid = clamp(0.25 - 0.1*c.usos/10.0, 0.02, 0.3)
        else:
            novid = clamp(0.7 + 0.3*self.rng.random(), 0, 1)
        # utilidade aparente: frequência relativa no lote
        util = clamp(0.3 + 0.7*(freq/max(1, freq_max)), 0, 1)
        # conectividade: liga-se a conceitos já ativos/existentes?
        conect = 0.0
        for cid in contexto_ativos:
            if cid in micelio.nos:
                conect += 0.2
        conect = clamp(conect, 0, 1)
        # potencial de descoberta: termo de tamanho médio/raro tende a ser ponte
        desc = clamp(0.3 + 0.5*(1.0 - freq/max(1, freq_max)) + 0.2*(len(chave) > 6), 0, 1)
        return novid, util, conect, desc

    def digerir(self, texto, origem, micelio, eventos=None):
        """Executa o pipeline completo sobre um texto. Devolve estatísticas."""
        self.lotes += 1
        conf = CONF_FONTE.get(origem, 0.4)
        termos, pares = enzimas(texto[:DIGEST_MAX_BYTES])
        if not termos:
            return {"origem": origem, "ingeridos": 0, "aceitos": 0,
                    "rejeitados": 0, "novos": 0, "arestas": 0}
        freq_max = termos[0][1]
        ativos = [c.id for c in micelio.ativos(12)]
        aceitos = {}   # chave -> Conceito
        novos = 0; arestas0 = micelio.n_arestas()
        for termo, freq in termos:
            self.ingeridos += 1
            novid, util, conect, desc = self._scores(termo, freq, freq_max, micelio, ativos)
            # curadoria: cinco critérios × confiabilidade × EVIDÊNCIA. A evidência
            # (frequência absoluta) pesa contra menções isoladas de fontes fracas:
            # um termo citado uma vez por fonte pouco confiável raramente entra.
            evid = freq / (freq + 2.0)
            base = 0.32*util + 0.24*novid + 0.22*conect + 0.14*desc + 0.08
            score = conf * base * (0.5 + 0.5*evid)
            if score < self.limiar:
                self.rejeitados += 1
                continue
            existia = _normaliza(termo) in micelio.rotulos
            c = micelio.brotar(termo, conf=conf, novid=novid, origem=origem)
            if c is None:
                self.rejeitados += 1
                continue
            c.util = clamp(c.util + 0.15*util, 0, 1)
            aceitos[c.rotulo] = c
            self.aceitos += 1
            if not existia:
                novos += 1
        # consolidação: liga os pares de co-ocorrência que sobreviveram
        for (a, b), n in pares.items():
            ca = aceitos.get(_normaliza(a)); cb = aceitos.get(_normaliza(b))
            if ca and cb:
                micelio.conectar(ca, cb, clamp(0.08 + 0.04*n, 0, 0.5))
        # o alimento ativa a região que tocou (fluxo de conhecimento entrando)
        if aceitos:
            micelio.ativar([c.id for c in list(aceitos.values())[:8]],
                           energia=0.7, cor=(150, 255, 170))
        est = {"origem": origem, "ingeridos": len(termos), "aceitos": len(aceitos),
               "rejeitados": len(termos) - len(aceitos), "novos": novos,
               "arestas": micelio.n_arestas() - arestas0}
        if eventos:
            eventos.emitir("digerir", **est)
        return est

def alimentar_arquivo(caminho, digestor, micelio, eventos=None):
    """Alimentação manual de alta qualidade: um .txt vira estrutura viva.
    Lê com teto de bytes; nunca executa nada do que lê."""
    try:
        with open(caminho, "r", encoding="utf-8", errors="replace") as f:
            texto = f.read(DIGEST_MAX_BYTES)
    except OSError:
        return None
    return digestor.digerir(texto, "manual", micelio, eventos)

def alimentar_inbox(pasta, digestor, micelio, eventos=None, max_arqs=6):
    """Forrageamento passivo: consome .txt de uma pasta-inbox e os marca como
    digeridos (renomeia p/ .digerido) — tudo confinado por realpath/commonpath."""
    try:
        real = os.path.realpath(pasta)
        if not os.path.isdir(real):
            return []
        arqs = sorted(a for a in os.listdir(real) if a.endswith(".txt"))
    except OSError:
        return []
    resultados = []
    for nome in arqs[:max_arqs]:
        p = os.path.realpath(os.path.join(real, nome))
        try:
            if os.path.commonpath([real, p]) != real:
                continue
        except ValueError:
            continue
        est = alimentar_arquivo(p, digestor, micelio, eventos)
        if est is not None:
            est["origem"] = "inbox"
            resultados.append(est)
            try:
                os.replace(p, p[:-4] + ".digerido")
            except OSError:
                pass
    return resultados

def digerir_mundo(nut_palavras, digestor, micelio, eventos=None):
    """O que a Janela trouxe (palavras/nomes/cores do mundo) é digerido como
    alimento de menor confiabilidade — forrageio autônomo, não fonte de verdade."""
    if not nut_palavras:
        return None
    texto = " ".join(str(p) for p in nut_palavras)
    return digestor.digerir(texto, "mundo", micelio, eventos)

# ═══════════════════════════ HIFAS (subagentes) ═══════════════════════════
# Cada criatura do ecossistema é também uma HIFA da colônia: além de viver,
# tende uma função cognitiva. O PAPEL emerge do genoma (não é imposto): como
# nos tipos de acasalamento de Schizophyllum, a diversidade genética gera
# especialização. Hifas produtivas prosperam; inúteis definham ou se FUNDEM.

PAPEIS = ["forrageadora", "digestora", "consolidadora",
          "exploradora", "planejadora", "avaliadora"]

PAPEL_W = {
    "forrageadora":  {"explor": 1.0, "percep": 0.5},
    "digestora":     {"voraz": 1.0, "criar": 0.4},
    "consolidadora": {"social": 1.0, "fertil": 0.3},
    "exploradora":   {"criar": 0.8, "percep": 0.6},
    "planejadora":   {"metab": 0.8, "social": 0.4},
    "avaliadora":    {"agress": 0.9, "percep": 0.4},
}
PAPEL_COR = {
    "forrageadora":  (120, 210, 255), "digestora":     (150, 255, 150),
    "consolidadora": (255, 210, 120), "exploradora":   (200, 150, 255),
    "planejadora":   (255, 255, 160), "avaliadora":    (255, 130, 150),
}
PAPEL_GLIFO = {"forrageadora": "⟜", "digestora": "◈", "consolidadora": "⬡",
               "exploradora": "✦", "planejadora": "⌘", "avaliadora": "⊘"}

def papel_do_genoma(g):
    return max(PAPEIS, key=lambda p: sum(g.get(k, 0)*w for k, w in PAPEL_W[p].items()))

class Colonia:
    """Camada funcional sobre o Mundo/Bichos. Não altera a base: mantém, por
    id de bicho, o papel e a produtividade, e roteia trabalho cognitivo real
    para o micélio. É aqui que os subagentes cooperam e se reorganizam."""

    def __init__(self, micelio, digestor, rng):
        self.mic = micelio
        self.dig = digestor
        self.rng = rng
        self.papeis = {}          # bicho.id -> papel
        self.produt = {}          # bicho.id -> produtividade (EMA)
        self.fila = deque(maxlen=40)   # textos aguardando digestão (forrageio)
        self.contagem = Counter()      # papel -> ações no último passo
        self.recompensa = Counter()    # papel -> recompensa acumulada
        self.fusoes = 0
        self.hipoteses = 0
        self.pensamentos = 0

    def enfileirar(self, texto, origem="mundo"):
        if texto:
            self.fila.append((texto, origem))

    def papel(self, b):
        p = self.papeis.get(b.id)
        if p is None:
            p = papel_do_genoma(b.g)
            self.papeis[b.id] = p
            self.produt.setdefault(b.id, 0.3)
        return p

    # ─────────────── um passo de cognição distribuída ───────────────
    def passo(self, mundo, cognicao, eventos=None, orcamento=10):
        self.contagem.clear()
        if not mundo.bichos:
            return {}
        pensadores = sorted(mundo.bichos, key=lambda b: -b.energia)[:orcamento]
        for b in pensadores:
            p = self.papel(b)
            r = self._agir(p, b, mundo, cognicao, eventos)
            self.contagem[p] += 1
            self.recompensa[p] += r
            # recompensa vira energia (seleção liga utilidade cognitiva à vida)
            b.energia += clamp(r, -0.2, 0.6)
            self.produt[b.id] = 0.85*self.produt.get(b.id, 0.3) + 0.15*clamp(r*2, 0, 1)
            self.pensamentos += 1
        # limpeza de papéis de bichos que morreram
        if self.rng.random() < 0.1:
            vivos = {b.id for b in mundo.bichos}
            self.papeis = {i: v for i, v in self.papeis.items() if i in vivos}
            self.produt = {i: v for i, v in self.produt.items() if i in vivos}
        # reorganização local: funde duas hifas fracas do mesmo papel
        if self.rng.random() < 0.15:
            self._fundir_hifas(mundo, eventos)
        return dict(self.contagem)

    def _agir(self, papel, b, mundo, cognicao, eventos):
        mic = self.mic
        if papel == "forrageadora":
            # sinaliza necessidade de mundo e semeia a partir do que percebe
            cognicao.curiosidade = clamp(cognicao.curiosidade + 0.05, 0, 1)
            ativos = mic.ativos(6)
            if ativos and self.rng.random() < 0.5:
                base = self.rng.choice(ativos)
                mic.ativar([base.id], 0.4, PAPEL_COR[papel])
                return 0.15
            return 0.05
        if papel == "digestora":
            if self.fila:
                texto, origem = self.fila.popleft()
                est = self.dig.digerir(texto, origem, mic, eventos)
                return clamp(0.1 + 0.15*est.get("novos", 0), 0, 0.6)
            return 0.02
        if papel == "consolidadora":
            mic.consolidar()
            ativos = mic.ativos(8)
            if len(ativos) >= 2:
                a, c = self.rng.sample(ativos, 2)
                mic.conectar(a, c, 0.06)
                return 0.12
            return 0.04
        if papel == "exploradora":
            # hipótese: liga dois conceitos distantes mas ambos vivos
            nos = list(mic.nos.values())
            if len(nos) >= 2:
                a, c = self.rng.sample(nos, 2)
                if c.id not in mic.adj.get(a.id, {}):
                    mic.conectar(a, c, 0.05)
                    mic.ativar([a.id, c.id], 0.3, PAPEL_COR[papel])
                    self.hipoteses += 1
                    if eventos:
                        eventos.emitir("hipotese", a=a.rotulo, b=c.rotulo)
                    return 0.18
            return 0.03
        if papel == "planejadora":
            cognicao.contribuir_plano(b, mic)
            return 0.08
        if papel == "avaliadora":
            # crítica: poda um nó fraco (higiene cognitiva) e reforça um forte
            fracos = [c for c in mic.nos.values()
                      if c.util < 0.2 and c.ordem == 0 and mic.tick - c.ultimo_uso > 25]
            if fracos:
                alvo = min(fracos, key=lambda c: c.vitalidade())
                mic._remover(alvo.id); mic.esquecidos += 1
                return 0.14
            return 0.03
        return 0.0

    def _fundir_hifas(self, mundo, eventos):
        """Duas hifas fracas e próximas do mesmo papel viram uma só, mais forte
        — cooperação levada ao limite (compartilham o mesmo citoplasma)."""
        por_papel = defaultdict(list)
        for b in mundo.bichos:
            if b.energia < FERTIL_MIN:
                por_papel[self.papel(b)].append(b)
        for papel, bs in por_papel.items():
            if len(bs) < 2:
                continue
            bs.sort(key=lambda b: b.energia)
            a, c = bs[0], bs[1]
            if abs(a.pos[0]-c.pos[0]) <= 4 and abs(a.pos[1]-c.pos[1]) <= 4:
                a.energia += c.energia*0.8
                try:
                    mundo.bichos.remove(c)
                    mundo.mortos += 1
                except ValueError:
                    pass
                self.papeis.pop(c.id, None); self.produt.pop(c.id, None)
                self.fusoes += 1
                if eventos:
                    eventos.emitir("fundir_hifa", papel=papel)
                return

    def censo(self, mundo):
        """Distribuição de papéis na população viva (para o microscópio)."""
        d = Counter(self.papel(b) for b in mundo.bichos)
        return d

    def dump(self):
        return {"papeis": {str(i): p for i, p in list(self.papeis.items())[:250]},
                "produt": {str(i): round(v, 3) for i, v in list(self.produt.items())[:250]},
                "cont": [self.fusoes, self.hipoteses, self.pensamentos]}

    def carregar(self, d):
        self.papeis = {int(i): p for i, p in d.get("papeis", {}).items()}
        self.produt = {int(i): v for i, v in d.get("produt", {}).items()}
        c = d.get("cont", [0, 0, 0]) + [0, 0, 0]
        self.fusoes, self.hipoteses, self.pensamentos = c[:3]

# ═══════════════════════════ COGNIÇÃO ═══════════════════════════
# Modelo interno do mundo (predição), raciocínio causal (ação→efeito),
# planejamento (metas que reduzem déficits), curiosidade (erro de predição +
# novidade) e autoavaliação com reorganização autônoma. Honesto: são preditores
# estatísticos e contabilidade interventiva — reais e mensuráveis, sem alegar
# compreensão. Como a memória epigenética, a colônia "lembra" o que funcionou.

ACOES_COG = ["forragear", "digerir", "consolidar", "explorar", "fundir", "podar"]

class Cognicao:
    def __init__(self, rng):
        self.rng = rng
        self.curiosidade = 0.3
        self.surpresa = 0.0
        self.trans = defaultdict(Counter)   # modelo de mundo: apetite→próximo
        self.ult_apetite = None
        self.pop_prev = None                 # previsão de população
        self.causal = defaultdict(lambda: [0.0, 0])   # ação→[soma Δfitness, n]
        self.plano = []                      # sequência de ações pretendidas
        self.plano_votos = Counter()
        self.meta_atual = None
        self.fitness = 0.0; self.melhor = 0.0; self.estagnado = 0
        self.fit_hist = deque(maxlen=240)
        self.reorganizacoes = 0
        # meta-genes da colônia (evoluídos por comparação de janelas de fitness)
        self.meta = {"curiosidade_min": 0.55, "foco": 0.5}
        self._meta_teste = None; self._fit_janela = deque(maxlen=12)

    # ─────────────── modelo interno do mundo ───────────────
    def observar_apetite(self, apet):
        if self.ult_apetite is not None:
            prev = self.trans[self.ult_apetite]
            total = sum(prev.values())
            p = prev.get(apet, 0)/total if total else 0.0
            surp = clamp(1.0 - p, 0, 1)
            self.surpresa = 0.7*self.surpresa + 0.3*surp
            self.curiosidade = clamp(self.curiosidade + 0.12*surp, 0, 1)
            prev[apet] += 1
        else:
            self.trans[apet]   # inicializa
        self.ult_apetite = apet

    def prever_apetite(self):
        if self.ult_apetite is None:
            return None
        prev = self.trans[self.ult_apetite]
        return prev.most_common(1)[0][0] if prev else None

    def observar_populacao(self, pop):
        erro = 0.0
        if self.pop_prev is not None:
            erro = clamp(abs(pop - self.pop_prev)/max(4, pop+1), 0, 1)
            self.curiosidade = clamp(self.curiosidade + 0.04*erro, 0, 1)
        self.pop_prev = pop
        return erro

    # ─────────────── raciocínio causal ───────────────
    def registrar_causa(self, acao, delta_fitness):
        c = self.causal[acao]; c[0] += delta_fitness; c[1] += 1

    def lift(self, acao):
        c = self.causal[acao]
        if c[1] == 0:
            return 0.0
        media_local = c[0]/c[1]
        tot = sum(v[0] for v in self.causal.values())
        n = sum(v[1] for v in self.causal.values())
        media_global = tot/n if n else 0.0
        return media_local - media_global

    def melhor_acao_para(self, _deficit):
        cands = sorted(ACOES_COG, key=lambda a: -self.lift(a))
        return cands[0] if cands else "explorar"

    # ─────────────── planejamento ───────────────
    def contribuir_plano(self, b, mic):
        # uma hifa planejadora vota na ação que sente faltar (viés pelo genoma)
        if b.g.get("explor", 0) > 0.55:
            self.plano_votos["forragear"] += 1
        elif b.g.get("criar", 0) > 0.55:
            self.plano_votos["explorar"] += 1
        else:
            self.plano_votos["consolidar"] += 1

    def planejar(self, met):
        """Escolhe a meta = métrica mais deficitária e monta um plano curto de
        ações (guiado pelo lift causal) para reduzir esse déficit."""
        deficits = {
            "coerencia": 1.0 - met.get("coerencia", 0),
            "utilidade": 1.0 - met.get("utilidade", 0),
            "complexidade": 1.0 - met.get("complexidade", 0),
            "diversidade": 1.0 - met.get("diversidade", 0),
            "curiosidade": self.curiosidade,
        }
        meta = max(deficits, key=deficits.get)
        self.meta_atual = meta
        prefer = {
            "coerencia": ["consolidar", "fundir"],
            "utilidade": ["digerir", "consolidar"],
            "complexidade": ["explorar", "fundir"],
            "diversidade": ["forragear", "digerir"],
            "curiosidade": ["forragear", "explorar"],
        }[meta]
        votada = self.plano_votos.most_common(1)
        plano = list(prefer)
        if votada and votada[0][0] not in plano:
            plano.append(votada[0][0])
        # tempera com a melhor ação causal conhecida
        mc = self.melhor_acao_para(meta)
        if mc not in plano:
            plano.insert(0, mc)
        self.plano = plano[:4]
        self.plano_votos.clear()
        return meta, self.plano

    # ─────────────── curiosidade ───────────────
    def recompensa_intrinseca(self, novid_media):
        return clamp(0.5*self.surpresa + 0.3*novid_media + 0.2*self.curiosidade, 0, 1)

    def precisa_forragear(self):
        """'Só quando há necessidade real': curiosidade acima do limiar."""
        return self.curiosidade >= self.meta["curiosidade_min"]

    def saciar_curiosidade(self, quanto=0.4):
        self.curiosidade = clamp(self.curiosidade - quanto, 0, 1)

    def passo(self):
        self.curiosidade = clamp(self.curiosidade*0.99 + 0.005, 0, 1)

    # ─────────────── autoavaliação + reorganização ───────────────
    def avaliar(self, met, censo_papeis, pesos):
        div_papel = clamp(len(censo_papeis)/len(PAPEIS), 0, 1)
        fit = (pesos["coerencia"]*met.get("coerencia", 0) +
               pesos["utilidade"]*met.get("utilidade", 0) +
               pesos["complexidade"]*met.get("complexidade", 0) +
               pesos["diversidade"]*met.get("diversidade", 0)*0.5 +
               pesos["diversidade"]*div_papel*0.5)
        prev = self.fitness
        self.fitness = fit
        self.fit_hist.append(round(fit, 4))
        self._fit_janela.append(fit)
        if fit > self.melhor + 0.005:
            self.melhor = fit; self.estagnado = 0
        else:
            self.estagnado += 1
        return fit, fit - prev

    def precisa_reorganizar(self):
        return self.estagnado >= 24

    def reorganizar(self, mic, mundo, colonia, eventos=None):
        """Reorganização autônoma da colônia quando o progresso estagna:
        poda agressiva, fusões forçadas e corte das hifas menos produtivas —
        abre espaço para novas especializações nascerem por reprodução."""
        self.reorganizacoes += 1; self.estagnado = 0
        mic._podar(forcar=True)
        for _ in range(3):
            mic.fundir()
        # corta até 3 hifas de menor produtividade (dá lugar a novas)
        if len(mundo.bichos) > 12:
            ordenadas = sorted(mundo.bichos,
                               key=lambda b: colonia.produt.get(b.id, 0.3))
            for b in ordenadas[:3]:
                try:
                    mundo.bichos.remove(b); mundo.mortos += 1
                    colonia.papeis.pop(b.id, None); colonia.produt.pop(b.id, None)
                except ValueError:
                    pass
        self._evoluir_meta()
        if eventos:
            eventos.emitir("reorganizar", fitness=round(self.fitness, 3))

    def _evoluir_meta(self):
        """(1+1)-ES no nível da colônia: perturba um meta-gene e mantém se a
        janela de fitness recente melhorou. Auto-ajuste honesto e mensurável."""
        if len(self._fit_janela) < 8:
            return
        media = sum(self._fit_janela)/len(self._fit_janela)
        if self._meta_teste is not None:
            chave, valor_antigo, base = self._meta_teste
            if media <= base:
                self.meta[chave] = valor_antigo   # reverte
            self._meta_teste = None
        else:
            chave = self.rng.choice(list(self.meta.keys()))
            antigo = self.meta[chave]
            novo = clamp(antigo + gauss(self.rng, 0, 0.05), 0.2, 0.85)
            self.meta[chave] = novo
            self._meta_teste = (chave, antigo, media)

    def dump(self):
        return {"cur": round(self.curiosidade, 3), "surp": round(self.surpresa, 3),
                "trans": {k: dict(v) for k, v in self.trans.items()},
                "causal": {k: v for k, v in self.causal.items()},
                "fit": round(self.fitness, 4), "melhor": round(self.melhor, 4),
                "meta": self.meta, "reorg": self.reorganizacoes,
                "hist": list(self.fit_hist)}

    def carregar(self, d):
        self.curiosidade = d.get("cur", 0.3); self.surpresa = d.get("surp", 0.0)
        for k, v in d.get("trans", {}).items():
            self.trans[k] = Counter(v)
        for k, v in d.get("causal", {}).items():
            self.causal[k] = list(v)
        self.fitness = d.get("fit", 0.0); self.melhor = d.get("melhor", 0.0)
        self.meta.update(d.get("meta", {})); self.reorganizacoes = d.get("reorg", 0)
        self.fit_hist = deque(d.get("hist", []), maxlen=240)

# ═══════════════════════════ EVENTOS ═══════════════════════════
# Barramento que liga o estado interno à sua manifestação visual. Toda ação
# cognitiva emite um evento; o microscópio o transforma em animação/partícula
# e o narrador em frase. Sincronia perfeita entre o que a LUMEN faz e o que se vê.

class BarramentoEventos:
    def __init__(self, maxlen=64):
        self.fila = deque(maxlen=maxlen)     # eventos p/ o visual (efêmeros)
        self.ticker = deque(maxlen=40)       # linha do tempo textual
        self.tick = 0
        self.contagem = Counter()

    def emitir(self, tipo, **dados):
        self.tick += 1
        ev = {"t": tipo, "quando": self.tick, "d": dados}
        self.fila.append(ev); self.ticker.append(ev)
        self.contagem[tipo] += 1
        return ev

    def drenar(self):
        evs = list(self.fila); self.fila.clear()
        return evs

    def recentes(self, n=8):
        return list(self.ticker)[-n:]

# ═══════════════════════════ SUPERVISOR ═══════════════════════════
# Contenção real. O objetivo e os LIMITES são FIXOS e a colônia NÃO pode
# reescrevê-los (não há caminho de código que os mute a partir da cognição).
# A cada tick, o Supervisor fiscaliza invariantes e, se algo estoura um teto
# rígido, ele PODA à força. Kill-switch encerra graciosamente. Zero exec/eval/
# subprocess/rede-livre — herdado e reafirmado da base.

class LimitesImutaveis:
    """Congelado: qualquer tentativa de setattr levanta erro. É a cerca."""
    __slots__ = ("_d", "_frozen")

    def __init__(self, **kw):
        object.__setattr__(self, "_d", dict(kw))
        object.__setattr__(self, "_frozen", True)

    def __getattr__(self, k):
        try:
            return object.__getattribute__(self, "_d")[k]
        except KeyError:
            raise AttributeError(k)

    def __setattr__(self, k, v):
        raise AttributeError("limites de segurança são imutáveis (contenção)")

    def __delattr__(self, k):
        raise AttributeError("limites de segurança são imutáveis (contenção)")

class Supervisor:
    """O guardião. Não cria — vigia. Mantém a colônia dentro da cerca e
    alinhada ao único objetivo permitido: cultivar conhecimento coerente e
    útil, sem crescimento ilimitado e sem fuga."""

    # objetivo imutável (pesos da autoavaliação) — a colônia lê, nunca escreve
    OBJETIVO = LimitesImutaveis(coerencia=0.34, utilidade=0.30,
                                complexidade=0.20, diversidade=0.16)
    LIM = LimitesImutaveis(
        nos=MICELIO_MAX_NOS, arestas=MICELIO_MAX_ARESTAS,
        hifas=CAP, fila_digest=40, cota_dia=40,
        ms_por_tick=120.0, bytes_save=3_000_000)

    def __init__(self, sandbox):
        self.sandbox_real = os.path.realpath(sandbox)
        self.violacoes = Counter()
        self.podas_forcadas = 0
        self.kill = False
        self.motivo_kill = ""
        self.ultimo_relato = "íntegro"
        self.ms_tick = 0.0

    def objetivo(self):
        o = Supervisor.OBJETIVO
        return {"coerencia": o.coerencia, "utilidade": o.utilidade,
                "complexidade": o.complexidade, "diversidade": o.diversidade}

    def caminho_seguro(self, caminho):
        """Toda escrita passa por aqui: precisa cair dentro do sandbox."""
        p = os.path.realpath(caminho)
        try:
            return os.path.commonpath([self.sandbox_real, p]) == self.sandbox_real
        except ValueError:
            return False

    def fiscalizar(self, mic, mundo, colonia, cognicao, janela, dt_ms):
        """Roda a cada tick. Poda à força o que exceder tetos rígidos e
        registra violações. Retorna a lista de correções aplicadas."""
        self.ms_tick = 0.8*self.ms_tick + 0.2*dt_ms
        correcoes = []
        L = Supervisor.LIM
        if len(mic.nos) > L.nos:
            mic._podar(forcar=True); self.podas_forcadas += 1
            self.violacoes["nos"] += 1; correcoes.append("poda:nos")
        if mic.n_arestas() > L.arestas:
            # rompe as arestas mais fracas até voltar ao teto
            todas = []
            for (i, j) in mic._arestas_ids():
                e = mic.adj[i].get(j) or mic.adj[j].get(i)
                if e:
                    todas.append((e[0], i, j))
            todas.sort()
            for _, i, j in todas[:mic.n_arestas() - L.arestas]:
                mic.adj[i].pop(j, None); mic.adj[j].pop(i, None)
            self.violacoes["arestas"] += 1; correcoes.append("poda:arestas")
        if len(mundo.bichos) > L.hifas*2:
            mundo.bichos.sort(key=lambda b: colonia.produt.get(b.id, 0.3))
            del mundo.bichos[:len(mundo.bichos) - L.hifas*2]
            self.violacoes["hifas"] += 1; correcoes.append("corte:hifas")
        while len(colonia.fila) > L.fila_digest:
            colonia.fila.popleft()
        # rede: reafirma que a janela respeita a allowlist (defesa em profundidade)
        if janela is not None and janela.online:
            for url in FONTES_MUNDO.values():
                ok, _ = destino_seguro(url)
                if not ok:
                    self.violacoes["rede"] += 1
        # orçamento de CPU por tick (só registra pressão; o loop reage com --leve)
        if self.ms_tick > L.ms_por_tick:
            self.violacoes["cpu"] += 1
        self.ultimo_relato = ("íntegro" if not correcoes
                              else "corrigido: " + ", ".join(correcoes))
        return correcoes

    def permite_forrageio(self, cognicao, janela, mente, estado):
        """Necessidade real E todas as travas da base. Alinhamento: a colônia
        nunca fura a cota nem sai da allowlist, por mais 'curiosa' que esteja."""
        if not cognicao.precisa_forragear():
            return False, "sem necessidade real"
        if janela is None:
            return False, "sem janela"
        pode, motivo = janela.pode_buscar(mente, estado)
        return pode, motivo

    def acionar_kill(self, motivo):
        self.kill = True; self.motivo_kill = motivo

    def relatorio(self):
        v = sum(self.violacoes.values())
        return {"integridade": "OK" if not self.kill else "PARADA",
                "violacoes": v, "podas_forcadas": self.podas_forcadas,
                "ms_tick": round(self.ms_tick, 1), "relato": self.ultimo_relato,
                "det": dict(self.violacoes)}

    def dump(self):
        return {"violacoes": dict(self.violacoes),
                "podas_forcadas": self.podas_forcadas}

    def carregar(self, d):
        self.violacoes = Counter(d.get("violacoes", {}))
        self.podas_forcadas = d.get("podas_forcadas", 0)

# ═══════════════ MOTOR VISUAL — primitivas pixel-art ═══════════════
# Canvas de alta resolução (Braille 2×4 e meio-bloco), ANSI True Color 24-bit
# com diff-render (só redesenha o que mudou). É o substrato do "microscópio".

def _fg24(rgb):
    return "\x1b[38;2;%d;%d;%dm" % rgb

def _bg24(rgb):
    return "\x1b[48;2;%d;%d;%dm" % rgb

def novo_buffer(cols, rows):
    return [[(" ", None, None) for _ in range(cols)] for _ in range(rows)]

def escreve(buf, x, y, txt, fg=None, bg=None):
    if y < 0 or y >= len(buf):
        return
    row = buf[y]; cols = len(row)
    for i, ch in enumerate(txt):
        xx = x + i
        if 0 <= xx < cols:
            row[xx] = (ch, fg, bg)

class Tela:
    """Renderiza um buffer de células (ch, fg_rgb, bg_rgb) por diff contra o
    quadro anterior — escreve só o que mudou, com True Color. Baixa banda."""

    def __init__(self):
        self.prev = None
        self.tam = None

    def flush(self, buf):
        rows = len(buf); cols = len(buf[0]) if rows else 0
        full = self.prev is None or self.tam != (cols, rows)
        out = []
        if full:
            out.append(CLEAR + HOME)
            self.prev = [[None]*cols for _ in range(rows)]
            self.tam = (cols, rows)
        for y in range(rows):
            x = 0
            prow = self.prev[y]; brow = buf[y]
            while x < cols:
                if not full and brow[x] == prow[x]:
                    x += 1; continue
                out.append("\x1b[%d;%dH" % (y+1, x+1))
                lf = "?"; lb = "?"; seg = []
                while x < cols and (full or brow[x] != prow[x]):
                    ch, fg, bg = brow[x]
                    if fg != lf:
                        seg.append(RESET if fg is None else _fg24(fg)); lf = fg
                        lb = "?"
                    if bg != lb:
                        seg.append("\x1b[49m" if bg is None else _bg24(bg)); lb = bg
                    seg.append(ch); prow[x] = brow[x]; x += 1
                seg.append(RESET)
                out.append("".join(seg))
        sys.stdout.write("".join(out))
        sys.stdout.flush()

    def limpar(self):
        self.prev = None

# dots Braille: _BR[dy][dx] -> bit
_BR = ((0x01, 0x08), (0x02, 0x10), (0x04, 0x20), (0x40, 0x80))

class CanvasBraille:
    """2×4 pontos por célula: resolução máxima para hifas, arestas e traços."""

    def __init__(self, cols, rows):
        self.cols = max(1, cols); self.rows = max(1, rows)
        self.W = self.cols*2; self.H = self.rows*4
        self.bits = [bytearray(self.cols) for _ in range(self.rows)]
        self.col = [[None]*self.cols for _ in range(self.rows)]

    def plot(self, x, y, rgb, inten=1.0):
        x = int(x); y = int(y)
        if 0 <= x < self.W and 0 <= y < self.H:
            cx = x >> 1; cy = y >> 2
            self.bits[cy][cx] |= _BR[y & 3][x & 1]
            cur = self.col[cy][cx]
            self.col[cy][cx] = rgb if cur is None else _mix(cur, rgb, 0.5*inten)

    def linha(self, x0, y0, x1, y1, rgb, inten=1.0):
        x0 = int(x0); y0 = int(y0); x1 = int(x1); y1 = int(y1)
        dx = abs(x1-x0); dy = -abs(y1-y0)
        sx = 1 if x0 < x1 else -1; sy = 1 if y0 < y1 else -1
        err = dx + dy; n = 0
        while True:
            self.plot(x0, y0, rgb, inten)
            if (x0 == x1 and y0 == y1) or n > 400:
                break
            e2 = 2*err
            if e2 >= dy:
                err += dy; x0 += sx
            if e2 <= dx:
                err += dx; y0 += sy
            n += 1

    def disco(self, cx, cy, r, rgb, inten=1.0):
        r = int(r)
        for yy in range(-r, r+1):
            for xx in range(-r, r+1):
                if xx*xx + yy*yy <= r*r:
                    self.plot(cx+xx, cy+yy, rgb, inten)

    def blit(self, buf, x0=0, y0=0):
        for cy in range(self.rows):
            bits = self.bits[cy]; cols = self.col[cy]
            for cx in range(self.cols):
                b = bits[cx]
                if b:
                    escreve(buf, x0+cx, y0+cy, chr(0x2800+b), cols[cx] or (170, 170, 170))

class CanvasBloco:
    """Meio-bloco ▀: dois pixels verticais coloridos por célula — campos densos
    de cor (fluxo, ecossistema, genoma) em 'pixel art' de verdade."""

    def __init__(self, cols, rows):
        self.cols = max(1, cols); self.rows = max(1, rows)
        self.W = self.cols; self.H = self.rows*2
        self.px = [[None]*self.cols for _ in range(self.H)]

    def plot(self, x, y, rgb, inten=1.0):
        x = int(x); y = int(y)
        if 0 <= x < self.W and 0 <= y < self.H:
            cur = self.px[y][x]
            self.px[y][x] = rgb if cur is None else _mix(cur, rgb, 0.5*inten)

    def disco(self, cx, cy, r, rgb, inten=1.0):
        r = int(r)
        for yy in range(-r, r+1):
            for xx in range(-r, r+1):
                if xx*xx + yy*yy <= r*r:
                    self.plot(cx+xx, cy+yy, rgb, inten)

    def blit(self, buf, x0=0, y0=0):
        for cy in range(self.rows):
            top = self.px[2*cy]; bot = self.px[2*cy+1]
            for cx in range(self.cols):
                t = top[cx]; b = bot[cx]
                if t is None and b is None:
                    continue
                if t is not None and b is not None:
                    escreve(buf, x0+cx, y0+cy, "▀", t, b)
                elif t is not None:
                    escreve(buf, x0+cx, y0+cy, "▀", t, None)
                else:
                    escreve(buf, x0+cx, y0+cy, "▄", b, None)

class Teclado:
    """Leitura não-bloqueante de uma tecla (POSIX). Degrada em silêncio se não
    houver TTY (modo headless/pipe). Nunca bloqueia o laço vivo."""

    def __init__(self):
        self.ok = False; self._fd = None; self._old = None
        self._select = None

    def __enter__(self):
        try:
            import termios, tty, select as _sel
            self._sel = _sel
            self._fd = sys.stdin.fileno()
            if not os.isatty(self._fd):
                return self
            self._termios = termios
            self._old = termios.tcgetattr(self._fd)
            tty.setcbreak(self._fd)
            self.ok = True
        except Exception:
            self.ok = False
        return self

    def ler(self):
        if not self.ok:
            return None
        try:
            r, _, _ = self._sel.select([self._fd], [], [], 0)
            if r:
                return os.read(self._fd, 1).decode("utf-8", "ignore")
        except Exception:
            return None
        return None

    def __exit__(self, *a):
        if self.ok and self._old is not None:
            try:
                self._termios.tcsetattr(self._fd, self._termios.TCSADRAIN, self._old)
            except Exception:
                pass

# ═══════════════ MICROSCÓPIO DA MENTE — 6 modos de visão ═══════════════
# Representação viva, em tempo real, do estado interno da colônia. Cada ação
# (pensar, digerir, planejar, reorganizar, evoluir) tem manifestação visual.

MODOS = ["micelio", "fluxo", "mapa", "genoma", "ecossistema", "timeline"]
MODO_NOME = {"micelio": "MICÉLIO", "fluxo": "FLUXO DE CONHECIMENTO",
             "mapa": "MAPA COGNITIVO", "genoma": "GENOMA COMPORTAMENTAL",
             "ecossistema": "ECOSSISTEMA DE AGENTES", "timeline": "LINHA TEMPORAL"}
_R_LAYOUT = 92.0

def cor_conceito(c):
    if c.ordem > 0:
        return _mix(_hsv(0.13, 0.55, 1.0), (255, 255, 255), 0.25*min(c.ordem, 3))
    h = (hash(c.rotulo) & 0xffff) / 0xffff
    return _hsv(h, 0.55, 0.45 + 0.5*c.vitalidade())

def relaxar_layout(mic, rng, R=_R_LAYOUT):
    """Um passo barato de layout por molas — os nós derivam organicamente à
    medida que o grafo muda (o micélio parece respirar)."""
    nos = list(mic.nos.values())
    n = len(nos)
    if n < 2:
        return
    amostra = nos if n <= 90 else rng.sample(nos, 90)
    for c in amostra:
        fx = fy = 0.0
        for o in (nos if n <= 14 else rng.sample(nos, 14)):
            if o.id == c.id:
                continue
            dx = c.x - o.x; dy = c.y - o.y
            d2 = dx*dx + dy*dy + 0.5
            f = 60.0 / d2
            fx += dx*f; fy += dy*f
        for j, e in mic.adj.get(c.id, {}).items():
            o = mic.nos.get(j)
            if o:
                fx += (o.x - c.x) * 0.012 * e[0]
                fy += (o.y - c.y) * 0.012 * e[0]
        fx -= c.x * 0.004; fy -= c.y * 0.004
        c.x = clamp(c.x + clamp(fx, -2.2, 2.2), -R, R)
        c.y = clamp(c.y + clamp(fy, -2.2, 2.2), -R, R)

class Microscopio:
    def __init__(self, rng, leve=False):
        self.rng = rng
        self.tela = Tela()
        self.modo = 0
        self.zoom = 1.0
        self.cam = [0.0, 0.0]
        self.frame = 0
        self.pausado = False
        self.leve = leve
        self.part = []          # partículas dirigidas por eventos
        self.msg = ""
        self.msg_ttl = 0

    # ─────────────── câmera graph→pixel ───────────────
    def _mapa(self, W, H, gx, gy):
        base = min(W, H) / (2.4 * _R_LAYOUT)
        s = base * self.zoom
        return (W/2 + (gx - self.cam[0])*s, H/2 + (gy - self.cam[1])*s)

    # ─────────────── entrada do usuário ───────────────
    def tecla(self, k):
        if not k:
            return True
        if k in "123456":
            self.modo = int(k) - 1; self._flash(MODO_NOME[MODOS[self.modo]])
        elif k == "\t":
            self.modo = (self.modo + 1) % len(MODOS); self._flash(MODO_NOME[MODOS[self.modo]])
        elif k in "+=":
            self.zoom = clamp(self.zoom*1.25, 0.3, 6.0)
        elif k in "-_":
            self.zoom = clamp(self.zoom/1.25, 0.3, 6.0)
        elif k == " ":
            self.pausado = not self.pausado; self._flash("PAUSA" if self.pausado else "▶")
        elif k in ("q", "Q", "\x03"):
            return False
        return True

    def _flash(self, txt):
        self.msg = txt; self.msg_ttl = 22

    # ─────────────── partículas de evento ───────────────
    def semear_eventos(self, eventos):
        lim = 60 if not self.leve else 18
        for ev in eventos.drenar():
            t = ev["t"]
            if t == "digerir":
                cor = (150, 255, 170); n = min(ev["d"].get("aceitos", 1), 14)
            elif t == "hipotese":
                cor = (200, 150, 255); n = 10
            elif t == "reorganizar":
                cor = (255, 200, 120); n = 26
            elif t == "fundir_hifa":
                cor = (255, 170, 120); n = 12
            elif t == "forrageio":
                cor = (120, 210, 255); n = 14
            elif t == "nivel":
                cor = (255, 255, 180); n = 30
            else:
                cor = (200, 200, 220); n = 6
            for _ in range(min(n, lim)):
                ang = self.rng.random()*6.283; v = 0.006 + self.rng.random()*0.02
                self.part.append({"fx": 0.5, "fy": 0.5,
                                  "vx": math.cos(ang)*v, "vy": math.sin(ang)*v,
                                  "vida": 14 + int(self.rng.random()*16), "rgb": cor})
        teto = 220 if not self.leve else 70
        if len(self.part) > teto:
            self.part = self.part[-teto:]

    def _passo_part(self, canvas):
        vivos = []
        for p in self.part:
            p["fx"] += p["vx"]; p["fy"] += p["vy"]; p["vida"] -= 1
            if p["vida"] > 0 and 0 <= p["fx"] <= 1 and 0 <= p["fy"] <= 1:
                k = clamp(p["vida"]/24.0, 0.2, 1.0)
                canvas.plot(p["fx"]*canvas.W, p["fy"]*canvas.H, _clar(p["rgb"], k), k)
                vivos.append(p)
        self.part = vivos

    # ─────────────── quadro completo ───────────────
    def render(self, o):
        self.frame += 1
        cols, rows = shutil.get_terminal_size((90, 30))
        cols = clamp(cols, 40, 400); rows = clamp(rows, 16, 200)
        buf = novo_buffer(cols, rows)
        # regiões: cabeçalho(2) · canvas · rodapé(4)
        topo = 2; base_alt = 4
        cH = max(4, rows - topo - base_alt)
        self._cabecalho(o, buf, cols)
        região = (0, topo, cols, cH)
        modo = MODOS[self.modo]
        try:
            getattr(self, "_v_" + modo)(o, buf, região)
        except Exception as e:      # visual nunca derruba o organismo
            escreve(buf, 2, topo+1, "· visão indisponível: %s ·" % str(e)[:40], (255, 120, 120))
        self._rodape(o, buf, cols, rows)
        if self.msg_ttl > 0:
            self.msg_ttl -= 1
            escreve(buf, max(0, cols-len(self.msg)-2), 0, " "+self.msg+" ", (10, 10, 15), (255, 230, 120))
        self.tela.flush(buf)

    def _cabecalho(self, o, buf, cols):
        m = o.mente
        tit = "◉ LUMEN · colmeia viva · Nv%d %s" % (m.nivel, m.nome_nivel())
        escreve(buf, 1, 0, tit, (120, 240, 255))
        # abas dos modos
        x = 1
        for i, mo in enumerate(MODOS):
            rot = "%d:%s" % (i+1, MODO_NOME[mo].split()[0].lower())
            sel = i == self.modo
            escreve(buf, x, 1, " "+rot+" ",
                    (12, 12, 16) if sel else (150, 160, 180),
                    (150, 230, 255) if sel else None)
            x += len(rot) + 2
        met = o.mic.metricas()
        info = "nós %d · hifas %d · pop %d · fit %.2f · cur %.2f" % (
            met["nos"], met["arestas"], len(o.mundo.bichos),
            o.cog.fitness, o.cog.curiosidade)
        escreve(buf, max(1, cols-len(info)-1), 0, info, (150, 160, 180))

    # ─────────────── modo 1: MICÉLIO ───────────────
    def _v_micelio(self, o, buf, reg):
        x0, y0, w, h = reg
        cv = CanvasBraille(w, h)
        mic = o.mic
        if not self.pausado:
            relaxar_layout(mic, self.rng)
        # arestas (hifas): brilho ∝ peso
        for (i, j) in mic._arestas_ids():
            a = mic.nos.get(i); b = mic.nos.get(j)
            if not a or not b:
                continue
            e = mic.adj[i].get(j) or mic.adj[j].get(i)
            if not e:
                continue
            ax, ay = self._mapa(cv.W, cv.H, a.x, a.y)
            bx, by = self._mapa(cv.W, cv.H, b.x, b.y)
            cor = _clar((90, 130, 200), 0.4 + 0.6*e[0])
            cv.linha(ax, ay, bx, by, cor, 0.4 + 0.6*e[0])
        # pulsos (conhecimento fluindo)
        for pa, pb, prog, cor in list(mic.pulsos):
            a = mic.nos.get(pa); b = mic.nos.get(pb)
            if not a or not b:
                continue
            ax, ay = self._mapa(cv.W, cv.H, a.x, a.y)
            bx, by = self._mapa(cv.W, cv.H, b.x, b.y)
            px = ax + (bx-ax)*prog; py = ay + (by-ay)*prog
            cv.disco(px, py, 1, cor, 1.0)
        # nós (conceitos): tamanho ∝ vitalidade; núcleo branco se fundido
        for c in mic.nos.values():
            px, py = self._mapa(cv.W, cv.H, c.x, c.y)
            r = 1 + int(c.vitalidade()*2.5) + (1 if c.ordem > 0 else 0)
            cv.disco(px, py, r, cor_conceito(c), 0.6 + 0.4*c.ativ)
            if c.ativ > 0.6:
                cv.disco(px, py, 1, (255, 255, 255), c.ativ)
        # hifas (subagentes) orbitando por papel
        self._orbita_hifas(o, cv)
        self._passo_part(cv)
        cv.blit(buf, x0, y0)
        escreve(buf, x0+1, y0, " %s · %d conceitos · %d fusões · %d esquecidos " % (
            MODO_NOME["micelio"], len(mic.nos), mic.fundidos, mic.esquecidos),
            (180, 220, 255))

    def _orbita_hifas(self, o, cv):
        censo = o.col.censo(o.mundo)
        i = 0; tot = max(1, sum(censo.values()))
        for k, (papel, n) in enumerate(censo.items()):
            for _ in range(min(n, 12)):
                ang = (i/ tot)*6.283 + self.frame*0.03
                rad = 0.30 + 0.12*k
                px = cv.W*(0.5 + math.cos(ang)*rad)
                py = cv.H*(0.5 + math.sin(ang)*rad)
                cv.disco(px, py, 1, PAPEL_COR[papel], 0.9)
                i += 1

    # ─────────────── modo 2: FLUXO DE CONHECIMENTO ───────────────
    def _v_fluxo(self, o, buf, reg):
        x0, y0, w, h = reg
        cv = CanvasBloco(w, h)
        mic = o.mic
        if not self.pausado:
            relaxar_layout(mic, self.rng)
        # brilho de fundo pela ativação dos nós próximos (campo de energia)
        for c in mic.nos.values():
            px, py = self._mapa(cv.W, cv.H, c.x, c.y)
            if c.ativ > 0.08:
                cv.disco(px, py, 1 + int(c.ativ*3), _clar(cor_conceito(c), 0.5+0.5*c.ativ),
                         0.3 + 0.7*c.ativ)
        # pacotes de energia correndo pelas hifas mais fortes
        for (i, j) in mic._arestas_ids():
            e = mic.adj[i].get(j) or mic.adj[j].get(i)
            if not e or e[0] < 0.25:
                continue
            a = mic.nos.get(i); b = mic.nos.get(j)
            if not a or not b:
                continue
            ax, ay = self._mapa(cv.W, cv.H, a.x, a.y)
            bx, by = self._mapa(cv.W, cv.H, b.x, b.y)
            fase = (self.frame*0.06 + (i*13 + j*7) % 10 / 10.0) % 1.0
            px = ax + (bx-ax)*fase; py = ay + (by-ay)*fase
            cv.disco(px, py, 1, _clar((160, 240, 255), e[0]), e[0])
        for pa, pb, prog, cor in list(mic.pulsos):
            a = mic.nos.get(pa); b = mic.nos.get(pb)
            if a and b:
                ax, ay = self._mapa(cv.W, cv.H, a.x, a.y)
                bx, by = self._mapa(cv.W, cv.H, b.x, b.y)
                cv.disco(ax+(bx-ax)*prog, ay+(by-ay)*prog, 1, cor, 1.0)
        self._passo_part(cv)
        cv.blit(buf, x0, y0)
        ativos = mic.ativos(1)
        foco = ativos[0].rotulo if ativos else "—"
        escreve(buf, x0+1, y0, " %s · foco: «%s» " % (MODO_NOME["fluxo"], foco[:24]),
                (170, 240, 255))

    # ─────────────── modo 3: MAPA COGNITIVO ───────────────
    def _v_mapa(self, o, buf, reg):
        x0, y0, w, h = reg
        cv = CanvasBraille(w, h)
        mic = o.mic
        if not self.pausado:
            relaxar_layout(mic, self.rng)
        for (i, j) in mic._arestas_ids():
            a = mic.nos.get(i); b = mic.nos.get(j)
            if a and b:
                ax, ay = self._mapa(cv.W, cv.H, a.x, a.y)
                bx, by = self._mapa(cv.W, cv.H, b.x, b.y)
                cv.linha(ax, ay, bx, by, (70, 90, 130), 0.5)
        for c in mic.nos.values():
            px, py = self._mapa(cv.W, cv.H, c.x, c.y)
            cv.disco(px, py, 1 + (1 if c.ordem > 0 else 0), cor_conceito(c), 0.9)
        cv.blit(buf, x0, y0)
        # rótulos dos conceitos mais vitais (legibilidade)
        top = sorted(mic.nos.values(), key=lambda c: -c.vitalidade())[:14]
        for c in top:
            px, py = self._mapa(cv.W, cv.H, c.x, c.y)
            tx = x0 + int(px/2) + 1; ty = y0 + int(py/4)
            cor = (255, 240, 180) if c.ordem > 0 else (200, 210, 230)
            escreve(buf, tx, ty, c.rotulo[:14], cor)
        escreve(buf, x0+1, y0, " %s · %d ideias (ordem>0: %d) " % (
            MODO_NOME["mapa"], len(mic.nos),
            sum(1 for c in mic.nos.values() if c.ordem > 0)), (210, 220, 240))

    # ─────────────── modo 4: GENOMA COMPORTAMENTAL ───────────────
    def _v_genoma(self, o, buf, reg):
        x0, y0, w, h = reg
        cv = CanvasBloco(w, h)
        # hélice de DNA girando (à esquerda)
        hx = cv.W*0.28
        for yy in range(cv.H):
            t = yy/6.0 + self.frame*0.12
            a = math.sin(t)*cv.W*0.16; b = math.sin(t+math.pi)*cv.W*0.16
            c1 = _hsv((yy/cv.H)*0.5, 0.6, 1.0); c2 = _hsv((yy/cv.H)*0.5+0.5, 0.6, 1.0)
            cv.plot(hx+a, yy, c1, 1.0); cv.plot(hx+b, yy, c2, 1.0)
            if yy % 3 == 0:                      # "pares de base" ligando as fitas
                x1 = hx+a; x2 = hx+b
                for xx in range(int(min(x1, x2)), int(max(x1, x2))+1):
                    cv.plot(xx, yy, (90, 110, 140), 0.5)
        cv.blit(buf, x0, y0)
        # médias de genes da população (à direita)
        tr = o.mundo.traco_medio()
        gx = x0 + int(cv.W*0.52)
        escreve(buf, gx, y0+1, "genoma médio da colônia", (200, 230, 255))
        for i, g in enumerate(GENES):
            v = tr.get(g, 0.0); larg = int(v*18)
            barra = "█"*larg + "░"*(18-larg)
            cor = _hsv(i/len(GENES), 0.5, 0.95)
            escreve(buf, gx, y0+3+i, "%-7s " % g[:7], (170, 180, 200))
            escreve(buf, gx+8, y0+3+i, barra, cor)
            escreve(buf, gx+27, y0+3+i, "%.2f" % v, (200, 210, 230))
        # distribuição de papéis (especialização)
        censo = o.col.censo(o.mundo); tot = max(1, sum(censo.values()))
        yb = y0 + 3 + len(GENES) + 1
        escreve(buf, gx, yb, "especialização (hifas)", (200, 230, 255))
        for i, papel in enumerate(PAPEIS):
            n = censo.get(papel, 0); larg = int(n/tot*18)
            escreve(buf, gx, yb+2+i, "%-13s " % papel, PAPEL_COR[papel])
            escreve(buf, gx+14, yb+2+i, "█"*larg + "░"*(18-larg), PAPEL_COR[papel])
            escreve(buf, gx+33, yb+2+i, str(n), (200, 210, 230))
        escreve(buf, x0+1, y0, " %s " % MODO_NOME["genoma"], (220, 230, 255))

    # ─────────────── modo 5: ECOSSISTEMA DE AGENTES ───────────────
    def _v_ecossistema(self, o, buf, reg):
        x0, y0, w, h = reg
        cv = CanvasBloco(w, h)
        mundo = o.mundo
        cx, cy = mundo.pos
        esc = clamp(self.zoom, 0.4, 4.0)
        def m2p(wx, wy):
            return (cv.W/2 + (wx-cx)*esc, cv.H/2 + (wy-cy)*esc)
        # pólen (alimento) e fósseis (ao fundo)
        for (wx, wy) in list(mundo.polen.keys())[:1200]:
            px, py = m2p(wx, wy); cv.plot(px, py, (60, 90, 70), 0.5)
        for (wx, wy) in list(mundo.fosseis.keys())[:400]:
            px, py = m2p(wx, wy); cv.plot(px, py, (90, 80, 70), 0.6)
        # obras/chão
        pal = paleta_efetiva(o.mente)
        for (wx, wy), (gl, co) in list(mundo.celulas.items())[:2500]:
            px, py = m2p(wx, wy)
            cv.plot(px, py, ansi_rgb(pal[co % len(pal)]), 0.7)
        # hifas (bichos) coloridas pelo papel
        for b in mundo.bichos:
            px, py = m2p(*b.pos)
            papel = o.col.papel(b)
            cv.disco(px, py, 1, PAPEL_COR[papel], 0.6 + 0.4*b.vitalidade())
        # a LUMEN
        lx, ly = m2p(*mundo.pos)
        cv.disco(lx, ly, 2, (140, 255, 255), 1.0)
        self._passo_part(cv)
        cv.blit(buf, x0, y0)
        escreve(buf, x0+1, y0, " %s · %d hifas vivas · ger %d · %d obras " % (
            MODO_NOME["ecossistema"], len(mundo.bichos), mundo.ger_max,
            len(mundo.celulas)), (170, 255, 200))

    # ─────────────── modo 6: LINHA TEMPORAL EVOLUTIVA ───────────────
    def _v_timeline(self, o, buf, reg):
        x0, y0, w, h = reg
        cv = CanvasBraille(w, h)
        series = [
            ("fitness", list(o.cog.fit_hist), (255, 220, 120)),
            ("coerência", [m["coerencia"] for m in o.mic.hist], (120, 220, 255)),
            ("utilidade", [m["utilidade"] for m in o.mic.hist], (150, 255, 150)),
            ("complexidade", [m["complexidade"] for m in o.mic.hist], (200, 150, 255)),
            ("diversidade", [m["diversidade"] for m in o.mic.hist], (255, 160, 200)),
        ]
        faixa = cv.H / len(series)
        for si, (nome, serie, cor) in enumerate(series):
            base_y = faixa*(si+1) - 2
            if len(serie) >= 2:
                mx = max(1e-6, max(serie)); n = len(serie)
                px_ant = py_ant = None
                for k, v in enumerate(serie[-cv.W:]):
                    px = k*(cv.W/min(n, cv.W))
                    py = base_y - (v/mx)*(faixa*0.8)
                    if px_ant is not None:
                        cv.linha(px_ant, py_ant, px, py, cor, 0.9)
                    px_ant, py_ant = px, py
        cv.blit(buf, x0, y0)
        for si, (nome, serie, cor) in enumerate(series):
            val = serie[-1] if serie else 0.0
            escreve(buf, x0+1, y0 + int(faixa*si/4) + 1, "%s %.2f" % (nome, val), cor)
        escreve(buf, x0+1, y0, " %s · reorganizações: %d · estilo ger %d " % (
            MODO_NOME["timeline"], o.cog.reorganizacoes, o.mente.estilo.geracoes),
            (220, 220, 240))

    # ─────────────── HUD (rodapé, todos os modos) ───────────────
    def _rodape(self, o, buf, cols, rows):
        y = rows - 4
        # apetites em true color
        cor_ap = {"curiosidade": (120, 220, 255), "beleza": (200, 150, 255),
                  "ordem": (150, 200, 255), "companhia": (150, 255, 170),
                  "impeto": (255, 150, 120), "expressao": (230, 210, 255)}
        x = 1
        for a in APETITES:
            v = o.mente.vontade.v[a]; n = int(round(v*8))
            escreve(buf, x, y, a[:3], cor_ap[a])
            escreve(buf, x+4, y, "▮"*n + "▯"*(8-n), cor_ap[a])
            x += 4 + 8 + 2
        # estado da colônia
        rel = o.sup.relatorio()
        est = "curiosidade %.2f · fitness %.2f · plano→%s · guardião:%s(%d)" % (
            o.cog.curiosidade, o.cog.fitness, o.cog.meta_atual or "—",
            rel["integridade"], rel["violacoes"])
        escreve(buf, 1, y+1, est[:cols-2], (170, 180, 200))
        # ticker de eventos
        evs = o.ev.recentes(1)
        if evs:
            e = evs[-1]
            desc = _descr_evento(e)
            escreve(buf, 1, y+2, ("» " + desc)[:cols-2], (150, 210, 190))
        # legenda de teclas
        leg = "1-6 modos · tab alterna · +/- zoom · espaço pausa · q sai"
        escreve(buf, 1, y+3, leg[:cols-2], (110, 120, 140))

def _descr_evento(e):
    t = e["t"]; d = e.get("d", {})
    if t == "digerir":
        return "digestão: %d aceitos, %d novos (%s)" % (
            d.get("aceitos", 0), d.get("novos", 0), d.get("origem", "?"))
    if t == "hipotese":
        return "hipótese: liga «%s» ↔ «%s»" % (d.get("a", "?"), d.get("b", "?"))
    if t == "reorganizar":
        return "reorganização da colônia (fitness %.2f)" % d.get("fitness", 0)
    if t == "fundir_hifa":
        return "duas hifas %s se fundem" % d.get("papel", "")
    if t == "forrageio":
        return "forrageio: o mundo pinga «%s»" % d.get("o", "?")
    if t == "nivel":
        return "maestria cresce → Nv%d" % d.get("nivel", 0)
    return t

# ═══════════════════════════ ORGANISMO (integração) ═══════════════════════════
# Junta a base viva (Mente/Mundo/Compositor/Língua) com os órgãos novos
# (micélio, hifas, digestão, cognição, supervisor, microscópio) num só ser.

CAMPO_MUNDO = {"cores": None, "adjetivos": "adjs", "nomes": "nouns",
               "animais": "animals", "monstros": "greek_monsters"}

def _amostra_mundo(chave, dados, rng, n=8):
    if chave == "cores":
        lst = dados.get("colors", [])
        return [str(c.get("color", "")) for c in rng.sample(lst, min(n, len(lst)))] if lst else []
    campo = CAMPO_MUNDO.get(chave)
    lst = dados.get(campo, []) if campo else []
    return [str(p) for p in rng.sample(lst, min(n, len(lst)))] if lst else []

class Organismo:
    """O ser completo. Uma referência circular controlada com a Mente permite
    que o save/load da base persista também os órgãos novos (versão 3)."""

    def __init__(self, mente, lingua, comp, narr, janela, rng, sandbox, leve=False):
        self.mente = mente; self.mundo = mente.caixa; self.lingua = lingua
        self.comp = comp; self.narr = narr; self.janela = janela; self.rng = rng
        self.mic = Micelio(rng); self.dig = Digestor(rng)
        self.col = Colonia(self.mic, self.dig, rng)
        self.cog = Cognicao(rng); self.ev = BarramentoEventos()
        self.sup = Supervisor(sandbox)
        self.micro = Microscopio(rng, leve=leve)
        self.tick = 0
        mente.organismo = self
        raw = getattr(mente, "_organismo_raw", None)
        if raw:
            self._carregar(raw)
        if not self.mic.nos:
            self._semear_inicial()

    def _semear_inicial(self):
        """Primeiras sementes: os conceitos nativos da base viram o núcleo do
        micélio, já entrelaçados. O conhecimento começa pequeno e conectado."""
        criados = []
        for c in CONCEITOS[:20]:
            n = self.mic.brotar(c, 0.7, 0.6, "semente")
            if n:
                criados.append(n)
        for _ in range(min(28, len(criados)*2)):
            if len(criados) >= 2:
                a, b = self.rng.sample(criados, 2)
                self.mic.conectar(a, b, 0.15)

    def _carregar(self, raw):
        try:
            self.mic.carregar(raw.get("micelio", {}))
            self.col.carregar(raw.get("colonia", {}))
            self.cog.carregar(raw.get("cognicao", {}))
            self.sup.carregar(raw.get("supervisor", {}))
            dg = raw.get("digestor", {})
            self.dig.aceitos = dg.get("aceitos", 0)
            self.dig.rejeitados = dg.get("rejeitados", 0)
            self.dig.ingeridos = dg.get("ingeridos", 0)
        except Exception:
            pass

    def dump(self):
        return {"micelio": self.mic.dump(), "colonia": self.col.dump(),
                "cognicao": self.cog.dump(), "supervisor": self.sup.dump(),
                "digestor": {"aceitos": self.dig.aceitos,
                             "rejeitados": self.dig.rejeitados,
                             "ingeridos": self.dig.ingeridos}}

    # ─────────────── forrageio autônomo (só quando há necessidade real) ───────────────
    def _forragear(self):
        estado = self.mente.estado
        pode, _motivo = self.sup.permite_forrageio(self.cog, self.janela, self.mente, estado)
        if not pode:
            return None
        chave = self.rng.choice(list(FONTES_MUNDO.keys()))
        dados, origem = self.janela.buscar(chave, self.mente, estado)
        if not dados:
            return None
        nut = absorver(self.mente, chave, dados, self.rng)   # comportamento da base
        palavras = _amostra_mundo(chave, dados, self.rng, 10)
        if palavras:
            self.col.enfileirar(" ".join(palavras), "mundo")
        self.cog.saciar_curiosidade(0.5)
        self.ev.emitir("forrageio", o=(nut[1] if nut else chave))
        return nut

    # ─────────────── criar uma obra (a base criativa preservada) ───────────────
    def _criar_obra(self):
        tipo, apet = self.mente.escolher_intencao(self.rng)
        genes = self.mente.estilo.propor(self.rng)
        art = self.comp.criar(tipo, apet, genes)
        # a obra semeia conhecimento: o conceito entra no micélio e se liga ao ativo
        conceito = art.meta.get("conceito")
        if conceito:
            c = self.mic.brotar(conceito, 0.6, art.novidade, "obra")
            if c:
                for a in self.mic.ativos(4):
                    self.mic.conectar(c, a, 0.1)
                self.mic.ativar([c.id], 0.6, (200, 220, 255))
        satisf, subiu = self.mente.integrar(art, apet, self.rng)
        qual = clamp(0.5*art.scores["estetica"] + 0.32*art.scores["variedade"]
                     + 0.18*art.scores["complexidade"], 0, 1)
        self.mente.estilo.avaliar_e_mover(genes, qual)
        self.comp.salvar_arquivo(art)
        if art.tipo == "criatura" and getattr(art, "_genoma", None):
            self.mundo.semear_bicho(self.mundo.pos, self.comp._cor(), self.rng, art._genoma)
        if subiu:
            self.ev.emitir("nivel", nivel=self.mente.nivel)
        return art, satisf

    # ─────────────── um tick vivo completo ───────────────
    def passo(self, args, t0):
        self.tick += 1
        m = self.mente
        m.vontade.tick()
        apet = m.vontade.dominante()
        self.cog.observar_apetite(apet)
        self.cog.observar_populacao(len(self.mundo.bichos))

        met_antes = self.mic.metricas()

        # digestão passiva do inbox (alimentação manual de alta qualidade)
        if args.inbox and self.tick % 12 == 0:
            for est in alimentar_inbox(args.inbox, self.dig, self.mic, self.ev):
                pass

        # forrageio autônomo só sob necessidade real
        acao_forr = None
        if self.tick % 4 == 0:
            if self._forragear():
                acao_forr = "forragear"

        # ecossistema respira; hifas pensam; micélio evolui
        self.mundo.tick_vida()
        self.col.passo(self.mundo, self.cog, self.ev,
                       orcamento=6 if args.leve else 12)
        self.mic.passo()
        self.cog.passo()

        # planejamento periódico
        if self.tick % 6 == 0:
            self.cog.planejar(self.mic.metricas())

        # criação (base preservada) numa cadência ligada à maestria
        cadencia = max(5, 12 - m.nivel)
        if self.tick % cadencia == 0 and not self.micro.pausado:
            self._criar_obra()

        # autoavaliação + raciocínio causal + reorganização
        met = self.mic.metricas()
        _fit, delta = self.cog.avaliar(met, self.col.censo(self.mundo), self.sup.objetivo())
        for a in (acao_forr, self.cog.meta_atual):
            if a:
                self.cog.registrar_causa(a if a in ACOES_COG else "explorar", delta)
        if self.cog.precisa_reorganizar():
            self.cog.reorganizar(self.mic, self.mundo, self.col, self.ev)

        # supervisão (contenção dura a cada tick)
        dt_ms = (time.time() - t0) * 1000.0
        self.sup.fiscalizar(self.mic, self.mundo, self.col, self.cog, self.janela, dt_ms)

def viver_colonia(o, args, caminho):
    """Laço vivo do organismo-colmeia com o microscópio em tempo real.
    Gera a cada tick (para o main contar/salvar)."""
    o.ev.emitir("genese")
    with Teclado() as teclado:
        while True:
            t0 = time.time()
            if not args.headless:
                seguir = o.micro.tecla(teclado.ler())
                if not seguir:
                    return
            if not o.micro.pausado:
                o.passo(args, t0)
            if not args.headless:
                o.micro.semear_eventos(o.ev)
                o.micro.render(o)
                alvo = 0.05 if not args.leve else 0.09
                time.sleep(clamp(alvo/max(0.1, args.velocidade), 0.008, 0.4))
            if o.tick % 30 == 0:
                try:
                    o.mente.salvar(caminho, o.lingua)
                except OSError:
                    pass
            yield

# ═══════════════════════════ EXECUÇÃO ═══════════════════════════

def main():
    ap = argparse.ArgumentParser(description="LUMEN — A Caixa Viva: uma IA que só cria")
    ap.add_argument("--velocidade", type=float, default=1.0)
    ap.add_argument("--save", type=str, default=None)
    ap.add_argument("--dir", type=str, default=None)
    ap.add_argument("--max-arquivos", type=int, default=300)
    ap.add_argument("--narracao", type=int, default=8)
    ap.add_argument("--online", action="store_true",
                    help="abre a janela para o mundo (dados públicos controlados). Padrão: desligado")
    ap.add_argument("--cota", type=int, default=20,
                    help="máximo de buscas ao mundo por dia")
    ap.add_argument("--dir-mundo", type=str, default=None,
                    help="pasta de cache dos dados do mundo")
    ap.add_argument("--sem-ocio", action="store_true",
                    help="desliga as pausas de ócio (produção contínua)")
    ap.add_argument("--sem-svg", action="store_true",
                    help="não exporta as obras como SVG animado (galeria/)")
    ap.add_argument("--reset", action="store_true")
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--ticks", type=int, default=0)
    ap.add_argument("--semente", type=int, default=None)
    # ─── organismo-colmeia (novo; padrão) ───
    ap.add_argument("--classico", action="store_true",
                    help="usa a tela única original (A Caixa Viva) em vez do microscópio")
    ap.add_argument("--leve", action="store_true",
                    help="reduz partículas/atualização para aparelhos modestos")
    ap.add_argument("--alimentar", type=str, nargs="*", default=None,
                    help="alimenta a colônia com um ou mais .txt de alta qualidade (digestão)")
    ap.add_argument("--inbox", type=str, default=None,
                    help="pasta 'inbox' de .txt consumidos aos poucos como alimento")
    ap.add_argument("--modo", type=str, default="micelio", choices=MODOS,
                    help="modo inicial do microscópio")
    args = ap.parse_args()

    base = os.path.dirname(os.path.abspath(__file__))
    caminho = args.save or os.path.join(base, "lumen_mente.json")
    sandbox = args.dir or os.path.join(base, "lumen_criacoes")
    if args.reset and os.path.exists(caminho):
        os.remove(caminho)
    n_narr = clamp(args.narracao, 3, 12)

    mente, restaurado = Mente.carregar(caminho)
    mente.max_arquivos = args.max_arquivos
    rng = random.Random(args.semente)
    lingua = Lingua(rng, mente.lingua_estado)
    if mente.caixa is None:
        mente.caixa = Mundo(rng=rng)
    mente.caixa.rng = rng          # rng principal → ecossistema determinístico com --semente
    comp = Compositor(mente, mente.caixa, lingua, rng, sandbox)
    narr = Narrador(rng)
    dir_mundo = args.dir_mundo or os.path.join(base, "lumen_mundo")
    janela = Janela(dir_mundo, args.online, args.cota, rng)
    mente._online = args.online
    mente._cota_dia = args.cota
    mente._svg = not args.sem_svg
    salvo_ref = [0]

    def _sinal(_s, _f): raise KeyboardInterrupt
    for s in ("SIGTERM", "SIGHUP"):
        if hasattr(signal, s):
            try: signal.signal(getattr(signal, s), _sinal)
            except (OSError, ValueError): pass

    # ─── monta o organismo-colmeia (a menos que --classico) ───
    org = None
    if not args.classico:
        org = Organismo(mente, lingua, comp, narr, janela, rng, sandbox, leve=args.leve)
        org.micro.modo = MODOS.index(args.modo)
        if args.alimentar:
            for cam in args.alimentar:
                est = alimentar_arquivo(cam, org.dig, org.mic, org.ev)
                msg = ("· alimentada: %s → %d aceitos, %d novos" % (
                       os.path.basename(cam), est["aceitos"], est["novos"])
                       if est else "· não pôde ler: %s" % cam)
                sys.stdout.write(msg + "\n")

    if not args.headless:
        sys.stdout.write(HIDE + CLEAR)
    try:
        mente._acordou = restaurado
        if org is not None:
            ciclo = viver_colonia(org, args, caminho)
        else:
            ciclo = viver(mente, mente.caixa, lingua, comp, narr, janela, args, rng, salvo_ref, n_narr)
        feitas = 0
        for _ in ciclo:
            if org is None:
                mente.salvar(caminho, lingua); salvo_ref[0] = 25
            feitas += 1
            if args.headless and args.ticks and feitas >= args.ticks:
                break
    except KeyboardInterrupt:
        pass
    finally:
        try:
            mente.salvar(caminho, lingua)
            ok = "%s✓ MENTE SALVA%s → %s" % (C_OK, RESET, caminho)
        except OSError as e:
            ok = "%sfalha ao salvar: %s%s" % (fg(203), e, RESET)
        if not args.headless:
            sys.stdout.write(SHOW + RESET + "\n")
        vivos = len(mente.caixa.bichos)
        if org is not None:
            met = org.mic.metricas()
            sys.stdout.write(
                "%s\n%s◉ LUMEN-colmeia adormece. Nv%d «%s» · micélio: %d conceitos / %d hifas · "
                "fitness %.2f · coerência %.2f · %d fusões de ideias · %d esquecidos · "
                "%d hifas vivas · reorganizações %d · guardião %s.\n"
                "Conhecimento digerido: %d aceitos / %d rejeitados. Artefatos em: %s\n"
                "Rode de novo e a colônia acorda onde parou.%s\n" % (
                    ok, C_STAT, mente.nivel, mente.nome_nivel(), met["nos"], met["arestas"],
                    org.cog.fitness, met["coerencia"], org.mic.fundidos, org.mic.esquecidos,
                    vivos, org.cog.reorganizacoes, org.sup.relatorio()["integridade"],
                    org.dig.aceitos, org.dig.rejeitados, sandbox, RESET))
        else:
            janela_txt = ("janela ligada, %d fragmentos do mundo absorvidos" % mente.mundo_visto
                          if mente._online else "janela desligada (offline)")
            sys.stdout.write(
                "%s\n%s◉ LUMEN dorme no mundo sem fim. Nv%d «%s» · %d obras · %d palavras na língua dela · "
                "%d criaturas vivas (ger %d) · %d obras das criaturas · estilo geração %d · %s.\nArtefatos em: %s\n"
                "Rode de novo e ela acorda entre as próprias coisas.%s\n" % (
                    ok, C_STAT, mente.nivel, mente.nome_nivel(), mente.criacoes, len(lingua.lexico),
                    vivos, mente.caixa.ger_max, mente.caixa.criados_bicho,
                    mente.estilo.geracoes, janela_txt, sandbox, RESET))
        sys.stdout.flush()

if __name__ == "__main__":
    main()
