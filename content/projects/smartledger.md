---
problem: "Many small shops and wholesalers keep stock, sales and customer dues on paper or in spreadsheets, and cannot rely on a constant internet connection. SmartLedger puts point-of-sale and bookkeeping on an Android device that works fully offline."
platform: "Android 10+ · phones, tablets, foldables"
---

## What it does

SmartLedger is an offline-first business management and point-of-sale app for retailers, wholesalers and small business owners. The internet is only needed for the optional encrypted backup to Google Drive.

## Key features

- **Inventory** — product catalogue, categories and brands, SKUs, barcode and QR support, stock adjustments with history, low-stock alerts
- **Sales & POS** — invoices, credit sales, partial payments, discounts and taxes, sales returns
- **Purchases** — purchase entry and history, purchase returns, supplier dues
- **Customers & suppliers** — profiles, outstanding dues, payment and purchase history
- **Finance** — income and expenses, investments, cash flow, profit and loss, ROI
- **Reports** — revenue, profit, sales trends, inventory, customer and supplier reports
- **Printing** — Bluetooth, USB and Wi-Fi thermal printers over ESC/POS, plus A4 PDF invoices

## Security

A ledger holds exactly the data a shop owner would least like to lose or leak, so the security model is part of the core design:

- The local database is encrypted with **SQLCipher**
- Keys are protected by the **Android Keystore**
- The app can be locked with a **PIN or biometrics**
- Google Drive backups are **encrypted** before they leave the device

## Architecture

The codebase follows Clean Architecture with MVVM: Compose screens observe ViewModels, use cases hold business rules, and repositories sit in front of Room. Dependencies are wired with Hilt; long-running work such as backups runs through WorkManager, and barcode scanning uses CameraX.

## Roadmap

Planned but not yet built: multi-business support, cloud sync and OCR, among others. See the repository README for the current list.
