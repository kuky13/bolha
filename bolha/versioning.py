# SPDX-License-Identifier: GPL-3.0-or-later
"""Versões da Bolha e leitura de metadados das versões antigas."""
import re

VERSION_PATTERN = r'[0-9]{1,6}(?:\.[0-9]{1,6}){2,3}'


def version_tuple(value):
    if not isinstance(value, str) or not re.fullmatch(VERSION_PATTERN, value):
        raise ValueError('Versão inválida.')
    parts = tuple(map(int, value.split('.')))
    return parts if len(parts) == 4 else (*parts, 0)


def compare_versions(left, right):
    a, b = version_tuple(left), version_tuple(right)
    return (a > b) - (a < b)


def windows_version(value):
    parts = version_tuple(value)
    if any(part > 65535 for part in parts):
        raise ValueError('Cada componente do instalador Windows deve caber em 16 bits.')
    return '.'.join(map(str, parts))
