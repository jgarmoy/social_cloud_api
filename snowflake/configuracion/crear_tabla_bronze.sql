use warehouse wh_social_cloud;
use role social_cloud;
use database social_cloud_bronze_db;

create or replace table perfiles_empresas_raw (
    empresa_id varchar(256),
    empresa_nombre varchar (256),
    empresa_categoria varchar(256),
    empresa_pais varchar(256),
    empresa_web varchar (256),
    empresa_email varchar(256),
    perfil_id varchar(256),
    username varchar(256),
    plataforma varchar(256),
    fecha_creacion_perfil varchar(256),
    activo varchar(256),
    semana_snapshot varchar(256),
    seguidores varchar(256),
    alcance_semanal varchar(256),
    impresiones_semanales varchar(256),
    visitas_perfil varchar(256),
    created_at varchar(256),
    updated_at varchar(256)
);

create or replace table audiencia_raw (
    tk_handle varchar(256),
    tk_platform varchar(256),
    snapshot_date varchar(256),
    gender_segment varchar(256),
    age_segment varchar(256),
    country varchar(256),
    audience_share_pct varchar(256),
    seg_followers varchar(256),
    ig_username varchar(256),
    ig_platform varchar(256),
    report_date varchar(256),
    audience_gender varchar(256),
    audience_age varchar(256),
    audience_country varchar(256),
    pct_audience varchar(256),
    follower_count_seg varchar(256),
    yt_handle varchar(256),
    network varchar(256),
    period varchar(256),
    sexo varchar(256),
    edad varchar(256),
    pais_audiencia varchar(256),
    porcentaje varchar(256),
    n_seguidores_seg varchar(256),
    empresa_id varchar(256),
    perfil_id varchar(256),
    created_at varchar(256),
    updated_at varchar(256)
);

create or replace table post_raw (
    post_id varchar(256),
    raw_json_id varchar(256),
    username varchar(256),
    empresa_id varchar(256),
    plataforma varchar(256),
    fecha_publicacion varchar(256),
    tipo_contenido varchar(256),
    descripcion varchar(256),
    patrocinado varchar(256),
    es_campana_bf varchar(256),
    hashtags varchar(256),
    visualizaciones varchar(256),
    alcance varchar(256),
    impresiones varchar(256),
    tipo_interaccion varchar(256),
    cantidad_interaccion varchar(256),
    engament_total varchar(256),
    source_api varchar(256),
    created_at varchar(256), 
    updated_at varchar(256)
);





