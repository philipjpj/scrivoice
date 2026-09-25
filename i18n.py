"""Traduzioni dell'interfaccia (italiano, inglese, spagnolo).

Il testo italiano scritto nel codice fa da chiave: tr("Trascrivo…") restituisce la versione nella
lingua attiva. Per aggiungere un testo nuovo basta aggiungere una voce a _T.
"""
import os

from PySide6.QtCore import QLibraryInfo, QTranslator
from PySide6.QtWidgets import QApplication

LANGUAGES = [("it", "Italiano"), ("en", "English"), ("es", "Español")]

_current = "en"
_qt_translator = None


def language():
    return _current


def set_language(lang):
    """lang: it | en | es; qualsiasi altro valore = inglese."""
    global _current, _qt_translator
    _current = lang if lang in dict(LANGUAGES) else "en"
    app = QApplication.instance()
    if app is None:
        return
    # testi standard di Qt (es. finestra di scelta del colore)
    if _qt_translator is not None:
        app.removeTranslator(_qt_translator)
        _qt_translator = None
    if _current != "en":
        translator = QTranslator()
        folder = QLibraryInfo.path(QLibraryInfo.TranslationsPath)
        if translator.load(os.path.join(folder, f"qtbase_{_current}.qm")):
            app.installTranslator(translator)
            _qt_translator = translator


def tr(text, **kwargs):
    if _current != "it":
        text = _T.get(text, {}).get(_current, text)
    return text.format(**kwargs) if kwargs else text


_T = {
    # ---- widget ----
    "Carico il modello…": {"en": "Loading model…", "es": "Cargando modelo…"},
    "Trascrivo…": {"en": "Transcribing…", "es": "Transcribiendo…"},
    "Incollato": {"en": "Pasted", "es": "Pegado"},
    "Errore": {"en": "Error", "es": "Error"},
    "Annullato": {"en": "Cancelled", "es": "Cancelado"},
    "Troppo breve": {"en": "Too short", "es": "Demasiado corto"},
    "Nessun parlato rilevato": {"en": "No speech detected", "es": "No se detectó voz"},
    "Scorciatoia non attiva: {e}": {"en": "Shortcut not active: {e}", "es": "Atajo no activo: {e}"},
    "{keys} è già usata da un'altra app: scegline un'altra nelle impostazioni": {
        "en": "{keys} is already used by another app: choose a different one in Settings",
        "es": "{keys} ya lo usa otra app: elige otro en los ajustes"},
    "Microfono non disponibile: {e}": {"en": "Microphone unavailable: {e}",
                                       "es": "Micrófono no disponible: {e}"},
    "Trascrizione fallita: {e}": {"en": "Transcription failed: {e}", "es": "Transcripción fallida: {e}"},
    "Incolla fallito, testo negli appunti ({e})": {
        "en": "Paste failed, text copied to clipboard ({e})",
        "es": "Error al pegar, texto en el portapapeles ({e})"},
    "Modello non caricato: {e}": {"en": "Model not loaded: {e}", "es": "Modelo no cargado: {e}"},
    # ---- permessi macOS ----
    "Manca il permesso Accessibilità": {"en": "Accessibility permission missing",
                                        "es": "Falta el permiso de Accesibilidad"},
    "Per incollare il testo serve il permesso Accessibilità: Impostazioni di Sistema → Privacy e "
    "sicurezza → Accessibilità → attiva {app}, poi riavvia ScriVoice.": {
        "en": "To paste text, Accessibility permission is needed: System Settings → Privacy & "
              "Security → Accessibility → turn on {app}, then restart ScriVoice.",
        "es": "Para pegar el texto hace falta el permiso de Accesibilidad: Ajustes del Sistema → "
              "Privacidad y seguridad → Accesibilidad → activa {app} y reinicia ScriVoice."},
    # ---- menu tray ----
    "Nascondi widget": {"en": "Hide widget", "es": "Ocultar widget"},
    "Mostra widget": {"en": "Show widget", "es": "Mostrar widget"},
    "Copia ultima trascrizione": {"en": "Copy last transcription", "es": "Copiar última transcripción"},
    "Apri cartella registrazioni": {"en": "Open recordings folder", "es": "Abrir carpeta de grabaciones"},
    "Impostazioni…": {"en": "Settings…", "es": "Ajustes…"},
    "Esci": {"en": "Quit", "es": "Salir"},
    "Informazioni": {"en": "About", "es": "Acerca de"},
    "Informazioni su ScriVoice": {"en": "About ScriVoice", "es": "Acerca de ScriVoice"},
    "Dettatura vocale: la voce viene trascritta sul tuo computer e il testo incollato dove stai "
    "scrivendo.": {
        "en": "Voice dictation: your voice is transcribed on your computer and the text is pasted "
              "where you are typing.",
        "es": "Dictado por voz: tu voz se transcribe en tu ordenador y el texto se pega donde "
              "estás escribiendo."},
    "Software libero e open source, licenza MIT.": {"en": "Free and open-source software, MIT license.",
                                                   "es": "Software libre y de código abierto, licencia MIT."},
    "Codice, aggiornamenti e segnalazioni: {link}": {"en": "Code, updates and issue reports: {link}",
                                                     "es": "Código, actualizaciones e incidencias: {link}"},
    "Avvia ScriVoice all'accensione del computer": {"en": "Start ScriVoice when the computer starts",
                                                     "es": "Iniciar ScriVoice al encender el ordenador"},
    "Impostazioni salvate.": {"en": "Settings saved.", "es": "Ajustes guardados."},
    # ---- temi, colori, dimensioni ----
    "Scuro": {"en": "Dark", "es": "Oscuro"},
    "Chiaro": {"en": "Light", "es": "Claro"},
    "Neon": {"en": "Neon", "es": "Neón"},
    "Rosso": {"en": "Red", "es": "Rojo"},
    "Blu": {"en": "Blue", "es": "Azul"},
    "Verde": {"en": "Green", "es": "Verde"},
    "Viola": {"en": "Purple", "es": "Morado"},
    "Arancio": {"en": "Orange", "es": "Naranja"},
    "Ciano": {"en": "Cyan", "es": "Cian"},
    "Magenta": {"en": "Magenta", "es": "Magenta"},
    "Piccolo": {"en": "Small", "es": "Pequeño"},
    "Medio": {"en": "Medium", "es": "Mediano"},
    "Grande": {"en": "Large", "es": "Grande"},
    # ---- pannello impostazioni ----
    "ScriVoice: impostazioni": {"en": "ScriVoice: settings", "es": "ScriVoice: ajustes"},
    "Generale": {"en": "General", "es": "General"},
    "Scorciatoie": {"en": "Shortcuts", "es": "Atajos"},
    "Trascrizione": {"en": "Transcription", "es": "Transcripción"},
    "Correzioni": {"en": "Corrections", "es": "Correcciones"},
    "Aspetto": {"en": "Appearance", "es": "Apariencia"},
    "Salva": {"en": "Save", "es": "Guardar"},
    "Annulla": {"en": "Cancel", "es": "Cancelar"},
    "Lingua": {"en": "Language", "es": "Idioma"},
    "Lingua dell'interfaccia:": {"en": "Interface language:", "es": "Idioma de la interfaz:"},
    "Lingua della dettatura:": {"en": "Dictation language:", "es": "Idioma del dictado:"},
    "Automatico (rileva la lingua)": {"en": "Automatic (detect language)",
                                      "es": "Automático (detectar idioma)"},
    "La lingua in cui parli. «Automatico» riconosce da solo italiano, inglese o spagnolo, "
    "ma sbaglia più spesso con frasi molto corte.": {
        "en": "The language you speak. “Automatic” recognizes Italian, English or Spanish on its "
              "own, but makes more mistakes with very short sentences.",
        "es": "El idioma en el que hablas. «Automático» reconoce por sí solo italiano, inglés o "
              "español, pero se equivoca más con frases muy cortas."},
    "Altro": {"en": "Other", "es": "Otros"},
    "Dopo l'incolla ripristina il contenuto precedente degli appunti": {
        "en": "Restore the previous clipboard content after pasting",
        "es": "Restaurar el contenido anterior del portapapeles después de pegar"},
    "Salva le registrazioni (WAV + testo) nella cartella recordings": {
        "en": "Save recordings (WAV + text) in the recordings folder",
        "es": "Guardar las grabaciones (WAV + texto) en la carpeta recordings"},
    "Scorciatoie da tastiera": {"en": "Keyboard shortcuts", "es": "Atajos de teclado"},
    "Avvia / ferma:": {"en": "Start / stop:", "es": "Iniciar / detener:"},
    "Tocco breve: avvia e poi ferma. Tenuta premuta: registra finché non rilasci.": {
        "en": "Short tap: start, then stop. Hold down: record until you release.",
        "es": "Toque breve: inicia y luego detiene. Mantener pulsado: graba hasta que sueltes."},
    "Solo ferma:": {"en": "Stop only:", "es": "Solo detener:"},
    "Uguale ad avvio": {"en": "Same as start", "es": "Igual que iniciar"},
    "Annulla registrazione:": {"en": "Cancel recording:", "es": "Cancelar grabación:"},
    "Disattivata": {"en": "Disabled", "es": "Desactivado"},
    "Push-to-talk dopo:": {"en": "Push-to-talk after:", "es": "Pulsar para hablar tras:"},
    "Premi la combinazione…": {"en": "Press the key combination…", "es": "Pulsa la combinación…"},
    "Rimuovi": {"en": "Remove", "es": "Quitar"},
    "Nessuna": {"en": "None", "es": "Ninguna"},
    "Microfono": {"en": "Microphone", "es": "Micrófono"},
    "Predefinito del sistema": {"en": "System default", "es": "Predeterminado del sistema"},
    "Dispositivo:": {"en": "Device:", "es": "Dispositivo:"},
    "Gli auricolari Bluetooth (es. AirPods) registrano in bassa qualità (16 kHz): se sei in un luogo "
    "silenzioso, il microfono del PC spesso è più preciso.": {
        "en": "Bluetooth earbuds (e.g. AirPods) record in low quality (16 kHz): in a quiet place, "
              "the PC microphone is often more accurate.",
        "es": "Los auriculares Bluetooth (p. ej. AirPods) graban en baja calidad (16 kHz): en un lugar "
              "silencioso, el micrófono del PC suele ser más preciso."},
    "Qualità della trascrizione": {"en": "Transcription quality", "es": "Calidad de la transcripción"},
    "Modello:": {"en": "Model:", "es": "Modelo:"},
    "Veloce: small (consigliato su questo PC)": {"en": "Fast: small (recommended on this PC)",
                                                 "es": "Rápido: small (recomendado en este PC)"},
    "Più preciso: medium (lento, circa 1,5 GB di RAM)": {
        "en": "More accurate: medium (slow, about 1.5 GB of RAM)",
        "es": "Más preciso: medium (lento, unos 1,5 GB de RAM)"},
    "Massima precisione: large-v3-turbo (molto lento, circa 2 GB di RAM)": {
        "en": "Maximum accuracy: large-v3-turbo (very slow, about 2 GB of RAM)",
        "es": "Máxima precisión: large-v3-turbo (muy lento, unos 2 GB de RAM)"},
    "Ricerca:": {"en": "Search:", "es": "Búsqueda:"},
    "Precisa (consigliata)": {"en": "Accurate (recommended)", "es": "Precisa (recomendada)"},
    "Veloce": {"en": "Fast", "es": "Rápida"},
    "Vocabolario personale:": {"en": "Personal vocabulary:", "es": "Vocabulario personal:"},
    "es. shortcut, task, React, nomi dei tuoi progetti…": {
        "en": "e.g. shortcut, task, React, your project names…",
        "es": "p. ej. shortcut, task, React, nombres de tus proyectos…"},
    "Parole, nomi e termini tecnici che usi spesso, separati da virgola.": {
        "en": "Words, names and technical terms you use often, separated by commas.",
        "es": "Palabras, nombres y términos técnicos que usas a menudo, separados por comas."},
    "Sostituzioni automatiche (locali, gratuite)": {"en": "Automatic replacements (local, free)",
                                                    "es": "Sustituciones automáticas (locales, gratis)"},
    "Quando Whisper sbaglia sempre la stessa parola, aggiungila qui: verrà sostituita su ogni "
    "trascrizione, solo se è una parola intera.": {
        "en": "When Whisper keeps getting the same word wrong, add it here: it will be replaced in "
              "every transcription, only as a whole word.",
        "es": "Cuando Whisper se equivoca siempre con la misma palabra, añádela aquí: se sustituirá "
              "en cada transcripción, solo si es una palabra completa."},
    "Parola sbagliata": {"en": "Wrong word", "es": "Palabra incorrecta"},
    "Parola giusta": {"en": "Correct word", "es": "Palabra correcta"},
    "Aggiungi": {"en": "Add", "es": "Añadir"},
    "Rimuovi selezionate": {"en": "Remove selected", "es": "Quitar seleccionadas"},
    "Stile del widget": {"en": "Widget style", "es": "Estilo del widget"},
    "Tema:": {"en": "Theme:", "es": "Tema:"},
    "Colore:": {"en": "Color:", "es": "Color:"},
    "Altro…": {"en": "Other…", "es": "Otro…"},
    "Scegli un colore qualsiasi": {"en": "Pick any color", "es": "Elige cualquier color"},
    "Colore di accento": {"en": "Accent color", "es": "Color de acento"},
    "Dimensione:": {"en": "Size:", "es": "Tamaño:"},
    "Opacità:": {"en": "Opacity:", "es": "Opacidad:"},
    "Nel tema Neon il colore scelto diventa anche il bagliore del bordo.": {
        "en": "In the Neon theme the chosen color also becomes the border glow.",
        "es": "En el tema Neón el color elegido también se convierte en el brillo del borde."},
    "serve una scorciatoia di avvio.": {"en": "a start shortcut is required.",
                                        "es": "se necesita un atajo para iniciar."},
    "avvio, stop e annulla devono essere diverse.": {"en": "start, stop and cancel must be different.",
                                                     "es": "iniciar, detener y cancelar deben ser distintos."},
    "stop e annulla devono essere diverse.": {"en": "stop and cancel must be different.",
                                              "es": "detener y cancelar deben ser distintos."},
    "la scorciatoia deve includere un tasto oltre ai modificatori.": {
        "en": "the shortcut must include a key besides the modifiers.",
        "es": "el atajo debe incluir una tecla además de los modificadores."},
    "Attenzione: «{key}» da solo verrà bloccato in tutte le app. Meglio una combinazione con "
    "Ctrl/Alt/Shift.": {
        "en": "Warning: “{key}” alone will be blocked in every app. Better use a combination "
              "with Ctrl/Alt/Shift.",
        "es": "Atención: «{key}» solo quedará bloqueado en todas las apps. Mejor una combinación con "
              "Ctrl/Alt/Shift."},
    "Non valido: {problems}": {"en": "Not valid: {problems}", "es": "No válido: {problems}"},
}
