import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';

import { BackendService } from './backend.service';

describe('BackendService', () => {
  let service: BackendService;
  let httpMock: HttpTestingController;
  const backendUrl = 'http://127.0.0.1:8080';

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [BackendService]
    });
    service = TestBed.inject(BackendService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('fetches AWS backend health', () => {
    service.getHealth().subscribe(health => {
      expect(health.status).toBe('healthy');
    });

    const req = httpMock.expectOne(`${backendUrl}/health`);
    expect(req.request.method).toBe('GET');
    req.flush({ status: 'healthy' });
  });

  it('maps verified sightings from AWS backend', () => {
    service.getHistoricalSightings().subscribe(sightings => {
      expect(sightings.length).toBe(1);
      expect(sightings[0].id).toBe('obis:OBIS_2024_001');
      expect(sightings[0].behavior).toBe('feeding');
      expect(sightings[0].year).toBe(2024);
    });

    const req = httpMock.expectOne(`${backendUrl}/api/verified-sightings`);
    expect(req.request.method).toBe('GET');
    req.flush({
      sightings: [
        {
          sighting_id: 'obis:OBIS_2024_001',
          latitude: 48.5158,
          longitude: -123.1526,
          observation_timestamp: '2024-06-15T14:30:00Z',
          behavior_primary: 'foraging',
          pod_size: 8,
          data_quality_score: 0.95,
          location_name: 'Lime Kiln Point'
        }
      ]
    });
  });

  it('maps live hydrophones from AWS backend', () => {
    service.getHydrophoneData().subscribe(hydrophones => {
      expect(hydrophones.length).toBe(1);
      expect(hydrophones[0].status).toBe('online');
      expect(hydrophones[0].streamUrl).toContain('orcasound');
    });

    const req = httpMock.expectOne(`${backendUrl}/api/live-hydrophones`);
    expect(req.request.method).toBe('GET');
    req.flush({
      hydrophones: [
        {
          id: 'rpi_orcasound_lab',
          name: 'Orcasound Lab',
          latitude: 48.5583,
          longitude: -123.1736,
          status: 'online',
          detecting: false,
          streamUrl: 'https://live.orcasound.net/listen/orcasound-lab'
        }
      ]
    });
  });

  it('maps realtime sighting events to Detection interface', () => {
    service.getRecentDetections().subscribe(detections => {
      expect(detections.length).toBe(1);
      expect(detections[0].hydrophone).toBe('Lime Kiln Point');
      expect(detections[0].callType).toBe('unknown');
    });

    const req = httpMock.expectOne(`${backendUrl}/api/realtime/events`);
    expect(req.request.method).toBe('GET');
    req.flush({
      events: [
        {
          id: 'event-1',
          event_type: 'sighting',
          source: 'local_obis',
          location_name: 'Lime Kiln Point',
          confidence: 0.91,
          timestamp: '2026-06-13T10:00:00Z'
        }
      ],
      stream_active: false,
      data_freshness: 'historical'
    });
  });

  it('requests spatial forecast for ML predictions', () => {
    service.generateMLPredictions('ensemble', 24, 0.5).subscribe(prediction => {
      expect(prediction.model).toBe('ensemble');
      expect(prediction.predictions.length).toBe(1);
      expect(prediction.metadata.maxProbability).toBe(0.81);
    });

    const req = httpMock.expectOne(`${backendUrl}/forecast/spatial`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.hours).toBe(24);
    req.flush({
      grid_points: [
        { lat: 48.5158, lng: -123.1526, probability: 0.81 },
        { lat: 48.6, lng: -123.0, probability: 0.25 }
      ]
    });
  });

  it('generates probability reports', () => {
    service.generateProbabilityReport(0.6).subscribe(report => {
      expect(report.report_id).toBe('report_123');
      expect(report.hotspots[0].name).toBe('Lime Kiln Point');
    });

    const req = httpMock.expectOne(`${backendUrl}/api/reports/probability`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.min_confidence).toBe(0.6);
    req.flush({
      report: {
        report_id: 'report_123',
        generated_at: '2026-06-13T10:00:00Z',
        region: 'san_juan_islands',
        summary: '1 hotspot generated',
        hotspots: [
          {
            hotspot_id: 'hotspot_1',
            name: 'Lime Kiln Point',
            center_latitude: 48.5158,
            center_longitude: -123.1526,
            radius_km: 2,
            probability: 0.81,
            confidence: 0.92,
            detection_count: 5,
            validated_detection_count: 4,
            source_count: 2,
            behavior_distribution: { feeding: 5 },
            environmental_factors: {},
            reason_codes: [],
            evidence_sighting_ids: []
          }
        ],
        cross_validation_summary: {},
        environmental_summary: {},
        data_quality_warnings: [],
        model_version: 'aws-probability-report-v1'
      }
    });
  });
});

