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
    conn.commit()
    conn.close()


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
