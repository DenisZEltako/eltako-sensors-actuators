# ELTAKO Sensors & Actuators für Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-3498db.svg)](https://hacs.xyz/)
[![Version](https://img.shields.io/badge/Version-0.1.146-3498db.svg)](https://github.com/DenisZEltako/eltako-sensors-actuators/releases)
[![Lizenz: MIT](https://img.shields.io/badge/Lizenz-MIT-3498db.svg)](LICENSE)

Home-Assistant-Integration für unterstützte ELTAKO EnOcean-Sensoren und -Aktoren. 
Sie verbindet kompatible Gateways lokal über eine serielle oder TCP-Verbindung und legt die erkannten Geräte als Entitäten
in Home Assistant an. Eine Cloud-Verbindung ist dafür nicht erforderlich.

> [!IMPORTANT]
> Dieses Projekt ist eine inoffizielle Community-Integration. Es ist kein
> offizielles Produkt der ELTAKO GmbH und wird nicht offiziell von der ELTAKO
> GmbH unterstützt.

## Funktionen

- Einrichtung über die Home-Assistant-Benutzeroberfläche
- Lokale Kommunikation über serielle oder TCP-Gateways
- Import einer mit EEDTOY erzeugten YAML-Konfiguration
- Unterstützung mehrerer Gateway-Blöcke innerhalb einer Konfiguration
- Home-Assistant-Entitäten für Sensoren, Binärsensoren, Taster, Schalter,
  Leuchten, Beschattung und Klima
- Aktualisierung eingehender Telegramme über `local_push`
- Deutsche und englische Übersetzungen
- Installation und Updates über HACS

## Unterstützte Gateways

- ELTAKO FAM14
- ELTAKO FAM-USB
- ELTAKO FGW14-USB
- Weitere von der Integration unterstützte serielle oder TCP-Verbindungen

## Unterstützte Geräte

Unterstützt werden ausgewählte Sensoren und Aktoren der ELTAKO-Baureihen 14,
61, 62 und 71. Die tatsächlich angelegten Entitäten richten sich nach den
Gerätedefinitionen des EEDTOY-YAML-Exports.

Dazu gehören unter anderem:

- Schalt-, Dimm-, Beschattungs- und RGBW-Aktoren
- Temperatur-, Feuchte-, Luftgüte- und Bewegungssensoren
- Fenster- und Türkontakte sowie EnOcean-Taster
- Heizungs- und Klimageräte einschließlich FHK- und FKS-SV-Profilen
- Stromzähler mit unterstützten EnOcean Equipment Profiles (EEPs)

## EEDTOY

Die Geräte- und Gateway-Konfiguration für diese Integration wird mit
[EEDTOY](https://github.com/DenisZEltako/eedtoy) erstellt. EEDTOY erzeugt den
YAML-Export, der anschließend über die Optionen der Integration in Home
Assistant importiert wird.

Das EEDTOY-Repository wird separat veröffentlicht. Bis zur Veröffentlichung
kann der Link noch auf eine nicht vorhandene GitHub-Seite führen.

## Installation mit HACS

HACS muss bereits in Home Assistant installiert sein. Mit dem folgenden Button
kann das Repository direkt in HACS geöffnet und als benutzerdefiniertes
Repository hinzugefügt werden:

[![Home Assistant öffnen und dieses Repository in HACS anzeigen](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=DenisZEltako&repository=eltako-sensors-actuators&category=integration)

Anschließend:

1. Das Repository in HACS hinzufügen.
2. **ELTAKO Sensors & Actuators** öffnen und **Herunterladen** auswählen.
3. Home Assistant neu starten.
4. **Einstellungen → Geräte & Dienste → Integration hinzufügen** öffnen.
5. Nach **ELTAKO Sensors & Actuators** suchen und die Einrichtung starten.

### Manuell als benutzerdefiniertes Repository hinzufügen

Falls der Button nicht verwendet werden kann:

1. In Home Assistant **HACS** öffnen.
2. Oben rechts das Menü öffnen und **Benutzerdefinierte Repositories** wählen.
3. Diese Repository-Adresse eintragen:

   ```text
   https://github.com/DenisZEltako/eltako-sensors-actuators
   ```

4. Als Kategorie **Integration** auswählen und das Repository hinzufügen.
5. Die Integration herunterladen und Home Assistant neu starten.

## Manuelle Installation ohne HACS

Den Ordner

```text
custom_components/eltako_sensors_actuators
```

nach

```text
/config/custom_components/eltako_sensors_actuators
```

kopieren und Home Assistant anschließend neu starten.

## Konfiguration

1. Unter **Einstellungen → Geräte & Dienste** die Integration hinzufügen.
2. Das Gateway sowie die serielle oder Netzwerkverbindung auswählen.
3. Die Optionen der Integration öffnen.
4. Die mit [EEDTOY](https://github.com/DenisZEltako/eedtoy) erzeugte
   YAML-Konfiguration einfügen oder importieren.
5. Bei mehreren Gateway-Blöcken den Hinweisen im Einrichtungsdialog folgen.

Unter Home Assistant OS und Linux sollte möglichst ein stabiler Gerätepfad wie
`/dev/serial/by-id/...` verwendet werden. Bezeichnungen wie `/dev/ttyUSB0`
können sich nach einem Neustart oder erneutem Anschließen des USB-Geräts ändern.

## Aktuelle Version

### 0.1.146

- Für FLGTF wird eine gemeinsame Entität **Letztes Telegramm** pro physischem
  Gerät verwendet.
- Der Zeitstempel wird durch die Profile A5-09-0C für TVOC und A5-04-02 für
  Temperatur und Luftfeuchtigkeit aktualisiert.
- Bereits vorhandene Diagnoseentitäten für EnOcean-IDs bleiben erhalten.
- Veraltete doppelte FLGTF-Zeitstempel werden beim Start aus der Entity Registry
  entfernt.
- Die Temperaturunterstützung für FBHT55ESB ist enthalten.
- Im Dialog für den EEDTOY-YAML-Import wird keine Versionsnummer mehr im Titel
  angezeigt.

## Fehler melden

Fehler und Verbesserungsvorschläge können über die
[GitHub-Issues](https://github.com/DenisZEltako/eltako-sensors-actuators/issues)
gemeldet werden. Hilfreich sind dabei:

- Home-Assistant-Version
- Version dieser Integration
- Gateway-Modell
- Betroffenes EEP und Gerätemodell
- Bereinigter YAML-Geräteabschnitt
- Relevante Einträge aus dem Home-Assistant-Protokoll

Bitte keine Passwörter, Zugangstoken, privaten Netzwerkdaten oder sonstigen
persönlichen Informationen veröffentlichen.

## Rechtlicher Hinweis

Dieses Projekt ist eine privat entwickelte, inoffizielle Community-Integration
für Home Assistant. Es ist kein offizielles Produkt der ELTAKO GmbH und wird
nicht offiziell von der ELTAKO GmbH unterstützt.

ELTAKO und die genannten Produktbezeichnungen sind Marken der ELTAKO GmbH. Name
und Logo werden ausschließlich zur Kennzeichnung kompatibler Produkte
verwendet. Daraus ergibt sich keine offizielle Unterstützung oder Empfehlung.

## Lizenz und Abhängigkeiten

Der Quellcode dieser Integration steht unter der [MIT-Lizenz](LICENSE).
Hinweise zu verwendeten Drittanbieter-Abhängigkeiten befinden sich in
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
