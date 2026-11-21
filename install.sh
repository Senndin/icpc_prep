#!/usr/bin/env bash
# Встановлення ICPC Prep у Linux / macOS
set -e
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
echo "Встановлення завершено. Запуск: ./run.sh"
