import { TestBed } from '@angular/core/testing';

import { PilotSubmissionService, PilotSighting } from './pilot-submission.service';

const STORAGE_KEY = 'orcast_pilot_sightings';

const sampleEntry: Omit<PilotSighting, 'id' | 'submittedAt'> = {
  place: 'Lime Kiln Point',
  observedAt: '2026-08-12T09:30',
  behavior: 'traveling',
  groupSize: 4,
  notes: 'Heading north along the west side.'
};

describe('PilotSubmissionService', () => {
  let service: PilotSubmissionService;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({});
    service = TestBed.inject(PilotSubmissionService);
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('returns [] when storage is empty', () => {
    expect(service.list()).toEqual([]);
  });

  it('save() persists and list() returns it', () => {
    const saved = service.save(sampleEntry);

    expect(saved.id).toBeTruthy();
    expect(saved.submittedAt).toBeTruthy();
    expect(saved.place).toBe('Lime Kiln Point');

    const listed = service.list();
    expect(listed.length).toBe(1);
    expect(listed[0].id).toBe(saved.id);
    expect(listed[0].behavior).toBe('traveling');
  });

  it('prepends the most recent submission', () => {
    const first = service.save({ ...sampleEntry, place: 'First' });
    const second = service.save({ ...sampleEntry, place: 'Second' });

    const listed = service.list();
    expect(listed.length).toBe(2);
    expect(listed[0].id).toBe(second.id);
    expect(listed[1].id).toBe(first.id);
  });

  it('clear() empties the list', () => {
    service.save(sampleEntry);
    expect(service.list().length).toBe(1);

    service.clear();
    expect(service.list()).toEqual([]);
  });

  it('list() returns [] when storage is corrupt', () => {
    localStorage.setItem(STORAGE_KEY, '{ not valid json');
    expect(service.list()).toEqual([]);
  });
});
