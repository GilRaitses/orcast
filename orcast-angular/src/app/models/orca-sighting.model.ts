/// <reference types="google.maps" />

export interface OrcaSighting {
  id: string;
  date: Date;
  latitude: number;
  longitude: number;
  behavior: BehaviorType;
  pod: string;
  location: string;
  groupSize: number;
  confidence: number;
  year: number;
}

export type BehaviorType = 'feeding' | 'traveling' | 'socializing' | 'resting' | 'unknown';

export type PodType = 'resident' | 'transient' | 'offshore';

export interface HydrophoneData {
  id: string;
  name: string;
  location: string;
  latitude: number;
  longitude: number;
  status: 'online' | 'offline';
  detecting: boolean;
  lastDetection: Date | null;
  streamUrl: string | null;
}

export interface Detection {
  id: string | number;
  timestamp: Date;
  hydrophone: string;
  hydrophoneId: string;
  confidence: number;
  frequency: number;
  duration: number;
  callType: 'resident' | 'transient' | 'unknown';
}

export interface MLPrediction {
  latitude: number;
  longitude: number;
  probability: number;
  hour: number;
}

export interface MLPredictionData {
  model: string;
  predictions: MLPrediction[];
  metadata: {
    totalPredictions: number;
    averageProbability: number;
    maxProbability: number;
  };
}

export interface ProbabilityHotspot {
  hotspot_id: string;
  name: string;
  center_latitude: number;
  center_longitude: number;
  radius_km: number;
  probability: number;
  confidence: number;
  detection_count: number;
  validated_detection_count: number;
  source_count: number;
  behavior_distribution: Record<string, number>;
  environmental_factors: Record<string, unknown>;
  reason_codes: string[];
  evidence_sighting_ids: string[];
}

export interface ProbabilityReportResponse {
  report_id: string;
  generated_at: string;
  region: string;
  summary: string;
  hotspots: ProbabilityHotspot[];
  cross_validation_summary: Record<string, unknown>;
  environmental_summary: Record<string, unknown>;
  data_quality_warnings: string[];
  model_version: string;
  storage_uri?: string | null;
}

export interface MapMarker {
  id: string;
  position: google.maps.LatLngLiteral;
  title: string;
  icon?: google.maps.Icon | google.maps.Symbol;
  data?: any;
}

export interface HeatMapPoint {
  location: google.maps.LatLng;
  weight: number;
}

export interface BackendResponse<T = any> {
  success: boolean;
  data: T;
  error?: string;
} 