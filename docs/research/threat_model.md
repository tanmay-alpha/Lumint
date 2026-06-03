# Lumint Threat Model

This document outlines the threat model for the **Lumint** platform, defining the attackers, target assets, boundaries, and overall security scope.

## 1. Attacker Model
We categorize potential adversaries into three tiers based on resources and sophistication:

| Attacker Class | Motivation | Sophistication | Typical Capabilities |
| :--- | :--- | :--- | :--- |
| **Script Kiddies / Ad-hoc Scammers** | Immediate financial theft | Low | Modifying transaction screenshots in Canva, registering basic lookalike URLs. |
| **Organized Fraud Rings** | Systemic credential harvesting | Medium | Distributed phishing campaigns, automated bulk receipt generation, stripping EXIF metadata. |
| **State-Sponsored / Advanced Groups** | Disrupting financial infrastructure | High | Advanced zero-day spoofs, ELA-resistant document edits, domain-generation algorithms (DGA). |

---

## 2. Target Assets
* **User Transaction Veracity**: Ensuring UPI transaction receipts submitted to merchants actually correspond to real payments.
* **Organizational Integrity**: Scanned business documents, tax compliance forms, and identification files processed by DocShield.
* **Attributed Threat Graph**: The Fraud DNA relationship nodes and campaign clusters which detail the attribution and TTPs of active attackers.

---

## 3. Assumptions & Trust Boundaries
* **Input Integrity**: The backend assumes that the file uploads and URL inputs are received via secure, authenticated routes (e.g. valid merchant dashboards).
* **Base OS Security**: The host OS environment running uvicorn/FastAPI is assumed to be secure and not pre-compromised.
* **Mock Isolation**: The mock execution paths used for API fallback do not expose real secrets.

---

## 4. Limitations & Vulnerabilities
* **Adversarial OCR Evasion**: Attackers using customized typography or layout spacing may partially evade basic OCR parsing rules.
* **ELA Limitations**: Double-compressed images or high-compression WebP/JPEG files can introduce compression artifacts that affect the accuracy of Error Level Analysis (ELA).
* **Attribution Blindness**: If attackers change their infrastructure (IPs, email domains) completely between events, Fraud DNA may not link them without shared behavioral keys.

---

## 5. Non-Goals
* **Active Intrusion Prevention**: Lumint is an intelligence and forensic platform. It does not actively block IP addresses or take down websites.
* **Cryptographic Signing of Receipts**: Lumint does not issue cryptographic payment signatures; it validates the visual and structural artifacts of receipts post-execution.
