-- Crear un warehouse
create warehouse if not exists WH_SOCIAL_CLOUD with
warehouse_size = XSMALL
max_cluster_count = 2
min_cluster_count = 1
auto_suspend = 60 -- Esto son en segundos, por defecto viene como 600 que son 10 minutos
auto_resume = true
comment = 'Warehouse para el proyecto';

-- Crear un rol
create role if not exists SOCIAL_CLOUD
comment = 'Rol para el proyecto';

-- Dar privilegios al rol anteriormente creado
grant usage on warehouse WH_SOCIAL_CLOUD to role SOCIAL_CLOUD; -- Permiso para usar el warehouse

GRANT CREATE DATABASE ON ACCOUNT TO ROLE SOCIAL_CLOUD; -- Permiso para base de datos existentes
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE WH_SOCIAL_CLOUD;
SET alumno = 'Juan Manuel';
SET env = 'DEV';--Crear 3 bases de datos
CREATE DATABASE IF NOT EXISTS SOCIAL_CLOUD_BRONZE_DB;
CREATE DATABASE IF NOT EXISTS SOCIAL_CLOUD_SILVER_DB;
CREATE DATABASE IF NOT EXISTS SOCIAL_CLOUD_GOLD_DB;


GRANT EXECUTE TASK ON ACCOUNT TO ROLE social_cloud;

GRANT CREATE SCHEMA ON DATABASE SOCIAL_CLOUD_GOLD_DB TO ROLE SOCIAL_CLOUD; -- Permiso para crear esquemas en la base de datos

GRANT CREATE TABLE ON ALL SCHEMAS IN DATABASE SOCIAL_CLOUD_GOLD_DB TO ROLE SOCIAL_CLOUD; -- Permiso para crear tablas en todos los esquemas de una base de datos
GRANT CREATE VIEW ON ALL SCHEMAS IN DATABASE SOCIAL_CLOUD_GOLD_DB TO ROLE SOCIAL_CLOUD; -- Permiso para crear vistas en todos los esquemas de una base de datos

GRANT CREATE TABLE ON FUTURE SCHEMAS IN DATABASE SOCIAL_CLOUD_GOLD_DB TO ROLE SOCIAL_CLOUD; -- Permiso para crear tablas en futuros esquemas en un base de datos
GRANT CREATE VIEW ON FUTURE SCHEMAS IN DATABASE SOCIAL_CLOUD_GOLD_DB TO ROLE SOCIAL_CLOUD; -- Permiso para crear vistas en futuros esquemas en una base de datos

GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN DATABASE SOCIAL_CLOUD_GOLD_DB TO ROLE SOCIAL_CLOUD; -- Permisos para tablas existentes que se creen en un futuro sobre una base de datos

GRANT SELECT, INSERT, UPDATE ON FUTURE TABLES IN DATABASE SOCIAL_CLOUD_GOLD_DB TO ROLE SOCIAL_CLOUD; -- Permisos para tablas que se creen en un futuro sobre una base de datos

USE ROLE SECURITYADMIN;

GRANT ROLE SOCIAL_CLOUD TO USER juanmanuelgarmoy; -- Asigno el rol a tu usuario
