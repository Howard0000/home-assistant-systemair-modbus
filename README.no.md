# Home Assistant – Systemair Modbus (SAVE)

**Norsk** · [Read in English](README.md)

[![HACS](https://img.shields.io/badge/HACS-Default-green.svg)](https://hacs.xyz/)

Dette er en **Home Assistant-integrasjon for Systemair SAVE-aggregater** med støtte for **Modbus TCP**.

Integrasjonen gir strukturert overvåking og styring av ventilasjonsaggregatet i Home Assistant, med fokus på **riktig luftmengde, energieffektiv drift og stabil entitetshåndtering**.

⚠️ **Merk:**  
Dette er et **uoffisielt community-prosjekt** og er ikke utviklet, støttet eller vedlikeholdt av Systemair.

⚠️ **Ansvarsfraskrivelse:**  
Denne integrasjonen leveres **som den er**, uten noen form for garanti.  
Bruk skjer **på eget ansvar**. Forfatteren tar ikke ansvar for skade, datatap eller feilfunksjon på ventilasjonsanlegg, utstyr eller eiendom.

Kontroller alltid endringer direkte på aggregatet og sørg for at systemet er riktig konfigurert.  
Er du i tvil, kontakt kvalifisert fagperson.

---

## ✨ Funksjoner

### Ventilasjon og drift
- Visning av faktisk drift basert på aggregatets konfigurasjon
- Temperaturer (ute, tilluft, avtrekk, ettervarme, osv.)
- Viftehastigheter og driftsstatus
- Varmegjenvinning
- Filterstatus og alarmer

### Energi og effektivitet
- **Eco-modus**
- Behovsstyrt ventilasjon (der aggregatet støtter dette)
- Borte- og feriemodus
- Energieffektiv drift basert på belastning og aggregatets konfigurasjon

### Komfort
- **Frikjøling (Free cooling)** når betingelser er oppfylt
- Party- og Boost-modus
- Manuell viftehastighetsstyring (Lav / Normal / Høy)

### Brukeropplevelse
- Norsk og engelsk språk (følger Home Assistant-språk)
- Konsistente og stabile entiteter
- Innebygde **knapper** for vanlige handlinger
- Robust håndtering av midlertidig bortfall av Modbus-forbindelse

---

## 📋 Systemair SAVE – støttede modeller

**Luftmengde-estimat (m³/h)** er kun tilgjengelig for modeller som er eksplisitt definert i koden og som deler forventet Modbus-registeroppsett.

**Forklaring:**
- ✅ = Ja / tilgjengelig  
- ⚙️ = Støttet, men ikke testet  
- ❌ = Ikke tilgjengelig  

> ⚠️ Merk: Eldre enheter med **CD4-kontroller** bruker et annet Modbus-registerkart enn enheter med **SAVE Touch**.  
> Støtte for CD4 er fortsatt under utvikling og er **ikke inkludert i nåværende stabile release**.  
> Hvis du tester en slik enhet, opprett gjerne en Issue og del erfaringene dine.

> Har du testet integrasjonen med en modell som ikke er merket som testet?  
> Gi gjerne beskjed ved å opprette en Issue, så kan denne listen oppdateres.

| Serie | Modell / Type | Modbus-støtte | Luftmengde-estimering (m³/h) | Testet |
|-------|---------------|----------------|-------------------------------|--------|
| VSR | VSR 150/B | ✅ | ✅ | ❌ |
| VSR | VSR 200/B | ✅ | ✅ | ❌ |
| VSR | VSR 300 | ✅ | ✅ | ❌ |
| VSR | VSR 400 | ✅ | ✅ | ❌ |
| VSR | VSR 500 | ✅ | ✅ | ❌ |
| VSR | VSR 700 | ✅ | ✅ | ❌ |
| VTR | VTR 100/B | ✅ | ✅ | ❌ |
| VTR | VTR 150/B | ✅ | ✅ | ❌ |
| VTR | VTR 250/B | ✅ | ✅ | ❌ |
| VTR | VTR 275/B | ✅ | ✅ | ❌ |
| VTR | VTR 300 | ✅ | ✅ | ✅ |
| VTR | VTR 350/B | ✅ | ✅ | ❌ |
| VTR | VTR 500 | ✅ | ✅ | ✅ |
| VTR | VTR 700 | ✅ | ✅ | ❌ |
| VTC | VTC 200–1 | ✅ | ❌ | ❌ |
| VTC | VTC 300 | ✅ | ❌ | ❌ |
| VTC | VTC 500 | ✅ | ❌ | ❌ |
| VTC | VTC 700 | ✅ | ❌ | ❌ |
| VSC | VSC 100 | ✅ | ❌ | ❌ |
| VSC | VSC 200 | ✅ | ❌ | ❌ |
| VSC | VSC 300 | ✅ | ❌ | ❌ |

> ✅ VTR 300: Bekreftet å fungere av en bruker i community (**SAVE Touch**, original Systemair Modbus-gateway, Modbus TCP).  
> ✅ VTR 500: Bekreftet å fungere av en bruker i community (testet med ekstern Modbus TCP-gateway).  
> ⚠️ CD4-enheter: Ikke verifisert enda og kan kreve et annet registerkart.

---

## 🏗️ Forutsetninger – aggregatvalg og luftmengde

Denne integrasjonen forutsetter at ventilasjonsanlegget er **riktig prosjektert og dimensjonert**.

- Aggregatet må være valgt basert på reelt luftbehov (m³/h)
- Luftmengder per sone må være riktig innregulert
- Home Assistant erstatter **ikke** profesjonell ventilasjonsprosjektering

Integrasjonen bygger på aggregatets eksisterende konfigurasjon og gir:
- overvåking
- styring
- automasjon

Feil aggregatvalg eller feil luftmengder kan ikke kompenseres med programvare.

---

## 🖥️ Eksempel på Lovelace-kort

Bildet under viser et eksempel på et Lovelace-kort bygget manuelt i Home Assistant
ved hjelp av entiteter fra denne integrasjonen.

> Selve kortet følger **ikke** med integrasjonen og kan tilpasses fritt.

![Ventilasjon Kort](image/Ventilasjon%20kort.png)

---

## 📦 Installasjon (HACS)

### Krav
- Home Assistant **2024.6** eller nyere
- Systemair SAVE-aggregat med Modbus-tilgang
- Modbus TCP  
  - Innebygd i aggregatet **eller**
  - Via ekstern gateway (f.eks. Elfin EW11)
- HACS (Home Assistant Community Store)

---

### Metode 1: Installer via HACS (anbefalt)

1. Åpne **HACS**
2. Gå til **Integrations**
3. Søk etter **Systemair Modbus**
4. Klikk **Last ned**
5. Start Home Assistant på nytt
6. Gå til **Innstillinger → Enheter og tjenester → Legg til integrasjon**
7. Velg **Systemair Modbus** og fyll inn:
   - IP-adresse
   - Port (vanligvis `502`)
   - Modbus slave-ID

---

### Metode 2: Installer som custom repository (manuelt)

> Denne metoden er hovedsakelig ment for utvikling, testing eller tidlig tilgang til endringer.

1. Åpne **HACS**
2. Gå til **Integrations**
3. Åpne menyen (tre prikker) → **Custom repositories**
4. Legg til dette repoet som **Integration**
5. Installer **Systemair Modbus**
6. Start Home Assistant på nytt
7. Gå til **Innstillinger → Enheter og tjenester → Legg til integrasjon**
8. Velg **Systemair Modbus** og fyll inn:
   - IP-adresse
   - Port (vanligvis `502`)
   - Modbus slave-ID

---

## ℹ️ Begrensninger og tekniske merknader

- **Pressure Guard (trykkvakt)** er en intern sikkerhetsfunksjon i aggregatet  
  → vises kun som status (read-only)
- Ikke alle SAVE-modeller støtter full stopp via Modbus  
  → der full stopp ikke er tilgjengelig, brukes lavest mulig viftehastighet
- Tilgjengelige funksjoner avhenger av aggregatmodell og konfigurasjon

---

## 🔌 Fysisk installasjon – Elfin EW11 (Modbus RTU → TCP)

Denne delen er kun relevant dersom aggregatet **ikke** har innebygd Modbus TCP.

### ⚠️ ADVARSEL
Koble alltid fra strømmen til ventilasjonsaggregatet før du åpner det.  
Er du usikker, kontakt kvalifisert fagperson.

### 1. Modbus-tilkobling på Systemair SAVE
Finn terminalene for ekstern kommunikasjon på hovedkortet:
- `A (+)`
- `B (–)`
- `24V`
- `GND`

![Eksempel koblingsskjema (VTR-500)](image/koblingsskjemaVTR-500.png)

### 2. Koble til Elfin EW11
Koble ledningene i henhold til skjemaet under:

![Koblingsskjema EW11](image/koblings%20skjema%20EW11.png)

---

### 3. Konfigurer Elfin EW11

1. Koble til Wi-Fi-nettverket `EW1x_...` (åpent nettverk)
2. Åpne webgrensesnittet: `http://10.10.100.254`
3. Logg inn med:
   - Brukernavn: `admin`
   - Passord: `admin`
4. Gå til **System Settings → WiFi Settings**
   - Sett **WiFi Mode** til `STA`
   - Koble til ditt lokale nettverk
5. Start enheten på nytt og sett **statisk IP**
6. Åpne **Serial Port Settings** og sett verdiene som vist:

![Serial Port Settings EW11](image/serial%20port%20settings%20EW11.png)

7. Åpne **Communication Settings** og legg til en Modbus-profil:

![Communication Settings EW11](image/communication%20settings%20EW11.png)

8. Under **Status** skal telleverk for datapakker øke:

![Kommunikasjonsstatus EW11](image/kommunikasjon%20EW11.png)

Når kommunikasjonen er bekreftet, kan IP-adressen brukes direkte i Home Assistant.

---

## 🙏 Anerkjennelser

Installasjonsveiledningen for Elfin EW11 (Modbus RTU → TCP) er basert på arbeid publisert på
[domotics.no](https://www.domotics.no/), skrevet av **Mads Nedrehagen**.

Spesiell takk til **Ztaeyn** for bidrag til forbedret håndtering av klimastatus (`hvac_action`) basert på TRIAC-registeret.

En KI-assistent har blitt brukt som støtte til feilsøking, refaktorering og forbedring av dokumentasjon under utviklingen.

Denne integrasjonen er **selvstendig utviklet** som en moderne Home Assistant-integrasjon.


---

## 📝 Lisens
MIT – se `LICENSE`
