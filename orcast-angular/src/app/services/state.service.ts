import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { BehaviorType, PodType } from '../models/orca-sighting.model';

export interface MapFilters {
  yearRange: { min: number; max: number };
  behaviors: BehaviorType[];
  podTypes: PodType[];
  confidenceThreshold: number;
}

export interface MLSettings {
  selectedModel: string;
  predictionHours: number;
  spatialResolution: number;
  confidenceThreshold: number;
}

export interface AppState {
  currentView: string;
  mapFilters: MapFilters;
  mlSettings: MLSettings;
  isLoading: boolean;
  errors: string[];
}

@Injectable({
  providedIn: 'root'
})
export class StateService {
  private initialState: AppState = {
    currentView: 'dashboard',
    mapFilters: {
      yearRange: { min: 1990, max: 2024 },
      behaviors: ['feeding', 'traveling', 'socializing', 'resting'],
      podTypes: ['resident', 'transient', 'offshore'],
      confidenceThreshold: 0.7
    },
    mlSettings: {
      selectedModel: 'pinn',
      predictionHours: 24,
      spatialResolution: 5,
      confidenceThreshold: 0.7
    },
    isLoading: false,
    errors: []
  };

  private stateSubject = new BehaviorSubject<AppState>(this.initialState);
  
  constructor() {
    // Load state from localStorage if available
    this.loadStateFromStorage();
  }

  // Observable getters
  get state$(): Observable<AppState> {
    return this.stateSubject.asObservable();
  }

  get currentView$(): Observable<string> {
    return new BehaviorSubject(this.stateSubject.value.currentView).asObservable();
  }

  get mapFilters$(): Observable<MapFilters> {
    return new BehaviorSubject(this.stateSubject.value.mapFilters).asObservable();
  }

  get mlSettings$(): Observable<MLSettings> {
    return new BehaviorSubject(this.stateSubject.value.mlSettings).asObservable();
  }

  get isLoading$(): Observable<boolean> {
    return new BehaviorSubject(this.stateSubject.value.isLoading).asObservable();
  }

  get errors$(): Observable<string[]> {
    return new BehaviorSubject(this.stateSubject.value.errors).asObservable();
  }

  // State updates
  updateCurrentView(view: string): void {
    this.updateState({ currentView: view });
  }

  updateMapFilters(filters: Partial<MapFilters>): void {
    const currentFilters = this.stateSubject.value.mapFilters;
    const updatedFilters = { ...currentFilters, ...filters };
    this.updateState({ mapFilters: updatedFilters });
  }

  updateMLSettings(settings: Partial<MLSettings>): void {
    const currentSettings = this.stateSubject.value.mlSettings;
    const updatedSettings = { ...currentSettings, ...settings };
    this.updateState({ mlSettings: updatedSettings });
  }

  setLoading(isLoading: boolean): void {
    this.updateState({ isLoading });
  }

  addError(error: string): void {
    const currentErrors = this.stateSubject.value.errors;
    this.updateState({ errors: [...currentErrors, error] });
  }

  clearErrors(): void {
    this.updateState({ errors: [] });
  }

  removeError(index: number): void {
    const currentErrors = this.stateSubject.value.errors;
    const updatedErrors = currentErrors.filter((_, i) => i !== index);
    this.updateState({ errors: updatedErrors });
  }

  // Year range helpers
  updateYearRange(min: number, max: number): void {
    this.updateMapFilters({ yearRange: { min, max } });
  }

  updateMaxYear(year: number): void {
    const currentRange = this.stateSubject.value.mapFilters.yearRange;
    this.updateMapFilters({ yearRange: { ...currentRange, max: year } });
  }

  // Behavior filter helpers
  toggleBehavior(behavior: BehaviorType): void {
    const currentBehaviors = this.stateSubject.value.mapFilters.behaviors;
    const updatedBehaviors = currentBehaviors.includes(behavior)
      ? currentBehaviors.filter(b => b !== behavior)
      : [...currentBehaviors, behavior];
    this.updateMapFilters({ behaviors: updatedBehaviors });
  }

  setBehaviors(behaviors: BehaviorType[]): void {
    this.updateMapFilters({ behaviors });
  }

  // Pod type filter helpers
  togglePodType(podType: PodType): void {
    const currentPodTypes = this.stateSubject.value.mapFilters.podTypes;
    const updatedPodTypes = currentPodTypes.includes(podType)
      ? currentPodTypes.filter(p => p !== podType)
      : [...currentPodTypes, podType];
    this.updateMapFilters({ podTypes: updatedPodTypes });
  }

  setPodTypes(podTypes: PodType[]): void {
    this.updateMapFilters({ podTypes });
  }

  // ML model helpers
  selectMLModel(model: string): void {
    this.updateMLSettings({ selectedModel: model });
  }

  updatePredictionHours(hours: number): void {
    this.updateMLSettings({ predictionHours: hours });
  }

  updateSpatialResolution(resolution: number): void {
    this.updateMLSettings({ spatialResolution: resolution });
  }

  updateMLConfidenceThreshold(threshold: number): void {
    this.updateMLSettings({ confidenceThreshold: threshold });
  }

  // Reset methods
  resetMapFilters(): void {
    this.updateState({ mapFilters: this.initialState.mapFilters });
  }

  resetMLSettings(): void {
    this.updateState({ mlSettings: this.initialState.mlSettings });
  }

  resetAllState(): void {
    this.stateSubject.next(this.initialState);
    this.saveStateToStorage();
  }

  // Get current values (synchronous)
  getCurrentState(): AppState {
    return this.stateSubject.value;
  }

  getCurrentFilters(): MapFilters {
    return this.stateSubject.value.mapFilters;
  }

  getCurrentMLSettings(): MLSettings {
    return this.stateSubject.value.mlSettings;
  }

  // Private methods
  private updateState(updates: Partial<AppState>): void {
    const currentState = this.stateSubject.value;
    const newState = { ...currentState, ...updates };
    this.stateSubject.next(newState);
    this.saveStateToStorage();
  }

  private saveStateToStorage(): void {
    try {
      const stateToSave = {
        mapFilters: this.stateSubject.value.mapFilters,
        mlSettings: this.stateSubject.value.mlSettings,
        currentView: this.stateSubject.value.currentView
      };
      localStorage.setItem('orcast-state', JSON.stringify(stateToSave));
    } catch (error) {
      console.warn('Failed to save state to localStorage:', error);
    }
  }

  private loadStateFromStorage(): void {
    try {
      const savedState = localStorage.getItem('orcast-state');
      if (savedState) {
        const parsedState = JSON.parse(savedState);
        const currentState = this.stateSubject.value;
        
        this.stateSubject.next({
          ...currentState,
          mapFilters: parsedState.mapFilters || currentState.mapFilters,
          mlSettings: parsedState.mlSettings || currentState.mlSettings,
          currentView: parsedState.currentView || currentState.currentView
        });
      }
    } catch (error) {
      console.warn('Failed to load state from localStorage:', error);
    }
  }
} 