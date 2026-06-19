import { Injectable } from '@angular/core';

export interface PilotSighting {
  id: string;
  place: string;
  observedAt: string;
  behavior: string;
  groupSize: number | null;
  notes: string;
  submittedAt: string;
}

const STORAGE_KEY = 'orcast_pilot_sightings';

/**
 * Stores pilot sighting submissions on the device (localStorage) for the
 * August pilot preview. Falls back to an in-memory array when localStorage
 * is unavailable (SSR, tests, privacy modes).
 */
@Injectable({ providedIn: 'root' })
export class PilotSubmissionService {
  private memory: PilotSighting[] = [];

  list(): PilotSighting[] {
    const store = this.storage();
    if (!store) {
      return [...this.memory];
    }
    try {
      const raw = store.getItem(STORAGE_KEY);
      if (!raw) {
        return [];
      }
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? (parsed as PilotSighting[]) : [];
    } catch {
      return [];
    }
  }

  save(entry: Omit<PilotSighting, 'id' | 'submittedAt'>): PilotSighting {
    const saved: PilotSighting = {
      ...entry,
      id: this.makeId(),
      submittedAt: new Date().toISOString()
    };

    const next = [saved, ...this.list()];
    this.persist(next);
    return saved;
  }

  clear(): void {
    this.persist([]);
  }

  private persist(entries: PilotSighting[]): void {
    this.memory = [...entries];
    const store = this.storage();
    if (!store) {
      return;
    }
    try {
      store.setItem(STORAGE_KEY, JSON.stringify(entries));
    } catch {
      // Keep the in-memory copy when persistence fails (e.g. quota, private mode).
    }
  }

  private storage(): Storage | null {
    try {
      if (typeof localStorage === 'undefined') {
        return null;
      }
      return localStorage;
    } catch {
      return null;
    }
  }

  private makeId(): string {
    try {
      if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
        return crypto.randomUUID();
      }
    } catch {
      // fall through to manual id
    }
    return `pilot-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
  }
}
