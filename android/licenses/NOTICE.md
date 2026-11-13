# Componentes incluídos no APK da Bolha

O código e as artes próprios seguem a GPL-3.0-or-later. Consulte também
os arquivos `LICENSE`, `NOTICE.md` e `licenses/BOLHA-ASSETS.md` no APK.

| Componente | Licença e origem |
| --- | --- |
| Chaquopy 17.2.0 | MIT. [Código](https://github.com/chaquo/chaquopy/tree/17.2.0) e [texto](Chaquopy-17.2.0.txt). |
| CPython 3.13.16 | PSF, com termos de versões anteriores e dependências. [Código](https://github.com/python/cpython/tree/v3.13.16) e [texto](CPython-3.13.16.txt). |
| OpenSSL 3.5.9 | Apache-2.0. [Código](https://github.com/openssl/openssl/tree/openssl-3.5.9) e [texto](OpenSSL-3.5.9.txt). |
| SQLite | Domínio público. [Código e declaração](https://www.sqlite.org/copyright.html). |
| bzip2, libffi e liblzma | [bzip2](bzip2-1.0.8.txt), [libffi](libffi-3.4.4.txt) e [XZ](XZ-5.4.6.txt). Textos de licença dos componentes do runtime CPython Android. [Empacotamento](https://github.com/beeware/cpython-android-source-deps). |
| NumPy 2.3.2 | BSD-3-Clause. [Código](https://github.com/numpy/numpy/tree/v2.3.2), [texto](NumPy-2.3.2.txt) e [wheels fornecidos pelo mantenedor Chaquopy](https://chaquo.com/pypi-upstream/numpy/). O APK contém o inventário em `assets/chaquopy/requirements-common.imy`. Textos adicionais para [LAPACK Lite](NumPy-LAPACK-Lite.txt), [Dragon4](NumPy-Dragon4.txt) e [libdivide](NumPy-libdivide.txt). |
| OpenBLAS, libc++ e libgfortran | Bibliotecas incluídas nos wheels NumPy Android. [OpenBLAS](OpenBLAS.txt), [libc++](LLVM-libcxx.txt) e [exceção GCC Runtime Library 3.1](GCC-Runtime-Library-Exception-3.1.txt). A libgfortran usa GPL-3.0-or-later com essa exceção. [Empacotamento do mantenedor](https://github.com/chaquo/chaquopy/tree/17.2.0/server/pypi/packages). |
