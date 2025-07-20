import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { BackendService } from './backend.service';
import { OrcaSighting, HydrophoneData, MLPredictionData } from '../models/orca-sighting.model';

describe('BackendService', () => {
  let service: BackendService;
  let httpMock: HttpTestingController;
  const backendUrl = 'https://orcast-production-backend-2cvqukvhga-uw.a.run.app';

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

  describe('Health Check', () => {
    it('should fetch health status', () => {
      const mockHealth = { status: 'healthy', version: 'v3.0' };

      service.getHealth().subscribe(health => {
        expect(health).toEqual(mockHealth);
      });

      const req = httpMock.expectOne(`${backendUrl}/health`);
      expect(req.request.method).toBe('GET');
      req.flush(mockHealth);
    });

    it('should handle health check errors', () => {
      service.getHealth().subscribe({
        next: () => fail('should have failed'),
        error: (error) => {
          expect(error).toBeTruthy();
        }
      });

      const req = httpMock.expectOne(`${backendUrl}/health`);
      req.flush('Server Error', { status: 500, statusText: 'Internal Server Error' });
    });
  });

  describe('Historical Sightings', () => {
    it('should fetch historical sightings from API', () => {
      const mockSightings: OrcaSighting[] = [
        {
          id: 'test-1',
          date: new Date('2024-01-01'),
          latitude: 48.5465,
          longitude: -123.0307,
          behavior: 'feeding',
          pod: 'J-Pod',
          location: 'Test Location',
          groupSize: 5,
          confidence: 0.85,
          year: 2024
        }
      ];

      const mockResponse = { success: true, data: mockSightings };

      service.getHistoricalSightings().subscribe(sightings => {
        expect(sightings).toEqual(mockSightings);
        expect(sightings.length).toBe(1);
        expect(sightings[0].behavior).toBe('feeding');
      });

      const req = httpMock.expectOne(`${backendUrl}/api/verified-sightings`);
      expect(req.request.method).toBe('GET');
      req.flush(mockResponse);
    });

    it('should fallback to mock data on API error', () => {
      service.getHistoricalSightings().subscribe(sightings => {
        expect(sightings).toBeTruthy();
        expect(sightings.length).toBeGreaterThan(0);
        // Should contain mock data
        expect(sightings[0]).toHaveProperty('id');
        expect(sightings[0]).toHaveProperty('behavior');
      });

      const req = httpMock.expectOne(`${backendUrl}/api/verified-sightings`);
      req.flush('API Error', { status: 500, statusText: 'Internal Server Error' });
    });
  });

  describe('Hydrophone Data', () => {
    it('should fetch hydrophone data from API', () => {
      const mockHydrophones: HydrophoneData[] = [
        {
          id: 'test-hydrophone',
          name: 'Test Hydrophone',
          location: 'Test Location',
          latitude: 48.5465,
          longitude: -123.0307,
          status: 'online',
          detecting: false,
          lastDetection: null,
          streamUrl: 'https://test.stream'
        }
      ];

      const mockResponse = { success: true, data: mockHydrophones };

      service.getHydrophoneData().subscribe(hydrophones => {
        expect(hydrophones).toEqual(mockHydrophones);
        expect(hydrophones[0].status).toBe('online');
      });

      const req = httpMock.expectOne(`${backendUrl}/api/live-hydrophones`);
      expect(req.request.method).toBe('GET');
      req.flush(mockResponse);
    });
  });

  describe('ML Predictions', () => {
    it('should generate ML predictions with correct parameters', () => {
      const mockPrediction: MLPredictionData = {
        model: 'pinn',
        predictions: [
          {
            latitude: 48.5465,
            longitude: -123.0307,
            probability: 0.85,
            hour: 0
          }
        ],
        metadata: {
          totalPredictions: 1,
          averageProbability: 0.85,
          maxProbability: 0.85
        }
      };

      const mockResponse = { success: true, data: mockPrediction };

      service.generateMLPredictions('pinn', 24, 0.7).subscribe(prediction => {
        expect(prediction).toEqual(mockPrediction);
        expect(prediction.model).toBe('pinn');
        expect(prediction.predictions.length).toBe(1);
      });

      const req = httpMock.expectOne(`${backendUrl}/api/ml/predict`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({
        model: 'pinn',
        hours: 24,
        threshold: 0.7,
        latitude: 48.5465,
        longitude: -123.0307
      });
      req.flush(mockResponse);
    });

    it('should fallback to mock predictions on API error', () => {
      service.generateMLPredictions('behavioral', 12, 0.8).subscribe(prediction => {
        expect(prediction).toBeTruthy();
        expect(prediction.model).toBe('behavioral');
        expect(prediction.predictions.length).toBeGreaterThan(0);
      });

      const req = httpMock.expectOne(`${backendUrl}/api/ml/predict`);
      req.flush('Prediction Error', { status: 503, statusText: 'Service Unavailable' });
    });
  });

  describe('Agent API', () => {
    it('should send agent queries correctly', () => {
      const mockResponse = { 
        success: true, 
        data: { answer: 'Test response from agent' } 
      };

      service.queryAgent('Test prompt').subscribe(response => {
        expect(response.answer).toBe('Test response from agent');
      });

      const req = httpMock.expectOne(`${backendUrl}/api/agent/query`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({ prompt: 'Test prompt' });
      req.flush(mockResponse);
    });
  });

  describe('Mock Data Generation', () => {
    it('should generate valid mock sightings data', () => {
      // Test private method through public API error fallback
      service.getHistoricalSightings().subscribe(sightings => {
        expect(sightings.length).toBeGreaterThan(100); // Should generate substantial data
        
        const sighting = sightings[0];
        expect(sighting.year).toBeGreaterThanOrEqual(1990);
        expect(sighting.year).toBeLessThanOrEqual(2024);
        expect(sighting.latitude).toBeGreaterThan(48);
        expect(sighting.longitude).toBeLessThan(-122);
        expect(['feeding', 'traveling', 'socializing', 'resting', 'unknown']).toContain(sighting.behavior);
      });

      const req = httpMock.expectOne(`${backendUrl}/api/verified-sightings`);
      req.flush('Force fallback to mock data', { status: 404, statusText: 'Not Found' });
    });

    it('should generate valid mock hydrophone data', () => {
      service.getHydrophoneData().subscribe(hydrophones => {
        expect(hydrophones.length).toBeGreaterThan(0);
        
        const hydrophone = hydrophones[0];
        expect(hydrophone.id).toBeTruthy();
        expect(hydrophone.name).toBeTruthy();
        expect(['online', 'offline']).toContain(hydrophone.status);
        expect(typeof hydrophone.latitude).toBe('number');
        expect(typeof hydrophone.longitude).toBe('number');
      });

      const req = httpMock.expectOne(`${backendUrl}/api/live-hydrophones`);
      req.flush('Force fallback', { status: 500, statusText: 'Server Error' });
    });
  });
}); 