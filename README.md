# ad-boilerplate

[![check-services](https://github.com/C4T-BuT-S4D/ad-boilerplate/actions/workflows/check-services.yml/badge.svg?branch=master&event=push)](https://github.com/C4T-BuT-S4D/ad-boilerplate/actions/workflows/check-services.yml)

Development workflow:

1) Create branch named `$SERVICE`.
2) Write your code in `services/$SERVICE`, `checkers/$SERVICE`, `sploits/$SERVICE` and `internal/$SERVICE` (if needed).
3) Validate your service with `SERVICE=$SERVICE ./check.py validate`.
4) Up your service with `SERVICE=$SERVICE ./check.py up`.
5) Check your service with `SERVICE=$SERVICE RUNS=200 ./check.py check`.
6) Down your service with `SERVICE=$SERVICE ./check.py down`.
7) Add your service to `.github/workflows/check-services.yml`, line 38.
8) Push your code and create pull request to master branch.

Don't forget to:
1) Add your checker requirements to `checkers/requirements.txt`.
2) Use `dedcleaner` container to delete old files if needed. Example can be found in `services/example/docker-compose.yml`.
3) Add info about your checker to `Checker` class. Example can be found in `checkers/example/checker.py`, line 11.
