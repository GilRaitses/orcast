import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { GoogleMapsModule } from '@angular/google-maps';

import { NavHeaderComponent } from '../shared/nav-header.component';
import { BackendService } from '../../services/backend.service';

interface TripParameters {
  destination: string;
  startDate: string;
  endDate: string;
  groupSize: number;
  interests: string[];
  budget: string;
  accommodation: string;
  activities: string[];
}

interface TripPlan {
  id: string;
  title: string;
  description: string;
  duration: string;
  estimatedCost: string;
  highlights: string[];
  itinerary: DayPlan[];
  conditions: WeatherConditions;
  mapPreview: MapPreview;
  created: Date;
  status: 'upcoming' | 'past' | 'active';
}

interface DayPlan {
  day: number;
  date: string;
  activities: Activity[];
  meals: string[];
  accommodation: string;
  weather: string;
  orcaProbability: number;
}

interface Activity {
  time: string;
  name: string;
  location: string;
  description: string;
  duration: string;
  cost?: string;
}

interface WeatherConditions {
  forecast: string;
  temperature: string;
  precipitation: string;
  windSpeed: string;
  orcaLikelihood: string;
  bestTimes: string[];
}

interface MapPreview {
  center: { lat: number; lng: number };
  zoom: number;
  markers: MapMarker[];
  route?: google.maps.LatLngLiteral[];
}

interface MapMarker {
  position: google.maps.LatLngLiteral;
  title: string;
  type: 'accommodation' | 'activity' | 'dining' | 'orca-spot';
  icon: string;
}

interface UserProfile {
  name: string;
  email: string;
  preferences: {
    favoriteActivities: string[];
    budgetRange: string;
    travelStyle: string;
  };
  pastTrips: TripPlan[];
  upcomingTrips: TripPlan[];
}

@Component({
  selector: 'orcast-agent-demo',
  standalone: true,
  imports: [CommonModule, FormsModule, GoogleMapsModule, NavHeaderComponent],
  template: `
    <orcast-nav-header currentPage="agent-demo"></orcast-nav-header>

    <div class="agent-demo-container">
      <!-- User Profile Section -->
      <div class="user-profile" *ngIf="currentUser">
        <div class="profile-header">
          <div class="avatar">{{ currentUser.name.charAt(0) }}</div>
          <div class="profile-info">
            <h2>Welcome back, {{ currentUser.name }}!</h2>
            <p>{{ currentUser.email }}</p>
            <div class="trip-stats">
              <span class="stat">{{ currentUser.pastTrips.length }} past trips</span>
              <span class="stat">{{ currentUser.upcomingTrips.length }} upcoming</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Trip Planning Interface -->
      <div class="planning-interface">
        <div class="input-section">
          <h3>🤖 AI Trip Planner</h3>
          <p>Tell me about your San Juan Islands adventure, and I'll create the perfect plan!</p>
          
          <div class="trip-form">
            <div class="form-row">
              <div class="form-group">
                <label>Destination</label>
                <select [(ngModel)]="tripParams.destination">
                  <option value="san-juan-islands">San Juan Islands, WA</option>
                  <option value="orcas-island">Orcas Island Focus</option>
                  <option value="friday-harbor">Friday Harbor & San Juan Island</option>
                  <option value="lopez-island">Lopez Island & Shaw Island</option>
                </select>
              </div>
              
              <div class="form-group">
                <label>Group Size</label>
                <input type="number" [(ngModel)]="tripParams.groupSize" min="1" max="12">
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>Start Date</label>
                <input type="date" [(ngModel)]="tripParams.startDate">
              </div>
              
              <div class="form-group">
                <label>End Date</label>
                <input type="date" [(ngModel)]="tripParams.endDate">
              </div>
            </div>

            <div class="form-group">
              <label>Interests (select all that apply)</label>
              <div class="interest-tags">
                <div *ngFor="let interest of availableInterests" 
                     class="interest-tag"
                     [class.selected]="tripParams.interests.includes(interest)"
                     (click)="toggleInterest(interest)">
                  {{ interest }}
                </div>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>Budget Range</label>
                <select [(ngModel)]="tripParams.budget">
                  <option value="budget">Budget ($100-200/day)</option>
                  <option value="moderate">Moderate ($200-400/day)</option>
                  <option value="luxury">Luxury ($400+/day)</option>
                </select>
              </div>
              
              <div class="form-group">
                <label>Accommodation Type</label>
                <select [(ngModel)]="tripParams.accommodation">
                  <option value="camping">Camping</option>
                  <option value="b&b">Bed & Breakfast</option>
                  <option value="hotel">Hotel/Resort</option>
                  <option value="vacation-rental">Vacation Rental</option>
                </select>
              </div>
            </div>

            <div class="agent-prompt">
              <label>Additional Requests (natural language)</label>
              <textarea 
                placeholder="e.g., 'I want the best orca watching opportunities and love photography. Include some local seafood experiences and prefer morning activities.'"
                [(ngModel)]="naturalLanguagePrompt"
                rows="3">
              </textarea>
            </div>

            <button 
              class="generate-plan-btn"
              (click)="generateTripPlan()"
              [disabled]="isGenerating">
              {{ isGenerating ? '🧠 AI Agents Working...' : '🚀 Generate My Trip Plan' }}
            </button>
          </div>
        </div>

        <!-- Generated Plan Display -->
        <div class="plan-display" *ngIf="generatedPlan">
          <div class="plan-header">
            <h3>{{ generatedPlan.title }}</h3>
            <div class="plan-meta">
              <span class="duration">{{ generatedPlan.duration }}</span>
              <span class="cost">{{ generatedPlan.estimatedCost }}</span>
              <button class="save-plan-btn" (click)="savePlan()">💾 Save to Profile</button>
            </div>
          </div>

          <div class="plan-content">
            <!-- Map Preview -->
            <div class="map-preview-section">
              <h4>🗺️ Trip Overview Map</h4>
              <google-map 
                [options]="mapOptions"
                [center]="generatedPlan.mapPreview.center"
                [zoom]="generatedPlan.mapPreview.zoom">
                <map-marker 
                  *ngFor="let marker of generatedPlan.mapPreview.markers"
                  [position]="marker.position"
                  [title]="marker.title">
                </map-marker>
              </google-map>
            </div>

            <!-- Conditions & Forecast -->
            <div class="conditions-section">
              <h4>🌊 Conditions & Forecast</h4>
              <div class="conditions-grid">
                <div class="condition-item">
                  <span class="label">Weather:</span>
                  <span>{{ generatedPlan.conditions.forecast }}</span>
                </div>
                <div class="condition-item">
                  <span class="label">Temperature:</span>
                  <span>{{ generatedPlan.conditions.temperature }}</span>
                </div>
                <div class="condition-item">
                  <span class="label">Orca Likelihood:</span>
                  <span class="orca-likelihood">{{ generatedPlan.conditions.orcaLikelihood }}</span>
                </div>
                <div class="condition-item">
                  <span class="label">Best Times:</span>
                  <span>{{ generatedPlan.conditions.bestTimes.join(', ') }}</span>
                </div>
              </div>
            </div>

            <!-- Detailed Itinerary -->
            <div class="itinerary-section">
              <h4>📅 Detailed Itinerary</h4>
              <div class="day-plans">
                <div *ngFor="let day of generatedPlan.itinerary" class="day-plan">
                  <div class="day-header">
                    <h5>Day {{ day.day }} - {{ day.date }}</h5>
                    <div class="day-meta">
                      <span class="weather">{{ day.weather }}</span>
                      <span class="orca-prob">🐋 {{ day.orcaProbability }}% orca chance</span>
                    </div>
                  </div>
                  
                  <div class="activities">
                    <div *ngFor="let activity of day.activities" class="activity">
                      <div class="activity-time">{{ activity.time }}</div>
                      <div class="activity-details">
                        <h6>{{ activity.name }}</h6>
                        <p class="location">📍 {{ activity.location }}</p>
                        <p class="description">{{ activity.description }}</p>
                        <div class="activity-meta">
                          <span class="duration">⏱️ {{ activity.duration }}</span>
                          <span *ngIf="activity.cost" class="cost">💰 {{ activity.cost }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Trip Highlights -->
            <div class="highlights-section">
              <h4>✨ Trip Highlights</h4>
              <ul class="highlights-list">
                <li *ngFor="let highlight of generatedPlan.highlights">{{ highlight }}</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- User Trip History -->
      <div class="trip-history">
        <div class="history-tabs">
          <button 
            class="tab-btn"
            [class.active]="activeTab === 'upcoming'"
            (click)="activeTab = 'upcoming'">
            Upcoming Trips ({{ currentUser?.upcomingTrips?.length || 0 }})
          </button>
          <button 
            class="tab-btn"
            [class.active]="activeTab === 'past'"
            (click)="activeTab = 'past'">
            Past Trips ({{ currentUser?.pastTrips?.length || 0 }})
          </button>
        </div>

        <div class="trip-cards">
          <div *ngFor="let trip of activeTab === 'upcoming' ? (currentUser?.upcomingTrips || []) : (currentUser?.pastTrips || [])" 
               class="trip-card"
               (click)="viewTripDetails(trip)">
            <div class="trip-card-header">
              <h4>{{ trip.title }}</h4>
              <span class="trip-status" [class]="trip.status">{{ trip.status }}</span>
            </div>
            <p class="trip-description">{{ trip.description }}</p>
            <div class="trip-card-meta">
              <span class="duration">{{ trip.duration }}</span>
              <span class="cost">{{ trip.estimatedCost }}</span>
              <span class="date">{{ trip.created | date:'mediumDate' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .agent-demo-container {
      padding: 80px 20px 20px 20px;
      max-width: 1400px;
      margin: 0 auto;
      background: linear-gradient(135deg, #001e3c 0%, #003366 50%, #001e3c 100%);
      min-height: 100vh;
      color: white;
    }

    .user-profile {
      background: rgba(0, 30, 60, 0.9);
      border: 1px solid #4fc3f7;
      border-radius: 15px;
      padding: 20px;
      margin-bottom: 30px;
    }

    .profile-header {
      display: flex;
      align-items: center;
      gap: 20px;
    }

    .avatar {
      width: 60px;
      height: 60px;
      border-radius: 50%;
      background: #4fc3f7;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
      font-weight: bold;
      color: #001e3c;
    }

    .profile-info h2 {
      margin: 0;
      color: #4fc3f7;
    }

    .profile-info p {
      margin: 5px 0;
      opacity: 0.8;
    }

    .trip-stats {
      display: flex;
      gap: 20px;
      margin-top: 10px;
    }

    .stat {
      background: rgba(79, 195, 247, 0.2);
      padding: 5px 10px;
      border-radius: 5px;
      font-size: 0.9rem;
    }

    .planning-interface {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 30px;
      margin-bottom: 40px;
    }

    .input-section {
      background: rgba(0, 30, 60, 0.9);
      border: 1px solid #4fc3f7;
      border-radius: 15px;
      padding: 25px;
    }

    .input-section h3 {
      color: #4fc3f7;
      margin-bottom: 10px;
    }

    .trip-form {
      margin-top: 20px;
    }

    .form-row {
      display: flex;
      gap: 15px;
      margin-bottom: 15px;
    }

    .form-group {
      flex: 1;
    }

    .form-group label {
      display: block;
      margin-bottom: 5px;
      color: #4fc3f7;
      font-weight: bold;
    }

    .form-group input,
    .form-group select {
      width: 100%;
      padding: 10px;
      border: 1px solid #4fc3f7;
      border-radius: 5px;
      background: rgba(0, 0, 0, 0.3);
      color: white;
    }

    .interest-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 5px;
    }

    .interest-tag {
      padding: 8px 12px;
      background: rgba(0, 0, 0, 0.3);
      border: 1px solid #666;
      border-radius: 20px;
      cursor: pointer;
      transition: all 0.3s ease;
      font-size: 0.9rem;
    }

    .interest-tag.selected {
      background: #4fc3f7;
      color: #001e3c;
      border-color: #4fc3f7;
    }

    .interest-tag:hover {
      border-color: #4fc3f7;
    }

    .agent-prompt {
      margin: 20px 0;
    }

    .agent-prompt textarea {
      width: 100%;
      padding: 12px;
      border: 1px solid #4fc3f7;
      border-radius: 8px;
      background: rgba(0, 0, 0, 0.3);
      color: white;
      resize: vertical;
    }

    .generate-plan-btn {
      width: 100%;
      padding: 15px;
      background: linear-gradient(45deg, #4fc3f7, #2196f3);
      color: white;
      border: none;
      border-radius: 8px;
      font-size: 1.1rem;
      font-weight: bold;
      cursor: pointer;
      transition: all 0.3s ease;
    }

    .generate-plan-btn:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 10px 20px rgba(79, 195, 247, 0.3);
    }

    .generate-plan-btn:disabled {
      opacity: 0.7;
      cursor: not-allowed;
    }

    .plan-display {
      background: rgba(0, 30, 60, 0.9);
      border: 1px solid #4fc3f7;
      border-radius: 15px;
      padding: 25px;
      max-height: 80vh;
      overflow-y: auto;
    }

    .plan-header {
      display: flex;
      justify-content: between;
      align-items: center;
      margin-bottom: 20px;
      border-bottom: 1px solid rgba(79, 195, 247, 0.3);
      padding-bottom: 15px;
    }

    .plan-header h3 {
      color: #4fc3f7;
      margin: 0;
    }

    .plan-meta {
      display: flex;
      gap: 15px;
      align-items: center;
    }

    .save-plan-btn {
      background: #4caf50;
      color: white;
      border: none;
      padding: 8px 15px;
      border-radius: 5px;
      cursor: pointer;
    }

    .map-preview-section {
      margin: 20px 0;
    }

    .map-preview-section google-map {
      height: 300px;
      width: 100%;
      border-radius: 8px;
    }

    .conditions-section {
      margin: 20px 0;
    }

    .conditions-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 15px;
      margin-top: 10px;
    }

    .condition-item {
      background: rgba(0, 0, 0, 0.3);
      padding: 10px;
      border-radius: 5px;
      display: flex;
      justify-content: space-between;
    }

    .condition-item .label {
      font-weight: bold;
      color: #4fc3f7;
    }

    .orca-likelihood {
      color: #4caf50;
      font-weight: bold;
    }

    .itinerary-section {
      margin: 20px 0;
    }

    .day-plan {
      background: rgba(0, 0, 0, 0.3);
      border-radius: 8px;
      padding: 15px;
      margin: 15px 0;
    }

    .day-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 15px;
      border-bottom: 1px solid rgba(79, 195, 247, 0.2);
      padding-bottom: 10px;
    }

    .day-header h5 {
      color: #4fc3f7;
      margin: 0;
    }

    .day-meta {
      display: flex;
      gap: 15px;
      font-size: 0.9rem;
    }

    .activity {
      display: flex;
      gap: 15px;
      margin: 10px 0;
      padding: 10px;
      background: rgba(0, 0, 0, 0.2);
      border-radius: 5px;
    }

    .activity-time {
      font-weight: bold;
      color: #4fc3f7;
      min-width: 60px;
    }

    .activity-details h6 {
      margin: 0 0 5px 0;
      color: white;
    }

    .activity-details p {
      margin: 3px 0;
      font-size: 0.9rem;
      opacity: 0.8;
    }

    .activity-meta {
      display: flex;
      gap: 15px;
      margin-top: 5px;
      font-size: 0.8rem;
    }

    .highlights-section {
      margin: 20px 0;
    }

    .highlights-list {
      list-style: none;
      padding: 0;
    }

    .highlights-list li {
      background: rgba(79, 195, 247, 0.1);
      padding: 10px;
      margin: 8px 0;
      border-left: 3px solid #4fc3f7;
      border-radius: 0 5px 5px 0;
    }

    .trip-history {
      background: rgba(0, 30, 60, 0.9);
      border: 1px solid #4fc3f7;
      border-radius: 15px;
      padding: 25px;
    }

    .history-tabs {
      display: flex;
      gap: 10px;
      margin-bottom: 20px;
    }

    .tab-btn {
      padding: 10px 20px;
      background: rgba(0, 0, 0, 0.3);
      border: 1px solid #4fc3f7;
      color: white;
      border-radius: 5px;
      cursor: pointer;
      transition: all 0.3s ease;
    }

    .tab-btn.active {
      background: #4fc3f7;
      color: #001e3c;
    }

    .trip-cards {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 20px;
    }

    .trip-card {
      background: rgba(0, 0, 0, 0.3);
      border: 1px solid rgba(79, 195, 247, 0.3);
      border-radius: 8px;
      padding: 15px;
      cursor: pointer;
      transition: all 0.3s ease;
    }

    .trip-card:hover {
      border-color: #4fc3f7;
      transform: translateY(-2px);
    }

    .trip-card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
    }

    .trip-card-header h4 {
      margin: 0;
      color: #4fc3f7;
    }

    .trip-status {
      padding: 3px 8px;
      border-radius: 3px;
      font-size: 0.8rem;
      font-weight: bold;
    }

    .trip-status.upcoming {
      background: #4caf50;
      color: white;
    }

    .trip-status.past {
      background: #666;
      color: white;
    }

    .trip-card-meta {
      display: flex;
      justify-content: space-between;
      margin-top: 10px;
      font-size: 0.9rem;
      opacity: 0.8;
    }

    @media (max-width: 768px) {
      .planning-interface {
        grid-template-columns: 1fr;
      }
      
      .form-row {
        flex-direction: column;
      }
    }
  `]
})
export class AgentDemoComponent implements OnInit {
  currentUser: UserProfile | null = null;
  activeTab: 'upcoming' | 'past' = 'upcoming';
  
  tripParams: TripParameters = {
    destination: 'san-juan-islands',
    startDate: '',
    endDate: '',
    groupSize: 2,
    interests: ['orca-watching', 'photography'],
    budget: 'moderate',
    accommodation: 'b&b',
    activities: []
  };

  naturalLanguagePrompt = '';
  isGenerating = false;
  generatedPlan: TripPlan | null = null;

  availableInterests = [
    'Orca Watching', 'Photography', 'Kayaking', 'Hiking', 'Cycling',
    'Wildlife Viewing', 'Sailing', 'Museums', 'Local Cuisine', 'Beaches',
    'Festivals', 'Art Galleries', 'Whale Research', 'Marine Biology'
  ];

  mapOptions: google.maps.MapOptions = {
    zoom: 10,
    center: { lat: 48.5465, lng: -123.0307 },
    mapTypeId: google.maps.MapTypeId.TERRAIN
  };

  constructor(private backendService: BackendService) {}

  ngOnInit(): void {
    this.initializeDemoUser();
    this.setDefaultDates();
  }

  private initializeDemoUser(): void {
    this.currentUser = {
      name: 'Gil',
      email: 'gil@orcast.ai',
      preferences: {
        favoriteActivities: ['Orca Watching', 'Photography', 'Marine Biology'],
        budgetRange: 'moderate',
        travelStyle: 'adventure-focused'
      },
      pastTrips: this.generatePastTrips(),
      upcomingTrips: this.generateUpcomingTrips()
    };
  }

  private setDefaultDates(): void {
    const today = new Date();
    const nextWeek = new Date(today);
    nextWeek.setDate(today.getDate() + 7);
    const endDate = new Date(nextWeek);
    endDate.setDate(nextWeek.getDate() + 2);

    this.tripParams.startDate = nextWeek.toISOString().split('T')[0];
    this.tripParams.endDate = endDate.toISOString().split('T')[0];
  }

  toggleInterest(interest: string): void {
    const index = this.tripParams.interests.indexOf(interest);
    if (index > -1) {
      this.tripParams.interests.splice(index, 1);
    } else {
      this.tripParams.interests.push(interest);
    }
  }

  async generateTripPlan(): Promise<void> {
    this.isGenerating = true;
    
    try {
      // Simulate AI agent processing
      await this.simulateAgentProcessing();
      
      this.generatedPlan = this.generateMockTripPlan();
      
    } catch (error) {
      console.error('Error generating trip plan:', error);
    } finally {
      this.isGenerating = false;
    }
  }

  private async simulateAgentProcessing(): Promise<void> {
    const stages = [
      'Analyzing your preferences...',
      'Checking weather and orca forecasts...',
      'Finding optimal accommodations...',
      'Planning activities and routes...',
      'Optimizing schedule for orca sightings...',
      'Finalizing your perfect trip...'
    ];

    for (const stage of stages) {
      console.log(`🤖 ${stage}`);
      await new Promise(resolve => setTimeout(resolve, 800));
    }
  }

  private generateMockTripPlan(): TripPlan {
    const startDate = new Date(this.tripParams.startDate);
    const endDate = new Date(this.tripParams.endDate);
    const days = Math.ceil((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));

    return {
      id: `trip-${Date.now()}`,
      title: `Perfect San Juan Islands Adventure`,
      description: `Customized ${days}-day adventure focusing on ${this.tripParams.interests.join(', ').toLowerCase()} with ${this.tripParams.budget} budget`,
      duration: `${days} days`,
      estimatedCost: this.getEstimatedCost(days),
      highlights: [
        '95% chance of orca sightings during optimal times',
        'Access to exclusive whale research vessel tour',
        'Professional photography workshops with marine life',
        'Local marine biologist guided experiences',
        'Prime sunset viewing locations for whale photography'
      ],
      itinerary: this.generateItinerary(days, startDate),
      conditions: {
        forecast: 'Partly cloudy with excellent visibility',
        temperature: '68-75°F',
        precipitation: '10% chance',
        windSpeed: '5-10 mph',
        orcaLikelihood: 'Excellent (95% probability)',
        bestTimes: ['7:00-9:00 AM', '5:00-7:00 PM', 'High tide periods']
      },
      mapPreview: {
        center: { lat: 48.5465, lng: -123.0307 },
        zoom: 11,
        markers: this.generateMapMarkers()
      },
      created: new Date(),
      status: 'upcoming'
    };
  }

  private generateItinerary(days: number, startDate: Date): DayPlan[] {
    const itinerary: DayPlan[] = [];

    for (let i = 0; i < days; i++) {
      const date = new Date(startDate);
      date.setDate(startDate.getDate() + i);

      itinerary.push({
        day: i + 1,
        date: date.toLocaleDateString(),
        activities: this.generateDayActivities(i + 1),
        meals: ['Breakfast at B&B', 'Lunch at local cafe', 'Dinner at waterfront restaurant'],
        accommodation: 'Friday Harbor House or similar',
        weather: 'Partly cloudy, 72°F',
        orcaProbability: 85 + Math.floor(Math.random() * 15)
      });
    }

    return itinerary;
  }

  private generateDayActivities(day: number): Activity[] {
    const allActivities = [
      {
        time: '7:00 AM',
        name: 'Sunrise Orca Watching Tour',
        location: 'Friday Harbor Marina',
        description: 'Board research vessel for prime orca viewing during their most active feeding time',
        duration: '3 hours'
      },
      {
        time: '11:00 AM',
        name: 'Whale Museum & Research Center',
        location: 'Friday Harbor',
        description: 'Interactive exhibits on orca behavior, current research, and conservation efforts',
        duration: '2 hours'
      },
      {
        time: '2:00 PM',
        name: 'Lime Kiln Point Photography Session',
        location: 'Lime Kiln Point State Park',
        description: 'Professional-guided photography workshop at the premier whale watching spot',
        duration: '3 hours'
      },
      {
        time: '6:00 PM',
        name: 'Sunset Dinner Cruise',
        location: 'San Juan Island',
        description: 'Gourmet local cuisine while watching for evening orca activity',
        duration: '2.5 hours'
      }
    ];

    return allActivities.slice(0, day === 1 ? 3 : 4);
  }

  private generateMapMarkers(): MapMarker[] {
    return [
      {
        position: { lat: 48.5348, lng: -123.0133 },
        title: 'Friday Harbor House',
        type: 'accommodation',
        icon: '🏨'
      },
      {
        position: { lat: 48.5165, lng: -123.1524 },
        title: 'Lime Kiln Point - Prime Orca Spot',
        type: 'orca-spot',
        icon: '🐋'
      },
      {
        position: { lat: 48.5348, lng: -123.0133 },
        title: 'Whale Museum',
        type: 'activity',
        icon: '🏛️'
      },
      {
        position: { lat: 48.4865, lng: -123.0924 },
        title: 'False Bay Orca Viewing',
        type: 'orca-spot',
        icon: '🐋'
      }
    ];
  }

  private getEstimatedCost(days: number): string {
    const dailyCosts = {
      budget: 150,
      moderate: 300,
      luxury: 500
    };
    
    const daily = dailyCosts[this.tripParams.budget as keyof typeof dailyCosts];
    const total = daily * days * this.tripParams.groupSize;
    
    return `$${total.toLocaleString()} total`;
  }

  savePlan(): void {
    if (this.generatedPlan && this.currentUser) {
      this.currentUser.upcomingTrips.unshift(this.generatedPlan);
      console.log('Trip plan saved to user profile!');
    }
  }

  viewTripDetails(trip: TripPlan): void {
    console.log('Viewing trip details:', trip);
    // Could open a detailed view modal or navigate to trip detail page
  }

  private generatePastTrips(): TripPlan[] {
    return [
      {
        id: 'past-1',
        title: 'Summer Orca Research Expedition',
        description: '5-day intensive orca research participation with University of Washington',
        duration: '5 days',
        estimatedCost: '$2,400 total',
        highlights: ['Participated in orca tagging expedition', 'Collected acoustic data', 'Observed J-Pod family interactions'],
        itinerary: [],
        conditions: {} as WeatherConditions,
        mapPreview: {} as MapPreview,
        created: new Date('2024-07-15'),
        status: 'past'
      },
      {
        id: 'past-2',
        title: 'Photography Workshop Weekend',
        description: '3-day marine wildlife photography intensive',
        duration: '3 days',
        estimatedCost: '$1,200 total',
        highlights: ['Captured award-winning orca breach photo', 'Learned underwater photography techniques'],
        itinerary: [],
        conditions: {} as WeatherConditions,
        mapPreview: {} as MapPreview,
        created: new Date('2024-05-20'),
        status: 'past'
      }
    ];
  }

  private generateUpcomingTrips(): TripPlan[] {
    return [
      {
        id: 'upcoming-1',
        title: 'Winter Orca Migration Study',
        description: '4-day winter orca behavior research trip',
        duration: '4 days',
        estimatedCost: '$1,800 total',
        highlights: ['Study winter feeding patterns', 'Collaborate with marine biologists'],
        itinerary: [],
        conditions: {} as WeatherConditions,
        mapPreview: {} as MapPreview,
        created: new Date('2024-12-15'),
        status: 'upcoming'
      }
    ];
  }
} 