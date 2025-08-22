set -e
set -x

cd "$(dirname "$0")/.."   

python -m app.backend_pre_start

alembic upgrade head

python -m app.initial_data
