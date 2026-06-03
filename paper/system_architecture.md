# System Architecture

```mermaid
graph TD
    subgraph Input Modalities
        URL[Phishing URL]
        Doc[Identity/Invoice PDF]
        UPI[UPI Screenshot]
        Context[Fraud DNA Graph]
    end

    subgraph Analyzers
        Phish[PhishShield]
        DocS[DocShield]
        UPIS[UPI Shield]
        DNA[Fraud DNA]
    end

    URL --> Phish
    Doc --> DocS
    UPI --> UPIS
    Context --> DNA

    Phish --> Fusion[Explainable Cross-Modal Fusion Engine]
    DocS --> Fusion
    UPIS --> Fusion
    DNA --> Fusion

    Fusion --> Dec[Risk Decision & Feature Attribution]
    
    subgraph Consensus & Verification
        Dec --> Agreement[Consensus & Agreement Layer]
        VT[VirusTotal Wrapper] --> Agreement
        US[Urlscan Wrapper] --> Agreement
    end
```

## Modular Analysis Engines

### 1. DocShield
Performs metadata sanitization, structural analysis, and OCR forgery scanning on PDF/Image documents.

### 2. PhishShield
Scans incoming URLs for high-risk domains, IP addresses, subdomains, and matches against known threat lists.

### 3. UPI Shield
Analyzes transaction screenshots:
- UTR validation and format checking.
- Error Level Analysis (ELA) for image compression inconsistencies.
- Font family and size variance checks.
- App shell signature recognition.

### 4. Fraud DNA
Maintains a contextual relationship database linking shared components (URLs, emails, phone numbers) across past fraud cases.
