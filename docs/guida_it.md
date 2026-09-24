# ScriVoice — Guida

**Parla, e il testo si scrive da solo dove stai scrivendo.** Gratuito e open source (licenza MIT). ScriVoice trascrive la tua voce sul tuo computer: è privato, funziona senza internet e incolla il testo nella chat, nell'email o nel documento che hai aperto.

![Il widget di ScriVoice](img/widget.png)

## 1. Requisiti

- **Windows:** Windows 10 o 11 a 64 bit.
- **Mac:** Mac con chip Apple (M1 o successivo), macOS 13 o successivo. I Mac con processore Intel non sono supportati.
- Circa 1,5 GB di spazio libero e un microfono (quello del computer va benissimo).

## 2. Installazione su Windows

1. Scarica **ScriVoiceSetup.exe** dalla pagina **Releases** del progetto su GitHub (github.com/philipjpj/scrivoice/releases) e aprilo.
2. Windows potrebbe mostrare **"Windows ha protetto il PC"**. È normale per i programmi nuovi: clicca **Ulteriori informazioni**, poi **Esegui comunque**.
3. Segui l'installazione: accetta la licenza e scegli se creare l'icona sul desktop e se avviare ScriVoice all'accensione.
4. Alla fine l'installazione prepara ScriVoice: può richiedere circa un minuto.

Non servono permessi di amministratore.

## 3. Installazione su Mac

1. Scarica **ScriVoice.dmg** dalla pagina **Releases** del progetto su GitHub (github.com/philipjpj/scrivoice/releases) e aprilo.
2. Trascina **ScriVoice** nella cartella **Applicazioni**.
3. Apri ScriVoice da Applicazioni. La prima volta il Mac dice che **non può verificare lo sviluppatore**: è normale per le app vendute fuori dall'App Store. Clicca **Fine**, poi apri **Impostazioni di Sistema → Privacy e sicurezza**, scorri in fondo e clicca **Apri comunque** accanto a ScriVoice. Serve solo la prima volta.
4. **Permessi:** quando il Mac li chiede, attiva ScriVoice in **Impostazioni di Sistema → Privacy e sicurezza**:
   - **Microfono:** per registrare la voce;
   - **Accessibilità:** per incollare il testo;
   - **Monitoraggio input:** per la scorciatoia da tastiera.
5. Dopo aver dato i permessi, chiudi ScriVoice (icona in alto → **Esci**) e riaprilo.

## 4. Come si usa

1. **Clicca** nella chat, nell'email o nel documento in cui vuoi scrivere.
2. **Tocca** la scorciatoia e parla, poi **toccala di nuovo**: il testo compare dove stavi scrivendo.
   Oppure **tienila premuta** mentre parli e rilasciala alla fine.
3. Il testo viene incollato ma **non inviato**, così puoi rileggerlo.

| | Windows | Mac |
|---|---|---|
| Scorciatoia | **Ctrl + Alt + Spazio** | **Ctrl + Shift + Spazio** |
| Annulla la registrazione | Esc | Esc |

Il **widget** mostra cosa sta succedendo: registrazione (con il volume), trascrizione e testo incollato. Puoi **trascinarlo** dove vuoi e **cliccarlo** per avviare o fermare. Con il **clic destro** sul widget, o sull'icona di ScriVoice vicino all'orologio o in alto sul Mac, apri il menu: **Impostazioni**, copia dell'ultima trascrizione, **Informazioni** ed **Esci**.

## 5. Impostazioni

![Impostazioni](img/settings.png)

- **Generale:** lingua dell'interfaccia e **lingua in cui parli** (italiano, inglese, spagnolo o automatica), avvio all'accensione.
- **Scorciatoie:** clicca un pulsante e premi la combinazione che preferisci.
- **Trascrizione:** microfono, precisione e **vocabolario personale**. Aggiungi nomi e parole tecniche che usi spesso: verranno riconosciuti meglio.
- **Correzioni:** se ScriVoice sbaglia sempre la stessa parola, aggiungila qui ("parola sbagliata → parola giusta").
- **Aspetto:** tema scuro, chiaro o neon, colore, dimensione e trasparenza del widget.

## 6. Problemi comuni

- **Il testo non viene incollato (Mac):** manca il permesso **Accessibilità**. Attivalo e riavvia ScriVoice.
- **La scorciatoia non fa niente (Mac):** manca il permesso **Monitoraggio input**.
- **"La scorciatoia è già usata da un'altra app" (Windows):** scegline un'altra in *Impostazioni → Scorciatoie*.
- **La scorciatoia non funziona in un programma aperto come amministratore (Windows):** è una protezione di Windows. Usa un programma normale o avvia anche ScriVoice come amministratore.
- **Riconosce male alcune parole:** aggiungile al vocabolario personale o alle correzioni. Un microfono vicino e un ambiente silenzioso aiutano. Gli auricolari Bluetooth registrano in qualità più bassa del microfono del computer.
- **Il testo è nella lingua sbagliata:** imposta la lingua in cui parli in *Impostazioni → Generale*.

## 7. Privacy

La tua voce viene trascritta **solo sul tuo computer** e non viene mai inviata a nessuno. ScriVoice non si collega a internet: nessun account, nessuna pubblicità e nessun tracciamento.

## 8. Disinstallare

- **Windows:** Impostazioni → App → App installate → ScriVoice → Disinstalla.
- **Mac:** esci da ScriVoice e trascina l'app nel Cestino. Le impostazioni sono in *~/Library/Application Support/ScriVoice*.
