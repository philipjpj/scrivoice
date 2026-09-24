# ScriVoice — Guide

**Speak, and the text writes itself where you are typing.** Free and open source (MIT license). ScriVoice transcribes your voice on your own computer: it is private, works offline and pastes the text into the chat, email or document you have open.

![The ScriVoice widget](img/widget.png)

## 1. Requirements

- **Windows:** Windows 10 or 11, 64-bit.
- **Mac:** Mac with Apple silicon (M1 or later), macOS 13 or later. Intel Macs are not supported.
- About 1.5 GB of free space and a microphone (the built-in one works fine).

## 2. Installing on Windows

1. Download **ScriVoiceSetup.exe** from the project's **Releases** page on GitHub (github.com/philipjpj/scrivoice/releases) and open it.
2. Windows may show **"Windows protected your PC"**. This is normal for new software: click **More info**, then **Run anyway**.
3. Follow the setup: accept the license and choose whether to create a desktop icon and start ScriVoice with Windows.
4. At the end the setup prepares ScriVoice: this can take about a minute.

No administrator rights are needed.

## 3. Installing on Mac

1. Download **ScriVoice.dmg** from the project's **Releases** page on GitHub (github.com/philipjpj/scrivoice/releases) and open it.
2. Drag **ScriVoice** to the **Applications** folder.
3. Open ScriVoice from Applications. The first time, your Mac says it **cannot verify the developer**: this is normal for apps sold outside the App Store. Click **Done**, then open **System Settings → Privacy & Security**, scroll to the bottom and click **Open Anyway** next to ScriVoice. This is needed only the first time.
4. **Permissions:** when your Mac asks, turn on ScriVoice in **System Settings → Privacy & Security**:
   - **Microphone:** to record your voice;
   - **Accessibility:** to paste the text;
   - **Input Monitoring:** for the keyboard shortcut.
5. After granting the permissions, quit ScriVoice (top icon → **Quit**) and open it again.

## 4. How to use it

1. **Click** into the chat, email or document where you want to write.
2. **Tap** the shortcut and speak, then **tap it again**: the text appears where you were typing.
   Or **hold it down** while you speak and release it at the end.
3. The text is pasted but **not sent**, so you can read it first.

| | Windows | Mac |
|---|---|---|
| Shortcut | **Ctrl + Alt + Space** | **Ctrl + Shift + Space** |
| Cancel the recording | Esc | Esc |

The **widget** shows what is happening: recording (with the volume), transcription and text pasted. You can **drag** it anywhere and **click** it to start or stop. **Right-click** the widget, or the ScriVoice icon near the clock (at the top on Mac), to open the menu: **Settings**, copy the last transcription, **About** and **Quit**.

## 5. Settings

![Settings](img/settings.png)

- **General:** interface language and **the language you speak** (Italian, English, Spanish or automatic), start with the computer.
- **Shortcuts:** click a button and press the combination you prefer.
- **Transcription:** microphone, accuracy and **personal vocabulary**. Add names and technical words you use often: they will be recognized better.
- **Corrections:** if ScriVoice always gets the same word wrong, add it here ("wrong word → right word").
- **Appearance:** dark, light or neon theme, color, size and opacity of the widget.

## 6. Troubleshooting

- **The text is not pasted (Mac):** the **Accessibility** permission is missing. Turn it on and restart ScriVoice.
- **The shortcut does nothing (Mac):** the **Input Monitoring** permission is missing.
- **"The shortcut is already used by another app" (Windows):** choose another one in *Settings → Shortcuts*.
- **The shortcut does not work in a program run as administrator (Windows):** this is a Windows protection. Use a normal program, or run ScriVoice as administrator too.
- **Some words are recognized wrongly:** add them to the personal vocabulary or to the corrections. A close microphone and a quiet room help. Bluetooth earbuds record at lower quality than the computer's microphone.
- **The text is in the wrong language:** set the language you speak in *Settings → General*.

## 7. Privacy

Your voice is transcribed **only on your computer** and is never sent to anyone. ScriVoice makes no internet connections: no accounts, no ads, no tracking.

## 8. Uninstalling

- **Windows:** Settings → Apps → Installed apps → ScriVoice → Uninstall.
- **Mac:** quit ScriVoice and drag the app to the Trash. Settings are in *~/Library/Application Support/ScriVoice*.
