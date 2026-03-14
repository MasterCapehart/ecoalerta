#!/usr/bin/env bash
set -euo pipefail

# Ejecuta tests contra PostgreSQL (Azure u otro host remoto) desde entorno local.
# Seguridad: exige una DB de pruebas para evitar dañar datos de trabajo.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [[ -x "venv/bin/python" ]]; then
  PYTHON_BIN="venv/bin/python"
elif [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN=".venv/bin/python"
else
  PYTHON_BIN="python3"
fi

required_vars=(
  "DB_HOST"
  "DB_PORT"
  "DB_NAME"
  "DB_USER"
  "DB_PASSWORD"
)

missing=()
for var in "${required_vars[@]}"; do
  if [[ -z "${!var:-}" ]]; then
    missing+=("$var")
  fi
done

if [[ "${#missing[@]}" -gt 0 ]]; then
  echo "Faltan variables de entorno requeridas: ${missing[*]}"
  echo "Define DB_HOST DB_PORT DB_NAME DB_USER DB_PASSWORD antes de ejecutar."
  exit 1
fi

db_name_lower="$(echo "${DB_NAME}" | tr '[:upper:]' '[:lower:]')"
if [[ "$db_name_lower" != *test* ]]; then
  echo "DB_NAME='${DB_NAME}' no parece una base de pruebas."
  echo "Por seguridad, usa una base cuyo nombre contenga 'test' (por ejemplo: ecoalerta_test)."
  exit 1
fi

export USE_SQLITE_LOCAL=0
export DEBUG="${DEBUG:-True}"
export DB_SSLMODE="${DB_SSLMODE:-require}"

DEFAULT_TESTS=(
  "reportes.tests.test_views"
  "reportes.tests.test_serializers"
)

if [[ "$#" -gt 0 ]]; then
  TEST_LABELS=("$@")
else
  TEST_LABELS=("${DEFAULT_TESTS[@]}")
fi

echo "Ejecutando tests con:"
echo "  Python: ${PYTHON_BIN}"
echo "  DB_HOST: ${DB_HOST}"
echo "  DB_PORT: ${DB_PORT}"
echo "  DB_NAME: ${DB_NAME}"
echo "  DB_SSLMODE: ${DB_SSLMODE}"
echo "  Labels: ${TEST_LABELS[*]}"

"${PYTHON_BIN}" manage.py test "${TEST_LABELS[@]}" --verbosity 2
