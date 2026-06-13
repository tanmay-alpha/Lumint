import { Metadata } from "next";

export const metadata: Metadata = {
  title: "About Lumint",
  description: "Privacy-first scam detection suite",
};

export default function About() {
  return (
    <main className="min-h-screen bg-[var(--canvas)] py-12 px-4">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold text-[var(--text-1)] mb-8">About Lumint</h1>

        <section className="mb-8">
          <h2 className="text-xl font-semibold text-[var(--text-1)] mb-3">What is Lumint?</h2>
          <p className="text-[var(--text-2)] leading-relaxed">
            Lumint is a free, privacy-first scam detection suite. All analysis runs in your browser —
            no images, URLs, or documents are uploaded to any server. Your data stays on your device.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold text-[var(--text-1)] mb-3">How the Shields Work</h2>

          <h3 className="text-base font-semibold text-[var(--brand)] mt-4 mb-2">UPI Shield</h3>
          <p className="text-[var(--text-2)] leading-relaxed">
            Uses Tesseract.js OCR to read UPI payment screenshots and extracts: UTR (12-digit
            transaction ID), amount, sender UPI, receiver UPI, and payment app. Cross-checks
            against 4 of 5 UPI signal heuristics (payment keywords, app name, @VPA, UTR pattern,
            rupee symbol) to reject non-UPI images like college IDs or random photos.
          </p>

          <h3 className="text-base font-semibold text-[var(--brand)] mt-4 mb-2">DocShield</h3>
          <p className="text-[var(--text-2)] leading-relaxed">
            Detects tampering in documents (Aadhaar, PAN, passport, invoices, certificates) using
            Error Level Analysis (ELA) and text pattern recognition. Runs OCR + pixel-difference
            analysis entirely in the browser.
          </p>

          <h3 className="text-base font-semibold text-[var(--brand)] mt-4 mb-2">PhishShield</h3>
          <p className="text-[var(--text-2)] leading-relaxed">
            Analyzes URLs for phishing indicators: suspicious TLDs, typosquatting (paypa1.com),
            IP-address hosting, and HTTPS misuse. Gives each URL a risk score and explanation.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold text-[var(--text-1)] mb-3">Privacy</h2>
          <p className="text-[var(--text-2)] leading-relaxed">
            Everything runs locally in your browser. We do not store your scans, images, or URLs.
            Your data never leaves your device. (The UPI and Doc analyzers are 100% client-side;
            the dashboard pages call a backend for analytics data only.)
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold text-[var(--text-1)] mb-3">Limitations</h2>
          <p className="text-[var(--text-2)] leading-relaxed">
            Lumint is a first-pass filter, not a definitive verdict. Always verify with the official
            source (your bank, the official website, the issuing authority). OCR accuracy depends
            on image quality — blurry, low-light, or stylized screenshots may produce poor results.
          </p>
        </section>
      </div>
    </main>
  );
}
