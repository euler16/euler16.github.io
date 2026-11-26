---
problem: "Most vocabulary apps want an account, a network connection and access to more of your phone than a word list needs. WordSmrt is built on the opposite assumption: learning data is personal, so it should never leave the device."
platform: "Android"
---

## What it does

WordSmrt is an Android app for learning English vocabulary, with Bangla meanings alongside English definitions. It ships with roughly 1,700 words and works completely offline.

Every word moves through four states — **New → Learning → Review → Mastered** — and words you struggle with are tracked separately. A spaced-repetition scheduler decides when a mastered word should come back for review, so practice time goes to the words you are about to forget.

## Key features

- Flashcards with persistent learning states
- Four-option vocabulary quizzes
- Spaced-repetition review scheduling
- Progress analytics and a mastery distribution view
- Bilingual English–Bangla dictionary search
- Pronunciation support
- Word of the Day, daily goals and study streaks
- An AMOLED-friendly dark interface

## Privacy by design

WordSmrt requests **no Android permissions** to function. There are no accounts, no servers and no cloud sync; progress is stored locally with Room and DataStore. With no network path out, there is very little to attack and nothing to leak — a deliberate design decision rather than an afterthought.

## Architecture

The UI is written in Jetpack Compose with Material 3. State flows one way through Kotlin `StateFlow`, so screens re-render reactively as the learning database changes.

```text
Compose UI  ──observes──▶  ViewModel (StateFlow)
                               │
                               ▼
                    Repository ─── Room (words, states, history)
                               └── DataStore (settings, goals, streaks)
```
