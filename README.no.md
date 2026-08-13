# Home Assistant -- Systemair Modbus (SAVE + CD4)

**Norsk** · [Read in English](README.md)

[![HACS](https://img.shields.io/badge/HACS-Default-green.svg)](https://hacs.xyz/)

Dette er en Home Assistant-integrasjon for Systemair
ventilasjonsaggregater med støtte for både **SAVE** og **eldre
CD4-systemer (eksperimentell støtte)**. med støtte for **Modbus TCP**.

Integrasjonen gir strukturert overvåking og styring av
ventilasjonsanlegget i Home Assistant, med fokus på **korrekt
luftmengde, energieffektiv drift, og stabil håndtering av entiteter**.

⚠️ **Merk:**\
Dette er et **uoffisielt community-prosjekt** og er **ikke utviklet,
støttet eller vedlikeholdt av Systemair**.

⚠️ **Ansvarsfraskrivelse:**\
Denne integrasjonen leveres **som den er**, uten noen form for garanti.\
Du bruker den **på eget ansvar**. Forfatteren er ikke ansvarlig for
eventuelle skader, datatap eller feilfunksjon på ventilasjonsanlegget
ditt, utstyr eller eiendom.

Verifiser alltid endringer direkte på aggregatet og sørg for at systemet
er korrekt konfigurert.\
Ved usikkerhet, kontakt kvalifisert fagperson.

------------------------------------------------------------------------

## ✨ Funksjoner

### Ventilasjon og drift

-   Visning av faktisk drift basert på aggregatets konfigurasjon
-   Temperaturer (ute, tilluft, avtrekk, ettervarmer, osv.)
-   Viftehastigheter og driftsstatus
-   Varmegjenvinning
-   Filterstatus, gjenværende tid og alarmer
-   Korrekt filter-reset (skriver tidsstempel til aggregatet)
-   Konfigurerbar filterbytte-periode

### Energieffektivitet

-   **Eco-modus**
-   Behovsstyrt ventilasjon (der aggregatet støtter dette)
-   Borte- og feriemodus
-   Energieffektiv drift basert på belastning og aggregatets
    konfigurasjon

### Komfort

-   **Frikjøling** når betingelser er oppfylt
-   Party- og Boost-modus
-   Manuell viftehastighetskontroll (Lav / Normal / Høy)
-   Skrivebart tilluft-temperatursetpunkt
-   Beregnet avkasttemperatur (utledet fra systemverdier)

### Brukeropplevelse

-   Norsk og engelsk språkstøtte (følger Home Assistant-språk)
-   Konsistente og stabile entiteter
-   Innebygde **knapper** for vanlige handlinger
-   Robust håndtering av midlertidig tap av Modbus-tilkobling

------------------------------------------------------------------------

## 🚀 Nylige forbedringer

Nylige versjoner inkluderer:

-   Skrivebart tilluft-setpunkt direkte fra Home Assistant
-   Korrekt filter-reset ved bruk av native tidsstempel-register
-   Konfigurerbar filterbytte-periode
-   Beregnet avkasttemperatur-sensor
-   Profilbasert Modbus-håndtering for bedre stabilitet på SAVE Connect
    og lignende gatewayer

## Integrasjonen er under aktiv utvikling med sterkt fokus på korrekthet, stabilitet og transparent entitetsoppførsel.

## 📋 Systemair SAVE -- støttede modeller

**Luftmengde-estimat (m³/h)** er kun tilgjengelig for modeller som er
eksplisitt definert i koden og deler forventet Modbus-registerlayout.

**Forklaring:** - ✅ = Ja / tilgjengelig\
- ⚙️ = Støttet, men ikke testet\
- ❌ = Ikke tilgjengelig

------------------------------------------------------------------------

### 🧪 CD4 (legacy) -- eksperimentell støtte

Støtte for eldre Systemair-aggregater med **CD4-kontroller** er
inkludert i integrasjonen og er betydelig utvidet i v1.3.0-beta.2.

⚠️ **Viktig:**

-   CD4 bruker et annet Modbus-registerkart enn SAVE
-   Støtten er fortsatt **eksperimentell** mens testing på ekte
    aggregater pågår
-   Tilgjengelige funksjoner kan variere mellom eldre aggregatmodeller
    og konfigurasjoner

### Hva som fungerer per nå

-   Native Home Assistant **Fan-entitet** for viftestyring
    -   Stopp / Lav / Medium / Høy
    -   Stopp vises bare når aggregatet tillater manuell stopp
-   Native Home Assistant **Climate-entitet**
    -   Valg av ønsket tillufttemperatur i fem dokumenterte trinn
    -   Visning av aktuell tillufttemperatur
    -   Viftemodus direkte fra Climate-entiteten
    -   Oppvarmingsstatus basert på faktisk ettervarmerstatus
-   Temperaturer for tilluft, avtrekk, avkast, uteluft og
    overoppheting/frostbeskyttelse
-   Faktisk SF / EF RPM (turtall)
-   Status for rotor, ettervarmer, avriming og alarm
-   Filterstatus og grunnleggende systemverdier
-   Tekniske og rå CD4-verdier er tilgjengelige som diagnostikk der det
    er relevant

### Testing og tilbakemelding

Hvis du har et CD4-basert aggregat, er tilbakemeldingen din svært
verdifull.

Det er spesielt nyttig å få bekreftet:

-   Viftestyring: Stopp / Lav / Medium / Høy
-   Temperaturstyring i alle fem trinn
-   Aktuell og ønsket temperatur i Climate-entiteten
-   Oppvarmingsstatus
-   Mapping av temperaturfølere
-   Rotor-, ettervarmer-, avrimings- og alarmstatus
-   Generell stabilitet og Modbus-kommunikasjon

Rapporter gjerne erfaringer og eventuelle feil via GitHub Issues.

------------------------------------------------------------------------

## ✅ Testede aggregater / kompatibilitet

| Serie | Modell / Type | Modbus-støtte | Luftmengde-estimat (m³/h) | Testet |
|---|---|:---:|:---:|:---:|
| VSR | VSR 150/B | ✅ | ✅ | ❌ |
| VSR | VSR 200/B | ✅ | ✅ | ❌ |
| VSR | VSR 300 | ✅ | ✅ | ✅ |
| VSR | VSR 400 | ✅ | ✅ | ❌ |
| VSR | VSR 500 | ✅ | ✅ | ✅ |
| VSR | VSR 700 | ✅ | ✅ | ❌ |
| VTR | VTR 100/B | ✅ | ✅ | ❌ |
| VTR | VTR 150/B | ✅ | ✅ | ❌ |
| VTR | VTR 250/B | ✅ | ✅ | ✅ |
| VTR | VTR 275/B | ✅ | ✅ | ❌ |
| VTR | VTR 300 | ✅ | ✅ | ✅ |
| VTR | VTR 350/B | ✅ | ✅ | ⚙️ |
| VTR | VTR 500 | ✅ | ✅ | ✅ |
| VTR | VTR 700 | ✅ | ✅ | ❌ |
| VTC | VTC 200-1 | ✅ | ❌ | ❌ |
| VTC | VTC 300 | ✅ | ❌ | ❌ |
| VTC | VTC 500 | ✅ | ❌ | ❌ |
| VTC | VTC 700 | ✅ | ❌ | ❌ |
| VSC | VSC 100 | ✅ | ❌ | ❌ |
| VSC | VSC 200 | ✅ | ❌ | ❌ |
| VSC | VSC 300 | ✅ | ❌ | ❌ |

> ✅ **VTR 300:** Bekreftet fungerende av bruker (SAVE Touch, original Systemair Modbus-gateway, Modbus TCP).  
> ✅ **VTR 500:** Bekreftet fungerende av bruker (testet med Elfin EW11 Modbus TCP-gateway).  
> ✅ **VTR 250:** Bekreftet fungerende av bruker (testet med Elfin EW11 Modbus TCP-gateway).  
> ⚙️ **VTR 350/B:** Rapportert fungerende, men ikke fullt verifisert på alle funksjoner.  
> ✅ **VSR 300:** Bekreftet fungerende av bruker (testet med Elfin EW11 Modbus TCP-gateway).  
> ✅ **VSR 500 (CD4 / legacy):** Bekreftet fungerende av bruker – viftestyring, temperaturstyring og sensorverdier testet.

------------------------------------------------------------------------

## 🏗️ Forutsetninger -- valg av aggregat og luftmengde

Denne integrasjonen forutsetter at ventilasjonsanlegget er **riktig
prosjektert og korrekt dimensjonert**.

-   Aggregatet må velges basert på reelle luftmengdebehov (m³/h)
-   Luftmengder per sone må være riktig balansert og innregulert
-   Home Assistant erstatter **ikke** profesjonell
    ventilasjonsprosjektering

Integrasjonen bygger på aggregatets eksisterende konfigurasjon og gir: -
overvåking - styring - automasjon

Feil valg av aggregat eller luftmengdekonfigurasjon kan ikke kompenseres
med programvare.

------------------------------------------------------------------------

## 🖥️ Eksempel på Lovelace-kort

Bildet under viser et eksempel på et Lovelace-kort satt opp manuelt i
Home Assistant ved bruk av entiteter fra denne integrasjonen.

> Selve kortet er **ikke inkludert** og kan fritt tilpasses ditt
> oppsett.

![Ventilation Card](image/Ventilasjon%20kort.png)

------------------------------------------------------------------------

## 📦 Installasjon (HACS)

### Krav

-   Home Assistant **2024.6** eller nyere
-   Systemair SAVE aggregat med Modbus-tilgang
-   Modbus TCP
    -   Innebygd i aggregatet **eller**
    -   Via en ekstern gateway (f.eks. Elfin EW11)
-   HACS (Home Assistant Community Store)

------------------------------------------------------------------------

### Metode 1: Installer via HACS (anbefalt)

1.  Åpne **HACS**
2.  Gå til **Integrations**
3.  Søk etter **Systemair Modbus**
4.  Klikk **Download**
5.  Restart Home Assistant
6.  Gå til **Settings → Devices & Services → Add integration**
7.  Velg **Systemair Modbus** og skriv inn:
    -   IP-adresse
    -   Port (vanligvis `502`)
    -   Modbus slave ID

------------------------------------------------------------------------

### Metode 2: Installer som et custom repository (manuelt)

> Denne metoden er hovedsakelig ment for utvikling, testing eller tidlig
> tilgang til endringer.

1.  Åpne **HACS**
2.  Gå til **Integrations**
3.  Åpne menyen (tre prikker) → **Custom repositories**
4.  Legg til dette repositoryet som en **Integration**
5.  Installer **Systemair Modbus**
6.  Restart Home Assistant
7.  Gå til **Settings → Devices & Services → Add integration**
8.  Velg **Systemair Modbus** og skriv inn:
    -   IP-adresse
    -   Port (vanligvis `502`)
    -   Modbus slave ID

------------------------------------------------------------------------

## ℹ️ Begrensninger og tekniske notater

-   **Pressure Guard** er en intern sikkerhetsfunksjon i aggregatet\
    → eksponeres kun som status (kun lesing)
-   Ikke alle SAVE-modeller støtter full stopp via Modbus\
    → der full stopp ikke er tilgjengelig brukes lavest mulige
    viftehastighet
-   Tilgjengelige funksjoner avhenger av modell og konfigurasjon

## 🔧 Modbus-gatewayer og ytelsesprofiler

Forskjellige Modbus TCP-gatewayer oppfører seg svært forskjellig i
praksis.

Noen gatewayer (som **Systemair SAVE Connect**) er relativt
underdimensjonerte og kan: - slite med store Modbus-leserequests -
avvise enkelte funksjonskoder (FC04 for input-register) - bli ustabile
hvis de polles for aggressivt

Andre gatewayer (f.eks. **Elfin EW11** og lignende) kan vanligvis
håndtere: - større batch-lesinger - mer aggressiv polling - normal bruk
av Modbus-funksjonskoder

For å håndtere dette tilbyr integrasjonen en
**Gateway-profil**-innstilling:

-   **Generic gateway** (standard)\
    Optimalisert for eksterne gatewayer som EW11. Bruker større batcher
    og raskere polling.

-   **Systemair SAVE Connect (safe mode)**\
    Bruker svært små batcher, unngår problematiske funksjonskoder og
    prioriterer stabilitet over hastighet.

Du kan endre gateway-profil fra integrasjonens **Options** uten
reinstallasjon.

Hvis du opplever tilfeldige lese-feil, trege oppdateringer eller dropp i
tilkoblingen med SAVE Connect, velg **Systemair SAVE Connect (safe
mode)** og vurder å bruke et høyere scan interval (f.eks. 30--60
sekunder).

------------------------------------------------------------------------

### 🔍 Feilsøking av tilkobling

Under oppsett utfører integrasjonen en rask TCP-tilkoblingstest før den
forsøker Modbus-kommunikasjon.

Hvis du får **"Failed to connect"**: - Sørg for at IP-adressen er
korrekt og nås fra Home Assistant - Verifiser at port `502` (eller
konfigurert port) er åpen og nåbar fra Home Assistant - Sjekk at enheten
du kobler til faktisk er et Modbus TCP-endepunkt (ikke bare et
UI/nettverksmodul) - Hvis du bruker SAVE Connect og opplever
ustabilitet, prøv **Systemair SAVE Connect (safe mode)** og øk scan
interval (f.eks. 30--60s)

Hvis Modbus fungerer fra en PC men ikke fra Home Assistant, skyldes
problemet ofte: - Forskjeller i nettverk/VLAN/brannmur mellom PC og Home
Assistant - Gateway-begrensninger eller særegenheter i håndtering av
tilkoblinger

------------------------------------------------------------------------

## 🔌 Fysisk installasjon -- Elfin EW11 (Modbus RTU → TCP)

Denne seksjonen er kun relevant hvis aggregatet **ikke** har innebygd
Modbus TCP.

### ⚠️ ADVARSEL

Koble alltid fra strømmen til aggregatet før du åpner det.\
Ved usikkerhet, kontakt kvalifisert fagperson.

### 1. Modbus-tilkobling på Systemair SAVE

Finn terminalene for ekstern kommunikasjon på hovedkortet: - `A (+)` -
`B (–)` - `24V` - `GND`

![Eksempel på koblingsskjema (VTR-500)](image/koblingsskjemaVTR-500.png)

### 2. Koble til Elfin EW11

Koble ledningene i henhold til diagrammet under:

![EW11 koblingsskjema](image/koblings%20skjema%20EW11.png)

------------------------------------------------------------------------

### 3. Konfigurer Elfin EW11

1.  Koble til Wi-Fi-nettverket `EW1x_...` (åpent nettverk)
2.  Åpne webgrensesnittet: `http://10.10.100.254`
3.  Logg inn med:
    -   Brukernavn: `admin`
    -   Passord: `admin`
4.  Gå til **System Settings → WiFi Settings**
    -   Sett **WiFi Mode** til `STA`
    -   Koble til ditt lokale nettverk
5.  Restart enheten og sett en **statisk IP**
6.  Åpne **Serial Port Settings** og konfigurer som vist:

![Serial Port Settings EW11](image/serial%20port%20settings%20EW11.png)

7.  Åpne **Communication Settings** og legg til en Modbus-profil:

![Communication Settings
EW11](image/communication%20settings%20EW11.png)

8.  Under **Status** skal pakk tellere øke:

![EW11 communication status](image/kommunikasjon%20EW11.png)

⚠️ **Viktig informasjon om pakketellere**

Systemair-aggregatet bruker **Modbus RTU**, som er en
**forespørsel/svar-protokoll**.\
Det betyr at aggregatet **ikke sender data av seg selv**.

Kommunikasjon starter først når en **Modbus-klient aktivt spør etter
data** (for eksempel Home Assistant-integrasjonen).

Derfor kan **pakkecounteren på EW11-statussiden stå på 0** helt til Home
Assistant forsøker å koble til.

Hvis du ser **0 pakker**:

1.  Fullfør konfigurasjonen av EW11
2.  Legg til integrasjonen i Home Assistant
3.  Start integrasjonen
4.  Sjekk deretter EW11-statussiden på nytt

Når Home Assistant begynner å lese Modbus-registere, vil
**pakkecounteren begynne å øke**.

Hvis den fortsatt står på 0, kontroller:

-   RS485-koblingene (`A` / `B`)
-   Baudrate
-   Parity og stop-bits
-   Modbus slave-ID

Når kommunikasjonen er bekreftet kan IP-adressen brukes direkte i Home
Assistant.

------------------------------------------------------------------------

## 🙏 Takk / bidragsytere

Guiden for Elfin EW11 (Modbus RTU → TCP) er basert på arbeid publisert
på [domotics.no](https://www.domotics.no/), skrevet av **Mads
Nedrehagen**.

Spesiell takk til [**Ztaeyn**](https://github.com/Ztaeyn) for bidrag til
forbedret håndtering av climate state (`hvac_action`) basert på
TRIAC-register.

Spesiell takk til [**larstobi**](https://github.com/larstobi) for bidrag
og testing av CD4-støtten, inkludert registerinformasjon og arbeidet med
viftestyring som bidro til videreutviklingen av den nye
CD4-implementasjonen.

En AI-assistent har blitt brukt til støtte i feilsøking, refaktorering
og dokumentasjonsforbedringer under utviklingen.

Denne integrasjonen er **uavhengig utviklet** som en moderne Home
Assistant-integrasjon.

------------------------------------------------------------------------

## 📝 Lisens

MIT -- se `LICENSE`

