# 🌬️ Systemair Modbus v2.0.0 — Én integrasjon. To protokoller. 🚀

**Norsk** · [Read in English](README.md)

[![HACS](https://img.shields.io/badge/HACS-Default-green.svg)](https://hacs.xyz/) ![Versjon](https://img.shields.io/badge/Versjon-2.0.0-blue) ![Modbus TCP](https://img.shields.io/badge/Modbus-TCP%2FIP-0A7EA4) ![Modbus RTU](https://img.shields.io/badge/Modbus-RTU-0A7EA4)

### 🎉 En milepæl for Systemair Modbus

**Modbus TCP/IP + Modbus RTU — samlet i én Home Assistant-integrasjon.**

Versjon **2.0.0** utvider integrasjonen med seriell Modbus RTU-kommunikasjon i tillegg til eksisterende TCP/IP, samtidig som støtten for **Systemair SAVE** og **eldre CD4-kontrollere (eksperimentell støtte)** videreføres.

- 🌐 **Modbus TCP/IP:** Tilkobling via Ethernet-/Wi-Fi-gateway, for eksempel Elfin EW11 eller en kompatibel Systemair-gateway.
- 🔌 **Modbus RTU:** Tilkobling via ESPHome-seriegrensesnitt, inkludert Home Assistant Connect AUX-2 med USB–RS485-adapter og ESP32-baserte RS485-enheter med kompatibel ESPHome seriell proxy.
- 🏠 **Én integrasjon:** De samme kjente Home Assistant-entitetene og styringsmulighetene, der aggregatet støtter funksjonene.
- 🛠️ **Bedre dokumentasjon:** Egne veiledninger for [TCP/IP](docs/modbus-tcp.no.md) og [RTU](docs/modbus-rtu.no.md).

Integrasjonen gir overvåking og styring av Systemair ventilasjonsaggregater med vekt på stabil kommunikasjon, energieffektiv drift og forutsigbare entiteter. Funksjoner varierer mellom modeller og konfigurasjoner; se kompatibilitetstabellen nedenfor for fysisk verifiserte tilkoblinger.

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

-   Justerbar varighet for peismodus (SAVE, 1–60 minutter)

### Brukeropplevelse

-   Norsk og engelsk språkstøtte (følger Home Assistant-språk)
-   Konsistente og stabile entiteter
-   Innebygde **knapper** for vanlige handlinger
-   Robust håndtering av midlertidig tap av Modbus-tilkobling

------------------------------------------------------------------------

## Nytt i v2.0.0

- Automatisk modellidentifikasjon for SAVE og CD4, med modellnavn i enhetsinformasjonen når tilgjengelig.
- Lesbar varmetype for CD4.
- Justerbar varighet for peismodus (SAVE, 1–60 minutter).
- Eco-varmeoffset (SAVE): 0–10 °C der registeret støttes.
- Slave-ID 1–247 for TCP og RTU; standardverdi 1.

## 🚀 Tidligere forbedringer (v1.3.0)

v1.3.0 inneholder betydelige forbedringer for både SAVE og eldre CD4-systemer:

- Forbedret status og entiteter for SAVE ettervarme / varmeeffekt
- Forbedret visning og diagnostikk for aktivert / aktiv ECO
- Utvidet styring og diagnostikk for frikjøling
- Nye diagnostiske entiteter for Auto / Demand Control
- Standard pollingintervall er endret fra 10 til 30 sekunder for å redusere
  Modbus-belastningen og potensielt forbedre stabiliteten til det fysiske touchdisplayet
- Betydelig utvidet støtte for eldre CD4-systemer
- Native CD4 Fan-entitet med sikker håndtering av manuell viftestopp
- Oppdatert CD4 Climate-entitet med automatisk temperaturområde basert på varmeelementkonfigurasjon
  - 12–22 °C med konfigurert varmeelement
  - 15–19 °C uten konfigurert varmeelement
- Støtte for CD4 Manual summer / temperatur AV
- Utvidet CD4-diagnostikk og registerstøtte

Integrasjonen er under aktiv utvikling med sterkt fokus på korrekthet,
stabilitet og transparent entitetsoppførsel.

---

## 📋 Støttede modeller og teststatus

Se kompatibilitetstabellen nedenfor for SAVE- og CD4-modeller, TCP/IP, RTU og luftmengde-estimat.

### 🧪 CD4 (legacy) – eksperimentell støtte

Støtte for eldre Systemair-aggregater med **CD4-kontroller** er inkludert
i integrasjonen og har blitt betydelig utvidet i v1.3.0.

⚠️ **Viktig:**

- CD4 bruker et annet Modbus-registerkart enn SAVE
- Støtten er fortsatt **eksperimentell** mens testing på fysiske aggregater fortsetter
- Tilgjengelige funksjoner kan variere mellom eldre aggregatmodeller og konfigurasjoner

### Hva som fungerer per nå

- Native Home Assistant **Fan-entitet** for viftestyring
  - Av / Lav / Medium / Høy
  - Av er bare tilgjengelig dersom aggregatet tillater manuell viftestopp
- Native Home Assistant **Climate-entitet**
  - Temperaturstyring med automatisk valgt område:
    - 12–22 °C med konfigurert varmeelement
    - 15–19 °C uten konfigurert varmeelement
  - Av / Manual summer
  - Aktuell tillufttemperatur
  - Viftemodus kan styres direkte fra Climate-entiteten
  - Varmestatus basert på faktisk status for ettervarmer
- Tilluft-, avtrekk-, avkast-, ute- og overopphetings-/frostbeskyttelsestemperaturer
- Faktiske SF / EF RPM-verdier
- Status for rotor, ettervarmer, avriming og alarm
- Filterstatus og grunnleggende systemverdier
- Tekniske og rå CD4-verdier er tilgjengelige som diagnostiske entiteter der dette er relevant

**Climate Av og Fan Av er to separate funksjoner.**

Climate Av setter CD4-temperaturreguleringen til Manual summer /
temperatur AV. Dette stopper **ikke** ventilasjonsviftene.

Fan Av er bare tilgjengelig dersom aggregatet rapporterer at manuell
viftestopp er tillatt.

### Testing og tilbakemelding

CD4-støtten er omfattende testet på fysisk VSR 500/CD4-hardware før v1.3.0.

Følgende oppførsel er verifisert på ekte hardware:

- Toveis temperaturstyring mellom Home Assistant og CD4-kontrolleren
- Climate Av / Manual summer og retur til temperaturstyring
- Automatisk temperaturområde basert på varmeelementkonfigurasjon:
  - 12–22 °C med elektrisk varmeelement aktivert/konfigurert
  - 15–19 °C uten elektrisk varmeelement aktivert/konfigurert
- Status for varmegjenvinning som følger fysisk drift på aggregatet
- Status for elektrisk ettervarme som følger fysisk drift
- Viftestyring og relevante sensorverdier

CD4 er fortsatt merket som eksperimentell fordi eldre aggregater og
konfigurasjoner kan variere. Tilbakemeldinger fra andre CD4-baserte
anlegg er derfor fortsatt svært velkomne.

Rapporter gjerne både vellykkede tester og uventet oppførsel via GitHub Issues.

------------------------------------------------------------------------

## ✅ Testede aggregater / kompatibilitet

**✅ = fysisk testet tilkobling. — = ikke bekreftet fysisk testet (betyr ikke at tilkoblingen ikke støttes).**

**Luftmengde-estimat** betyr at modellen har en modellspesifikk beregning i integrasjonen. Det betyr ikke at beregningen er verifisert mot målte luftmengder. Spesielt er maksimumsverdien for VTR 300 SAVE ikke uavhengig verifisert. CD4 har ikke denne beregningen.

| Serie | Modell / type | Kontroller | TCP/IP testet | RTU testet | Luftmengde-estimat (m³/h) |
|---|---|---|:---:|:---:|:---:|
| VSR | VSR 150 | CD4 | — | — | ❌ |
| VSR | VSR 150/B | SAVE | — | — | ✅ |
| VSR | VSR 200/B | SAVE | — | — | ✅ |
| VSR | VSR 300 | SAVE | ✅ | — | ✅ |
| VSR | VSR 300 | CD4 | — | — | ❌ |
| VSR | VSR 300DE | CD4 | — | — | ❌ |
| VSR | VSR 400 | SAVE | — | — | ✅ |
| VSR | VSR 500 | SAVE | — | — | ✅ |
| VSR | VSR 500 | CD4 | ✅ | — | ❌ |
| VSR | VSR 700 | SAVE | — | — | ✅ |
| VTR | VTR 100/B | SAVE | — | — | ✅ |
| VTR | VTR 150K | SAVE | — | — | ✅ |
| VTR | VTR 150K | CD4 | ✅ | — | ❌ |
| VTR | VTR 150/B | SAVE | — | — | ✅ |
| VTR | VTR 200B | CD4 | — | — | ❌ |
| VTR | VTR 250/B | SAVE | ✅ | — | ✅ |
| VTR | VTR 275/B | SAVE | — | — | ✅ |
| VTR | VTR 300 | SAVE | ✅ | — | ✅ |
| VTR | VTR 300 | CD4 | — | — | ❌ |
| VTR | VTR 350/B | SAVE | ✅ | — | ✅ |
| VTR | VTR 500 | SAVE | ✅ | ✅ | ✅ |
| VTR | VTR 500 | CD4 | — | — | ❌ |
| VTR | VTR 700 | SAVE | — | — | ✅ |
| VTC | VTC 100 | CD4 | — | — | ❌ |
| VTC | VTC 200 | CD4 | — | — | ❌ |
| VTC | VTC 200-1 | SAVE | — | — | ✅ |
| VTC | VTC 300 | SAVE | — | — | ✅ |
| VTC | VTC 300 | CD4 | — | — | ❌ |
| VTC | VTC 500 | SAVE | — | — | ✅ |
| VTC | VTC 700 | SAVE | — | — | ✅ |
| VTC | VTC 700 | CD4 | — | — | ❌ |
| VSC | VSC 100 | SAVE | — | — | ✅ |
| VSC | VSC 200 | SAVE | — | — | ✅ |
| VSC | VSC 300 | SAVE | — | — | ✅ |
| VR | VR 400 | CD4 | — | — | ❌ |
| VR | VR 700 | CD4 | ✅ | — | ❌ |
| VR | VR 700DK | CD4 | — | — | ❌ |
| VR | VR 400DE | CD4 | — | — | ❌ |

**Bekreftet i tidligere dokumentasjon:** VSR 300, VTR 250/B, VTR 300 og VTR 500 (SAVE) via TCP/IP, samt VSR 500 (CD4) og VTR 150K (CD4) via TCP/IP. VTR 350/B er rapportert fungerende, men ikke fullstendig funksjonstestet. VTR 500 SAVE er testet med lesing og skriving via RTU med både AUX-2 og ESP32-C6.

---

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

- Home Assistant **2024.6** eller nyere (kravet i tidligere README; kontroller mot aktuell release)
- Et Systemair SAVE- eller CD4-aggregat med kompatibel Modbus-tilgang
- HACS for anbefalt installasjonsmetode
- En kompatibel TCP/IP-gateway eller RTU-serieforbindelse

### Installer integrasjonen

1. Åpne **HACS → Integrations**.
2. Søk etter **Systemair Modbus** og velg **Download**. Dersom integrasjonen ikke er tilgjengelig i HACS-søket, kan repositoryet legges til som **Custom repository** av typen **Integration**.
3. Start Home Assistant på nytt.
4. Gå til **Innstillinger → Enheter og tjenester → Legg til integrasjon → Systemair Modbus**.
5. Velg **Modbus TCP/IP (nettverk)** eller **Modbus RTU (seriell)**.
6. Følg veiledningen for valgt tilkoblingstype nedenfor.

### 🔌 Tilkoblingsveiledninger

| Tilkobling | Veiledning | Eksempel på utstyr |
|---|---|---|
| Modbus TCP/IP | **[TCP/IP – norsk](docs/modbus-tcp.no.md)** · [English](docs/modbus-tcp.md) | Elfin EW11, Systemair SAVE Connect |
| Modbus RTU | **[RTU – norsk](docs/modbus-rtu.no.md)** · [English](docs/modbus-rtu.md) | Home Assistant Connect AUX-2 med USB–RS485-adapter |

Begge veiledningene dekker fysisk tilkobling, konfigurering i Home Assistant og feilsøking. **AUX-2 krever en ekstern USB–RS485-adapter i AUX-2 sin USB-port** for tilkobling til RS485 A/B på aggregatet.

---

## 🔄 Oppgradering fra tidligere versjoner

### Gjenopprett gamle SAVE-entitets-ID-er

Under **Innstillinger → Enheter og tjenester → Systemair Modbus → Konfigurer (Alternativer)** finnes valget **«Gjenopprett gamle SAVE-entitets-ID-er (engangsoperasjon, krever sikkerhetskopi)»**.

Dette er en engangsfunksjon for brukere som trenger å gjenopprette tidligere SAVE-entitets-ID-er etter endringer i integrasjonen. Funksjonen er normalt **ikke nødvendig** ved installasjon eller oppgradering.

**Ta en sikkerhetskopi av Home Assistant før du bruker funksjonen.** Ikke aktiver den dersom entitetene allerede fungerer som forventet.

Ved gjenoppretting av tidligere ID-er kan Recorder gi advarsler dersom det allerede finnes historikk. Historikk fra midlertidige ID-er blir ikke nødvendigvis slått sammen med opprinnelig historikk. Dette påvirker ikke Modbus-kommunikasjon eller styring. Kontroller entiteter etter oppgradering.

---

## ℹ️ Begrensninger og tekniske notater

-   **Pressure Guard** er en intern sikkerhetsfunksjon i aggregatet\
    → eksponeres kun som status (kun lesing)
-   Ikke alle SAVE-modeller støtter full stopp via Modbus\
    → der full stopp ikke er tilgjengelig brukes lavest mulige
    viftehastighet
-   Tilgjengelige funksjoner avhenger av modell og konfigurasjon

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

Spesiell takk til [**stboee**](https://github.com/stboee) for omfattende
registerundersøkelser, funksjonsforslag og testing av SAVE-funksjonalitet
knyttet til ettervarme, ECO, frikjøling og Auto / Demand Control.

Spesiell takk til [**gljo**](https://github.com/gljo) (Glen Tore Johansen)
for omfattende og svært verdifull testing på fysisk VSR 500/CD4-hardware.
Testingen hans har vært et viktig bidrag til CD4-implementasjonen i v1.3.0
og har verifisert toveis temperaturstyring, Manual summer / Av, de
varmeelementavhengige temperaturområdene 12–22 °C og 15–19 °C,
varmegjenvinningsstatus, elektrisk ettervarmestatus, viftestyring og
generell CD4-oppførsel.

En AI-assistent har blitt brukt til støtte i feilsøking, refaktorering
og dokumentasjonsforbedringer under utviklingen.

Denne integrasjonen er **uavhengig utviklet** som en moderne Home
Assistant-integrasjon.

------------------------------------------------------------------------

## 📝 Lisens

MIT -- se `LICENSE`

