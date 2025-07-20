import { TestBed } from '@angular/core/testing';
import { StateService } from './state.service';
import { BehaviorType, PodType } from '../models/orca-sighting.model';

describe('StateService', () => {
  let service: StateService;

  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
    
    TestBed.configureTestingModule({});
    service = TestBed.inject(StateService);
  });

  afterEach(() => {
    localStorage.clear();
  });

  describe('Initial State', () => {
    it('should be created with default values', () => {
      const state = service.getCurrentState();
      
      expect(state.currentView).toBe('dashboard');
      expect(state.mapFilters.yearRange.min).toBe(1990);
      expect(state.mapFilters.yearRange.max).toBe(2024);
      expect(state.mapFilters.behaviors).toEqual(['feeding', 'traveling', 'socializing', 'resting']);
      expect(state.mapFilters.podTypes).toEqual(['resident', 'transient', 'offshore']);
      expect(state.mlSettings.selectedModel).toBe('pinn');
      expect(state.isLoading).toBe(false);
      expect(state.errors).toEqual([]);
    });

    it('should provide observable streams', (done) => {
      service.state$.subscribe(state => {
        expect(state).toBeTruthy();
        expect(state.currentView).toBe('dashboard');
        done();
      });
    });
  });

  describe('Current View Management', () => {
    it('should update current view', () => {
      service.updateCurrentView('historical');
      
      const state = service.getCurrentState();
      expect(state.currentView).toBe('historical');
    });

    it('should emit current view changes', (done) => {
      service.currentView$.subscribe(view => {
        if (view === 'realtime') {
          expect(view).toBe('realtime');
          done();
        }
      });

      service.updateCurrentView('realtime');
    });
  });

  describe('Map Filters Management', () => {
    it('should update year range', () => {
      service.updateYearRange(2000, 2020);
      
      const filters = service.getCurrentFilters();
      expect(filters.yearRange.min).toBe(2000);
      expect(filters.yearRange.max).toBe(2020);
    });

    it('should update max year only', () => {
      service.updateMaxYear(2023);
      
      const filters = service.getCurrentFilters();
      expect(filters.yearRange.max).toBe(2023);
      expect(filters.yearRange.min).toBe(1990); // Should remain unchanged
    });

    it('should toggle behaviors', () => {
      service.toggleBehavior('feeding');
      
      const filters = service.getCurrentFilters();
      expect(filters.behaviors).not.toContain('feeding');
      
      service.toggleBehavior('feeding');
      expect(service.getCurrentFilters().behaviors).toContain('feeding');
    });

    it('should set behaviors directly', () => {
      const newBehaviors: BehaviorType[] = ['feeding', 'traveling'];
      service.setBehaviors(newBehaviors);
      
      const filters = service.getCurrentFilters();
      expect(filters.behaviors).toEqual(newBehaviors);
    });

    it('should toggle pod types', () => {
      service.togglePodType('resident');
      
      const filters = service.getCurrentFilters();
      expect(filters.podTypes).not.toContain('resident');
      
      service.togglePodType('resident');
      expect(service.getCurrentFilters().podTypes).toContain('resident');
    });

    it('should set pod types directly', () => {
      const newPodTypes: PodType[] = ['resident', 'transient'];
      service.setPodTypes(newPodTypes);
      
      const filters = service.getCurrentFilters();
      expect(filters.podTypes).toEqual(newPodTypes);
    });
  });

  describe('ML Settings Management', () => {
    it('should select ML model', () => {
      service.selectMLModel('behavioral');
      
      const settings = service.getCurrentMLSettings();
      expect(settings.selectedModel).toBe('behavioral');
    });

    it('should update prediction hours', () => {
      service.updatePredictionHours(48);
      
      const settings = service.getCurrentMLSettings();
      expect(settings.predictionHours).toBe(48);
    });

    it('should update spatial resolution', () => {
      service.updateSpatialResolution(3);
      
      const settings = service.getCurrentMLSettings();
      expect(settings.spatialResolution).toBe(3);
    });

    it('should update ML confidence threshold', () => {
      service.updateMLConfidenceThreshold(0.85);
      
      const settings = service.getCurrentMLSettings();
      expect(settings.confidenceThreshold).toBe(0.85);
    });

    it('should emit ML settings changes', (done) => {
      service.mlSettings$.subscribe(settings => {
        if (settings.selectedModel === 'ensemble') {
          expect(settings.selectedModel).toBe('ensemble');
          done();
        }
      });

      service.selectMLModel('ensemble');
    });
  });

  describe('Loading State Management', () => {
    it('should manage loading state', () => {
      service.setLoading(true);
      expect(service.getCurrentState().isLoading).toBe(true);
      
      service.setLoading(false);
      expect(service.getCurrentState().isLoading).toBe(false);
    });

    it('should emit loading state changes', (done) => {
      service.isLoading$.subscribe(isLoading => {
        if (isLoading === true) {
          expect(isLoading).toBe(true);
          done();
        }
      });

      service.setLoading(true);
    });
  });

  describe('Error Management', () => {
    it('should add errors', () => {
      service.addError('Test error 1');
      service.addError('Test error 2');
      
      const errors = service.getCurrentState().errors;
      expect(errors).toEqual(['Test error 1', 'Test error 2']);
    });

    it('should remove specific errors by index', () => {
      service.addError('Error 1');
      service.addError('Error 2');
      service.addError('Error 3');
      
      service.removeError(1); // Remove 'Error 2'
      
      const errors = service.getCurrentState().errors;
      expect(errors).toEqual(['Error 1', 'Error 3']);
    });

    it('should clear all errors', () => {
      service.addError('Error 1');
      service.addError('Error 2');
      
      service.clearErrors();
      
      const errors = service.getCurrentState().errors;
      expect(errors).toEqual([]);
    });

    it('should emit error changes', (done) => {
      service.errors$.subscribe(errors => {
        if (errors.length === 1) {
          expect(errors[0]).toBe('Test error');
          done();
        }
      });

      service.addError('Test error');
    });
  });

  describe('State Persistence', () => {
    it('should save state to localStorage', () => {
      service.updateCurrentView('ml-predictions');
      service.selectMLModel('ensemble');
      service.updateMaxYear(2023);
      
      // Check if localStorage has been updated
      const savedState = localStorage.getItem('orcast-state');
      expect(savedState).toBeTruthy();
      
      const parsedState = JSON.parse(savedState!);
      expect(parsedState.currentView).toBe('ml-predictions');
      expect(parsedState.mlSettings.selectedModel).toBe('ensemble');
      expect(parsedState.mapFilters.yearRange.max).toBe(2023);
    });

    it('should load state from localStorage on initialization', () => {
      // Set up localStorage with test data
      const testState = {
        currentView: 'historical',
        mapFilters: {
          yearRange: { min: 2000, max: 2020 },
          behaviors: ['feeding'],
          podTypes: ['resident'],
          confidenceThreshold: 0.8
        },
        mlSettings: {
          selectedModel: 'behavioral',
          predictionHours: 48,
          spatialResolution: 3,
          confidenceThreshold: 0.9
        }
      };
      
      localStorage.setItem('orcast-state', JSON.stringify(testState));
      
      // Create new service instance to trigger loading
      const newService = TestBed.inject(StateService);
      const state = newService.getCurrentState();
      
      expect(state.currentView).toBe('historical');
      expect(state.mapFilters.yearRange.max).toBe(2020);
      expect(state.mapFilters.behaviors).toEqual(['feeding']);
      expect(state.mlSettings.selectedModel).toBe('behavioral');
    });

    it('should handle corrupted localStorage gracefully', () => {
      localStorage.setItem('orcast-state', 'corrupted json data');
      
      // Should not crash and use default state
      const newService = TestBed.inject(StateService);
      const state = newService.getCurrentState();
      
      expect(state.currentView).toBe('dashboard');
      expect(state.mapFilters.yearRange.max).toBe(2024);
    });
  });

  describe('Reset Functionality', () => {
    it('should reset map filters to defaults', () => {
      service.toggleBehavior('feeding');
      service.updateMaxYear(2020);
      
      service.resetMapFilters();
      
      const filters = service.getCurrentFilters();
      expect(filters.behaviors).toEqual(['feeding', 'traveling', 'socializing', 'resting']);
      expect(filters.yearRange.max).toBe(2024);
    });

    it('should reset ML settings to defaults', () => {
      service.selectMLModel('ensemble');
      service.updatePredictionHours(72);
      
      service.resetMLSettings();
      
      const settings = service.getCurrentMLSettings();
      expect(settings.selectedModel).toBe('pinn');
      expect(settings.predictionHours).toBe(24);
    });

    it('should reset all state to defaults', () => {
      service.updateCurrentView('historical');
      service.selectMLModel('behavioral');
      service.addError('Test error');
      
      service.resetAllState();
      
      const state = service.getCurrentState();
      expect(state.currentView).toBe('dashboard');
      expect(state.mlSettings.selectedModel).toBe('pinn');
      expect(state.errors).toEqual([]);
    });
  });
}); 