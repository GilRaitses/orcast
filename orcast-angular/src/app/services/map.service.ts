/// <reference types="google.maps" />

import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { MapMarker, HeatMapPoint, OrcaSighting, HydrophoneData, MLPrediction } from '../models/orca-sighting.model';

@Injectable({
  providedIn: 'root'
})
export class MapService {
  private mapSubject = new BehaviorSubject<google.maps.Map | null>(null);
  private markersSubject = new BehaviorSubject<google.maps.Marker[]>([]);
  private heatMapLayersSubject = new BehaviorSubject<google.maps.visualization.HeatmapLayer[]>([]);
  
  // Default map center (San Juan Islands)
  private readonly defaultCenter = { lat: 48.5465, lng: -123.0307 };
  private readonly defaultZoom = 11;

  constructor() {}

  // Observable getters
  get map$(): Observable<google.maps.Map | null> {
    return this.mapSubject.asObservable();
  }

  get markers$(): Observable<google.maps.Marker[]> {
    return this.markersSubject.asObservable();
  }

  get heatMapLayers$(): Observable<google.maps.visualization.HeatmapLayer[]> {
    return this.heatMapLayersSubject.asObservable();
  }

  // Initialize map
  initializeMap(mapElement: HTMLElement): google.maps.Map {
    const map = new google.maps.Map(mapElement, {
      zoom: this.defaultZoom,
      center: this.defaultCenter,
      mapTypeId: google.maps.MapTypeId.HYBRID,
      styles: [
        {
          featureType: 'poi',
          stylers: [{ visibility: 'off' }]
        },
        {
          featureType: 'transit',
          stylers: [{ visibility: 'off' }]
        }
      ]
    });

    this.mapSubject.next(map);
    return map;
  }

  // Clear all markers
  clearMarkers(): void {
    const currentMarkers = this.markersSubject.value;
    currentMarkers.forEach(marker => marker.setMap(null));
    this.markersSubject.next([]);
  }

  // Clear all heat map layers
  clearHeatMapLayers(): void {
    const currentLayers = this.heatMapLayersSubject.value;
    currentLayers.forEach(layer => layer.setMap(null));
    this.heatMapLayersSubject.next([]);
  }

  // Add historical sighting markers
  addHistoricalSightings(sightings: OrcaSighting[], filters?: any): void {
    const map = this.mapSubject.value;
    if (!map) return;

    this.clearMarkers();

    const filteredSightings = this.filterSightings(sightings, filters);
    const markers: google.maps.Marker[] = [];

    filteredSightings.forEach(sighting => {
      const marker = new google.maps.Marker({
        position: { lat: sighting.latitude, lng: sighting.longitude },
        map: map,
        icon: {
          path: google.maps.SymbolPath.CIRCLE,
          scale: 8 + (sighting.groupSize / 5),
          fillColor: this.getBehaviorColor(sighting.behavior),
          fillOpacity: 0.8,
          strokeColor: '#ffffff',
          strokeWeight: 2
        },
        title: `${sighting.location} - ${sighting.behavior} (${sighting.year})`
      });

      // Add info window
      const infoWindow = new google.maps.InfoWindow({
        content: this.createSightingInfoContent(sighting)
      });

      marker.addListener('click', () => {
        infoWindow.open(map, marker);
      });

      markers.push(marker);
    });

    this.markersSubject.next(markers);
  }

  // Add hydrophone markers
  addHydrophones(hydrophones: HydrophoneData[]): void {
    const map = this.mapSubject.value;
    if (!map) return;

    this.clearMarkers();

    const markers: google.maps.Marker[] = [];

    hydrophones.forEach(hydrophone => {
      const marker = new google.maps.Marker({
        position: { lat: hydrophone.latitude, lng: hydrophone.longitude },
        map: map,
        icon: {
          path: google.maps.SymbolPath.CIRCLE,
          scale: hydrophone.detecting ? 20 : 15,
          fillColor: this.getHydrophoneColor(hydrophone),
          fillOpacity: 0.8,
          strokeColor: '#ffffff',
          strokeWeight: 2
        },
        title: `${hydrophone.name} - ${hydrophone.status}`
      });

      // Add detection animation for active hydrophones
      if (hydrophone.detecting) {
        this.createDetectionWave(marker.getPosition()!, map);
      }

      // Add info window
      const infoWindow = new google.maps.InfoWindow({
        content: this.createHydrophoneInfoContent(hydrophone)
      });

      marker.addListener('click', () => {
        infoWindow.open(map, marker);
      });

      markers.push(marker);
    });

    this.markersSubject.next(markers);
  }

  // Add ML prediction heat map
  addMLPredictionHeatMap(predictions: MLPrediction[], model: string): void {
    const map = this.mapSubject.value;
    if (!map) return;

    this.clearHeatMapLayers();

    // Create heat map data
    const heatMapData: google.maps.visualization.WeightedLocation[] = predictions.map(pred => ({
      location: new google.maps.LatLng(pred.latitude, pred.longitude),
      weight: pred.probability
    }));

    // Create heat map layer
    const heatMapLayer = new google.maps.visualization.HeatmapLayer({
      data: heatMapData,
      map: map,
      radius: 40,
      opacity: 0.7,
      gradient: this.getModelGradient(model)
    });

    // Add high-probability markers
    const highProbPredictions = predictions.filter(p => p.probability > 0.8);
    const markers: google.maps.Marker[] = [];

    highProbPredictions.forEach(pred => {
      const marker = new google.maps.Marker({
        position: { lat: pred.latitude, lng: pred.longitude },
        map: map,
        icon: {
          path: google.maps.SymbolPath.CIRCLE,
          scale: 15,
          fillColor: '#ff4444',
          fillOpacity: 0.8,
          strokeColor: '#ffffff',
          strokeWeight: 2
        },
        title: `High Probability: ${(pred.probability * 100).toFixed(1)}%`
      });

      markers.push(marker);
    });

    this.heatMapLayersSubject.next([heatMapLayer]);
    this.markersSubject.next(markers);
  }

  // Center map on coordinates
  centerMap(lat: number, lng: number, zoom?: number): void {
    const map = this.mapSubject.value;
    if (!map) return;

    map.setCenter({ lat, lng });
    if (zoom) {
      map.setZoom(zoom);
    }
  }

  // Private helper methods
  private filterSightings(sightings: OrcaSighting[], filters?: any): OrcaSighting[] {
    if (!filters) return sightings;

    return sightings.filter(sighting => {
      // Year filter
      if (filters.maxYear && sighting.year > filters.maxYear) return false;
      if (filters.minYear && sighting.year < filters.minYear) return false;

      // Behavior filter
      if (filters.behaviors && filters.behaviors.length > 0) {
        if (!filters.behaviors.includes(sighting.behavior)) return false;
      }

      // Pod type filter
      if (filters.podTypes && filters.podTypes.length > 0) {
        const podType = this.getPodType(sighting.pod);
        if (!filters.podTypes.includes(podType)) return false;
      }

      return true;
    });
  }

  private getBehaviorColor(behavior: string): string {
    switch (behavior) {
      case 'feeding': return '#ff4444';
      case 'traveling': return '#44ff44';
      case 'socializing': return '#4444ff';
      case 'resting': return '#ffff44';
      default: return '#ff44ff';
    }
  }

  private getHydrophoneColor(hydrophone: HydrophoneData): string {
    if (hydrophone.status === 'offline') return '#999999';
    if (hydrophone.detecting) return '#ff4444';
    return '#4fc3f7';
  }

  private getPodType(podName: string): string {
    if (podName.includes('J-') || podName.includes('K-') || podName.includes('L-')) {
      return 'resident';
    } else if (podName.includes('T-')) {
      return 'transient';
    } else {
      return 'offshore';
    }
  }

  private getModelGradient(modelType: string): string[] {
    const gradients: { [key: string]: string[] } = {
      pinn: [
        'rgba(0, 255, 255, 0)',
        'rgba(0, 255, 255, 1)',
        'rgba(0, 127, 255, 1)',
        'rgba(127, 0, 255, 1)',
        'rgba(255, 0, 255, 1)'
      ],
      behavioral: [
        'rgba(0, 255, 0, 0)',
        'rgba(0, 255, 0, 1)',
        'rgba(127, 255, 0, 1)',
        'rgba(255, 255, 0, 1)',
        'rgba(255, 127, 0, 1)',
        'rgba(255, 0, 0, 1)'
      ],
      ensemble: [
        'rgba(255, 255, 0, 0)',
        'rgba(255, 255, 0, 1)',
        'rgba(255, 192, 0, 1)',
        'rgba(255, 128, 0, 1)',
        'rgba(255, 64, 0, 1)',
        'rgba(255, 0, 0, 1)'
      ]
    };

    return gradients[modelType] || gradients.ensemble;
  }

  private createDetectionWave(position: google.maps.LatLng, map: google.maps.Map): void {
    const wave = new google.maps.Circle({
      center: position,
      radius: 100,
      strokeColor: '#ff4444',
      strokeOpacity: 0.8,
      strokeWeight: 2,
      fillOpacity: 0,
      map: map
    });

    // Animate the wave
    let radius = 100;
    const animation = setInterval(() => {
      radius += 50;
      wave.setRadius(radius);
      
      if (radius > 1000) {
        wave.setMap(null);
        clearInterval(animation);
      }
    }, 100);
  }

  private createSightingInfoContent(sighting: OrcaSighting): string {
    return `
      <div style="color: #001e3c; min-width: 200px;">
        <h3>${sighting.location}</h3>
        <p><strong>Date:</strong> ${sighting.date.toLocaleDateString()}</p>
        <p><strong>Pod:</strong> ${sighting.pod}</p>
        <p><strong>Behavior:</strong> ${sighting.behavior}</p>
        <p><strong>Group Size:</strong> ${sighting.groupSize} individuals</p>
        <p><strong>Confidence:</strong> ${(sighting.confidence * 100).toFixed(0)}%</p>
      </div>
    `;
  }

  private createHydrophoneInfoContent(hydrophone: HydrophoneData): string {
    return `
      <div style="color: #001e3c; min-width: 200px;">
        <h3>${hydrophone.name}</h3>
        <p><strong>Location:</strong> ${hydrophone.location}</p>
        <p><strong>Status:</strong> ${hydrophone.status}</p>
        <p><strong>Detecting:</strong> ${hydrophone.detecting ? 'YES' : 'No'}</p>
        ${hydrophone.lastDetection ? 
          `<p><strong>Last Detection:</strong> ${this.getTimeAgo(hydrophone.lastDetection)}</p>` : ''}
        ${hydrophone.streamUrl ? 
          `<button onclick="window.open('${hydrophone.streamUrl}', '_blank')" 
                   style="background: #4fc3f7; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;">
              🔊 Listen Live
          </button>` : ''}
      </div>
    `;
  }

  private getTimeAgo(date: Date): string {
    const minutes = Math.floor((Date.now() - date.getTime()) / (1000 * 60));
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  }
} 