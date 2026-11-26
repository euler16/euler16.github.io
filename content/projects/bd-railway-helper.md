---
problem: "Booking a ticket on Bangladesh Railway's e-ticket site means repeating the same search, train and seat steps every time — usually against the clock. BD Railway Helper automates the tedious, non-sensitive parts of booking your own ticket."
platform: "Google Chrome · Manifest V3"
---

## What it does

BD Railway Helper is a personal Chrome extension for the Bangladesh Railway e-ticket site. It fills in the search form, finds the train and class you chose, locks seats, and then **stops at the OTP screen** so you complete the booking yourself.

Release notes add departure-time-based train selection, automatic detection of train information, on-page progress tracking, and seat selection that can split a booking across compartments when no single coach has enough free seats.

## Deliberate boundaries

The most important design decision is what the extension refuses to do. It never touches:

- login credentials
- CAPTCHA
- one-time passwords (OTP)
- payment

Automation that stays clear of authentication and payment keeps the user in control of every security-sensitive step, avoids storing secrets, and respects the protections the ticketing site puts in place. It is a tool for booking your own ticket, not for bulk purchasing.

## How it is built

The extension uses the Manifest V3 model: a background service worker coordinates the flow, a content script interacts with the page, and a small popup holds your preferences.

```text
manifest.json     MV3 manifest and permissions
background.js     service worker — orchestrates the booking flow
content.js        runs in the e-ticket page
flow.js           step-by-step booking logic
selectors.js      DOM selectors kept in one place
overlay.js        on-page progress overlay
popup.*           settings UI
```

Keeping the site's selectors in a single file means a change to the e-ticket page's markup is a one-file fix.
