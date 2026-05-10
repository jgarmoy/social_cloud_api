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
import uuid
import hashlib

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
        if any(x in p for x in ["insta", "ig"]):
            plat_cannon = "Instagram"
        elif any(x in p for x in ["tik", "tk"]):
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

        # Añadir justo antes de llamar a Gemini
        hora   = random.randint(1, 6)
        minuto = random.randint(0, 59)
        segundo = random.randint(0, 59)
        created_at_nuevo = f"{semana_snapshot} {hora:02d}:{minuto:02d}:{segundo:02d}.000"

        client = conectar_gemini()

        respuesta = client.models.generate_content(
            model = "gemini-3-flash-preview",
            config=types.GenerateContentConfig(
                system_instruction = """
                    Eres un analista de datos experto en redes sociales. Genera datos demográficos coherentes y realistas. Devuelve estrictamente un objeto JSON con la estructura indicada
                """,
                response_mime_type = "application/json"
            ),
            contents = construir_prompt({
                "num_prompt": 1,
                "snapshot_date": semana_snapshot,
                "created_at": created_at_nuevo,
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
            "snapshot_date": semana_snapshot,
            "created_at_nuevo": created_at_nuevo
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

        if candidatos.empty:
            return JsonResponse({"error": "No quedan perfiles activos sin procesar"}, status=400)

        perfil_elegido = candidatos.sample(n=1).iloc[0]

        seguidores_actuales = int(perfil_elegido['SEGUIDORES'])
        seguidores_min      = max(500, seguidores_actuales - 400)
        seguidores_max      = seguidores_actuales + 1500
        alcance_min         = int(seguidores_max * 0.05)
        alcance_max         = int(seguidores_max * 0.40)

        client = conectar_gemini()

        respuesta = client.models.generate_content(
            model="gemini-3-flash-preview",
            config=types.GenerateContentConfig(
                system_instruction="""
                    Eres un analista de datos experto en redes sociales. Genera datos demográficos coherentes y realistas. Devuelve estrictamente un objeto JSON con la estructura indicada.
                """
                ,
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
                    col: convertir_valor(perfil_elegido[col])
                    for col in perfil_elegido.index
                }
            }
        })
    

def post_gemini(request):
    
    if request.method == "POST":
        cuerpo = json.loads(request.body)
        fecha_publicacion = cuerpo.get("fecha_publicacion")
        perfil_id = cuerpo.get("perfil_id")
        empresa_id = cuerpo.get("empresa_id")
        username = cuerpo.get("username")
        plataforma = cuerpo.get("plataforma")

        ultimo_post_id = cuerpo.get("ultimo_post_id", "P103861")
        num_max_post   = int(ultimo_post_id[1:])
        next_post_num  = f"P{num_max_post + 1:06d}" # Rellena con ceros a la izquierda hasta 6 dígitos
        raw_json = str(uuid.uuid4())

        es_viral = random.random() < 0.01
        if es_viral:
            likes_min = 500000
            likes_max = 2000000
        else:
            likes_min = 10
            likes_max = 35000

        es_error_tracking = random.random() < 0.03
        if es_error_tracking:
            visualizaciones = 0
            alcance = random.randint(500, 120000)
            impresiones = 0
        else:
            alcance = random.randint(500, 120000)
            visualizaciones = int(alcance * random.uniform(0.8, 1.0))
            impresiones = int(alcance * random.uniform(1.2, 3.5))

        tipo_contenido = random.choices(
            ['Reel', 'Story', 'Post estático', 'Carrusel', 'Vídeo'],
            weights = [0.42, 0.24, 0.15, 0.12, 0.08]
        )[0]

        source_api = random.choices(
            ['api_v1', 'api_v2', 'manual_export'],
            weights = [0.40, 0.35, 0.25]
        )[0]

        patrocinado = random.random() < 0.15

        client = conectar_gemini()

        respuesta = client.models.generate_content(
            model="gemini-3-flash-preview",
            config=types.GenerateContentConfig(
                system_instruction = """
                    Eres un asistente que responde a las preguntas de los usuarios de manera clara y consisa. Devuelve solamente  un json con la respuesta a la pregunta del usuario
                """,
                response_mime_type="application/json"
            ),
            contents=construir_prompt({
                "num_prompt" : 3,
                "post_id" : next_post_num,
                "raw_json_id" : raw_json,
                "username" : username,
                "empresa_id" : empresa_id,
                "plataforma" : plataforma,
                "fecha_publicacion": fecha_publicacion,
                "tipo_contenido" : tipo_contenido,
                "patrocinado" : patrocinado,
                "visualizaciones" : visualizaciones,
                "alcance" : alcance,
                "impresiones" : impresiones,
                "likes_min" : likes_min,
                "likes_max" : likes_max,
                "source_api" : source_api,
                "es_viral" : es_viral,
            })
        )
        datos = json.loads(respuesta.text)
        filas_post = datos.get("records", [])

        return JsonResponse({"records": filas_post})

def conectar_gemini():
    load_dotenv()

    return genai.Client(api_key = os.getenv("GEMINI_API_KEY"))

def convertir_valor(val):
    if pd.isna(val) or str(val).lower() == "nan":
        return None
    if isinstance(val, (np.bool_,)):
        return bool(val)
    if isinstance(val, np.integer):
        return int(val)
    if isinstance(val, np.floating):
        return float(val)
    return val


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
            created_at: "{json_data['created_at']}" — usa exactamente este valor en todos los registros
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
            4. CREATED_AT debe tener el formato "YYYY-MM-DD HH:MM:SS.000" con fecha "{json_data["semana_snapshot"]}" y hora aleatoria entre 01:00 y 06:00.
            Ejemplo: "{json_data["semana_snapshot"]} 03:42:15.000"
            5. UPDATED_AT debe ser null.
 
            Estructura requerida:
            EMPRESA_ID, EMPRESA_NOMBRE, EMPRESA_CATEGORIA, EMPRESA_PAIS, EMPRESA_WEB, EMPRESA_EMAIL, 
            PERFIL_ID, USERNAME, PLATAFORMA, FECHA_CREACION_PERFIL, ACTIVO, SEMANA_SNAPSHOT, 
            SEGUIDORES, ALCANCE_SEMANAL, IMPRESIONES_SEMANALES, VISITAS_PERFIL, CREATED_AT, UPDATED_AT
        '''
    elif json_data["num_prompt"] == 3: # raw_posts_interacciones
        pid = json_data["post_id"]
        rjid = json_data["raw_json_id"]
        uname = json_data["username"]
        eid = json_data["empresa_id"]
        plat = json_data["plataforma"]
        fecha = json_data["fecha_publicacion"]
        tc = json_data["tipo_contenido"]
        pat = json_data["patrocinado"]
        viz = json_data["visualizaciones"]
        alc = json_data["alcance"]
        imp = json_data["impresiones"]
        lmin = json_data["likes_min"]
        lmax = json_data["likes_max"]
        src = json_data["source_api"]
        viral = json_data["es_viral"]
 
        return f"""
            Genera exactamente 4 registros para la tabla raw_posts_interacciones.
            Son las 4 filas del mismo post, una por tipo de interacción.
            
            CAMPOS IGUALES EN LAS 4 FILAS — copia exactamente estos valores:
            post_id:          "{pid}"
            raw_json_id:      "{rjid}"
            username:         "{uname}"
            empresa_id:       "{eid}"
            plataforma:       "{plat}"
            fecha_publicacion:"{fecha}"
            tipo_contenido:   "{tc}"
            patrocinado:      {str(pat).lower()}
            es_campana_bf:    false
            visualizaciones:  {viz}
            alcance:          {alc}
            impresiones:      {imp}{"  ← error de tracking, impresiones y visualizaciones = 0" if imp == 0 else ""}
            source_api:       "{src}"
            created_at: "{fecha} HH:MM:SS.000" con entre 1 y 6 horas sumadas a la fecha_publicacion
            Ejemplo: "{fecha} 05:23:41.000"
            updated_at:       null
            {"⚠️ POST VIRAL — likes muy altos, es normal" if viral else ""}
            
            CAMPOS QUE CAMBIAN EN CADA FILA:
            Genera una fila por cada tipo_interaccion en este orden:
            
            1. tipo_interaccion: "Like"
                cantidad_interaccion: entero entre {lmin:,} y {lmax:,}
            
            2. tipo_interaccion: "Comentario"
                cantidad_interaccion: entre 0% y 20% del valor de Like
            
            3. tipo_interaccion: "Compartir"
                cantidad_interaccion: entre 0% y 12% del valor de Like
            
            4. tipo_interaccion: "Guardado"
                cantidad_interaccion: entre 0% y 25% del valor de Like
            
            engagement_total: suma de las 4 cantidades (igual en las 4 filas)
            
            CAMPO LIBRE — genera tú:
            descripcion: texto en inglés de 15 a 30 palabras
            hashtags: entre 2 y 6 hashtags en español (ej: "#marketing #tendencias")
            
            ESQUEMA EXACTO DE CADA FILA:
            {{
            "post_id": "string", "raw_json_id": "string", "username": "string",
            "empresa_id": "string", "plataforma": "string",
            "fecha_publicacion": "string", "tipo_contenido": "string",
            "descripcion": "string|null", "patrocinado": "boolean",
            "es_campana_bf": "boolean", "hashtags": "string",
            "visualizaciones": "integer", "alcance": "integer", "impresiones": "integer",
            "tipo_interaccion": "string", "cantidad_interaccion": "integer",
            "engagement_total": "integer", "source_api": "string",
            "created_at": "string", "updated_at": null
            }}
            
            Devuelve: {{"records": [ ...exactamente 4 objetos... ]}}
        """
