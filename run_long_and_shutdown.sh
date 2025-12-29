#!/usr/bin/env bash

set -e  # corta ante cualquier error
set -o pipefail

echo "==== Inicio ejecución LONG ===="
date

# Activar entorno virtual
source .venv/bin/activate

# Ejecutar generator.entrypoint 10 veces
for i in {1..10}
do
  echo "---- Ejecución LONG $i ----"
  .venv/bin/python -m generator.entrypoint 1 long
done

echo "==== Ejecución scheduler ===="
date

# Ejecutar scheduler (log en archivo)
mkdir -p logs
.venv/bin/python -m generator.publications.run_scheduler >> logs/cron_agendamiento.log 2>&1

echo "==== Proceso finalizado correctamente ===="
date

# Apagar el PC
echo "Apagando el sistema..."
sudo shutdown -h now
