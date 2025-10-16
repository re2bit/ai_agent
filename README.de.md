Lokale KI auf dem Mac Pro 5,1 — mit einem Retro-Macintosh SE/30 als Frontend

Deutsch (English version: see README.md)

Einleitung
Dieses Projekt dreht sich ganz bewusst darum, eine lokale KI-Lösung vor Ort laufen zu lassen, direkt auf dem Mac Pro 5.1. Es geht also nicht darum, auf riesige Cloud-Infrastrukturen oder eine ständige Internetverbindung angewiesen zu sein. Stattdessen läuft alles direkt vor Ort – quasi im eigenen Showroom – auf dieser Retro-Hardware aus 2009. Damit zeige ich, dass man die Kontrolle über die eigenen Daten behält und keine externen Rechenzentren nötig sind. Alles läuft lokal, ohne Netz und doppelten Boden, und auf einer Hardware, die man heute fast schon als Retro bezeichnen könnte.

Motivation
Wer kennt ihn nicht, diesen charmanten Moment aus Star Trek IV: Zurück in die Gegenwart, in dem Scotty versucht, mit einem Computer zu sprechen – und nur eine Maus bekommt? Genau das hat mich inspiriert.

Ich möchte meinen Macintosh SE/30 aus den 80ern in genau so eine Situation versetzen, sodass er tatsächlich auf ein „Hallo Computer“ antworten kann – natürlich mit einem kleinen Trick im Hintergrund. Der Clou dabei: Die Intelligenz steckt nicht im SE/30 selbst, sondern wird über eine clevere Verbindung mit einem Mac Pro 5.1 bereitgestellt, der mit einer modernen lokalen AI-Architektur läuft.

Das Ganze ist nicht nur ein persönliches Spaßprojekt, sondern bewusst offen für andere Retro-Gaming-Fans und Entwicklerinnen, die Lust haben, dieses charmante Crossover zwischen Vergangenheit und Zukunft mitzudenken und mitzugestalten.

Status Quo
Hardware: Macintosh SE/30
- Der SE/30 läuft grundsätzlich und wurde in ein MacEffects Clear Case transplantiert – einem transparenten Acrylgehäuse, das das Innenleben sichtbar macht.
- Ein vollständiger Recap (Tausch der alten Kondensatoren) steht noch aus.
- Das System nutzt eine BlueSCSI-Erweiterung, um SD-Karten als Massenspeicher einzubinden.
- Es ist eine drahtlose Ethernet-Schnittstelle geplant bzw. teilweise integriert, um Netzwerkkonnektivität herzustellen.
- Das Diskettenlaufwerk ist noch nicht ganz einsatzbereit, da durch den Umbau die Spaltmaße leicht abweichen – hier steht noch Feintuning an.
- Ein Betriebssystem ist aktuell noch nicht installiert, das wird aber Teil des nächsten Schritts sein.

Hardware: Mac Pro 5.1 (2009)
- Der Mac Pro ist funktionstüchtig und wurde mit einer geflashten Radeon RX 6800 ausgestattet, um maximale Kompatibilität bei gleichzeitig hoher Rechenleistung zu erreichen.
- Ursprünglich als Gaming-Rechner genutzt, wird der Mac Pro nun auf eine neue Rolle als lokale KI-Plattform vorbereitet.

Software-Stack
- Basis bildet ein minimalistisches Setup mit NixOS, in dem alle Dienste containerisiert laufen.
- Verwendete Tools:
  - FastAPI als Backend
  - LangGraph zur Orchestrierung von KI-Agenten
  - Open WebUI als optionales Interface
  - Erste Prototypen eines RAG-Agents (Retrieval-Augmented Generation)
  - Eine einfache Toolchain, die Anleitungen aus dem Internet extrahiert – auch ohne vorheriges Indexing
  - Geplant: Anbindung einer lokalen Datenbank mit kontextrelevantem Wissen

Projektstruktur (Auszug)
- a — Projekthilfsskript (siehe Befehle unten)
- compose.yml, compose.override.yml — Docker Compose Setup
- src/agent-server — FastAPI Backend, Agents, Graphen, Tools, Prompts
- libs/open-webui — Open WebUI (optional)
- docker/*, config/* — Container-Builds und Service-Konfigurationen
- data/, test/ — Daten und Tests

Voraussetzungen
- Docker und Docker Compose v2
- macOS: GNU sed (gsed) wird für einige Toggles benötigt
  - Installation via Homebrew: brew install gnu-sed
- Optional: jq, yq (falls yq fehlt, wird eine Docker-Variante verwendet)

Schnellstart
1) Lokale Konfiguration initialisieren
   - ./a i
   - Erstellt .env und compose.override.yml, falls nicht vorhanden.
2) Services starten
   - ./a s            # startet alle in compose definierten Services
3) UI öffnen (optional)
   - ./a o            # öffnet http://localhost:8080 im Standardbrowser (macOS)
4) Logs prüfen
   - ./a l            # alle Logs
   - ./a lf as        # folgt den Logs des agent-server

Häufige Befehle (./a)
- ./a i                      Initialisiert lokale Umgebungsdateien
- ./a s [SERVICE]            Startet einen bestimmten Service oder alle
- ./a d [SERVICE]            Stoppt einen bestimmten Service oder alle
- ./a b SERVICE              Baut einen Service
- ./a bma SERVICE            Multi-Arch Build (nur für Base Images; siehe Label)
- ./a e SERVICE CMD...       Führt einen Befehl im Container aus
- ./a l [SERVICE]            Zeigt Logs (inkl. init-Logs, wenn vorhanden)
- ./a lf [SERVICE]           Folgt den Logs
- ./a m [alembic args]       Führt Alembic im agent-server aus (Standard: upgrade head)
- ./a w [options] [SERVICE]  Compose watch für Live-Rebuilds
- ./a td                     Schaltet einen Debug-Schalter in .env um
- ./a ti                     Schaltet Init-Container in compose.override.yml um
- ./a dpsw                   Beobachtet Compose-Service-Status
- ./a rc                     Startet alle Container neu (down + up -d)
- ./a rd                     Setzt Services mit Label resetableDb zurück
- ./a o                      Öffnet die Standard-UI-URL

Hinweise
- Beim ersten Start werden Images gebaut/gezogen; das kann dauern.
- Ziel ist der vollständig Offline-Betrieb, sobald Images und Modelle lokal verfügbar sind. Einige optionale Tools (z.B. Websuche) benötigen Konnektivität.

Roadmap
- SE/30-Netzwerkbridge und OS-Setup finalisieren (Retro-Frontend aktivieren)
- RAG-Pipeline stabilisieren, lokale Wissensbasis/Vector-DB anbinden
- Toolchain für Anleitungs-Extraktion ohne Pre-Indexing ausbauen
- Einfache Modellverwaltung für den Offline-Betrieb bereitstellen

Mitmachen
Das Projekt ist bewusst offen für Retro-Fans und Entwickler:innen. Wenn dich der „Hallo, Computer“-Moment aus Star Trek genauso begeistert, mach gerne mit!

Lizenz
Noch offen. Bis eine Lizenz ergänzt wird, gelten alle Rechte als vorbehalten.

Kontakt
Fragen, Ideen oder Hardware-Setups zum Testen? Eröffne gern ein Issue oder sende einen PR.
