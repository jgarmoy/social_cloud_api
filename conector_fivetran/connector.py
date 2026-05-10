# Imports 
import requests
from fivetran_connector_sdk import Connector
from fivetran_connector_sdk import Operations as op
from fivetran_connector_sdk import Logging as log

# Fechas fijas para la ingesta
FECHA_SEMANA_PERFILES = "2025-01-06"
FECHA_SNAPSHOT_AUDIENCIA = "2025-01-05"
FECHA_POST = "2025-01-01"

# Schema
def schema(configuration: dict):
    return [
        {
            "table": "raw_perfiles_empresas",
            "primary_key": ["perfil_id", "semana_snapshot"]
        },
        {
            "table": "raw_audiencia_demografica"
        },
        {
            "table": "raw_posts_interacciones",
            "primary_key": ["post_id", "tipo_interaccion"]
        }
    ]

# Llamar a la API
def llamar_api(base_url: str, endpoint:str, payload: dict) -> dict:
    """Llama al endpoint pasado de la API y devuelve el JSON"""
    url = f"{base_url.rstrip('/')}/{endpoint.strip('/')}/"
    respuesta = requests.post(url, json=payload, timeout=180)
    respuesta.raise_for_status()
    return respuesta.json()


# Update
def update(configuration: dict, state: dict):
    api_url = configuration["api_base_url"]

    perfiles_procesados = state.get("perfiles_procesados", [])
    log.info(f"Perfiles procesados previamente: {len(perfiles_procesados)}")

    # ==============
    # == Perfiles ==
    # ==============

    log.info(f"Llamando a /perfiles/ -> semana_snapshot: {FECHA_SEMANA_PERFILES}")

    respuesta_perfiles = llamar_api(
        api_url,
        "perfiles",
        {
            "semana_snapshot" : FECHA_SEMANA_PERFILES,
            "perfiles_excluidos": perfiles_procesados
        }
    )

    nueva_fila = respuesta_perfiles["record"]
    ctx = respuesta_perfiles["context"]

    op.upsert(table="raw_perfiles_empresas", data=nueva_fila)
    log.info(f"Perfil upserted → {ctx['perfil_id']} / {nueva_fila['SEMANA_SNAPSHOT']}")

    fila_anterior = ctx["fila_anterior"]
    fila_anterior["UPDATED_AT"] = nueva_fila["CREATED_AT"]
    op.upsert(table="raw_perfiles_empresas", data=fila_anterior)
    log.info(f"Fila anterior cerrada → {fila_anterior['SEMANA_SNAPSHOT']} / UPDATED_AT = {nueva_fila['CREATED_AT']}")

    # ===============
    # == Audiencia ==
    # ===============

    log.info(f"Llamando a /audiencia/ → snapshot: {FECHA_SNAPSHOT_AUDIENCIA}")

    respuesta_audiencia = llamar_api(
        api_url,
        "audiencia",
        {
            "semana_snapshot": FECHA_SNAPSHOT_AUDIENCIA,
            "perfil_id": ctx["perfil_id"],
            "empresa_id": ctx["empresa_id"],
            "username": ctx["username"],
            "plataforma": ctx["plataforma"],
            "seguidores": ctx["seguidores"],
        }
    )

    segmentos = respuesta_audiencia["records"]
    for segmento in segmentos:
        op.upsert(table="raw_audiencia_demografica", data=segmento)

    log.info(f"Audiencia upserted → {len(segmentos)} segmentos nuevos")

    created_at_nuevo = respuesta_audiencia["created_at_nuevo"]
    filas_anteriores = respuesta_audiencia["filas_anteriores"]
    for fila in filas_anteriores:
        fila["UPDATED_AT"] = created_at_nuevo 
        op.upsert(table = "raw_audiencia_demografica", data=fila)

    log.info(f"Snapshot anterior cerrado → {len(filas_anteriores)} filas con updated_at = {created_at_nuevo}")

    # ===========
    # == Posts ==
    # ===========

    log.info(f"Llamando a /post/ → fecha_publicacion: {FECHA_POST}")

    respuesta_post = llamar_api(
        api_url,
        "post",
        {
            "fecha_publicacion": FECHA_POST,
            "perfil_id": ctx["perfil_id"],
            "empresa_id": ctx["empresa_id"],
            "username": ctx["username"],
            "plataforma": ctx["plataforma"],
            "ultimo_post_id"   : state.get("ultimo_post_id", "P103861")
        }
    )

    filas_post = respuesta_post["records"]
    for fila in filas_post:
        op.upsert(table="raw_posts_interacciones", data=fila)
    
    log.info(f"Post upserted → {filas_post[0]['post_id']} ({len(filas_post)} filas)")
    nuevo_state = {
        "perfiles_procesados": perfiles_procesados + [ctx["perfil_id"]],
        "ultimo_post_id"     : filas_post[0]["post_id"]
    }

    op.checkpoint(state = nuevo_state)
    log.info(
        f"Checkpoint guardado → "
        f"{len(nuevo_state['perfiles_procesados'])} perfiles procesados en total"
    )

connector = Connector(update = update, schema = schema)

if __name__ == "__main__":
    connector.debug(
        configuration={"api_base_url": "https://social-cloud-api.onrender.com/social_cloud/api/v1"},
        state={"perfiles_procesados": ["P00169", "P00124"], "ultimo_post_id": "P103863"}
    )