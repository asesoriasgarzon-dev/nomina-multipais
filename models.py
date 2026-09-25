import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "instance", "nomina.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS nominas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pais TEXT NOT NULL,
            periodo TEXT NOT NULL,
            empleado_json TEXT NOT NULL,
            novedades_json TEXT NOT NULL,
            resultado_json TEXT NOT NULL,
            creado_en TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS liquidaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pais TEXT NOT NULL,
            empleado_json TEXT NOT NULL,
            datos_json TEXT NOT NULL,
            resultado_json TEXT NOT NULL,
            creado_en TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS empleados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pais TEXT NOT NULL,
            identificacion TEXT NOT NULL,
            nombre TEXT NOT NULL,
            cargo TEXT,
            salario_base REAL,
            fecha_ingreso TEXT,
            estado TEXT NOT NULL DEFAULT 'activo',
            actualizado_en TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(pais, identificacion)
        )
        """
    )
    # Corridas del motor normativo: INSERT-only. Cada corrida guarda su snapshot de entrada, su
    # snapshot normativo (por hash) y la versión del motor, para poder reproducirla aunque las
    # reglas cambien después. Los triggers impiden modificarla o borrarla.
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS payroll_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_uid TEXT NOT NULL UNIQUE,
            nomina_id INTEGER,
            country TEXT NOT NULL,
            period TEXT NOT NULL,
            run_type TEXT NOT NULL,
            status TEXT NOT NULL,
            engine_version TEXT NOT NULL,
            ruleset_version TEXT NOT NULL,
            normative_hash TEXT NOT NULL,
            input_hash TEXT NOT NULL,
            result_hash TEXT NOT NULL,
            trace_hash TEXT NOT NULL,
            es_demo INTEGER NOT NULL DEFAULT 0,
            run_json TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS normative_snapshots (
            hash TEXT PRIMARY KEY,
            country TEXT NOT NULL,
            ruleset_version TEXT NOT NULL,
            documents_json TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    for table in ("payroll_runs", "normative_snapshots"):
        conn.execute(
            f"CREATE TRIGGER IF NOT EXISTS {table}_no_update BEFORE UPDATE ON {table} "
            f"BEGIN SELECT RAISE(ABORT, '{table} es inmutable'); END"
        )
        conn.execute(
            f"CREATE TRIGGER IF NOT EXISTS {table}_no_delete BEFORE DELETE ON {table} "
            f"BEGIN SELECT RAISE(ABORT, '{table} es inmutable'); END"
        )
    conn.commit()
    conn.close()


def guardar_payroll_run(run_dict, documents, nomina_id=None, es_demo=False):
    """Guarda una corrida (INSERT-only) y su snapshot normativo (una sola copia por hash)."""
    norm = run_dict["normative_snapshot"]
    conn = get_db()
    conn.execute(
        "INSERT OR IGNORE INTO normative_snapshots (hash, country, ruleset_version, documents_json) VALUES (?, ?, ?, ?)",
        (norm["content_hash"], norm["country"], norm["ruleset_version"], json.dumps(documents, ensure_ascii=False)),
    )
    cur = conn.execute(
        "INSERT INTO payroll_runs (run_uid, nomina_id, country, period, run_type, status, engine_version, "
        "ruleset_version, normative_hash, input_hash, result_hash, trace_hash, es_demo, run_json) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (run_dict["run_id"], nomina_id, run_dict["country"], run_dict["period"]["end"][:7], run_dict["run_type"],
         run_dict["status"], run_dict["engine_version"], run_dict["ruleset_version"], norm["content_hash"],
         run_dict["input_snapshot"]["hash"], run_dict["result_hash"], run_dict["trace_hash"], 1 if es_demo else 0,
         json.dumps(run_dict, ensure_ascii=False)),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def _run_row(row):
    if row is None:
        return None
    data = json.loads(row["run_json"])
    data["db_id"] = row["id"]
    data["nomina_id"] = row["nomina_id"]
    data["es_demo"] = bool(row["es_demo"])
    return data


def obtener_payroll_run(run_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM payroll_runs WHERE id = ?", (run_id,)).fetchone()
    conn.close()
    return _run_row(row)


def obtener_payroll_run_por_nomina(nomina_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM payroll_runs WHERE nomina_id = ? ORDER BY id DESC LIMIT 1", (nomina_id,)).fetchone()
    conn.close()
    return _run_row(row)


def obtener_snapshot_normativo(content_hash):
    conn = get_db()
    row = conn.execute("SELECT documents_json FROM normative_snapshots WHERE hash = ?", (content_hash,)).fetchone()
    conn.close()
    return json.loads(row["documents_json"]) if row else None


def guardar_nomina(pais, periodo, empleado, novedades, resultado):
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO nominas (pais, periodo, empleado_json, novedades_json, resultado_json) "
        "VALUES (?, ?, ?, ?, ?)",
        (pais, periodo, json.dumps(empleado), json.dumps(novedades), json.dumps(resultado)),
    )
    conn.commit()
    nueva_id = cur.lastrowid
    conn.close()
    return nueva_id


def obtener_nomina(nomina_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM nominas WHERE id = ?", (nomina_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    return {
        "id": row["id"],
        "pais": row["pais"],
        "periodo": row["periodo"],
        "empleado": json.loads(row["empleado_json"]),
        "novedades": json.loads(row["novedades_json"]),
        "resultado": json.loads(row["resultado_json"]),
        "creado_en": row["creado_en"],
    }


def listar_nominas():
    conn = get_db()
    rows = conn.execute("SELECT * FROM nominas ORDER BY creado_en DESC").fetchall()
    conn.close()
    result = []
    for row in rows:
        result.append({
            "id": row["id"],
            "pais": row["pais"],
            "periodo": row["periodo"],
            "empleado": json.loads(row["empleado_json"]),
            "resultado": json.loads(row["resultado_json"]),
            "creado_en": row["creado_en"],
        })
    return result


def guardar_liquidacion(pais, empleado, datos, resultado):
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO liquidaciones (pais, empleado_json, datos_json, resultado_json) "
        "VALUES (?, ?, ?, ?)",
        (pais, json.dumps(empleado), json.dumps(datos), json.dumps(resultado)),
    )
    conn.commit()
    nueva_id = cur.lastrowid
    conn.close()
    return nueva_id


def obtener_liquidacion(liquidacion_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM liquidaciones WHERE id = ?", (liquidacion_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    return {
        "id": row["id"],
        "pais": row["pais"],
        "empleado": json.loads(row["empleado_json"]),
        "datos": json.loads(row["datos_json"]),
        "resultado": json.loads(row["resultado_json"]),
        "creado_en": row["creado_en"],
    }


def listar_liquidaciones():
    conn = get_db()
    rows = conn.execute("SELECT * FROM liquidaciones ORDER BY creado_en DESC").fetchall()
    conn.close()
    result = []
    for row in rows:
        result.append({
            "id": row["id"],
            "pais": row["pais"],
            "empleado": json.loads(row["empleado_json"]),
            "datos": json.loads(row["datos_json"]),
            "resultado": json.loads(row["resultado_json"]),
            "creado_en": row["creado_en"],
        })
    return result


def _empleado_row_to_dict(row):
    return {
        "id": row["id"],
        "pais": row["pais"],
        "identificacion": row["identificacion"],
        "nombre": row["nombre"],
        "cargo": row["cargo"],
        "salario_base": row["salario_base"],
        "fecha_ingreso": row["fecha_ingreso"],
        "estado": row["estado"],
        "actualizado_en": row["actualizado_en"],
    }


def upsert_empleado(pais, identificacion, nombre, cargo, salario_base, fecha_ingreso, estado="activo"):
    """Inserta un empleado nuevo, o actualiza el existente si ya hay uno con
    la misma identificación en ese país (así una recarga de Excel no crea
    duplicados: pisa la ficha anterior con los datos nuevos)."""
    conn = get_db()
    conn.execute(
        """
        INSERT INTO empleados (pais, identificacion, nombre, cargo, salario_base, fecha_ingreso, estado, actualizado_en)
        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(pais, identificacion) DO UPDATE SET
            nombre=excluded.nombre,
            cargo=excluded.cargo,
            salario_base=excluded.salario_base,
            fecha_ingreso=excluded.fecha_ingreso,
            estado=excluded.estado,
            actualizado_en=CURRENT_TIMESTAMP
        """,
        (pais, identificacion, nombre, cargo, salario_base, fecha_ingreso, estado),
    )
    conn.commit()
    conn.close()


def marcar_estado_empleado(pais, identificacion, estado):
    conn = get_db()
    conn.execute(
        "UPDATE empleados SET estado = ?, actualizado_en = CURRENT_TIMESTAMP "
        "WHERE pais = ? AND identificacion = ?",
        (estado, pais, identificacion),
    )
    conn.commit()
    conn.close()


def listar_empleados(pais=None):
    conn = get_db()
    if pais:
        rows = conn.execute(
            "SELECT * FROM empleados WHERE pais = ? ORDER BY nombre", (pais,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM empleados ORDER BY pais, nombre").fetchall()
    conn.close()
    return [_empleado_row_to_dict(r) for r in rows]


def obtener_empleado(pais, identificacion):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM empleados WHERE pais = ? AND identificacion = ?",
        (pais, identificacion),
    ).fetchone()
    conn.close()
    return _empleado_row_to_dict(row) if row else None
