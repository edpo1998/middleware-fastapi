#! /usr/bin/env bash
set -e
set -x

# 1) Ponte siempre en la raíz del proyecto, para que "app" sea tu paquete top-level
cd "$(dirname "$0")/.."   

# 2) Inicializa la DB (el módulo vive en app/tests)
python -m app.backend_pre_start

# 3) Aplica migraciones (alembic.ini en la raíz o ajusta -c path)
alembic upgrade head

# 4) Crea datos iniciales
python -m app.seed_local
