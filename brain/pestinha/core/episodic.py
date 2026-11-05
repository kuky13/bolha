"""
EPISODIC - o que aconteceu de verdade, e o que fazer da próxima vez.

Memória episódica: cada travessura vira um episódio
    contexto (atividade + emoção) -> ação -> resultado -> valência
Ex.: WORK|curioso -> bilhete -> dispensado em 1,2 s -> -0,76

Seleção de ações: um bandit contextual (tabela por contexto, sem rede
profunda). A rede neural continua decidindo o que ele SENTE; esta tabela
decide qual travessura fazer, pelo que deu certo antes naquele contexto.
As regras de segurança (permissões, tela cheia, limite de objetos) vêm
antes e não são aprendidas.

Sono: consolida a memória. Refaz a tabela a partir dos episódios guardados,
pesando os recentes mais que os antigos.
"""

from ..log import log
import json
import math
import random
import time
from collections import deque
from datetime import datetime

from ..store import read_json, write_json, write_lines

ACTIONS = ["meme", "foto", "bilhete", "atravessar", "nada"]
CORNER_ACTIONS = ["meme_canto", "bilhete_canto", "nada"]

PRIOR = 0.1                 # otimismo inicial: tudo vale tentar
PRIOR_WEIGHT = 2.0          # quantos "episódios imaginários" o otimismo vale
GLOBAL_WEIGHT = 3.0         # com poucos episódios no contexto, usa a média geral da ação
RECENCY_HALF_LIFE = 150     # episódios: na consolidação, metade do peso a cada 150
MAX_COUNT = 40              # aprendizado online nunca fica "duro" demais
KEEP_EPISODES = 500
MAX_CONTEXTS = 256
MAX_ACTIONS = 32
CASTIGO_VALENCIA = -0.8     # travessura seguida de castigo conta como muito ruim


def _sem_nan(valor):
    """Recusa NaN e infinito: uma constante assim quebraria o aprendizado sem aviso."""
    raise ValueError(f"constante não permitida: {valor}")


def _episodio_valido(ep):
    """Um episódio salvo só vale se tiver contexto e ação do tipo certo; o resto é descartado ao carregar."""
    if not isinstance(ep, dict) or not isinstance(ep.get("contexto"), str) or len(ep['contexto']) > 128 or not ep.get("acao"):
        return False
    if not isinstance(ep.get("acao"), str) or len(ep['acao']) > 40:
        return False
    v = ep.get("valencia")
    return type(v) in (int, float) and math.isfinite(v) and -1.0 <= v <= 1.0


def _estatistica_valida(par):
    """[n, média] com n não negativo e média finita dentro de [-1, 1]."""
    n, media = par
    if type(n) not in (int, float) or type(media) not in (int, float):
        raise ValueError("estatística com tipo errado")
    n, media = float(n), float(media)
    if not (math.isfinite(n) and math.isfinite(media)) or n < 0 or not -1.0 <= media <= 1.0:
        raise ValueError("estatística inválida")
    return [n, media]


def _tabela_valida(bruta, por_contexto):
    """Descarta o que não tem o formato da memória; o que sobra fica igual ao que foi gravado."""
    if not isinstance(bruta, dict):
        return {}
    out = {}
    try:
        if por_contexto:
            for ctx, acoes in list(bruta.items())[-MAX_CONTEXTS:]:
                if isinstance(ctx, str) and isinstance(acoes, dict):
                    out[ctx] = {a: _estatistica_valida(v) for a, v in list(acoes.items())[-MAX_ACTIONS:] if isinstance(a, str) and len(a) <= 40}
        else:
            out = {a: _estatistica_valida(v) for a, v in bruta.items() if isinstance(a, str)}
    except (TypeError, ValueError):
        return {}
    return out


def dismiss_valence(elapsed, patience=30.0):
    """Fechou na hora: -0,8. Fechou depois de 30 s: -0,2."""
    return -0.8 + 0.6 * min(elapsed / patience, 1.0)


class EpisodicMemory:
    """Memória de travessuras: lembra o que deu certo em cada situação (atividade + emoção) e escolhe a próxima ação por tentativa e erro."""
    def __init__(self, episodes_path, prefs_path, rng=None):
        """Guarda os caminhos dos arquivos de episódios e de preferências."""
        self.episodes_path = episodes_path
        self.prefs_path = prefs_path
        self.open = []              # episódios esperando o resultado
        self.recent = []            # episódios resolvidos (em RAM)
        self.table = {}             # "ATIVIDADE|emoção" -> {ação: [n, média]}
        self.totals = {}            # ação -> [n, média] (todos os contextos)
        self.last_choice = None     # (contexto, ação, motivo) para o terminal
        self.ultima_acao = None     # episódio da última travessura, para o castigo ensinar
        self._contador = 0
        self.dirty = False
        self.rng = rng or random.Random()

    # ---------------- escolha ----------------

    @staticmethod
    def context(activity, emotion):
        """Chave de contexto: atividade e emoção juntas (ex.: 'PROGRAMMING|feliz')."""
        return f"{activity}|{emotion}"

    def estimate(self, ctx, action):
        """Estimativa de quão boa é uma ação num contexto; com pouca experiência, puxa para a média geral."""
        n, mean = self.table.get(ctx, {}).get(action, [0, 0.0])
        gn, gmean = self.totals.get(action, [0, 0.0])
        base = (PRIOR * PRIOR_WEIGHT + gmean * min(gn, GLOBAL_WEIGHT)) / (PRIOR_WEIGHT + min(gn, GLOBAL_WEIGHT))
        return (n * mean + GLOBAL_WEIGHT * base) / (n + GLOBAL_WEIGHT)

    def choose(self, ctx, allowed, epsilon, bias=None):
        """Escolhe uma ação permitida: a melhor na maior parte das vezes, e às vezes (epsilon) uma aleatória, para explorar."""
        if not allowed:
            return None
        if self.rng.random() < epsilon:
            action = self.rng.choice(allowed)
            self.last_choice = (ctx, action, "explorando")
            return action
        scored = sorted(((self.estimate(ctx, a) + (bias or {}).get(a, 0), a) for a in allowed), reverse=True)
        best = scored[0][0]
        ties = [a for score, a in scored if score >= best - 1e-9]
        action = self.rng.choice(ties)
        self.last_choice = (ctx, action, f"melhor estimativa {best:+.2f}")
        return action

    # ---------------- episódios ----------------

    def start(self, ctx, action, thing=None):
        """Começa um episódio: registra a ação e o contexto, esperando o resultado (aceitar, dispensar, fugir)."""
        if len(self.open) >= 12:
            self._resolve(self.open[0], 'sem resposta', 0.0)
        self._contador += 1
        episode = {
            "id": f"{time.time_ns()}-{self._contador}",     # identidade estável (para revisar depois)
            "quando": datetime.now().isoformat(timespec="seconds"),
            "contexto": ctx,
            "acao": action,
            "inicio": time.monotonic(),
            "thing": thing,
            "carinho": False,
        }
        self.open.append(episode)
        self.ultima_acao = episode
        return episode

    def punir(self, now, janela):
        """
        Castigo logo depois de uma travessura: exatamente aquele episódio vira ruim.
        Aberto, é resolvido como castigo. Já resolvido, o registro dele é revisado (no
        arquivo também), para o sono reconstruir o mesmo valor sem contar duas vezes.
        """
        ep = self.ultima_acao
        if ep is None or now - ep["inicio"] > janela or ep["acao"] == "nada":
            return None
        self.ultima_acao = None
        if any(aberto is ep for aberto in self.open):
            self._resolve(ep, "castigo logo depois", CASTIGO_VALENCIA)
        else:
            self._revisar(ep["id"], "castigo logo depois", CASTIGO_VALENCIA)
        return ep["acao"]

    def _revisar(self, ep_id, result, valence):
        """Troca o resultado de um episódio já resolvido (RAM, tabela e arquivo)."""
        record = next((r for r in self.recent if r.get("id") == ep_id), None)
        if record is None:
            return
        antigo = record["valencia"]
        record["resultado"], record["valencia"] = result, round(valence, 3)
        self.dirty = True
        for stats in (self.table.setdefault(record["contexto"], {}).setdefault(record["acao"], [1, antigo]),
                      self.totals.setdefault(record["acao"], [1, antigo])):
            stats[1] += (valence - antigo) / max(stats[0], 1)    # substitui uma amostra da média
        log(f"[memória] {record['contexto']} -> {record['acao']}: revisado, {result} ({valence:+.2f})")

    def on_dismiss(self, thing, elapsed, patience):
        """Você dispensou a travessura: vale mais se foi rápido, e a valência fica registrada."""
        for ep in list(self.open):
            if ep["thing"] is thing:
                valence = dismiss_valence(elapsed, patience)
                self._resolve(ep, f"dispensado em {elapsed:.1f} s", valence)

    def on_interaction(self):
        """Você deu atenção ao pet logo depois de uma ação dele: conta a favor."""
        for ep in self.open:
            ep["carinho"] = True

    def tick(self, now, keep_ok, window):
        """Ausência de resposta é neutra; carinho e dispensa são sinais explícitos."""
        for ep in list(self.open):
            age = now - ep["inicio"]
            if ep["thing"] is not None:
                if age >= keep_ok:
                    self._resolve(ep, 'recebeu carinho' if ep['carinho'] else 'sem resposta', 0.6 if ep['carinho'] else 0.0)
            elif age >= window:
                result = "você deu atenção depois" if ep["carinho"] else "nada aconteceu"
                self._resolve(ep, result, 0.5 if ep["carinho"] else 0.0)

    def deslocar(self, segundos):
        """A pausa não conta: os episódios pendentes ganham o tempo parado de volta."""
        for ep in self.open:
            ep["inicio"] += segundos
        if self.ultima_acao is not None and not any(ep is self.ultima_acao for ep in self.open):
            self.ultima_acao["inicio"] += segundos        # a janela do castigo também não corre na pausa

    def cancel_thing(self, thing):
        """Remove episódio pendente sem penalizar quando um recurso externo falha."""
        for ep in list(self.open):
            if ep["thing"] is thing:
                self.open.remove(ep)
                if self.ultima_acao is ep:
                    self.ultima_acao = None

    def drop_open_things(self):
        """Objetos limpos pela bandeja: leve negativo (você quis a tela limpa)."""
        for ep in list(self.open):
            if ep["thing"] is not None:
                self._resolve(ep, "limpo pela bandeja", -0.1)

    def _resolve(self, ep, result, valence):
        """Fecha um episódio com o resultado final e grava no histórico e no aprendizado."""
        self.open.remove(ep)
        record = {
            "id": ep.get("id"),
            "quando": ep["quando"],
            "contexto": ep["contexto"],
            "acao": ep["acao"],
            "resultado": result,
            "valencia": round(valence, 3),
        }
        self.recent.append(record)
        self.recent = self.recent[-KEEP_EPISODES:]
        self._learn(record["contexto"], record["acao"], valence)
        self.dirty = True
        log(f"[memória] {record['contexto']} -> {record['acao']}: {result} ({valence:+.2f})")

    def _learn(self, ctx, action, valence):
        """Atualiza as médias de uma ação no contexto e no geral (limitadas, para não travar em um valor antigo)."""
        for stats in (self.table.setdefault(ctx, {}).setdefault(action, [0, 0.0]),
                      self.totals.setdefault(action, [0, 0.0])):
            stats[0] = min(stats[0] + 1, MAX_COUNT)
            stats[1] += (valence - stats[1]) / stats[0]
        while len(self.table) > MAX_CONTEXTS:
            del self.table[next(iter(self.table))]

    # ---------------- sono: consolidação ----------------

    def consolidate(self):
        """Refaz as preferências a partir dos episódios, com peso para os recentes."""
        episodes = self._read_episodes()
        if not episodes:
            return []
        table, totals = {}, {}
        newest = len(episodes)
        for i, ep in enumerate(episodes):
            w = 0.5 ** ((newest - 1 - i) / RECENCY_HALF_LIFE)
            for stats in (table.setdefault(ep["contexto"], {}).setdefault(ep["acao"], [0.0, 0.0]),
                          totals.setdefault(ep["acao"], [0.0, 0.0])):
                stats[0] += w
                stats[1] += w * ep["valencia"]
        self.table = {c: {a: [min(n, MAX_COUNT), s / n] for a, (n, s) in acts.items()} for c, acts in table.items()}
        self.totals = {a: [min(n, MAX_COUNT), s / n] for a, (n, s) in totals.items()}
        self.dirty = True
        self.save()
        return self.preferences()

    def preferences(self, top=6):
        """Contextos com preferência mais marcada: [(contexto, ação, média, n)]."""
        rows = [(c, a, mean, n) for c, acts in self.table.items() for a, (n, mean) in acts.items() if n >= 1]
        return sorted(rows, key=lambda r: -abs(r[2]) * min(r[3], 5))[:top]

    def _read_episodes(self):
        """Lê o histórico de episódios do arquivo, ignorando linhas inválidas."""
        if self.dirty or not self.episodes_path.exists():
            return list(self.recent)
        out = []
        lines = deque(maxlen=KEEP_EPISODES)
        try:
            with self.episodes_path.open(encoding='utf-8', errors='replace') as source:
                while True:
                    line = source.readline(4097)
                    if not line: break
                    if len(line) > 4096:
                        while line and not line.endswith('\n'): line = source.readline(4097)
                        continue
                    lines.append(line)
        except OSError:
            return list(self.recent)
        for line in lines:
            try:
                registro = json.loads(line, parse_constant=_sem_nan)
            except ValueError:
                continue                        # linha ilegível: pula só ela
            if _episodio_valido(registro):
                out.append(registro)
        return out

    # ---------------- persistência ----------------

    def save(self):
        """Grava as preferências aprendidas (tabela por contexto e média geral)."""
        data = {"tabela": self.table, "geral": self.totals, "saved_at": time.time()}
        try:
            write_json(self.prefs_path, data, indent=1)
            if self.dirty:
                write_lines(self.episodes_path, [json.dumps(ep, ensure_ascii=False) for ep in self.recent[-KEEP_EPISODES:]])
                self.dirty = False
        except OSError as error:
            log(f"[memória] não salvou as preferências: {error}")

    def load(self):
        """Lê as preferências salvas, validando cada valor; o que estiver errado volta ao padrão."""
        data = read_json(self.prefs_path, default=None)
        if isinstance(data, dict):
            self.table = dict(list(_tabela_valida(data.get("tabela"), por_contexto=True).items())[-MAX_CONTEXTS:])
            self.totals = dict(list(_tabela_valida(data.get("geral"), por_contexto=False).items())[-MAX_ACTIONS:])
        self.recent = self._read_episodes()[-KEEP_EPISODES:]
        self.dirty = True
