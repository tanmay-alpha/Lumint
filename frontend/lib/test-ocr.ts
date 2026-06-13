import Tesseract from 'tesseract.js';

export async function debugOCR(imageFile: File): Promise<void> {
  console.log('=== Tesseract OCR Debug ===');
  const result = await Tesseract.recognize(imageFile, 'eng');
  const text = result.data.text;
  console.log('Confidence:', result.data.confidence);
  console.log('--- RAW TEXT START ---');
  console.log(text);
  console.log('--- RAW TEXT END ---');
  console.log('--- LINES ---');
  text.split('\n').forEach((line, i) => {
    console.log(`Line ${i}: "${line}"`);
  });
  console.log('--- 12-DIGIT CANDIDATES ---');
  const candidates = text.match(/\d{10,15}/g) || [];
  candidates.forEach(c => console.log(`  ${c} (len=${c.length})`));
  console.log('--- AMOUNT CANDIDATES ---');
  const amounts = text.match(/(?:rs\.?|inr|₹)\s*[\d,]+(?:\.\d+)?/gi) || [];
  amounts.forEach(a => console.log(`  ${a}`));
  console.log('--- VPA CANDIDATES ---');
  const vpas = text.match(/[a-z0-9._-]+@[a-z0-9.-]+/gi) || [];
  vpas.forEach(v => console.log(`  ${v}`));
}
