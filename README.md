# 👁 Eye Timer

**A free Mac menu bar app that actually respects when you're away.**

Every 20 minutes, look 20 feet away for 20 seconds — the NHS-recommended 20-20-20 rule for digital eye strain. Eye Timer is the only app that pauses when you lock your screen and resets when you come back.

---

## The problem with every other app

Every 20-20-20 timer has the same flaw: **it keeps counting when your screen is locked.**

Come back from a meeting or a coffee break and your "20-minute window" is already depleted — even though your eyes were resting the whole time.

Eye Timer fixes that.

---

## What it does

- **Lives in your menu bar** — `👁 18:42` counting down silently, no Dock icon
- **Auto-starts on login** — install once, it runs forever in the background
- **Pauses on screen lock** — lock your Mac and the timer stops
- **Resets on unlock** — come back to a fresh 20 minutes, every time
- **Native macOS notifications** — a gentle nudge at break time, with a rotating tip
- **20-second rest countdown** — switches to `🌿 18s` so you know when to look back
- **Daily break counter** — click the icon to see how many breaks you've taken today

---

## Screenshot

```
┌─────────────────────────────────────────┐
│  ♪  ⌨  🔋  📶  👁 18:42               │  ← menu bar
├─────────────────────────────────────────┤
│  Work — 18:42 until break               │
│  Breaks today: 3                        │
│  ─────────────────────────────────────  │
│  ⏸  Pause                              │
│  ↺  Reset                              │
│  ─────────────────────────────────────  │
│  Quit                                   │
└─────────────────────────────────────────┘
```

---

## Install

### Option 1 — Download (recommended)
Download the latest `.dmg` from [Releases](../../releases), open it, and drag Eye Timer to your Applications folder. That's it.

> **First launch:** macOS may show an "unidentified developer" warning.  
> Right-click the app → **Open** → **Open** to bypass it.

### Option 2 — Run from source

```bash
# 1. Clone the repo
git clone https://github.com/Sandeeparcot/eye-timer.git
cd eye-timer

# 2. Install dependencies
pip3 install rumps pyobjc-framework-Cocoa

# 3. Run
python3 eye_timer.py
```

The `👁 20:00` icon appears in your menu bar immediately.

**Optional — auto-start on login:**
```bash
chmod +x setup.sh && ./setup.sh
```

---

## Requirements

- macOS 12.0 (Monterey) or later
- Python 3.9+ (for running from source)

---

## Why I built this

My left eye was flickering for over a month.

My optometrist told me to do the 20-20-20 rule — look 20 feet away for 20 seconds, every 20 minutes. Simple enough. So I downloaded every timer app I could find.

They all had the same problem. Lock your screen, step away, come back — and the 20-minute window had ticked down while you were gone. That's not how eye rest works.

So I built one that does it right. It took a weekend. It's free. It's open source.

If your eyes hurt at the end of the day, this is for you.

---

## How it works

Eye Timer hooks into macOS's native distributed notification system to detect screen lock and unlock events — the same mechanism macOS uses internally.

```python
# Listens for native macOS lock/unlock events
nc = NSDistributedNotificationCenter.defaultCenter()
nc.addObserver_selector_name_object_(
    observer, "handleLock:",   "com.apple.screenIsLocked",   None
)
nc.addObserver_selector_name_object_(
    observer, "handleUnlock:", "com.apple.screenIsUnlocked", None
)
```

On lock: timer pauses.  
On unlock: timer resets to a fresh 20 minutes and resumes automatically.

Full architecture notes in [INSTRUCTIONS.md](INSTRUCTIONS.md).

---

## Roadmap

- [x] Menu bar countdown
- [x] Auto-start on launch
- [x] Screen lock / unlock detection
- [x] Native notifications with rotating tips
- [x] Daily break counter
- [ ] Custom intervals (preferences panel)
- [ ] Do Not Disturb / Focus mode awareness
- [ ] Blink reminder (every 5 minutes)
- [ ] Weekly break report
- [ ] Calendar integration (auto-pause in meetings)
- [ ] Apple Health integration
- [ ] Optometrist-designed exercise library

---

## Contributing

PRs welcome — especially for the roadmap items above.

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/custom-intervals`)
3. Commit your changes
4. Open a pull request

Please read [INSTRUCTIONS.md](INSTRUCTIONS.md) for the code architecture before diving in.

---

## Building from source

```bash
pip3 install py2app rumps pyobjc-framework-Cocoa
chmod +x build.sh && ./build.sh
```

Produces `dist/Eye Timer.app` and `EyeTimer-1.0.0.dmg`.  
See [INSTRUCTIONS.md](INSTRUCTIONS.md) for signing and notarisation.

---

## Licence

Apache 2.0 — see [LICENSE](LICENSE).

You're free to use, modify, and redistribute the code.  
**"Eye Timer"** is a trademark of Sandeep Arcot — forks must use a different name.  
See [NOTICE](NOTICE) for details.

---

## The science

Digital eye strain (asthenopia) affects an estimated 65% of adults who use screens regularly. Symptoms include eye fatigue, headaches, blurred vision, and dry eyes.

The 20-20-20 rule — recommended by the NHS, the American Optometric Association, and most optometrists — is the simplest evidence-based intervention: every 20 minutes of screen time, look at something at least 20 feet away for 20 seconds. This relaxes the ciliary muscles that control lens focus and reduces cumulative strain.

Eye Timer makes it automatic.

---

⭐ **If this helps your eyes, a star helps others find it.**

*Built by [Sandeep Arcot](https://github.com/Sandeeparcot) · [eyetimer.app](https://eyetimer.app) · Free forever*
