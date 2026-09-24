<p align="center"><img src="assets/app_icon.png" width="120" alt="ScriVoice logo"></p>

<h1 align="center">ScriVoice</h1>

<p align="center"><b>Private voice dictation for Windows and Mac.</b><br>
Press a shortcut, speak, and your words are typed wherever you are writing —
ChatGPT, Claude, email, Slack, Word, any app.<br>
100% on your computer. Free and open source.</p>

<p align="center"><a href="https://github.com/philipjpj/scrivoice/releases/latest"><b>⬇ Download ScriVoice</b></a></p>

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

## Download and install (no technical skills needed)

**1. Check your computer**

- **Windows:** Windows 10 or 11 (64-bit).
- **Mac:** only Macs with an **Apple chip**. To check: **Apple menu** (top-left corner) → **About This Mac**. If you see
  **"Chip Apple M1"** (or M2, M3, M4…) it works. If you see **"Processor … Intel"**, it is not supported.
- About **1.5 GB** of free space.

**2. Download one file**

Open the [**download page**](https://github.com/philipjpj/scrivoice/releases/latest), scroll to **Assets** and
click the file for your computer:

| Your computer | File to download |
|---|---|
| Windows | **`ScriVoiceSetup-1.0.0.exe`** |
| Mac | **`ScriVoice-1.0.0-mac-AppleSilicon.dmg`** |

> The version number in the file name may be higher. Ignore the two **"Source code"** files: they are
> for programmers and cannot be installed.

**3. Install**

<details open><summary><b>Windows</b></summary>

1. Double-click the downloaded `ScriVoiceSetup-….exe`.
2. Windows may show **"Windows protected your PC"**. This is normal for free apps without a paid
   certificate: click **More info**, then **Run anyway**.
3. Click **Next** a few times. At the end, setup "prepares" ScriVoice for about a minute.
4. Open **ScriVoice** from the Start menu. No administrator rights are needed.

</details>

<details open><summary><b>Mac</b></summary>

1. Double-click the downloaded `.dmg` and **drag ScriVoice into Applications**.
2. Open ScriVoice from Applications. The first time the Mac says it **cannot verify the developer**
   (normal for apps outside the App Store): click **Done**, open **System Settings → Privacy & Security**,
   scroll down and click **Open Anyway**. Only the first time.
3. When asked, allow ScriVoice in **System Settings → Privacy & Security**: **Microphone**,
   **Accessibility** (to paste the text) and **Input Monitoring** (for the shortcut).
4. Quit ScriVoice (icon at the top of the screen → **Quit**) and open it again.

</details>

**4. Use it**

1. Click into the app where you want to write (a chat, an email, a document…).
2. Press **Ctrl + Alt + Space** (Windows) or **Ctrl + Shift + Space** (Mac) and speak,
   then press it again. Or hold it down while you speak. **Esc** cancels.
3. The text appears where you were typing. **Right-click** the small widget for **Settings**
   (language, shortcut, microphone, theme…).

Full guide with pictures: [ScriVoice Guide (PDF)](docs/ScriVoice-Guide-EN.pdf)

---

## For developers

Run from source (Python 3.10+):

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
