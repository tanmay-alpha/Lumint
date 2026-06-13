const STORAGE_KEY = 'lumint_scan_history';
const MAX_HISTORY = 50;

export interface ScanHistoryEntry {
  id: string;
  shield: 'upi' | 'doc' | 'phish';
  timestamp: number;
  verdict: string;
  label: string;
  score: number;
  fileName?: string;
  url?: string;
}

export function saveScan(entry: Omit<ScanHistoryEntry, 'id' | 'timestamp'>): ScanHistoryEntry {
  const newEntry: ScanHistoryEntry = {
    ...entry,
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    timestamp: Date.now(),
  };
  if (typeof window === 'undefined') return newEntry;
  try {
    const history = getScanHistory();
    history.unshift(newEntry);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(history.slice(0, MAX_HISTORY)));
  } catch (e) {
    console.warn('localStorage unavailable:', e);
  }
  return newEntry;
}

export function getScanHistory(): ScanHistoryEntry[] {
  if (typeof window === 'undefined') return [];
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
  } catch {
    return [];
  }
}

export function clearScanHistory(): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {}
}
