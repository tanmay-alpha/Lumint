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
  const matches = text.match(/\b\d{12}\b/g);
  if (matches && matches.length > 0) return matches[0];
  const phonepeMatch = text.match(/[Tt]\d{10,15}/);
  if (phonepeMatch) return phonepeMatch[0].substring(1);
  return null;
}

function extractAmount(text: string): number | null {
  const rupeeMatch = text.match(/₹\s*([\d,]+(?:\.\d{1,2})?)/);
  if (rupeeMatch) return parseFloat(rupeeMatch[1].replace(/,/g, ''));
  const rsMatch = text.match(/(?:rs\.?|inr)\s*([\d,]+(?:\.\d{1,2})?)/i);
  if (rsMatch) return parseFloat(rsMatch[1].replace(/,/g, ''));
  const amountMatch = text.match(/(?:amount|paid|received|sent)[:\s]+(?:rs\.?|₹)?\s*([\d,]+)/i);
  if (amountMatch) return parseFloat(amountMatch[1].replace(/,/g, ''));
  return null;
}

function extractVPA(text: string): string | null {
  const vpaMatch = text.match(/[a-zA-Z0-9._-]+@[a-zA-Z][a-zA-Z0-9]+/);
  return vpaMatch ? vpaMatch[0] : null;
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
  if (t.includes('phonepe') || t.includes('phone pe')) return 'PhonePe';
  if (t.includes('google pay') || t.includes('gpay')) return 'Google Pay';
  if (t.includes('paytm')) return 'Paytm';
  if (t.includes('bhim')) return 'BHIM';
  if (t.includes('amazon pay')) return 'Amazon Pay';
  return null;
}

interface ELAResult {
  score: number;
  regionCount: number;
  maxRegionArea: number;
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
