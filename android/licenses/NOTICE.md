# Componentes incluídos no APK da Bolha

O código e as artes próprios seguem a GPL-3.0-or-later. Consulte também
os arquivos `LICENSE`, `NOTICE.md` e `licenses/BOLHA-ASSETS.md` no APK.

| Componente | Licença e origem |
| --- | --- |
| Chaquopy 17.0.0 | MIT. [Código](https://github.com/chaquo/chaquopy/tree/17.0.0) e [texto](Chaquopy-17.0.0.txt). |
| CPython 3.11.14 | PSF, com termos de versões anteriores e dependências. [Código](https://github.com/python/cpython/tree/v3.11.14) e [texto](CPython-3.11.14.txt). |
| OpenSSL 3.0.18 | Apache-2.0. [Código](https://github.com/openssl/openssl/tree/openssl-3.0.18) e [texto](OpenSSL-3.0.18.txt). |
| SQLite 3.50.4 | Domínio público. [Código](https://www.sqlite.org/src/tree?ci=version-3.50.4) e [declaração](https://www.sqlite.org/copyright.html). |
| bzip2 1.0.8, libffi 3.4.4 e liblzma (XZ Utils 5.4.6) | [bzip2](bzip2-1.0.8.txt), [libffi](libffi-3.4.4.txt) e [XZ](XZ-5.4.6.txt). [Empacotamento do Python para Android](https://github.com/beeware/cpython-android-source-deps). |
| NumPy 1.26.2 | BSD-3-Clause. [Código](https://github.com/numpy/numpy/tree/v1.26.2). O APK contém o texto do NumPy e o inventário de componentes em `assets/chaquopy/requirements-common.imy`. Textos adicionais para [LAPACK Lite](NumPy-LAPACK-Lite.txt) e [Dragon4](NumPy-Dragon4.txt). |
| OpenBLAS 0.2.20, libc++ 18 e libgfortran 4.9 | Os textos fornecidos pelos pacotes Chaquopy estão no mesmo arquivo `requirements-common.imy`. [Código e scripts de empacotamento](https://github.com/chaquo/chaquopy/tree/17.0.0/server/pypi/packages). A libgfortran usa GPL-3.0-or-later com a [exceção GCC Runtime Library 3.1](GCC-Runtime-Library-Exception-3.1.txt). |
