import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';

import { BackendService } from './backend.service';
import { inBounds, isInWater } from './geo-region';

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

  it('drops out-of-bounds sightings and snaps on-shore coordinates into water', () => {
    service.getHistoricalSightings().subscribe(sightings => {
      // The Tacoma point is out of region and dropped; only Lime Kiln remains.
      expect(sightings.length).toBe(1);
      expect(sightings[0].id).toBe('lime-kiln');

      // Lime Kiln's seed coordinate sits on the island shore. After conversion
      // it must be nudged into water and stay inside the region.
      expect(inBounds(sightings[0].latitude, sightings[0].longitude)).toBe(true);
      expect(isInWater(sightings[0].latitude, sightings[0].longitude)).toBe(true);
    });

    const req = httpMock.expectOne(`${backendUrl}/api/verified-sightings`);
    req.flush({
      sightings: [
        {
          sighting_id: 'lime-kiln',
          latitude: 48.5158,
          longitude: -123.1526,
          observation_timestamp: '2024-06-15T14:30:00Z',
          behavior_primary: 'foraging',
          pod_size: 8,
          data_quality_score: 0.95,
          location_name: 'Lime Kiln Point'
        },
        {
          sighting_id: 'tacoma',
          latitude: 47.349,
          longitude: -122.325,
          observation_timestamp: '2024-06-15T14:30:00Z',
          behavior_primary: 'traveling',
          pod_size: 3
        }
      ]
    });
  });

  it('does not fabricate a pod when the source omits one', () => {
    service.getHistoricalSightings().subscribe(sightings => {
      expect(sightings.length).toBe(1);
      // No pod field on the source item: pod must be undefined, never 'J-Pod'.
      expect(sightings[0].pod).toBeUndefined();
    });

    const req = httpMock.expectOne(`${backendUrl}/api/verified-sightings`);
    req.flush({
      sightings: [
        {
          sighting_id: 'no-pod',
          latitude: 48.55,
          longitude: -123.2,
          observation_timestamp: '2024-06-15T14:30:00Z',
          behavior_primary: 'feeding',
          pod_size: 5,
          ecotype: 'resident'
        }
      ]
    });
  });

  it('keeps a pod label only when the source actually provides one', () => {
    service.getHistoricalSightings().subscribe(sightings => {
      expect(sightings[0].pod).toBe('T49A');
    });

    const req = httpMock.expectOne(`${backendUrl}/api/verified-sightings`);
    req.flush({
      sightings: [
        {
          sighting_id: 'has-pod',
          latitude: 48.55,
          longitude: -123.2,
          observation_timestamp: '2024-06-15T14:30:00Z',
          behavior_primary: 'feeding',
          pod_size: 5,
          pod: 'T49A'
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

  it('filters out-of-region hydrophones (e.g. MaST Center in Tacoma)', () => {
    service.getHydrophoneData().subscribe(hydrophones => {
      expect(hydrophones.length).toBe(1);
      expect(hydrophones[0].name).toBe('Orcasound Lab');
      expect(hydrophones.some(h => h.name === 'MaST Center')).toBe(false);
    });

    const req = httpMock.expectOne(`${backendUrl}/api/live-hydrophones`);
    req.flush({
      hydrophones: [
        {
          id: 'rpi_orcasound_lab',
          name: 'Orcasound Lab',
          latitude: 48.5583,
          longitude: -123.1736,
          status: 'online',
          detecting: false
        },
        {
          id: 'rpi_mast_center',
          name: 'MaST Center',
          latitude: 47.349,
          longitude: -122.325,
          status: 'online',
          detecting: false
        },
        {
          id: 'rpi_port_townsend',
          name: 'Port Townsend',
          latitude: 48.135,
          longitude: -122.76,
          status: 'online',
          detecting: false
        }
      ]
    });
  });

  it('maps realtime sighting events to Detection interface with coordinates', () => {
    service.getRecentDetections().subscribe(detections => {
      expect(detections.length).toBe(1);
      expect(detections[0].hydrophone).toBe('Haro Strait');
      expect(detections[0].locationName).toBe('Haro Strait');
      // Point is already in water, so it passes through unchanged.
      expect(detections[0].latitude).toBe(48.55);
      expect(detections[0].longitude).toBe(-123.2);
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
          location_name: 'Haro Strait',
          location: { lat: 48.55, lng: -123.2 },
          confidence: 0.91,
          timestamp: '2026-06-13T10:00:00Z'
        }
      ],
      stream_active: false,
      data_freshness: 'historical'
    });
  });

  it('drops realtime events whose coordinates fall outside the region', () => {
    service.getRecentDetections().subscribe(detections => {
      expect(detections.length).toBe(1);
      expect(detections[0].locationName).toBe('North San Juan Channel');
    });

    const req = httpMock.expectOne(`${backendUrl}/api/realtime/events`);
    req.flush({
      events: [
        {
          id: 'in-region',
          location_name: 'North San Juan Channel',
          location: { lat: 48.55, lng: -123.2 },
          timestamp: '2026-06-13T10:00:00Z'
        },
        {
          id: 'tacoma',
          location_name: 'MaST Center',
          location: { lat: 47.349, lng: -122.325 },
          timestamp: '2026-06-13T10:00:00Z'
        }
      ]
    });
  });

  it('maps realtime events to typed MapEvents and skips events missing coordinates', () => {
    service.getMapEvents().subscribe(mapEvents => {
      expect(mapEvents.length).toBe(2);

      const visual = mapEvents.find(e => e.id === 'visual-1')!;
      expect(visual.kind).toBe('visual');
      expect(visual.source).toBe('obis_verified');
      expect(visual.latitude).toBe(48.55);
      expect(visual.longitude).toBe(-123.2);
      expect(visual.locationName).toBe('Haro Strait');
      expect(visual.confidence).toBe(0.91);
      expect(visual.timestamp instanceof Date).toBe(true);

      const acoustic = mapEvents.find(e => e.id === 'acoustic-1')!;
      expect(acoustic.kind).toBe('acoustic');
      expect(acoustic.source).toBe('orcahello');
      expect(acoustic.confidence).toBe(0.5);

      expect(mapEvents.some(e => e.id === 'no-coords')).toBe(false);
    });

    const req = httpMock.expectOne(`${backendUrl}/api/realtime/events`);
    expect(req.request.method).toBe('GET');
    req.flush({
      events: [
        {
          id: 'visual-1',
          source: 'obis_verified',
          event_type: 'sighting',
          confidence: 0.91,
          timestamp: '2026-06-13T10:00:00Z',
          location: { lat: 48.55, lng: -123.2 },
          location_name: 'Haro Strait',
          validation_status: 'verified'
        },
        {
          id: 'acoustic-1',
          source: 'orcahello',
          event_type: 'detection',
          timestamp: '2026-06-13T11:00:00Z',
          location: { lat: 48.56, lng: -123.18 },
          validation_status: 'verified'
        },
        {
          id: 'no-coords',
          source: 'community',
          event_type: 'sighting',
          confidence: 0.7,
          timestamp: '2026-06-13T12:00:00Z',
          location: {},
          location_name: 'Unknown',
          validation_status: 'pending'
        }
      ]
    });
  });

  it('requests spatial forecast for ML predictions', () => {
    service.generateMLPredictions(24, 0.5).subscribe(prediction => {
      expect(prediction.model).toBe('aws-deterministic-hotspot-v1');
      expect(prediction.predictions.length).toBe(1);
      expect(prediction.metadata.maxProbability).toBe(0.81);
      expect(prediction.metadata.unfilteredMaxProbability).toBe(0.81);
      expect(prediction.metadata.thresholdAutoAdjusted).toBe(false);
      expect(prediction.metadata.thresholdApplied).toBe(0.5);
    });

    const req = httpMock.expectOne(`${backendUrl}/forecast/spatial`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.hours).toBe(24);
    req.flush({
      model_version: 'aws-deterministic-hotspot-v1',
      grid_points: [
        { lat: 48.5158, lng: -123.1526, probability: 0.81 },
        { lat: 48.6, lng: -123.0, probability: 0.25 }
      ]
    });
  });

  it('auto-adjusts threshold when max probability is below requested threshold', () => {
    service.generateMLPredictions(24, 0.5).subscribe(prediction => {
      expect(prediction.metadata.unfilteredMaxProbability).toBe(0.081);
      expect(prediction.metadata.thresholdAutoAdjusted).toBe(true);
      expect(prediction.metadata.thresholdApplied).toBe(0.08);
      expect(prediction.predictions.length).toBe(1);
      expect(prediction.predictions[0].probability).toBe(0.081);
    });

    const req = httpMock.expectOne(`${backendUrl}/forecast/spatial`);
    req.flush({
      model_version: 'aws-deterministic-hotspot-v1',
      grid_points: [
        { lat: 48.5158, lng: -123.1526, probability: 0.081 }
      ]
    });
  });

  it('uses response.model when model_version is absent', () => {
    service.generateMLPredictions(24, 0.05).subscribe(prediction => {
      expect(prediction.model).toBe('custom-model-v2');
    });

    const req = httpMock.expectOne(`${backendUrl}/forecast/spatial`);
    req.flush({
      model: 'custom-model-v2',
      grid_points: [
        { lat: 48.5158, lng: -123.1526, probability: 0.5 }
      ]
    });
  });

  it('submits community sightings with honeypot and returns the parsed body', () => {
    const payload = {
      place: 'Lime Kiln Point',
      latitude: 48.5158,
      longitude: -123.1526,
      observed_at: '2026-06-15T14:30:00.000Z',
      behavior: 'feeding',
      count: 3,
      notes: 'Heading north',
      observer_name: 'Sam'
    };

    service.submitCommunitySighting(payload).subscribe(result => {
      expect(result.id).toBe('community_1');
      expect(result.status).toBe('pending');
    });

    const req = httpMock.expectOne(`${backendUrl}/api/community/sightings`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.place).toBe('Lime Kiln Point');
    expect(req.request.body.behavior).toBe('feeding');
    expect(req.request.body.website).toBe('');
    req.flush({ id: 'community_1', status: 'pending' });
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

