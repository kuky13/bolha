# SPDX-License-Identifier: GPL-3.0-or-later
# Adapted from Pestinha by @mille-okws and contributors; see NOTICE.md.
"""
PHYSICS - corpo 2D do pet: gravidade, inércia, rotação, quique e pouso.

Coordenadas lógicas do Qt (as mesmas de QCursor.pos()). O corpo é uma
caixa (half_w x half_h) girada pelo ângulo; para colidir usamos a caixa
que envolve o corpo girado. Plataformas são as barras de título das janelas.
"""

import math
from ..ajustes import (
    GRAVIDADE as GRAVITY,
    QUICA as RESTITUTION,
    ATRITO_CHAO as GROUND_FRICTION,
    ARRASTO_AR as AIR_DRAG,
    ARRASTO_GIRO_AR as ANGULAR_DRAG,
    MOLA_ENDIREITAR as RIGHTING_K,
    AMORTECIMENTO_ENDIREITAR as RIGHTING_DAMP,
    GIRO_MAXIMO as MAX_SPIN,
    BOTOES_JANELA as CLOSE_BUTTONS,
)



def wrap_angle(deg):
    """Ângulo em graus, normalizado para o intervalo de -180 a 180."""
    return (deg + 180.0) % 360.0 - 180.0


def _area_em(areas, x, y):
    """Retângulo que contém o ponto, ou None quando ele está num vão entre monitores."""
    return next((a for a in areas if a[0] <= x < a[2] and a[1] <= y < a[3]), None)


def _tem_vizinha(areas, atual, lado, coordenada, extensao, monitores=None):
    """Diz se há outro monitor encostado naquele lado e se o corpo cabe na abertura."""
    monitores = monitores or areas
    indice = areas.index(atual) if atual in areas else 0
    left, top, right, bottom = monitores[indice]
    for outro_indice, area in enumerate(areas):
        if outro_indice == indice:
            continue
        m_left, m_top, m_right, m_bottom = monitores[outro_indice]
        a_left, a_top, a_right, a_bottom = area
        if lado == "left":
            encosta = abs(m_right - left) <= 1
            cabe = a_top <= coordenada < a_bottom
        elif lado == "right":
            encosta = abs(m_left - right) <= 1
            cabe = a_top <= coordenada < a_bottom
        elif lado == "top":
            encosta = abs(m_bottom - top) <= 1
            cabe = a_left <= coordenada < a_right
        else:
            encosta = abs(m_top - bottom) <= 1
            cabe = a_left <= coordenada < a_right
        if encosta and cabe:
            return True
    return False


def _physical_neighbor(areas, displays, source, side, coordinate):
    """Vizinha por pixels físicos: Qt/Windows pode deixar vãos artificiais em DIP."""
    if not displays or source not in areas:return None
    i=areas.index(source);a=displays[i];scale=a.get('scaleFactor',1)
    ax,ay=a.get('nativeX',a['x']),a.get('nativeY',a['y'])
    ar=ax+a.get('nativeWidth',a.get('monitorWidth',a['width'])*scale)
    ab=ay+a.get('nativeHeight',a.get('monitorHeight',a['height'])*scale)
    value=(ay+(coordinate-a.get('monitorY',a['y']))*scale) if side in ('left','right') else (ax+(coordinate-a.get('monitorX',a['x']))*scale)
    for j,b in enumerate(displays):
        if i==j:continue
        sb=b.get('scaleFactor',1);bx,by=b.get('nativeX',b['x']),b.get('nativeY',b['y'])
        br=bx+b.get('nativeWidth',b.get('monitorWidth',b['width'])*sb)
        bb=by+b.get('nativeHeight',b.get('monitorHeight',b['height'])*sb)
        adjacent=abs((br-ax) if side=='left' else (bx-ar) if side=='right' else (bb-ay) if side=='top' else (by-ab))<=2
        target=areas[j]
        mapped=(b.get('monitorY',b['y'])+(value-by)/sb) if side in ('left','right') else (b.get('monitorX',b['x'])+(value-bx)/sb)
        lo,hi=(target[1],target[3]) if side in ('left','right') else (target[0],target[2])
        if adjacent and lo<=mapped<hi:return j,mapped,scale/sb
    return None

def _transfer(body,areas,displays,source):
    """Transporta o centro pela costura física e conserva a velocidade em pixels/s."""
    for side,passed,coordinate in (('left',body.x<source[0],body.y),('right',body.x>=source[2],body.y),('top',body.y<source[1],body.x),('bottom',body.y>=source[3],body.x)):
        if not passed:continue
        peer=_physical_neighbor(areas,displays,source,side,coordinate)
        if peer is None:continue
        index,mapped,ratio=peer;target=areas[index]
        if side=='left':body.x=target[2]-(source[0]-body.x)*ratio;body.y=mapped
        elif side=='right':body.x=target[0]+(body.x-source[2])*ratio;body.y=mapped
        elif side=='top':body.y=target[3]-(source[1]-body.y)*ratio;body.x=mapped
        else:body.y=target[1]+(body.y-source[3])*ratio;body.x=mapped
        body.vx*=ratio;body.vy*=ratio;body.grounded=False;body.platform=None
        return target
    return source


class Body:
    """Corpo na tela: posição, velocidade, ângulo e contato com as superfícies (chão e janelas)."""
    def __init__(self, x, y, half_w, half_h, circular=False):
        """Cria o corpo em (x, y), com metade da largura e da altura (para medir o contato)."""
        self.x, self.y = x, y
        self.vx = self.vy = 0.0
        self.angle = 0.0          # graus, 0 = em pé
        self.omega = 0.0          # graus/s
        self.half_w, self.half_h = half_w, half_h
        self.circular = circular
        self.grounded = False
        self.platform = None      # hwnd da janela onde está pousado, ou None (chão)
        self.surface = 0.0        # y da superfície onde está apoiado
        self.impacts = []         # velocidades das batidas desde a última leitura (px/s)
        self.landing_contact = None
        self.held = False         # sendo segurado pelo mouse

    def pop_impacts(self):
        """Devolve as batidas desde a última vez e zera a lista (para a rede sentir a batida)."""
        out, self.impacts = self.impacts, []
        return out

    def extents(self):
        """Metade da largura e da altura do corpo já girado (para saber onde a base encosta)."""
        if self.circular:
            return self.half_w, self.half_h
        a = math.radians(self.angle)
        c, s = abs(math.cos(a)), abs(math.sin(a))
        return self.half_w * c + self.half_h * s, self.half_w * s + self.half_h * c

    def resting_angle(self):
        """Lado mais próximo para assentar (0 em pé, ±90 tombado, 180 de ponta-cabeça)."""
        return round(self.angle / 90.0) * 90.0

    def upright(self):
        """Diz se o corpo está em pé (inclinado menos de 30 graus)."""
        return abs(wrap_angle(self.angle)) < 30.0

    def step(self, dt, bounds, platforms, areas=None, monitors=None, displays=None):
        """
        bounds: (left, top, right, bottom) da área de trabalho.
        platforms: [(hwnd, left, right, top)] barras de título candidatas.
        areas: áreas de todos os monitores; bordas compartilhadas viram passagens.
        monitors: geometria física das telas, usada para reconhecer vizinhança apesar da barra de tarefas.
        """
        self.landing_contact = None
        if self.held:
            return
        left, top, right, bottom = bounds

        if not self.grounded:
            self.vy += GRAVITY * dt
            self.vx -= self.vx * AIR_DRAG * dt
            self.omega -= self.omega * ANGULAR_DRAG * dt
        else:
            self.vx -= self.vx * GROUND_FRICTION * dt
            target = self.resting_angle()
            self.omega += ((target - self.angle) * RIGHTING_K - self.omega * RIGHTING_DAMP) * dt

        self.omega = max(-MAX_SPIN, min(MAX_SPIN, self.omega))
        self.angle += self.omega * dt
        if abs(self.angle) > 3600:
            self.angle = wrap_angle(self.angle)

        ex, ey = self.extents()
        prev_bottom = self.y + ey
        self.x += self.vx * dt
        self.y += self.vy * dt

        areas = list(areas or [bounds])
        monitors = list(monitors or areas)
        if bounds not in areas:                       # adaptadores/testes podem fornecer um mundo próprio
            areas = [bounds]
            monitors = [bounds]
        if displays and len(displays)==len(areas):
            atual = _transfer(self,areas,displays,bounds)
            prev_bottom=self.y+ey-self.vy*dt
        else:atual = _area_em(areas, self.x, self.y) or bounds
        def neighbor(side,coordinate,extent):
            if displays:return _physical_neighbor(areas,displays,atual,side,coordinate) is not None
            return _tem_vizinha(areas,atual,side,coordinate,extent,monitors)
        left, top, right, bottom = atual

        # paredes: uma borda compartilhada com outro monitor é uma passagem
        if self.x - ex < left and not neighbor("left",self.y,ey):
            self.x = left + ex
            self.impacts.append(abs(self.vx))
            self.vx = abs(self.vx) * RESTITUTION
            self.omega += self.vy * 0.15
        elif self.x + ex > right and not neighbor("right",self.y,ey):
            self.x = right - ex
            self.impacts.append(abs(self.vx))
            self.vx = -abs(self.vx) * RESTITUTION
            self.omega -= self.vy * 0.15
        if self.y - ey < top and not neighbor("top",self.x,ex):
            self.y = top + ey
            self.impacts.append(abs(self.vy))
            self.vy = abs(self.vy) * RESTITUTION

        # apoiado: acompanha a superfície; se ela sumiu/mexeu ou ele saiu da beirada, cai
        if self.grounded:
            surface = bottom
            if self.platform is not None:
                plat = next((p for p in platforms if p[0] == self.platform), None)
                if plat is None or not (plat[1] <= self.x <= plat[2] - CLOSE_BUTTONS) or abs(plat[3] - self.surface) > 4:
                    self.grounded = False
                    self.platform = None
                else:
                    surface = plat[3]
            elif abs(self.surface - bottom) > 4:
                self.grounded = False                 # o monitor vizinho tem outro nível de chão
            if self.grounded:
                self.surface = surface
                self.y = surface - ey
                self.vy = 0.0
                return

        # pouso numa barra de título (só caindo, vindo de cima)
        new_bottom = self.y + ey
        if self.vy > 0:
            cruzadas = [(p_top, hwnd) for hwnd, p_left, p_right, p_top in platforms
                        if p_left <= self.x <= p_right - CLOSE_BUTTONS and prev_bottom <= p_top + 2 <= new_bottom + 2
                        and new_bottom >= p_top]
            if cruzadas:
                p_top, hwnd = min(cruzadas)          # a primeira superfície que a queda encontra é a mais alta
                self._land(p_top, ey, hwnd)
                return

        # chão (acima da barra de tarefas)
        if self.y + ey >= bottom and not neighbor("bottom",self.x,ex):
            self._land(bottom, ey, None)

    def _land(self, surface, ey, platform):
        """Pousa o corpo sobre uma superfície (chão ou janela): para de cair e guarda onde pousou."""
        self.y = surface - ey
        self.surface = surface
        self.landing_contact = abs(self.vy), wrap_angle(self.angle)
        self.impacts.append(abs(self.vy))
        if self.vy > 260:
            self.vy = -self.vy * RESTITUTION
            self.omega += self.vx * 0.4
            return
        self.vy = 0.0
        self.grounded = True
        self.platform = platform

    def jump(self, vx, vy, spin=0.0):
        """Dá um impulso: muda a velocidade e tira o corpo do chão (com giro opcional)."""
        self.grounded = False
        self.platform = None
        self.vx, self.vy = vx, vy
        self.omega += spin
