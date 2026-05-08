from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from google.genai import types
from dotenv import load_dotenv
from google import genai
import os
import json
import random
import pandas as pd
import numpy as np
import re

# Create your views here.
def audiencia_gemini(request):

    if request.method == "POST":
        cuerpo = json.loads(request.body)
        semana_snapshot = cuerpo.get("semana_snapshot")
        perfil_id = cuerpo.get("perfil_id")
        empresa_id = cuerpo.get("empresa_id")
        username = cuerpo.get("username")
        plataforma_raw = cuerpo.get("plataforma")
        seguidores = cuerpo.get("seguidores")

        p = str(plataforma_raw).lower().strip()
        if any(x in p for x in ["instagram", "insta", "ig"]):
            plat_cannon = "Instagram"
        elif any(x in p for x in ["TikTok", "tik", "tk"]):
            plat_cannon = "TikTok"
        else:
            plat_cannon = "YouTube"

        tipos_columnas = {
            'TK_HANDLE': str,
            'TK_PLATFORM': str,
            'GENDER_SEGMENT': str,
            'AGE_SEGMENT': str,
            'COUNTRY': str,
            'IG_USERNAME': str,
            'IG_PLATFORM': str,
            'AUDIENCE_GENDER': str,
            'AUDIENCE_AGE': str,
            'AUDIENCE_COUNTRY': str,
            'YT_HANDLE': str,
            'NETWORK': str,
            'SEXO': str,
            'EDAD': str,
            'PAIS_AUDIENCIA': str,
            'EMPRESA_ID': str,
            'PERFIL_ID': str,
            'AUDIENCE_SHARE_PCT': float,
            'SEG_FOLLOWERS': float,
            'PCT_AUDIENCE': float,
            'FOLLOWER_COUNT_SEG': float,
            'PORCENTAJE': float,
            'N_SEGUIDORES_SEG': float
        }

        columnas_fecha = [
            'SNAPSHOT_DATE', 
            'REPORT_DATE', 
            'PERIOD', 
            'CREATED_AT', 
            'UPDATED_AT'
        ]

        df = pd.read_csv(
            "csv_raw/raw_audiencia_demografica.csv",
            dtype=tipos_columnas,
            parse_dates=columnas_fecha,
            low_memory=False
        )

        if plat_cannon == "TikTok":
            df_perfil = df[(df["PERFIL_ID"] == perfil_id) & (df["TK_PLATFORM"].notna())]
            fecha_col = "SNAPSHOT_DATE"
        elif plat_cannon == "Instagram":
            df_perfil = df[(df["PERFIL_ID"] == perfil_id) & (df["IG_PLATFORM"].notna())]
            fecha_col = "REPORT_DATE"
        else:
            df_perfil = df[(df["PERFIL_ID"] == perfil_id) & (df["NETWORK"].notna())]
            fecha_col = "PERIOD"

        ultimo_snapshot = df_perfil[df_perfil['UPDATED_AT'].isna()]

        client = conectar_gemini()

        respuesta = client.models.generate_content(
            model="gemini-3-flash-preview",
            config=types.GenerateContentConfig(
                system_instruction="Eres un analista de datos experto en redes sociales. Genera datos demográficos coherentes y realistas. Devuelve estrictamente un objeto JSON con la estructura indicada",
                response_mime_type = "application/json"
            ),
            contents=construir_prompt({
                "num_prompt": 1,
                "snapshot_date": semana_snapshot,
                "perfil_id": perfil_id,
                "empresa_id": empresa_id,
                "username": username,
                "plat_cannon": plat_cannon,
                "seguidores": seguidores
            })
        )

        texto_bruto = respuesta.text

        try:
            match = re.search(r'\{.*\}', texto_bruto, re.DOTALL)
            if match:
                texto_limpio = match.group(0)
                datos = json.loads(texto_limpio)
            else:
                # Si no hay llaves, algo salió muy mal con la IA
                datos = {"records": []}
                
        except json.JSONDecodeError as e:
            print(f"Error fatal de decodificación: {e}")
            datos = {"records": []}
        nuevos_registros = datos.get("records", [])

        filas_anteriores = []
        if not ultimo_snapshot.empty:
            for _, fila in ultimo_snapshot.iterrows():
                filas_anteriores.append({
                    col: (None if pd.isna(fila[col]) or str(fila[col]).lower() == "nan" else fila[col])
                    for col in fila.index
                })

        return JsonResponse({
            "records": nuevos_registros,
            "filas_anteriores": filas_anteriores,
            "snapshot_date": semana_snapshot
        })

def perfiles_gemini(request):

    if request.method == "POST":
        cuerpo = json.loads(request.body)
        semana_snapshot = cuerpo.get("semana_snapshot")
        perfiles_excluidos = cuerpo.get("perfiles_excluidos", [])

        df_sin_excluidos = pd.read_csv("csv_raw/raw_perfiles_empresas.csv")

        df_disponibles = df_sin_excluidos[~df_sin_excluidos['PERFIL_ID'].isin(perfiles_excluidos)]

        if df_disponibles.empty:
            return JsonResponse({"error": "No hay perfiles disponibles para procesar"}, status=400)

        candidatos = df_disponibles[(df_disponibles["ACTIVO"] == True) & (df_disponibles["UPDATED_AT"].isna())]

        perfil_elegido = candidatos.sample(n=1).iloc[0]

        seguidores_actuales = int(perfil_elegido['SEGUIDORES'])
        seguidores_min      = max(500, seguidores_actuales - 400)
        seguidores_max      = seguidores_actuales + 1500
        alcance_min         = int(seguidores_max * 0.05)
        alcance_max         = int(seguidores_max * 0.40)

        print(perfil_elegido)

        client = conectar_gemini()

        respuesta = client.models.generate_content(
            model="gemini-3-flash-preview",
            config=types.GenerateContentConfig(
                system_instruction=(
                    """
                        Eres un analista de datos experto. Tu tarea es generar métricas de redes sociales coherentes y realistas basadas en el perfil de empresa proporcionado. 
                        Debes devolver estrictamente un objeto JSON que siga la estructura exacta de columnas del dataset.
                    """
                ),
                response_mime_type="application/json"
            ),
            contents=construir_prompt({
                "num_prompt": 2,
                "semana_snapshot": semana_snapshot,
                "seguidores_actuales": seguidores_actuales,
                "seguidores_min": seguidores_min,
                "seguidores_max": seguidores_max,
                "alcance_min": alcance_min,
                "alcance_max": alcance_max,
                "contexto_perfil": f"""
                    Datos reales del perfil:
                    EMPRESA_ID: {perfil_elegido['EMPRESA_ID']}
                    EMPRESA_NOMBRE: {perfil_elegido['EMPRESA_NOMBRE']}
                    EMPRESA_CATEGORIA: {perfil_elegido['EMPRESA_CATEGORIA']} 
                    EMPRESA_PAIS: {perfil_elegido['EMPRESA_PAIS']} 
                    EMPRESA_WEB: {perfil_elegido['EMPRESA_WEB']} 
                    EMPRESA_EMAIL: {perfil_elegido['EMPRESA_EMAIL']} 
                    PERFIL_ID: {perfil_elegido['PERFIL_ID']} 
                    USERNAME: {perfil_elegido['USERNAME']} 
                    PLATAFORMA: {perfil_elegido['PLATAFORMA']} 
                    FECHA_CREACION_PERFIL: {perfil_elegido['FECHA_CREACION_PERFIL']}
                    ACTIVO: {perfil_elegido['ACTIVO']}
                """
            })
        )

        datos = json.loads(respuesta.text)
        return JsonResponse({
            "record": datos,
            "context": {
                "perfil_id" : str(perfil_elegido['PERFIL_ID']),
                "empresa_id": str(perfil_elegido['EMPRESA_ID']),
                "username"  : str(perfil_elegido['USERNAME']),
                "plataforma": str(perfil_elegido['PLATAFORMA']),
                "seguidores": int(datos.get('SEGUIDORES')),
                "fila_anterior": {
                    col: (None if pd.isna(perfil_elegido[col]) or str(perfil_elegido[col]) == "nan" 
                        else perfil_elegido[col])
                    for col in perfil_elegido.index
                }
            }
        })
    

def post_gemini(request):
    client = conectar_gemini()

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        config=types.GenerateContentConfig(
            system_instruction="Eres un asistente que responde a las preguntas de los usuarios de manera clara y consisa. Devuelve solamente  un json con la respuesta a la pregunta del usuario"
        ),
        contents=construir_prompt({
            "num_prompt": 3,
            "semana_snapshot": ""
        })
    )
    json_response = json.loads(response.text)

    return JsonResponse(json_response)

def conectar_gemini():
    load_dotenv()

    return genai.Client(api_key = os.getenv("GEMINI_API_KEY"))


def construir_prompt(json_data):
    if json_data["num_prompt"] == 1: # raw_audiencia_demografica
        plat = json_data["plat_cannon"]
        seg = json_data["seguidores"]
        snap = json_data["snapshot_date"]
        pid = json_data["perfil_id"]
        eid = json_data["empresa_id"]
        uname = json_data["username"]
 
        # Columnas por completar por plataforma (el resto deben ser null)
        if plat == "TikTok":
            cols_activas = "tk_handle, tk_platform, snapshot_date, gender_segment, age_segment, country, audience_share_pct, seg_followers"
            handle_col = f"tk_handle: {uname}"
            platform_col = f'tk_platform: "TikTok" (typo el 12%: "TK", "tiktok")'
            fecha_col = f'snapshot_date: "{snap}"'
            genero_col = "gender_segment"
            edad_col = "age_segment"
            pais_col = "country"
            pct_col = "audience_share_pct"
            seg_col = "seg_followers"
        elif plat == "Instagram":
            cols_activas = "ig_username, ig_platform, report_date, audience_gender, audience_age, audience_country, pct_audience, follower_count_seg"
            handle_col = f"ig_username: {uname}"
            platform_col = f'ig_platform: "Instagram" (typo el 12%: "IG", "Insta", "INSTAGRAM")'
            fecha_col = f'report_date: "{snap}"'
            genero_col = "audience_gender"
            edad_col = "audience_age"
            pais_col = "audience_country"
            pct_col = "pct_audience"
            seg_col = "follower_count_seg"
        else: 
            cols_activas = "yt_handle, network, period, sexo, edad, pais_audiencia, porcentaje, n_seguidores_seg"
            handle_col = f"yt_handle: {uname}"
            platform_col = f'network: "YouTube" (typo el 12%: "YT", "youtube")'
            fecha_col = f'period: "{snap}"'
            genero_col = "sexo"
            edad_col = "edad"
            pais_col = "pais_audiencia"
            pct_col = "porcentaje"
            seg_col = "n_seguidores_seg"
 
        return f"""
            Genera entre 15 y 18 registros de audiencia demográfica para la tabla raw_audiencia_demografica.
            Cada fila es un segmento de audiencia (combinación género + edad + país) del perfil indicado.
            
            CONTEXTO DEL PERFIL:
            perfil_id:  {pid}
            empresa_id: {eid}
            username:   {uname}
            plataforma: {plat}
            seguidores: {seg}
            snapshot:   {snap}
            
            COLUMNAS A RELLENAR (solo las de {plat}, el resto = null):
            {handle_col}
            {platform_col}
            {fecha_col}
            {genero_col}: "Hombre", "Mujer" o "No binario"
            {edad_col}: "18-24", "25-34", "35-44", "45-54" o "55+"
            {pais_col}: España, México, Argentina, Colombia, Chile, Perú,
                        Estados Unidos, Venezuela, Ecuador, Uruguay — null el 7%
            {pct_col}: entre 0.5 y 20.0
            {seg_col}: redondear ({pct_col} * {seg} / 100) a entero
            empresa_id: "{eid}"
            perfil_id:  "{pid}"
            created_at: "{snap}THH:MM:SS" con hora aleatoria entre 01:00 y 06:00,
                        IGUAL en todos los registros de este snapshot
            updated_at: null en todos (snapshot más reciente)
            
            REGLAS:
            - Genera entre 15 y 18 filas con combinaciones distintas de género + edad
            - No hace falta cubrir todos los países, sí todos los géneros y edades
            - El resto de columnas (de otras plataformas) deben ser null
            
            ESQUEMA COMPLETO (28 columnas, la mayoría null):
            {{
            "tk_handle": null, "tk_platform": null, "snapshot_date": null,
            "gender_segment": null, "age_segment": null, "country": null,
            "audience_share_pct": null, "seg_followers": null,
            "ig_username": null, "ig_platform": null, "report_date": null,
            "audience_gender": null, "audience_age": null,
            "audience_country": null, "pct_audience": null, "follower_count_seg": null,
            "yt_handle": null, "network": null, "period": null,
            "sexo": null, "edad": null, "pais_audiencia": null,
            "porcentaje": null, "n_seguidores_seg": null,
            "empresa_id": "{eid}", "perfil_id": "{pid}",
            "created_at": "...", "updated_at": null
            }}
            
            Devuelve: {{"records": [ ...entre 15 y 18 objetos... ]}}
        """
    elif json_data["num_prompt"] == 2: # raw_perfiles_empresas
        contexto_perfil = json_data["contexto_perfil"]

        return f'''
            Basado en este contexto del perfil:
            {json_data["contexto_perfil"]}
 
            Genera una nueva entrada de datos para la semana: {json_data["semana_snapshot"]}.
 
            Reglas:
            1. Mantén los datos identificadores del contexto (IDs, Nombres, Plataforma).
            2. Genera métricas siguiendo estrictamente estos rangos:
               - SEGUIDORES: entero entre {json_data["seguidores_min"]} y {json_data["seguidores_max"]}
                 (la semana anterior tenía {json_data["seguidores_actuales"]} seguidores)
               - ALCANCE_SEMANAL: entero entre {json_data["alcance_min"]} y {json_data["alcance_max"]}
               - IMPRESIONES_SEMANALES: entre 1.2 y 3.0 veces el valor de ALCANCE_SEMANAL,
                 SIEMPRE mayor que ALCANCE_SEMANAL
               - VISITAS_PERFIL: entre el 1% y el 8% de SEGUIDORES
            3. ACTIVO debe ser True.
            4. CREATED_AT debe ser "{json_data["semana_snapshot"]}THH:MM:SS"
               con hora aleatoria entre 01:00 y 06:00.
            5. UPDATED_AT debe ser null.
 
            Estructura requerida:
            EMPRESA_ID, EMPRESA_NOMBRE, EMPRESA_CATEGORIA, EMPRESA_PAIS, EMPRESA_WEB, EMPRESA_EMAIL, 
            PERFIL_ID, USERNAME, PLATAFORMA, FECHA_CREACION_PERFIL, ACTIVO, SEMANA_SNAPSHOT, 
            SEGUIDORES, ALCANCE_SEMANAL, IMPRESIONES_SEMANALES, VISITAS_PERFIL, CREATED_AT, UPDATED_AT
        '''
    elif json_data["num_prompt"] == 3: # raw_posts_interacciones
        return f'''
            Eres un generador de datos sintéticos para redes sociales. Devuelve ÚNICAMENTE un objeto JSON válido, sin explicaciones ni markdown.

            IMPORTANTE: cada post se representa con exactamente 4 filas, una por tipo_interaccion (Like, Comentario, Compartir, Guardado). Todos los campos son idénticos entre las 4 filas salvo tipo_interaccion y cantidad_interaccion.

            ━━━ SECCIÓN 1 — UPDATE ━━━
            Modifica las métricas de este post existente. Los campos de identidad NO cambian
            (post_id, raw_json_id, username, empresa_id, plataforma, fecha_publicacion, tipo_contenido).

            Las 4 filas actuales del post:
            {json.dumps(rows_to_update, ensure_ascii=False, default=str)}

            Reglas del UPDATE:
            - cantidad_interaccion de cada tipo varía ±5-15% respecto al valor original
            - engagement_total = suma de los 4 nuevos valores de cantidad_interaccion
            - Si impresiones era 0 en el original: corrígelo a un valor > 0 (simulando fix de tracking)
            - updated_at: timestamp ISO posterior al created_at original, con fecha de hoy
            - Devuelve las 4 filas actualizadas

            ━━━ SECCIÓN 2 — INSERTs nuevos ━━━
            Genera exactamente {n_inserts} posts nuevos ({n_inserts * 4} filas en total, 4 por post).
            Usa estos pares username+empresa_id existentes:
            {json.dumps(pares, ensure_ascii=False)}

            Reglas de los INSERTs:
            - post_id: desde P{next_post_num:06d} incrementando, mismo post_id en las 4 filas
            - raw_json_id: UUID v4 único por post, igual en las 4 filas
            - fecha_publicacion: entre "2025-01-06" y "2025-01-13"
            - tipo_contenido con distribución: Reel 40%, Story 25%, Post estático 15%, Carrusel 12%, Video 8%
            - Like: entre 10 y 35000 (1% de posts: entre 500000 y 2000000 — viral)
            - Comentario: 0-20% del Like, Compartir: 0-12%, Guardado: 0-25%
            - engagement_total = suma de los 4 tipos
            - impresiones = 0 en el 3% de los posts (error de tracking) → visualizaciones también 0
            - descripcion: null el 7% de las veces
            - patrocinado: true el 15% de las veces, es_campana_bf: false
            - plataforma con typos el 12% de las veces
            - source_api: "api_v1" 40%, "api_v2" 35%, "manual_export" 25%
            - created_at: fecha_publicacion + entre 1 y 6 horas, updated_at: null el 7% de las veces

            ESQUEMA EXACTO (cada una de las filas):
            {"post_id": string, "raw_json_id": string (UUID), "username": string,
            "empresa_id": string, "plataforma": string, "fecha_publicacion": string (ISO),
            "tipo_contenido": string, "descripcion": string|null, "patrocinado": boolean,
            "es_campana_bf": boolean, "hashtags": string (2-6), 
            "visualizaciones": integer, "alcance": integer, "impresiones": integer,
            "tipo_interaccion": string, "cantidad_interaccion": integer,
            "engagement_total": integer, "source_api": string,
            "created_at": string (ISO), "updated_at": string|null}

            Devuelve:
            {"update": [ ...4 filas actualizadas... ], "inserts": [ ...{n_inserts * 4} filas nuevas... ]}
        '''
