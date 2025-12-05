# Junie Guidelines

Diese Richtlinien definieren klar, wie in diesem Projekt Tests auszuführen sind und welche Erwartungen dabei gelten. Bitte halte dich strikt daran.

## Tests ausführen (einziger erlaubter Weg)

- Immer den Wrapper verwenden: `./a ut`
- Niemals direkt `pytest` (oder Varianten) auf dem Host ausführen.

### Beispiele

- Alle Tests ausführen:
  ```bash
  ./a ut
  ```
- Bestimmtes Verzeichnis testen:
  ```bash
  ./a ut src/agent_server/tests
  ```
- Bestimmte Datei testen:
  ```bash
  ./a ut src/agent_server/tests/adapters/test_database.py
  ```
- Einzelnen Test laufen lassen (mit -q für ruhige Ausgabe):
  ```bash
  ./a ut src/agent_server/tests/adapters/test_database.py::TestStateModelMapper::test_simple_map_state_to_model -q
  ```

## Hintergrund / Ablauf

- Tests laufen innerhalb eines Docker-Containers (Service: `as`).
- Das Skript `a` entscheidet automatisch:
  - Läuft der Service bereits → es wird `docker compose exec` genutzt.
  - Läuft der Service noch nicht → es wird `docker compose run` genutzt.
- Wenn die Datei `.expectServiceRunning` im Projektroot vorhanden ist, wird vorausgesetzt, dass der Service läuft (überspringt die Laufzeitprüfung und nutzt direkt `exec`).

## Erwartungen & Regeln

- `pytest` niemals direkt aufrufen. Immer über `./a ut` gehen.
- Sorge dafür, dass Docker lokal funktionsfähig ist; die Tests werden im Container ausgeführt.
- Der Container-Name für die Tests ist `as` (agent-server).

## Verbotene Befehle

- `pytest`
- `python -m pytest`

## CI-Hinweis

- In CI-Pipelines ebenfalls `./a ut` verwenden oder äquivalente Container-Aufrufe, die das gleiche Verhalten sicherstellen.

## Fehlerbehebung (Quick Tips)

- „Docker may not be working correctly“: Stelle sicher, dass Docker läuft und wiederhole den Befehl.
- Tests sehr langsam beim ersten Start: Der erste `run` lädt Images/Abhängigkeiten – nach dem Start des Services beschleunigt `exec` Folgeläufe.
- Service gezielt starten, falls gewünscht:
  ```bash
  ./a s as
  ```

Stand: 2025-12-03 19:50