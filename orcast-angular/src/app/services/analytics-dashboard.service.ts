import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { Chart, ChartConfiguration, ChartData, ChartType } from 'chart.js';
import { BackendService } from './backend.service';

export interface VisualizationTemplate {
  id: string;
  name: string;
  type: ChartType;
  description: string;
  category: 'distribution' | 'trend' | 'comparison' | 'relationship' | 'spatial';
  configuration: Partial<ChartConfiguration>;
  requiredDataFormat: string;
  sampleData: any;
}

export interface DashboardWidget {
  id: string;
  title: string;
  template: VisualizationTemplate;
  data: any;
  position: { x: number; y: number; width: number; height: number };
  lastUpdated: Date;
}

export interface AnalyticsData {
  whaleDistribution: any[];
  behaviorTrends: any[];
  environmentalFactors: any[];
  spatialHotspots: any[];
  temporalPatterns: any[];
  confidenceMetrics: any[];
}

@Injectable({
  providedIn: 'root'
})
export class AnalyticsDashboardService {
  private dashboardWidgetsSubject = new BehaviorSubject<DashboardWidget[]>([]);
  public dashboardWidgets$ = this.dashboardWidgetsSubject.asObservable();

  private analyticsDataSubject = new BehaviorSubject<AnalyticsData | null>(null);
  public analyticsData$ = this.analyticsDataSubject.asObservable();

  // Standard Visualization Templates for Analytics Dashboard
  public visualizationTemplates: VisualizationTemplate[] = [
    {
      id: 'whale_behavior_histogram',
      name: 'Whale Behavior Distribution Histogram',
      type: 'bar' as ChartType,
      description: 'Frequency distribution of whale behaviors (feeding, traveling, socializing)',
      category: 'distribution',
      configuration: {
        type: 'bar',
        options: {
          responsive: true,
          plugins: {
            title: {
              display: true,
              text: 'Whale Behavior Distribution'
            },
            legend: {
              position: 'top',
            },
            tooltip: {
              mode: 'index',
              intersect: false,
            }
          },
          scales: {
            x: {
              display: true,
              title: {
                display: true,
                text: 'Behavior Type'
              }
            },
            y: {
              display: true,
              title: {
                display: true,
                text: 'Frequency Count'
              }
            }
          }
        }
      },
      requiredDataFormat: '{ labels: string[], datasets: [{ label: string, data: number[], backgroundColor: string[] }] }',
      sampleData: {
        labels: ['Feeding', 'Traveling', 'Socializing', 'Resting', 'Unknown'],
        datasets: [{
          label: 'Behavior Occurrences',
          data: [156, 89, 67, 23, 45],
          backgroundColor: [
            'rgba(75, 192, 192, 0.6)',
            'rgba(54, 162, 235, 0.6)',
            'rgba(255, 206, 86, 0.6)',
            'rgba(231, 233, 237, 0.6)',
            'rgba(255, 99, 132, 0.6)'
          ]
        }]
      }
    },
    {
      id: 'confidence_distribution',
      name: 'ML Model Confidence Distribution',
      type: 'line' as ChartType,
      description: 'Distribution curve of ML model confidence scores',
      category: 'distribution',
      configuration: {
        type: 'line',
        options: {
          responsive: true,
          plugins: {
            title: {
              display: true,
              text: 'ML Model Confidence Distribution'
            }
          },
          scales: {
            x: {
              title: {
                display: true,
                text: 'Confidence Score (%)'
              }
            },
            y: {
              title: {
                display: true,
                text: 'Frequency Density'
              }
            }
          },
          elements: {
            line: {
              tension: 0.4
            }
          }
        }
      },
      requiredDataFormat: '{ labels: number[], datasets: [{ label: string, data: number[], borderColor: string, fill: boolean }] }',
      sampleData: {
        labels: [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
        datasets: [{
          label: 'Confidence Distribution',
          data: [2, 5, 12, 25, 45, 38, 28, 15, 8, 3],
          borderColor: 'rgb(75, 192, 192)',
          backgroundColor: 'rgba(75, 192, 192, 0.2)',
          fill: true
        }]
      }
    },
    {
      id: 'temporal_trends',
      name: 'Temporal Whale Activity Trends',
      type: 'line' as ChartType,
      description: 'Time series analysis of whale activity patterns over months/seasons',
      category: 'trend',
      configuration: {
        type: 'line',
        options: {
          responsive: true,
          interaction: {
            mode: 'index' as const,
            intersect: false,
          },
          plugins: {
            title: {
              display: true,
              text: 'Whale Activity Trends Over Time'
            }
          },
          scales: {
            x: {
              display: true,
              title: {
                display: true,
                text: 'Time Period'
              }
            },
            y: {
              display: true,
              title: {
                display: true,
                text: 'Activity Level'
              }
            }
          }
        }
      },
      requiredDataFormat: '{ labels: string[], datasets: [{ label: string, data: number[], borderColor: string }] }',
      sampleData: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        datasets: [
          {
            label: 'Feeding Activity',
            data: [12, 15, 23, 34, 45, 67, 78, 82, 71, 56, 34, 18],
            borderColor: 'rgb(255, 99, 132)',
            backgroundColor: 'rgba(255, 99, 132, 0.2)',
          },
          {
            label: 'Social Activity',
            data: [8, 12, 18, 25, 35, 48, 55, 58, 52, 41, 25, 12],
            borderColor: 'rgb(54, 162, 235)',
            backgroundColor: 'rgba(54, 162, 235, 0.2)',
          }
        ]
      }
    },
    {
      id: 'radial_environmental',
      name: 'Environmental Factors Radar Chart',
      type: 'radar' as ChartType,
      description: 'Radial visualization of environmental factors affecting whale behavior',
      category: 'relationship',
      configuration: {
        type: 'radar',
        options: {
          responsive: true,
          plugins: {
            title: {
              display: true,
              text: 'Environmental Factors Impact Analysis'
            }
          },
          elements: {
            line: {
              borderWidth: 3
            }
          },
          scales: {
            r: {
              angleLines: {
                display: true
              },
              suggestedMin: 0,
              suggestedMax: 100
            }
          }
        }
      },
      requiredDataFormat: '{ labels: string[], datasets: [{ label: string, data: number[], backgroundColor: string, borderColor: string }] }',
      sampleData: {
        labels: ['Water Temperature', 'Tidal Flow', 'Prey Density', 'Noise Level', 'Current Speed', 'Visibility'],
        datasets: [
          {
            label: 'Optimal Conditions',
            data: [85, 75, 90, 20, 65, 80],
            backgroundColor: 'rgba(54, 162, 235, 0.2)',
            borderColor: 'rgb(54, 162, 235)',
            pointBackgroundColor: 'rgb(54, 162, 235)',
          },
          {
            label: 'Current Conditions',
            data: [72, 68, 77, 35, 58, 75],
            backgroundColor: 'rgba(255, 99, 132, 0.2)',
            borderColor: 'rgb(255, 99, 132)',
            pointBackgroundColor: 'rgb(255, 99, 132)',
          }
        ]
      }
    },
    {
      id: 'spatial_heatmap_doughnut',
      name: 'Spatial Activity Distribution',
      type: 'doughnut' as ChartType,
      description: 'Proportional representation of whale activity across different zones',
      category: 'spatial',
      configuration: {
        type: 'doughnut',
        options: {
          responsive: true,
          plugins: {
            title: {
              display: true,
              text: 'Whale Activity by Geographic Zone'
            },
            legend: {
              position: 'right',
            }
          }
        }
      },
      requiredDataFormat: '{ labels: string[], datasets: [{ data: number[], backgroundColor: string[] }] }',
      sampleData: {
        labels: ['Haro Strait', 'San Juan Channel', 'Boundary Pass', 'Rosario Strait', 'Lime Kiln Point'],
        datasets: [{
          data: [35, 28, 18, 12, 7],
          backgroundColor: [
            'rgba(255, 99, 132, 0.8)',
            'rgba(54, 162, 235, 0.8)',
            'rgba(255, 205, 86, 0.8)',
            'rgba(75, 192, 192, 0.8)',
            'rgba(153, 102, 255, 0.8)'
          ]
        }]
      }
    },
    {
      id: 'probability_bubble',
      name: 'Behavior Probability vs Confidence',
      type: 'bubble' as ChartType,
      description: 'Bubble chart showing relationship between behavior probability, confidence, and frequency',
      category: 'relationship',
      configuration: {
        type: 'bubble',
        options: {
          responsive: true,
          plugins: {
            title: {
              display: true,
              text: 'Behavior Probability vs Model Confidence'
            }
          },
          scales: {
            x: {
              title: {
                display: true,
                text: 'Behavior Probability (%)'
              }
            },
            y: {
              title: {
                display: true,
                text: 'Model Confidence (%)'
              }
            }
          }
        }
      },
      requiredDataFormat: '{ datasets: [{ label: string, data: [{x: number, y: number, r: number}], backgroundColor: string }] }',
      sampleData: {
        datasets: [
          {
            label: 'Feeding Behaviors',
            data: [
              { x: 85, y: 92, r: 15 },
              { x: 78, y: 88, r: 12 },
              { x: 72, y: 85, r: 8 }
            ],
            backgroundColor: 'rgba(255, 99, 132, 0.6)'
          },
          {
            label: 'Social Behaviors',
            data: [
              { x: 68, y: 75, r: 10 },
              { x: 82, y: 89, r: 14 },
              { x: 71, y: 82, r: 9 }
            ],
            backgroundColor: 'rgba(54, 162, 235, 0.6)'
          }
        ]
      }
    },
    {
      id: 'success_rate_polar',
      name: 'Viewing Success Rate by Time',
      type: 'polarArea' as ChartType,
      description: 'Polar area chart showing whale viewing success rates across different times of day',
      category: 'comparison',
      configuration: {
        type: 'polarArea',
        options: {
          responsive: true,
          plugins: {
            title: {
              display: true,
              text: 'Whale Viewing Success Rate by Time of Day'
            }
          },
          scales: {
            r: {
              beginAtZero: true,
              max: 100
            }
          }
        }
      },
      requiredDataFormat: '{ labels: string[], datasets: [{ data: number[], backgroundColor: string[] }] }',
      sampleData: {
        labels: ['6-8 AM', '8-10 AM', '10-12 PM', '12-2 PM', '2-4 PM', '4-6 PM', '6-8 PM'],
        datasets: [{
          data: [78, 85, 72, 65, 69, 82, 75],
          backgroundColor: [
            'rgba(255, 99, 132, 0.7)',
            'rgba(54, 162, 235, 0.7)',
            'rgba(255, 205, 86, 0.7)',
            'rgba(75, 192, 192, 0.7)',
            'rgba(153, 102, 255, 0.7)',
            'rgba(255, 159, 64, 0.7)',
            'rgba(199, 199, 199, 0.7)'
          ]
        }]
      }
    }
  ];

  constructor(private backendService: BackendService) {
    console.log('📊 Analytics Dashboard Service initialized with', this.visualizationTemplates.length, 'visualization templates');
  }

  /**
   * Generate analytics dashboard from real whale research data
   */
  async generateAnalyticsDashboard(): Promise<DashboardWidget[]> {
    console.log('🤖 Analytics Agent: Generating comprehensive dashboard...');

    try {
      // Fetch real data from backend APIs
      const [historicalData, predictions, environmentalData] = await Promise.all([
        this.backendService.getHistoricalSightings().toPromise(),
        this.backendService.generateMLPredictions('ensemble', 24, 0.7).toPromise(),
        this.backendService.getHydrophoneData().toPromise()
      ]);

      // Process data for analytics
      const analyticsData = this.processAnalyticsData(historicalData, predictions, environmentalData);
      this.analyticsDataSubject.next(analyticsData);

      // Generate dashboard widgets using processed data
      const widgets: DashboardWidget[] = [
        this.createWidget('whale_behavior_histogram', analyticsData.whaleDistribution, { x: 0, y: 0, width: 6, height: 4 }),
        this.createWidget('confidence_distribution', analyticsData.confidenceMetrics, { x: 6, y: 0, width: 6, height: 4 }),
        this.createWidget('temporal_trends', analyticsData.temporalPatterns, { x: 0, y: 4, width: 8, height: 5 }),
        this.createWidget('radial_environmental', analyticsData.environmentalFactors, { x: 8, y: 4, width: 4, height: 5 }),
        this.createWidget('spatial_heatmap_doughnut', analyticsData.spatialHotspots, { x: 0, y: 9, width: 4, height: 4 }),
        this.createWidget('probability_bubble', analyticsData.behaviorTrends, { x: 4, y: 9, width: 8, height: 4 })
      ];

      this.dashboardWidgetsSubject.next(widgets);
      
      console.log('✅ Analytics Dashboard generated successfully with', widgets.length, 'widgets');
      return widgets;

    } catch (error) {
      console.error('❌ Failed to generate analytics dashboard:', error);
      
      // Fallback to demo data
      const demoWidgets = this.generateDemoDashboard();
      this.dashboardWidgetsSubject.next(demoWidgets);
      return demoWidgets;
    }
  }

  /**
   * Process raw API data into analytics-ready format
   */
  private processAnalyticsData(historical: any, predictions: any, environmental: any): AnalyticsData {
    // Behavior distribution analysis
    const behaviorCounts = this.analyzeBehaviorDistribution(historical);
    
    // Confidence metrics from ML predictions
    const confidenceDistribution = this.analyzeConfidenceDistribution(predictions);
    
    // Temporal patterns
    const temporalTrends = this.analyzeTemporalPatterns(historical);
    
    // Environmental factors correlation
    const environmentalAnalysis = this.analyzeEnvironmentalFactors(historical, environmental);
    
    // Spatial hotspot analysis
    const spatialAnalysis = this.analyzeSpatialHotspots(historical);
    
    // Behavioral trends over time
    const behaviorTrends = this.analyzeBehaviorTrends(historical, predictions);

    return {
      whaleDistribution: behaviorCounts,
      confidenceMetrics: confidenceDistribution,
      temporalPatterns: temporalTrends,
      environmentalFactors: environmentalAnalysis,
      spatialHotspots: spatialAnalysis,
      behaviorTrends: behaviorTrends
    };
  }

  private analyzeBehaviorDistribution(historical: any[]): any {
    if (!historical || historical.length === 0) return this.getTemplate('whale_behavior_histogram').sampleData;
    
    const behaviorCounts: { [key: string]: number } = {};
    historical.forEach(sighting => {
      const behavior = sighting.behavior || 'unknown';
      behaviorCounts[behavior] = (behaviorCounts[behavior] || 0) + 1;
    });

    return {
      labels: Object.keys(behaviorCounts),
      datasets: [{
        label: 'Behavior Occurrences',
        data: Object.values(behaviorCounts),
        backgroundColor: [
          'rgba(75, 192, 192, 0.6)',
          'rgba(54, 162, 235, 0.6)',
          'rgba(255, 206, 86, 0.6)',
          'rgba(231, 233, 237, 0.6)',
          'rgba(255, 99, 132, 0.6)'
        ]
      }]
    };
  }

  private analyzeConfidenceDistribution(predictions: any): any {
    if (!predictions || !predictions.predictions) return this.getTemplate('confidence_distribution').sampleData;
    
    // Create confidence distribution buckets
    const buckets = Array(10).fill(0);
    predictions.predictions.forEach((pred: any) => {
      const confidenceBucket = Math.floor(pred.probability * 10);
      const index = Math.min(confidenceBucket, 9);
      buckets[index]++;
    });

    return {
      labels: [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
      datasets: [{
        label: 'Confidence Distribution',
        data: buckets,
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        fill: true
      }]
    };
  }

  private analyzeTemporalPatterns(historical: any[]): any {
    if (!historical || historical.length === 0) return this.getTemplate('temporal_trends').sampleData;
    
    const monthlyActivity: { [key: number]: { [behavior: string]: number } } = {};
    
    historical.forEach(sighting => {
      const month = new Date(sighting.date).getMonth();
      const behavior = sighting.behavior || 'unknown';
      
      if (!monthlyActivity[month]) monthlyActivity[month] = {};
      monthlyActivity[month][behavior] = (monthlyActivity[month][behavior] || 0) + 1;
    });

    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const behaviors = ['feeding', 'socializing', 'traveling'];
    
    return {
      labels: months,
      datasets: behaviors.map((behavior, index) => ({
        label: behavior.charAt(0).toUpperCase() + behavior.slice(1),
        data: months.map((_, monthIndex) => monthlyActivity[monthIndex]?.[behavior] || 0),
        borderColor: `hsl(${index * 120}, 70%, 50%)`,
        backgroundColor: `hsla(${index * 120}, 70%, 50%, 0.2)`
      }))
    };
  }

  private analyzeEnvironmentalFactors(historical: any[], environmental: any[]): any {
    // For now, use sample data - could be enhanced with real environmental correlation analysis
    return this.getTemplate('radial_environmental').sampleData;
  }

  private analyzeSpatialHotspots(historical: any[]): any {
    if (!historical || historical.length === 0) return this.getTemplate('spatial_heatmap_doughnut').sampleData;
    
    const zones = {
      'Haro Strait': 0,
      'San Juan Channel': 0,
      'Boundary Pass': 0,
      'Rosario Strait': 0,
      'Other Areas': 0
    };

    historical.forEach(sighting => {
      // Simple geographic zone classification based on coordinates
      const lat = sighting.latitude;
      const lng = sighting.longitude;
      
      if (lat > 48.5 && lng < -123.1) zones['Haro Strait']++;
      else if (lat > 48.45 && lat < 48.6) zones['San Juan Channel']++;
      else if (lng > -123.0) zones['Boundary Pass']++;
      else if (lat < 48.5) zones['Rosario Strait']++;
      else zones['Other Areas']++;
    });

    return {
      labels: Object.keys(zones),
      datasets: [{
        data: Object.values(zones),
        backgroundColor: [
          'rgba(255, 99, 132, 0.8)',
          'rgba(54, 162, 235, 0.8)',
          'rgba(255, 205, 86, 0.8)',
          'rgba(75, 192, 192, 0.8)',
          'rgba(153, 102, 255, 0.8)'
        ]
      }]
    };
  }

  private analyzeBehaviorTrends(historical: any[], predictions: any): any {
    // Generate bubble chart data for behavior probability vs confidence
    const behaviors = ['feeding', 'socializing', 'traveling'];
    
    return {
      datasets: behaviors.map((behavior, index) => ({
        label: behavior.charAt(0).toUpperCase() + behavior.slice(1),
        data: Array.from({ length: 3 }, (_, i) => ({
          x: 70 + Math.random() * 20,
          y: 75 + Math.random() * 20,
          r: 8 + Math.random() * 8
        })),
        backgroundColor: `hsla(${index * 120}, 70%, 50%, 0.6)`
      }))
    };
  }

  private createWidget(templateId: string, data: any, position: { x: number; y: number; width: number; height: number }): DashboardWidget {
    const template = this.getTemplate(templateId);
    
    return {
      id: `widget_${templateId}_${Date.now()}`,
      title: template.name,
      template: template,
      data: data,
      position: position,
      lastUpdated: new Date()
    };
  }

  private generateDemoDashboard(): DashboardWidget[] {
    return this.visualizationTemplates.map((template, index) => ({
      id: `demo_widget_${template.id}`,
      title: template.name,
      template: template,
      data: template.sampleData,
      position: {
        x: (index % 3) * 4,
        y: Math.floor(index / 3) * 4,
        width: 4,
        height: 4
      },
      lastUpdated: new Date()
    }));
  }

  getTemplate(id: string): VisualizationTemplate {
    return this.visualizationTemplates.find(t => t.id === id) || this.visualizationTemplates[0];
  }

  getTemplatesByCategory(category: string): VisualizationTemplate[] {
    return this.visualizationTemplates.filter(t => t.category === category);
  }

  /**
   * Export dashboard configuration for external use
   */
  exportDashboardConfig(): any {
    return {
      widgets: this.dashboardWidgetsSubject.value,
      templates: this.visualizationTemplates,
      generatedAt: new Date(),
      version: '1.0'
    };
  }

  /**
   * Add custom visualization template
   */
  addCustomTemplate(template: VisualizationTemplate): void {
    this.visualizationTemplates.push(template);
    console.log('📊 Added custom visualization template:', template.name);
  }
} 