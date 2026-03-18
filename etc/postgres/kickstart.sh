#!/bin/bash

set -e

psql -v ON_ERROR_STOP=1 --username "postgres" <<-EOSQL
    CREATE ROLE "libretime" WITH LOGIN PASSWORD '$POSTGRES_PASSWORD';
    CREATE DATABASE "libretime"
        TEMPLATE template0
        ENCODING 'UTF8'
        OWNER "libretime";
    GRANT ALL PRIVILEGES ON DATABASE "libretime" TO "libretime";
EOSQL
