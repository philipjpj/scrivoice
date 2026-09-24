<p align="center"><img src="assets/app_icon.png" width="120" alt="ScriVoice logo"></p>

<h1 align="center">ScriVoice</h1>

<p align="center"><b>Private voice dictation for Windows and Mac.</b><br>
Press a shortcut, speak, and your words are typed wherever you are writing —
ChatGPT, Claude, email, Slack, Word, any app.<br>
100% on your computer. Free and open source.</p>

<p align="center"><a href="https://github.com/philipjpj/scrivoice/releases/latest"><b>⬇ Download the latest version</b></a></p>

---

## Features

- **Private** — your voice is transcribed on your own computer with a built-in
  [Whisper](https://github.com/openai/whisper) model. No audio or text ever leaves your device.
  No account, no internet connection, no tracking.
- **Works in any app** — the text is pasted where your cursor is, **without sending**: you read it first.
- **Tap or hold** — tap the shortcut to start and stop, or hold it while you speak (push-to-talk).
- **Italian, English, Spanish** — or automatic language detection. Interface in the same three languages.
- **Personal vocabulary and corrections** — teach it names and technical words.
- **Tiny floating widget** — shows recording, volume and status. Dark, light or neon theme.

## Install

| | Download | Requirements |
|---|---|---|
| **Windows** | `ScriVoiceSetup-x.y.z.exe` | Windows 10/11, 64-bit |
| **Mac** | `ScriVoice-x.y.z-mac-AppleSilicon.dmg` | Apple silicon (M1 or later), macOS 13+ |

Get both from the [Releases page](https://github.com/philipjpj/scrivoice/releases/latest). About 1.5 GB of free space is needed.

- **Windows:** open the installer. If Windows shows *"Windows protected your PC"*, click **More info → Run anyway**
  (the app is not code-signed).
- **Mac:** drag ScriVoice to Applications. The first time, macOS says it cannot verify the developer: open
  **System Settings → Privacy & Security** and click **Open Anyway**. Then allow **Microphone**, **Accessibility**
  (to paste) and **Input Monitoring** (for the shortcut), and restart ScriVoice.

Full guides with pictures: [English](docs/ScriVoice-Guide-EN.pdf) · [Italiano](docs/ScriVoice-Guida-IT.pdf)

## How to use

1. Click into the app where you want to write.
2. Press **Ctrl + Alt + Space** (Windows) or **Ctrl + Shift + Space** (Mac), speak, press it again.
   Or hold it down while you speak. **Esc** cancels.
3. The text appears where you were typing. Right-click the widget for **Settings**.

## In italiano

ScriVoice è un programma **gratuito** di dettatura vocale per Windows e Mac: premi la scorciatoia, parli e il
testo viene scritto dove stai scrivendo. La voce viene trascritta **sul tuo computer**, senza internet.
Scaricalo dalla pagina [Releases](https://github.com/philipjpj/scrivoice/releases/latest) e segui la
[guida in italiano](docs/ScriVoice-Guida-IT.pdf).

## Run from source / build

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt        # Windows: .venv\Scripts\pip
.venv/bin/python main.py
```

(`install.bat` / `install.command` do the same with a double click.)

Packages are built by [GitHub Actions](.github/workflows/release.yml) when a `v*` tag is pushed:
`python packaging/prepare.py` (model, icons, third-party licenses), then PyInstaller
(`packaging/scrivoice.spec`), then Inno Setup on Windows (`packaging/windows/installer.iss`) or an ad-hoc
signed DMG on Mac (`packaging/mac/build_dmg.sh`). Every build runs `--selftest`, which transcribes a sample
audio file with the packaged app.

Main modules: `main.py` (app), `transcriber.py` (faster-whisper), `recorder.py` (microphone),
`paster*.py` (paste into the active window), `hotkey*.py` (global shortcuts: `RegisterHotKey` on Windows,
`pynput` on Mac), `widget.py`, `settings_dialog.py`, `i18n.py` (translations; the Italian text is the key).

## License

[MIT](LICENSE) © philipjpj. The distributed apps include third-party components under their own licenses
(Qt/PySide6 and pynput under the LGPL v3, Whisper model under MIT, and others) — see
`THIRD_PARTY_LICENSES.txt` inside the app.
