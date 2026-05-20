USE ROLE SOCIAL_CLOUD;
USE WAREHOUSE WH_SOCIAL_CLOUD;

-- Comprobar ejecuciones pro
SELECT *
FROM TABLE(
    pro_social_cloud_bronze_db.INFORMATION_SCHEMA.TASK_HISTORY(
        RESULT_LIMIT => 20
    )
)
WHERE NAME in ('SYNC_AUDIENCIA', 'SYNC_PERFILES', 'SYNC_POSTS')
ORDER BY SCHEDULED_TIME DESC;

-- Comprobar ejecuciones pre
SELECT *
FROM TABLE(
    pre_social_cloud_bronze_db.INFORMATION_SCHEMA.TASK_HISTORY(
        RESULT_LIMIT => 20
    )
)
WHERE NAME in ('SYNC_AUDIENCIA', 'SYNC_PERFILES', 'SYNC_POSTS')
ORDER BY SCHEDULED_TIME DESC;

-- Comprobar ejecuciones dev
SELECT *
FROM TABLE(
    dev_social_cloud_bronze_db.INFORMATION_SCHEMA.TASK_HISTORY(
        RESULT_LIMIT => 20
    )
)
WHERE NAME in ('SYNC_AUDIENCIA', 'SYNC_PERFILES', 'SYNC_POSTS')
ORDER BY SCHEDULED_TIME DESC;

-- Comprobar resultados pro
SELECT *
FROM pro_social_cloud_bronze_db.SOCIAL_CLOUD_CONECTOR_PRO.RAW_AUDIENCIA_DEMOGRAFICA
WHERE _FIVETRAN_SYNCED::DATE > '2026-05-09'
ORDER BY _FIVETRAN_SYNCED DESC;

SELECT *
FROM pro_social_cloud_bronze_db.SOCIAL_CLOUD_CONECTOR_PRO.RAW_PERFILES_EMPRESAS
WHERE _FIVETRAN_SYNCED::DATE > '2026-05-09'
ORDER BY _FIVETRAN_SYNCED DESC;

SELECT *
FROM pro_social_cloud_bronze_db.SOCIAL_CLOUD_CONECTOR_PRO.raw_posts_interacciones
WHERE _FIVETRAN_SYNCED::DATE > '2026-05-09'
ORDER BY _FIVETRAN_SYNCED DESC;

-- Comprobar resultados pre
SELECT *
FROM pre_social_cloud_bronze_db.SOCIAL_CLOUD_SCHEMA.RAW_AUDIENCIA_DEMOGRAFICA
WHERE _FIVETRAN_SYNCED::DATE > '2026-05-09'
ORDER BY _FIVETRAN_SYNCED DESC;

SELECT *
FROM pre_social_cloud_bronze_db.SOCIAL_CLOUD_SCHEMA.RAW_PERFILES_EMPRESAS
WHERE _FIVETRAN_SYNCED::DATE > '2026-05-09'
ORDER BY _FIVETRAN_SYNCED DESC;

SELECT *
FROM pre_social_cloud_bronze_db.SOCIAL_CLOUD_SCHEMA.raw_posts_interacciones
WHERE _FIVETRAN_SYNCED::DATE > '2026-05-09'
ORDER BY _FIVETRAN_SYNCED DESC;

-- Comprobar resultados dev
SELECT *
FROM dev_social_cloud_bronze_db.SOCIAL_CLOUD_SCHEMA.RAW_AUDIENCIA_DEMOGRAFICA
WHERE _FIVETRAN_SYNCED::DATE > '2026-05-09'
ORDER BY _FIVETRAN_SYNCED DESC;

SELECT *
FROM dev_social_cloud_bronze_db.SOCIAL_CLOUD_SCHEMA.RAW_PERFILES_EMPRESAS
WHERE _FIVETRAN_SYNCED::DATE > '2026-05-09'
ORDER BY _FIVETRAN_SYNCED DESC;

SELECT *
FROM dev_social_cloud_bronze_db.SOCIAL_CLOUD_SCHEMA.raw_posts_interacciones
WHERE _FIVETRAN_SYNCED::DATE > '2026-05-09'
ORDER BY _FIVETRAN_SYNCED DESC;

-- Descripción tablas pro
DESC TABLE pro_social_cloud_bronze_db.SOCIAL_CLOUD_SCHEMA.RAW_POSTS_INTERACCIONES;
DESC TABLE pro_social_cloud_bronze_db.SOCIAL_CLOUD_SCHEMA.RAW_AUDIENCIA_DEMOGRAFICA;
DESC TABLE pro_social_cloud_bronze_db.SOCIAL_CLOUD_SCHEMA.RAW_PERFILES_EMPRESAS;

DESC TABLE pro_social_cloud_bronze_db.SOCIAL_CLOUD_CONECTOR_PRO.RAW_POSTS_INTERACCIONES;
DESC TABLE pro_social_cloud_bronze_db.SOCIAL_CLOUD_CONECTOR_PRO.RAW_AUDIENCIA_DEMOGRAFICA;
DESC TABLE pro_social_cloud_bronze_db.SOCIAL_CLOUD_CONECTOR_PRO.RAW_PERFILES_EMPRESAS;

-- Descripción tablas pre
DESC TABLE pre_social_cloud_bronze_db.SOCIAL_CLOUD_SCHEMA.RAW_POSTS_INTERACCIONES;
DESC TABLE pre_social_cloud_bronze_db.SOCIAL_CLOUD_SCHEMA.RAW_AUDIENCIA_DEMOGRAFICA;
DESC TABLE pre_social_cloud_bronze_db.SOCIAL_CLOUD_SCHEMA.RAW_PERFILES_EMPRESAS;

-- Descripción tablas dev
DESC TABLE dev_social_cloud_bronze_db.SOCIAL_CLOUD_SCHEMA.RAW_POSTS_INTERACCIONES;
DESC TABLE dev_social_cloud_bronze_db.SOCIAL_CLOUD_SCHEMA.RAW_AUDIENCIA_DEMOGRAFICA;
DESC TABLE dev_social_cloud_bronze_db.SOCIAL_CLOUD_SCHEMA.RAW_PERFILES_EMPRESAS;

-- Ejecutar tareas pro
EXECUTE TASK pro_social_cloud_bronze_db.SOCIAL_CLOUD_SCHEMA.sync_perfiles;

EXECUTE TASK pro_social_cloud_bronze_db.SOCIAL_CLOUD_SCHEMA.sync_posts;

EXECUTE TASK pro_social_cloud_bronze_db.SOCIAL_CLOUD_SCHEMA.sync_audiencia;

-- Ejecutar tareas pre
EXECUTE TASK pre_social_cloud_bronze_db.SOCIAL_CLOUD_SCHEMA.sync_perfiles;

EXECUTE TASK pre_social_cloud_bronze_db.SOCIAL_CLOUD_SCHEMA.sync_posts;

EXECUTE TASK pre_social_cloud_bronze_db.SOCIAL_CLOUD_SCHEMA.sync_audiencia;

-- Ejecutar tareas dev
EXECUTE TASK dev_social_cloud_bronze_db.SOCIAL_CLOUD_SCHEMA.sync_perfiles;

EXECUTE TASK dev_social_cloud_bronze_db.SOCIAL_CLOUD_SCHEMA.sync_posts;

EXECUTE TASK dev_social_cloud_bronze_db.SOCIAL_CLOUD_SCHEMA.sync_audiencia;

-- ============================================================
-- VERIFICACIÓN — comprobar que las tasks están activas
-- ============================================================
-- Comprobar tasks activas pro
SHOW TASKS IN SCHEMA pro_social_cloud_bronze_db.SOCIAL_CLOUD_SCHEMA;

-- Comprobar tasks activas pre
SHOW TASKS IN SCHEMA pre_social_cloud_bronze_db.SOCIAL_CLOUD_SCHEMA;

-- Comprobar tasks activas dev
SHOW TASKS IN SCHEMA dev_social_cloud_bronze_db.SOCIAL_CLOUD_SCHEMA;