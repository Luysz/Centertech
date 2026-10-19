import os
from pathlib import Path

import psycopg
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="CenterTech API")


@app.get("/mapa")
def mapa():
    return FileResponse(BASE_DIR / "mapa.html")


@app.get("/historico-pagina")
def historico_pagina():
    return FileResponse(BASE_DIR / "historico.html")


def conectar_banco():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise HTTPException(
            status_code=500,
            detail="Variável de ambiente DATABASE_URL não configurada.",
        )
    return psycopg.connect(database_url, connect_timeout=10)


class LeituraSensor(BaseModel):
    gpio: int
    valor: int


@app.get("/")
def inicio():
    return {"projeto": "CenterTech", "status": "API funcionando"}


@app.get("/health")
def health():
    try:
        with conectar_banco() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        return {"status": "ok", "banco": "conectado"}
    except Exception:
        raise HTTPException(status_code=503, detail="Não foi possível conectar ao banco de dados.")


@app.get("/vagas")
def listar_vagas():
    with conectar_banco() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, codigo, status, latitude, longitude
                FROM vagas
                ORDER BY id
            """)
            vagas = cursor.fetchall()
            return [
                {
                    "id": vaga[0],
                    "codigo": vaga[1],
                    "status": vaga[2],
                    "latitude": float(vaga[3]) if vaga[3] is not None else None,
                    "longitude": float(vaga[4]) if vaga[4] is not None else None,
                }
                for vaga in vagas
            ]


@app.get("/historico")
def listar_historico():
    with conectar_banco() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT h.id, v.codigo, h.status, h.data_hora
                FROM historico_status h
                JOIN vagas v ON v.id = h.vaga_id
                ORDER BY h.data_hora DESC
                LIMIT 50
            """)
            registros = cursor.fetchall()
            return [
                {
                    "id": registro[0],
                    "vaga": registro[1],
                    "status": registro[2],
                    "data_hora": registro[3].isoformat(),
                }
                for registro in registros
            ]


@app.post("/sensores")
def receber_sensor(leitura: LeituraSensor):
    if leitura.valor not in (0, 1):
        raise HTTPException(status_code=400, detail="O valor do sensor deve ser 0 ou 1.")

    novo_status = "ocupada" if leitura.valor == 0 else "livre"

    with conectar_banco() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT vaga_id
                FROM sensores
                WHERE gpio = %s AND ativo = TRUE
            """, (leitura.gpio,))
            sensor = cursor.fetchone()
            if sensor is None:
                raise HTTPException(status_code=404, detail="Sensor não encontrado ou inativo.")

            vaga_id = sensor[0]
            cursor.execute("""
                UPDATE vagas
                SET status = %s
                WHERE id = %s
                RETURNING codigo
            """, (novo_status, vaga_id))
            vaga = cursor.fetchone()
            if vaga is None:
                raise HTTPException(status_code=404, detail="Vaga vinculada ao sensor não encontrada.")

            cursor.execute("""
                INSERT INTO historico_status (vaga_id, status)
                VALUES (%s, %s)
            """, (vaga_id, novo_status))
            conn.commit()

    return {
        "mensagem": "Sensor atualizado",
        "gpio": leitura.gpio,
        "valor": leitura.valor,
        "vaga": vaga[0],
        "status": novo_status,
    }
