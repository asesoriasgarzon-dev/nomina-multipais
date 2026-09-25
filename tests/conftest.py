"""Las pruebas nunca tocan la base de datos real (instance/nomina.db): se redirige ANTES de importar app."""

import os
import tempfile

import models

_TMP = tempfile.mkdtemp(prefix="nomina-tests-")
models.DB_PATH = os.path.join(_TMP, "tests.db")
