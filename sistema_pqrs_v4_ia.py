#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════
  SISTEMA INTELIGENTE DE PQRS - VERSIÓN 4.0 CON IA REAL
═══════════════════════════════════════════════════════════════════
"""

import sqlite3
import re
import os
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class SistemaPQRSIA:

    def __init__(self):
        self.db = 'pqrs_sistema.db'
        self.conn = None

        # 🔥 CAMBIO IMPORTANTE:
        # NO cargar modelo aquí (evita que la nube se caiga)
        self.modelo_embeddings = None

        # Cache de embeddings
        self.cache_embeddings = {}
        self.cache_file = 'embeddings_cache.pkl'

        self.sinonimos = {
            'eliminar': ['borrar', 'quitar', 'remover', 'sacar', 'anular', 'cancelar'],
            'actualizar': ['modificar', 'cambiar', 'editar', 'corregir', 'ajustar'],
            'crear': ['generar', 'agregar', 'añadir', 'insertar', 'registrar'],
            'consultar': ['ver', 'revisar', 'buscar', 'verificar'],
            'asignar': ['asociar', 'vincular', 'relacionar'],
            'comision': ['comisión', 'fee', 'cargo'],
            'credito': ['crédito', 'prestamo', 'préstamo'],
            'vendedor': ['asesor', 'comercial'],
            'concesionario': ['dealer'],
            'liquidacion': ['liquidación', 'settlement'],
            'estado': ['status', 'estatus'],
            'certificado': ['certificate'],
            'factura': ['invoice', 'recibo'],
        }

        self.inicializar()
        self.cargar_cache_embeddings()

    # 🔥 NUEVO MÉTODO (CARGA BAJO DEMANDA)
    def obtener_modelo(self):
        if self.modelo_embeddings is None:
            print("🔄 Cargando modelo de IA...")
            self.modelo_embeddings = SentenceTransformer(
                'paraphrase-multilingual-MiniLM-L12-v2'
            )
            print("✅ Modelo cargado")
        return self.modelo_embeddings

    def inicializar(self):
        self.conn = sqlite3.connect(self.db, check_same_thread=False)
        c = self.conn.cursor()

        c.execute('''
            CREATE TABLE IF NOT EXISTS casos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                categoria TEXT,
                problema TEXT,
                sql TEXT,
                respuesta TEXT,
                usos INTEGER DEFAULT 0,
                efectividad INTEGER DEFAULT 0,
                conceptos_clave TEXT,
                complejidad INTEGER DEFAULT 1
            )
        ''')

        self.conn.commit()

        c.execute('SELECT COUNT(*) FROM casos')
        if c.fetchone()[0] == 0:
            self.cargar_desde_archivo()

    def generar_embedding(self, texto):
        texto_limpio = texto.strip()

        # 🔥 CAMBIO AQUÍ: usar modelo bajo demanda
        modelo = self.obtener_modelo()
        embedding = modelo.encode(texto_limpio, convert_to_numpy=True)

        return embedding

    def cargar_cache_embeddings(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'rb') as f:
                    self.cache_embeddings = pickle.load(f)
                print(f"✅ Cache cargado: {len(self.cache_embeddings)} casos")
            except:
                self.cache_embeddings = {}

    def guardar_cache_embeddings(self):
        with open(self.cache_file, 'wb') as f:
            pickle.dump(self.cache_embeddings, f)

    def calcular_embedding_caso(self, caso_id, problema):
        if caso_id not in self.cache_embeddings:
            self.cache_embeddings[caso_id] = self.generar_embedding(problema)
            self.guardar_cache_embeddings()

        return self.cache_embeddings[caso_id]

    def cargar_desde_archivo(self):
        archivo = 'PQRS_NUEVAS_CON_SQL.txt'

        if not os.path.exists(archivo):
            print(f"⚠️ Archivo {archivo} no encontrado")
            return

        print(f"🔄 Cargando casos desde {archivo}...")

        with open(archivo, 'r', encoding='utf-8') as f:
            contenido = f.read()

        bloques = contenido.split('========================')
        casos_cargados = 0

        for bloque in bloques:
            if '--- PROBLEMA ---' not in bloque:
                continue

            try:
                cat_match = re.search(r'CATEGOR[ÍI]A:\s*(.+)', bloque)
                categoria = cat_match.group(1).strip() if cat_match else "General"

                prob_match = re.search(r'--- PROBLEMA ---\s*(.+?)\s*---', bloque, re.DOTALL)
                problema = prob_match.group(1).strip() if prob_match else ""

                sql_match = re.search(r'--- SOLUCI[ÓO]N T[ÉE]CNICA.*?---\s*(.+?)\s*(?:TIEMPO:|ESTADO:|$)', bloque, re.DOTALL)
                sql = sql_match.group(1).strip() if sql_match else ""

                resp_match = re.search(r'--- SOLUCI[ÓO]N ---\s*(.+?)\s*---', bloque, re.DOTALL)
                respuesta = resp_match.group(1).strip() if resp_match else ""

                if problema and sql:
                    c = self.conn.cursor()
                    c.execute('''
                        INSERT INTO casos (categoria, problema, sql, respuesta)
                        VALUES (?, ?, ?, ?)
                    ''', (categoria, problema, sql, respuesta))

                    caso_id = c.lastrowid

                    # 🔥 embedding se genera bajo demanda
                    self.calcular_embedding_caso(caso_id, problema)

                    casos_cargados += 1

            except Exception as e:
                print(f"⚠️ Error procesando bloque: {e}")
                continue

        self.conn.commit()
        print(f"✅ {casos_cargados} casos cargados")

    def buscar_similar_ia(self, problema):
        c = self.conn.cursor()
        c.execute('SELECT id, categoria, problema, sql, respuesta FROM casos')
        casos = c.fetchall()

        if not casos:
            return None

        embedding_nuevo = self.generar_embedding(problema)
        ranking = []

        for caso in casos:
            caso_id, cat, prob_bd, sql, resp = caso

            embedding_caso = self.calcular_embedding_caso(caso_id, prob_bd)

            similitud = cosine_similarity(
                embedding_nuevo.reshape(1, -1),
                embedding_caso.reshape(1, -1)
            )[0][0]

            ranking.append({
                'id': caso_id,
                'categoria': cat,
                'problema': prob_bd,
                'sql': sql,
                'respuesta': resp,
                'similitud': float(similitud)
            })

        ranking.sort(key=lambda x: x['similitud'], reverse=True)
        return ranking


# Compatibilidad
SistemaPQRSUltra = SistemaPQRSIA
