# Empaquetado de Proyectos Python

---

Este tutorial te guía a través del proceso de empaquetar un proyecto simple de
Python. Te mostrará cómo agregar los archivos necesarios y la estructura para
crear el paquete, cómo construir el paquete, y cómo subirlo al Índice de
Paquetes de Python (PyPI).

1. Actualiza `pip` y asegúrate de tener las herramientas necesarias instaladas.

```bash
python -m pip install --upgrade pip
```

# Un proyecto simple

Este tutorial utiliza un proyecto simple llamado `example_package_pg2_tecba`.

Crea la siguiente estructura de archivos localmente:

```text
pg2_practica_7/
└── src/
    └── example_package_pg2_tecba/
        ├── __init__.py
        └── primer_modulo.py
```

El directorio que contiene los archivos Python debe coincidir con el nombre del
proyecto. Esto simplifica la configuración y es más obvio para los usuarios que
instalan el paquete.

Crear el archivo `__init__.py` es recomendado porque la existencia de un archivo
`__init__.py` permite a los usuarios importar el directorio como un paquete
regular, incluso si (como es el caso en este tutorial) `__init__.py` está vacío.

`primer_modulo.py` es un ejemplo de un módulo dentro del paquete que podría
contener la lógica (funciones, clases, constantes, etc.) de tu paquete. Abre ese
archivo e ingresa el siguiente contenido:

```python
def add_one(number):
    return number + 1
```

Si no estás familiarizado con los `módulos <Module>` de Python y los
`paquetes de importación <Import Package>` tómate unos minutos para leer la
[documentación de Python sobre paquetes y módulos](https://docs.python.org/3/tutorial/modules.html#packages).

# Creando los archivos del paquete

Ahora agregarás archivos que se usan para preparar el proyecto para
distribución. Cuando termines, la estructura del proyecto se verá así:

```text
pg2_practica_7/
├── LICENSE
├── pyproject.toml
├── README.md
├── src/
│   └── example_package_pg2_tecba/
│       ├── __init__.py
│       └── example.py
└── tests/
```

# Creando un directorio de pruebas

`tests/` es un marcador de posición para archivos de prueba. Déjalo vacío por
ahora.

## Configurando metadatos de project.toml

Abre `pyproject.toml` e ingresa el siguiente contenido. Cambia el `name` por el
nombre de tu paquete;

```toml
[build-system]
requires = ['setuptools>=40.8.0', 'wheel']
build-backend = 'setuptools.build_meta:__legacy__'
```

## Configurando metadatos en setup.cfg y setup.py

Abre `setup.cfg` e ingresa el siguiente contenido.

```ini
[metadata]
name = example_package_pg2_tecba
version = 0.0.1
description = Reemplaza aquí con una descripción corta de tu paquete
long_description = file:README.md
long_description_content_type = text/markdown
url = https://github.com/yefeza/example_package_pg2_tecba
author = Yeison Fernandez
author_email = contacto@90horasporsemana.com
license = MIT
classifiers =
    Intended Audience :: Developers
    Programming Language :: Python
    Topic :: Software Development

[options]
include_package_data = true
package_dir=
    =src
packages=find:
python_requires = >=3.6
install_requires =

[options.packages.find]
where=src

```

Abre `setup.py` e ingresa el siguiente contenido.

```python
from setuptools import setup

if __name__ == "__main__":
    setup()
```

# Creando README.md

Abre `README.md` e ingresa la documentación de tu paquete. Puedes personalizar
esto si quieres. Aquí hay un ejemplo simple:

```md
# Example Package

A simple example package to demonstrate packaging and distribution with Python.

This is a simple example package. You can use
[GitHub-flavored Markdown](https://guides.github.com/features/mastering-markdown/)
```

# Creando una LICENCIA

Es importante que cada paquete subido al Índice de Paquetes de Python incluya
una licencia. Esto les dice a los usuarios que instalan tu paquete los términos
bajo los cuales pueden usar tu paquete. Para ayuda eligiendo una licencia, ve
<https://choosealicense.com/>. Una vez que hayas elegido una licencia, abre
`LICENSE` e ingresa el texto de la licencia. Por ejemplo, si hubieras elegido la
licencia MIT:

```text
Copyright (c) 2018 The Python Packaging Authority

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

La mayoría de los backends de construcción incluyen automáticamente archivos de
licencia en los paquetes.

# Generando archivos de distribución

El siguiente paso es generar `paquetes de distribución` para el paquete. Estos
son archivos que se suben al Índice de Paquetes de Python y pueden ser
instalados por `pip`.

Asegúrate de tener la última versión de `build` de PyPi instalada:

```bash
python -m pip install --upgrade build
```

Ahora ejecuta este comando desde el mismo directorio donde se encuentra
`pyproject.toml`:

```bash
python3 -m build
```

Este comando debería generar mucho texto y una vez completado debería generar
dos archivos en el directorio `dist`:

```text
dist/
├── example_package_pg2_tecba-0.0.1-py3-none-any.whl
└── example_package_pg2_tecba-0.0.1.tar.gz
```

# Subiendo los archivos de distribución

¡Finalmente, es hora de subir tu paquete al Índice de Paquetes de Python!

Lo primero que necesitarás hacer es registrar una cuenta en PyPI, que es una
instancia separada del índice de paquetes destinada a pruebas y experimentación.
Para registrar una cuenta, ve a <https://pypi.org/account/register/> y completa
los pasos en esa página. También necesitarás verificar tu dirección de correo
electrónico antes de poder subir cualquier paquete.

Para subir tu proyecto de forma segura, necesitarás un
[token API](https://pypi.org/help/#apitoken) de PyPI. Crea uno en
<https://pypi.org/manage/account/#api-tokens>, estableciendo el "Scope" a
"Entire account". **No cierres la página hasta que hayas copiado y guardado el
token --- no verás ese token otra vez.**

Ahora que estás registrado, puedes usar `twine` para subir los paquetes de
distribución. Necesitarás instalar Twine:

```bash
python -m pip install --upgrade twine
```

Una vez instalado, ejecuta Twine para subir todos los archivos en `dist`:

```bash
python -m twine upload --repository pypi dist/*
```

Se te pedirá un token API. Usa el valor del token, incluyendo el prefijo
`pypi-`. Ten en cuenta que la entrada estará oculta, así que asegúrate de pegar
correctamente.

Después de que el comando se complete, deberías ver una salida similar a esta:

```
Uploading distributions to https://pypi.org/legacy/
Enter your API token:
Uploading example_package_pg2_tecba-0.0.1-py3-none-any.whl
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 8.2/8.2 kB • 00:01 • ?
Uploading example_package_pg2_tecba-0.0.1.tar.gz
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 6.8/6.8 kB • 00:00 • ?
```

Una vez subido, tu paquete debería ser visible en PyPI; por ejemplo:
`https://pypi.org/project/example_package_pg2_tecba`.

# Instalando tu paquete recién subido

Puedes usar `pip` para instalar tu paquete y verificar que funciona. Crea un
`entorno virtual` e instala tu paquete desde PyPI:

::: tab Unix/macOS

```bash
python3 -m pip install example-package-pg2-tecba
```

pip debería instalar el paquete y la salida debería verse algo así:

```text
Collecting example-package-TU-NOMBRE-DE-USUARIO-AQUÍ
  Downloading https://test-files.pythonhosted.org/packages/.../example_package_pg2_tecba_0.0.1-py3-none-any.whl
Installing collected packages: example_package_pg2_tecba
Successfully installed example_package_pg2_tecba-0.0.1
```

Puedes probar que se instaló correctamente importando el paquete. Asegúrate de
estar aún en tu entorno virtual, luego ejecuta Python:

```bash
python
```

e importa el paquete:

```pycon
>>> from example_package_pg2_tecba import primer_modulo
>>> primer_modulo.add_one(2)
3
```
