/**
 * Client-side UPI screenshot analyzer.
 * Runs entirely in the browser using Tesseract.js (OCR) + Canvas API (ELA).
 * No backend needed. No data leaves the user's device.
 */

import Tesseract from 'tesseract.js';

export interface UPIAnalysisResult {
  verdict: 'GENUINE' | 'SUSPICIOUS' | 'HIGH_RISK' | 'NOT_UPI' | 'ERROR';
  label: string;
  score: number;
  confidence: number;
  extracted: {
    utr: string | null;
    amount: number | null;
    vpa: string | null;
    timestamp: string | null;
    app: string | null;
  };
  signals: Array<{
    check: string;
    passed: boolean;
    detail?: string;
  }>;
  ocr_text: string;
  processing_time_ms: number;
  model_version: string;
}

async function runOCR(imageFile: File): Promise<{ text: string; confidence: number }> {
  const result = await Tesseract.recognize(imageFile, 'eng');
  return {
    text: result.data.text,
    confidence: result.data.confidence / 100,
  };
}

function extractUTR(text: string): string | null {
  // NPCI standard: UPI UTR is exactly 12 digits. Reject anything else.
  // Strategy 1: UTR/Txn ID/Transaction ID/PhonePe Transaction ID context,
  // followed by digits (Tesseract may insert spaces — strip them out).
  const utrContext = [
    /(?:UTR|Txn\s*ID|Transaction\s*ID|Txn\s*Ref|UPI\s*Ref|PhonePe\s*Transaction\s*ID)[\s:.]*([\d\s]{10,25})/gi,
  ];
  for (const pattern of utrContext) {
    const matches = text.matchAll(pattern);
    for (const match of matches) {
      const digits = (match[1] || '').replace(/\D/g, '');
      if (digits.length === 12) return digits;
    }
  }
  // Strategy 2: any standalone 12-digit run in the text.
  const allNumbers = text.match(/(?<!\d)\d{12}(?!\d)/g) || [];
  if (allNumbers.length > 0) return allNumbers[0] || null;
  return null;
}

function extractAmount(text: string): number | null {
  // Strategy 1: contextual — "Rs 25,000" / "Amount: 1500" / "₹1,500"
  const contextualPatterns = [
    /(?:rs\.?|inr|₹|amount|paid|received|sent|pay)[\s.:]+([\d,]+(?:\.\d{1,2})?)/gi,
  ];
  for (const pattern of contextualPatterns) {
    const matches = text.matchAll(pattern);
    for (const match of matches) {
      const num = match[1].replace(/,/g, '');
      const parsed = parseFloat(num);
      if (!isNaN(parsed) && parsed >= 1 && parsed <= 1000000) return parsed;
    }
  }
  // Strategy 2: Indian-formatted comma numbers (25,000 / 1,50,000 / 10,00,000)
  const commaNumbers = text.match(/\d{1,2}(?:,\d{2,3})+/g) || [];
  if (commaNumbers.length > 0) {
    const parsed = commaNumbers
      .map(s => parseInt(s.replace(/,/g, ''), 10))
      .filter(n => n >= 1 && n <= 1000000)
      .sort((a, b) => b - a);
    if (parsed.length > 0) return parsed[0];
  }
  // Strategy 3 (REMOVED): the "pick any 3-7 digit number" fallback caused
  // college-ID years and roll numbers to be reported as amounts.
  return null;
}

function extractVPA(text: string): string | null {
  // Strategy 1: VPA near keyword (paid to / from / to / vpa / upi id).
  const vpaContextPatterns = [
    /(?:paid\s*to|from|to|vpa|upi\s*id)[\s:]+([a-z0-9._-]+@[a-z0-9.-]+)/gi,
  ];
  for (const pattern of vpaContextPatterns) {
    const matches = text.matchAll(pattern);
    for (const match of matches) return match[1];
  }
  // Strategy 2: any handle@domain.
  const vpaPattern = /[a-z0-9._-]{3,}@[a-z0-9.-]{2,}/gi;
  const matches = text.match(vpaPattern);
  if (matches && matches.length > 0) return matches[0];
  return null;
}

function extractTimestamp(text: string): string | null {
  const dateMatch = text.match(/\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}/i);
  if (dateMatch) return dateMatch[0];
  const slashMatch = text.match(/\d{1,2}\/\d{1,2}\/\d{2,4}/);
  if (slashMatch) return slashMatch[0];
  const timeMatch = text.match(/\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?/);
  if (timeMatch) return timeMatch[0];
  return null;
}

function detectApp(text: string): string | null {
  const t = text.toLowerCase();
  // Word boundaries prevent false matches (e.g. "phone" in an address).
  if (/\b(phonepe|phone pe|phone_pe)\b/.test(t)) return 'PhonePe';
  if (/\b(googlepay|google pay|gpay|g pay)\b/.test(t)) return 'Google Pay';
  if (/\b(paytm)\b/.test(t)) return 'Paytm';
  if (/\b(bhim)\b/.test(t)) return 'BHIM';
  if (/\b(amazonpay|amazon pay)\b/.test(t)) return 'Amazon Pay';
  return null;
}

interface ELAResult {
  score: number;
  regionCount: number;
  maxRegionArea: number;
}

async function isScreenshotLikely(img: HTMLImageElement): Promise<boolean> {
  // Screenshots have:
  // 1. Sharp edges (not blurred from camera)
  // 2. Solid color backgrounds (white/dark)
  // 3. No skin tones (not a photo of a person)
  // 4. Pixel-perfect text (not OCR-noisy)
  const canvas = document.createElement('canvas');
  canvas.width = Math.min(img.width, 400);
  canvas.height = Math.min(img.height, 400);
  const ctx = canvas.getContext('2d');
  if (!ctx) return true; // Assume yes if we can't analyze

  ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
  const data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;

  const totalPixels = canvas.width * canvas.height;
  let whitePixels = 0;
  let darkPixels = 0;
  let skinTonePixels = 0;

  for (let i = 0; i < data.length; i += 4) {
    const r = data[i];
    const g = data[i + 1];
    const b = data[i + 2];
    // White/near-white (typical screenshot background)
    if (r > 230 && g > 230 && b > 230) whitePixels++;
    // Dark/near-black
    if (r < 25 && g < 25 && b < 25) darkPixels++;
    // Skin tone (rough): high R, mid G, lower B, R>G>B
    if (r > 180 && g > 130 && g < 200 && b > 100 && b < 160 && r > g && g > b) {
      skinTonePixels++;
    }
  }

  const whiteRatio = whitePixels / totalPixels;
  const darkRatio = darkPixels / totalPixels;
  const skinRatio = skinTonePixels / totalPixels;

  // Reject if too much skin tone (photo of a person, like an ID card).
  if (skinRatio > 0.15) return false;
  // Screenshots typically have either lots of white OR lots of dark.
  if (whiteRatio + darkRatio < 0.40) return false;

  return true;
}

async function computeELA(imageFile: File): Promise<ELAResult> {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => {
      const canvas = document.createElement('canvas');
      canvas.width = img.width;
      canvas.height = img.height;
      const ctx = canvas.getContext('2d');
      if (!ctx) return resolve({ score: 0, regionCount: 0, maxRegionArea: 0 });
      ctx.drawImage(img, 0, 0);
      const originalData = ctx.getImageData(0, 0, canvas.width, canvas.height).data;

      const tempCanvas = document.createElement('canvas');
      tempCanvas.width = img.width;
      tempCanvas.height = img.height;
      const tempCtx = tempCanvas.getContext('2d');
      if (!tempCtx) return resolve({ score: 0, regionCount: 0, maxRegionArea: 0 });
      tempCtx.drawImage(img, 0, 0);
      const jpegUrl = tempCanvas.toDataURL('image/jpeg', 0.9);

      const resavedImg = new Image();
      resavedImg.onload = () => {
        const resaveCtx = canvas.getContext('2d');
        if (!resaveCtx) return resolve({ score: 0, regionCount: 0, maxRegionArea: 0 });
        resaveCtx.drawImage(resavedImg, 0, 0);
        const resavedData = resaveCtx.getImageData(0, 0, canvas.width, canvas.height).data;

        const width = canvas.width;
        const height = canvas.height;
        const threshold = 25;
        const visited = new Uint8Array(width * height);
        let totalDiff = 0;
        let regionCount = 0;
        let maxRegionArea = 0;

        for (let i = 0; i < originalData.length; i += 4) {
          const r = Math.abs(originalData[i] - resavedData[i]);
          const g = Math.abs(originalData[i + 1] - resavedData[i + 1]);
          const b = Math.abs(originalData[i + 2] - resavedData[i + 2]);
          totalDiff += (r + g + b) / 3;
        }

        for (let y = 0; y < height; y++) {
          for (let x = 0; x < width; x++) {
            const idx = y * width + x;
            if (visited[idx]) continue;
            const pixelIdx = idx * 4;
            const r = Math.abs(originalData[pixelIdx] - resavedData[pixelIdx]);
            const g = Math.abs(originalData[pixelIdx + 1] - resavedData[pixelIdx + 1]);
            const b = Math.abs(originalData[pixelIdx + 2] - resavedData[pixelIdx + 2]);
            const diff = (r + g + b) / 3;
            if (diff > threshold) {
              let regionSize = 0;
              const stack: Array<[number, number]> = [[x, y]];
              while (stack.length > 0) {
                const [cx, cy] = stack.pop()!;
                const ci = cy * width + cx;
                if (cx < 0 || cx >= width || cy < 0 || cy >= height) continue;
                if (visited[ci]) continue;
                const cpi = ci * 4;
                const cr = Math.abs(originalData[cpi] - resavedData[cpi]);
                const cg = Math.abs(originalData[cpi + 1] - resavedData[cpi + 1]);
                const cb = Math.abs(originalData[cpi + 2] - resavedData[cpi + 2]);
                const cd = (cr + cg + cb) / 3;
                if (cd <= threshold) continue;
                visited[ci] = 1;
                regionSize++;
                stack.push([cx + 1, cy], [cx - 1, cy], [cx, cy + 1], [cx, cy - 1]);
              }
              if (regionSize > 100) {
                regionCount++;
                if (regionSize > maxRegionArea) maxRegionArea = regionSize;
              }
            }
          }
        }

        const avgEla = totalDiff / (width * height);
        resolve({
          score: Math.min(1.0, avgEla / 50),
          regionCount,
          maxRegionArea: maxRegionArea / (width * height),
        });
      };
      resavedImg.src = jpegUrl;
    };
    img.onerror = () => resolve({ score: 0, regionCount: 0, maxRegionArea: 0 });
    img.src = URL.createObjectURL(imageFile);
  });
}

export async function analyzeUPIClientSide(imageFile: File): Promise<UPIAnalysisResult> {
  const startTime = performance.now();

  try {
    const ocr = await runOCR(imageFile);
    const text = ocr.text;

    if (!text || text.trim().length < 5) {
      return {
        verdict: 'NOT_UPI',
        label: 'Not a UPI Screenshot',
        score: 0,
        confidence: 0,
        extracted: { utr: null, amount: null, vpa: null, timestamp: null, app: null },
        signals: [{ check: 'No readable text found', passed: false, detail: 'Image may be blank, rotated, or not a payment screenshot' }],
        ocr_text: text || '',
        processing_time_ms: Math.round(performance.now() - startTime),
        model_version: 'client-v1.0-ocr-only',
      };
    }

    // Screenshot detection: reject photos of ID cards / documents / people.
    // Skin-tone-heavy or natural-photo images are not payment screenshots.
    const imgEl = new Image();
    await new Promise<void>((resolve) => {
      imgEl.onload = () => resolve();
      imgEl.onerror = () => resolve();
      imgEl.src = URL.createObjectURL(imageFile);
    });
    if (imgEl.width > 0) {
      const isScreenshot = await isScreenshotLikely(imgEl);
      if (!isScreenshot) {
        return {
          verdict: 'NOT_UPI',
          label: 'Not a UPI Screenshot',
          score: 0,
          confidence: 0,
          extracted: { utr: null, amount: null, vpa: null, timestamp: null, app: null },
          signals: [{ check: 'Image appears to be a photo, not a screenshot', passed: false, detail: 'UPI Shield analyzes payment screenshots, not photos of documents or ID cards.' }],
          ocr_text: text.substring(0, 1000),
          processing_time_ms: Math.round(performance.now() - startTime),
          model_version: 'client-v1.0-screenshot-fail',
        };
      }
    }

    // UPI-presence gate. Non-UPI images (college IDs, PDFs, random photos) fail
    // here and never reach extraction/ELA, so we don't fabricate amounts.
    const textLower = text.toLowerCase();
    const hasPaymentKeyword = /(?:amount|paid|received|sent|debited|credited|utr|transaction|upi|@)/i.test(text);
    const hasUPIApp = /(phonepe|google\s*pay|gpay|paytm|bhim|amazon\s*pay)/i.test(textLower);
    const hasVPA = /@/.test(text);
    const hasUTR = /\d{10,18}/.test(text);
    const hasRupee = /(rs\.?|inr|₹)/i.test(text);

    const upiSignals = [hasPaymentKeyword, hasUPIApp, hasVPA, hasUTR, hasRupee].filter(Boolean).length;
    if (upiSignals < 4) {
      const missing: Array<{ check: string; passed: false }> = [];
      if (!hasPaymentKeyword) missing.push({ check: 'No payment keywords', passed: false });
      if (!hasUPIApp) missing.push({ check: 'No UPI app detected', passed: false });
      if (!hasVPA) missing.push({ check: 'No @VPA detected', passed: false });
      return {
        verdict: 'NOT_UPI',
        label: 'Not a UPI Screenshot',
        score: 0,
        confidence: ocr.confidence,
        extracted: { utr: null, amount: null, vpa: null, timestamp: null, app: null },
        signals: [
          { check: 'Missing UPI evidence', passed: false, detail: "This doesn't appear to be a UPI payment screenshot. Look for UTR, amount, or @VPA." },
          ...missing,
        ],
        ocr_text: text.substring(0, 1000),
        processing_time_ms: Math.round(performance.now() - startTime),
        model_version: 'client-v1.0-gate-fail',
      };
    }

    const utr = extractUTR(text);
    const amount = extractAmount(text);
    const vpa = extractVPA(text);
    const timestamp = extractTimestamp(text);
    const app = detectApp(text);
    const ela = await computeELA(imageFile);

    const signals: UPIAnalysisResult['signals'] = [];
    let score = 0;

    if (utr) {
      signals.push({ check: `UTR: ${utr}`, passed: true });
    } else {
      signals.push({ check: 'UTR missing or invalid', passed: false });
      score += 25;
    }

    if (amount && amount > 0) {
      signals.push({ check: `Amount: Rs ${amount}`, passed: true });
    } else {
      signals.push({ check: 'Amount not detected', passed: false });
      score += 15;
    }

    if (vpa) {
      signals.push({ check: `VPA: ${vpa}`, passed: true });
    } else {
      signals.push({ check: 'VPA not detected', passed: false });
      score += 20;
    }

    if (app) {
      signals.push({ check: `Detected: ${app}`, passed: true });
    } else {
      signals.push({ check: 'No UPI app detected', passed: false });
      score += 10;
    }

    if (ela.score > 0.20) {
      signals.push({ check: `Pixel tampering detected (ELA: ${ela.score.toFixed(3)})`, passed: false, detail: `${ela.regionCount} tampered regions` });
      score += 30;
    } else if (ela.score > 0.10) {
      signals.push({ check: `Moderate ELA: ${ela.score.toFixed(3)}`, passed: false });
      score += 15;
    } else {
      signals.push({ check: `No tampering (ELA: ${ela.score.toFixed(3)})`, passed: true });
    }

    if (ocr.confidence < 0.40) {
      signals.push({ check: `Low OCR confidence: ${Math.round(ocr.confidence * 100)}%`, passed: false });
      score += 10;
    }

    let verdict: UPIAnalysisResult['verdict'];
    let label: string;
    if (score >= 60) {
      verdict = 'HIGH_RISK';
      label = 'High Risk - Likely Tampered';
    } else if (score >= 30) {
      verdict = 'SUSPICIOUS';
      label = 'Suspicious - Check Carefully';
    } else {
      verdict = 'GENUINE';
      label = 'Looks Genuine';
    }

    return {
      verdict,
      label,
      score: Math.min(100, score),
      confidence: ocr.confidence,
      extracted: { utr, amount, vpa, timestamp, app },
      signals,
      ocr_text: text.substring(0, 1000),
      processing_time_ms: Math.round(performance.now() - startTime),
      model_version: 'client-v1.0-heuristic+ela',
    };
  } catch (err: any) {
    return {
      verdict: 'ERROR',
      label: 'Analysis Failed',
      score: 0,
      confidence: 0,
      extracted: { utr: null, amount: null, vpa: null, timestamp: null, app: null },
      signals: [{ check: 'Error', passed: false, detail: err.message }],
      ocr_text: '',
      processing_time_ms: Math.round(performance.now() - startTime),
      model_version: 'client-v1.0-error',
    };
  }
}
