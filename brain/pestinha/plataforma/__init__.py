# SPDX-License-Identifier: GPL-3.0-or-later
"""Adaptador Windows; o fallback só permite testar o núcleo sem desktop."""
import sys
if sys.platform == 'win32':
    from .windows import (ocioso_segundos, processo_ativo, retangulo_ativo, tela_cheia,
                          janelas_visiveis)
    TEM_INICIO_AUTOMATICO = True
else:
    def ocioso_segundos(): return 0.0
    def processo_ativo(): return 'unknown'
    def retangulo_ativo(escala=1.0): return None
    def tela_cheia(): return False
    def janelas_visiveis(excluir, escala=1.0): return []
    def sem_foco_nativo(janela_id): pass
    def iniciar_atalho(callback): return False
    def inicia_com_sistema(): return False
    def definir_inicio_com_sistema(ligado): return False
    TEM_INICIO_AUTOMATICO = False
