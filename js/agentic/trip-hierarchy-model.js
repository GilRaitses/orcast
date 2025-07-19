/**
 * Hierarchical Trip Data Model for ORCAST
 * 
 * Structure:
 * Trip → Days → Day Trips → Stops → Activities → Viewing Zones
 */

class TripHierarchyModel {
    constructor() {
        this.schema = this.defineSchema();
        this.validators = this.defineValidators();
    }

    defineSchema() {
        return {
            trip: {
                id: 'string', // Unique trip identifier
                title: 'string', // Human-readable trip title
                description: 'string', // Trip description
                duration: 'number', // Total days
                startDate: 'ISO_date_string',
                endDate: 'ISO_date_string',
                
                // Trip-level metadata
                constraints: 'object', // Original user constraints
                totalCost: 'number', // Estimated total cost
                groupSize: 'number', // Number of participants
                difficulty: 'enum:easy|moderate|challenging',
                
                // Analytics and confidence
                overallProbability: 'number', // 0-1 overall success probability
                confidence: 'number', // 0-1 confidence in plan
                
                // Hierarchy
                days: 'array[Day]', // Array of Day objects
                
                // Metadata
                createdAt: 'ISO_datetime_string',
                updatedAt: 'ISO_datetime_string',
                createdBy: 'string', // Agent or user
                version: 'string'
            },

            day: {
                id: 'string', // Unique day identifier
                tripId: 'string', // Parent trip reference
                dayNumber: 'number', // 1-based day number
                date: 'ISO_date_string', // Specific date
                
                // Day-level information
                theme: 'string', // Daily theme (e.g., "High-probability foraging zones")
                weather: 'object', // Weather forecast/conditions
                tidalConditions: 'object', // Tidal information
                
                // Day statistics
                estimatedCost: 'number',
                estimatedTravelTime: 'number', // Minutes
                totalViewingTime: 'number', // Minutes
                probabilityScore: 'number', // 0-1 daily probability
                
                // Hierarchy
                dayTrips: 'array[DayTrip]', // Array of DayTrip objects
                
                // Metadata
                alternatives: 'array[object]', // Alternative day plans
                contingencyPlans: 'array[object]' // Weather/condition backup plans
            },

            dayTrip: {
                id: 'string', // Unique day trip identifier
                dayId: 'string', // Parent day reference
                title: 'string', // Trip title
                description: 'string',
                
                // Timing
                startTime: 'time_string', // "09:00"
                endTime: 'time_string', // "15:00"
                duration: 'number', // Minutes
                
                // Trip characteristics
                type: 'enum:land_based|boat_based|mixed',
                transportationMethod: 'string',
                difficulty: 'enum:easy|moderate|challenging',
                cost: 'number',
                
                // Planning metadata
                probabilityScore: 'number', // 0-1 trip probability
                confidence: 'number', // 0-1 confidence
                reasoning: 'string', // Why this trip is recommended
                
                // Hierarchy
                stops: 'array[Stop]', // Array of Stop objects
                
                // Logistics
                meetingPoint: 'object', // GPS coordinates and description
                equipment: 'array[string]', // Required equipment
                tips: 'array[string]' // Helpful tips
            },

            stop: {
                id: 'string', // Unique stop identifier
                dayTripId: 'string', // Parent day trip reference
                name: 'string', // Stop name
                description: 'string',
                
                // Location
                coordinates: 'object', // {lat, lng}
                address: 'string',
                accessInfo: 'string', // How to access this stop
                
                // Timing
                arrivalTime: 'time_string',
                departureTime: 'time_string',
                duration: 'number', // Minutes at this stop
                
                // Stop characteristics
                type: 'enum:viewing_point|parking|rest_area|facility',
                facilities: 'array[string]', // Available facilities
                accessibility: 'object', // Accessibility information
                cost: 'number', // Cost for this stop (parking, entry, etc.)
                
                // Viewing information
                viewingConditions: 'object',
                probabilityScore: 'number', // 0-1 orca probability at this stop
                bestViewingTimes: 'array[object]', // Optimal times
                
                // Hierarchy
                activities: 'array[Activity]', // Array of Activity objects
                
                // Content
                photos: 'array[object]', // Available photos
                videos: 'array[object]', // Available videos
                reviews: 'array[object]' // User reviews/experiences
            },

            activity: {
                id: 'string', // Unique activity identifier
                stopId: 'string', // Parent stop reference
                title: 'string', // Activity title
                description: 'string',
                
                // Activity details
                type: 'enum:viewing|photography|education|hiking|boat_tour',
                duration: 'number', // Minutes
                cost: 'number',
                difficulty: 'enum:easy|moderate|challenging',
                
                // Requirements
                equipment: 'array[string]', // Required equipment
                skills: 'array[string]', // Required skills
                groupSize: 'object', // {min, max, optimal}
                
                // Orca-specific
                expectedBehaviors: 'array[string]', // Expected orca behaviors
                probabilityScore: 'number', // 0-1 probability for this activity
                seasonality: 'object', // Seasonal information
                
                // Hierarchy
                viewingZones: 'array[ViewingZone]', // Array of ViewingZone objects
                
                // Content and guidance
                instructions: 'array[string]', // Step-by-step instructions
                tips: 'array[string]', // Expert tips
                safetyInfo: 'array[string]', // Safety information
                alternatives: 'array[object]' // Alternative activities
            },

            viewingZone: {
                id: 'string', // Unique zone identifier
                activityId: 'string', // Parent activity reference
                name: 'string', // Zone name
                description: 'string',
                
                // Precise location
                coordinates: 'object', // {lat, lng}
                bounds: 'object', // Zone boundaries
                area: 'number', // Square meters
                
                // Zone characteristics
                type: 'enum:feeding_zone|traveling_corridor|resting_area|play_zone',
                waterDepth: 'number', // Meters
                substrate: 'string', // Bottom type
                currentFlow: 'object', // Current information
                
                // Orca data
                probability: 'number', // 0-1 current orca probability
                confidence: 'number', // 0-1 confidence in probability
                recentSightings: 'array[object]', // Recent sighting data
                historicalData: 'object', // Historical patterns
                
                // Environmental
                environmental: 'object', // Current environmental conditions
                prey: 'object', // Prey availability information
                humanActivity: 'object', // Vessel traffic, noise levels
                
                // Behavioral predictions
                expectedBehaviors: 'array[object]', // Predicted behaviors with probabilities
                optimalConditions: 'object', // Optimal viewing conditions
                timeWindows: 'array[object]', // Best viewing time windows
                
                // Vector space data
                vectorEmbedding: 'array[number]', // 128-dimensional vector
                similarity: 'object', // Similarity to other zones
                content: 'object', // Available content (photos, videos, descriptions)
                
                // Real-time data
                liveData: 'object', // Real-time environmental/sighting data
                alerts: 'array[object]', // Current alerts or notifications
                lastUpdated: 'ISO_datetime_string'
            }
        };
    }

    defineValidators() {
        return {
            trip: (trip) => this.validateTrip(trip),
            day: (day) => this.validateDay(day),
            dayTrip: (dayTrip) => this.validateDayTrip(dayTrip),
            stop: (stop) => this.validateStop(stop),
            activity: (activity) => this.validateActivity(activity),
            viewingZone: (zone) => this.validateViewingZone(zone)
        };
    }

    /**
     * Create a new trip with the hierarchical structure
     */
    createTrip(tripData) {
        const trip = {
            id: this.generateId('trip'),
            title: tripData.title || 'ORCAST Orca Watching Adventure',
            description: tripData.description || '',
            duration: tripData.duration || 3,
            startDate: tripData.startDate || new Date().toISOString().split('T')[0],
            endDate: this.calculateEndDate(tripData.startDate, tripData.duration),
            
            constraints: tripData.constraints || {},
            totalCost: 0,
            groupSize: tripData.groupSize || 1,
            difficulty: tripData.difficulty || 'easy',
            
            overallProbability: 0,
            confidence: 0,
            
            days: [],
            
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
            createdBy: 'multi-agent-orchestrator',
            version: '1.0'
        };

        this.validateTrip(trip);
        return trip;
    }

    /**
     * Add a day to a trip
     */
    addDay(trip, dayData) {
        const day = {
            id: this.generateId('day'),
            tripId: trip.id,
            dayNumber: trip.days.length + 1,
            date: this.calculateDayDate(trip.startDate, trip.days.length),
            
            theme: dayData.theme || `Day ${trip.days.length + 1} Adventure`,
            weather: dayData.weather || {},
            tidalConditions: dayData.tidalConditions || {},
            
            estimatedCost: 0,
            estimatedTravelTime: 0,
            totalViewingTime: 0,
            probabilityScore: 0,
            
            dayTrips: [],
            
            alternatives: [],
            contingencyPlans: []
        };

        trip.days.push(day);
        this.updateTripMetadata(trip);
        return day;
    }

    /**
     * Add a day trip to a day
     */
    addDayTrip(day, dayTripData) {
        const dayTrip = {
            id: this.generateId('daytrip'),
            dayId: day.id,
            title: dayTripData.title || 'Orca Viewing Expedition',
            description: dayTripData.description || '',
            
            startTime: dayTripData.startTime || '09:00',
            endTime: dayTripData.endTime || '15:00',
            duration: this.calculateDuration(dayTripData.startTime, dayTripData.endTime),
            
            type: dayTripData.type || 'land_based',
            transportationMethod: dayTripData.transportationMethod || 'car',
            difficulty: dayTripData.difficulty || 'easy',
            cost: dayTripData.cost || 0,
            
            probabilityScore: dayTripData.probabilityScore || 0,
            confidence: dayTripData.confidence || 0,
            reasoning: dayTripData.reasoning || '',
            
            stops: [],
            
            meetingPoint: dayTripData.meetingPoint || {},
            equipment: dayTripData.equipment || [],
            tips: dayTripData.tips || []
        };

        day.dayTrips.push(dayTrip);
        this.updateDayMetadata(day);
        return dayTrip;
    }

    /**
     * Add a stop to a day trip
     */
    addStop(dayTrip, stopData) {
        const stop = {
            id: this.generateId('stop'),
            dayTripId: dayTrip.id,
            name: stopData.name || 'Viewing Location',
            description: stopData.description || '',
            
            coordinates: stopData.coordinates || {},
            address: stopData.address || '',
            accessInfo: stopData.accessInfo || '',
            
            arrivalTime: stopData.arrivalTime || '',
            departureTime: stopData.departureTime || '',
            duration: stopData.duration || 60,
            
            type: stopData.type || 'viewing_point',
            facilities: stopData.facilities || [],
            accessibility: stopData.accessibility || {},
            cost: stopData.cost || 0,
            
            viewingConditions: stopData.viewingConditions || {},
            probabilityScore: stopData.probabilityScore || 0,
            bestViewingTimes: stopData.bestViewingTimes || [],
            
            activities: [],
            
            photos: stopData.photos || [],
            videos: stopData.videos || [],
            reviews: stopData.reviews || []
        };

        dayTrip.stops.push(stop);
        this.updateDayTripMetadata(dayTrip);
        return stop;
    }

    /**
     * Add an activity to a stop
     */
    addActivity(stop, activityData) {
        const activity = {
            id: this.generateId('activity'),
            stopId: stop.id,
            title: activityData.title || 'Orca Watching',
            description: activityData.description || '',
            
            type: activityData.type || 'viewing',
            duration: activityData.duration || 30,
            cost: activityData.cost || 0,
            difficulty: activityData.difficulty || 'easy',
            
            equipment: activityData.equipment || [],
            skills: activityData.skills || [],
            groupSize: activityData.groupSize || {min: 1, max: 10, optimal: 4},
            
            expectedBehaviors: activityData.expectedBehaviors || [],
            probabilityScore: activityData.probabilityScore || 0,
            seasonality: activityData.seasonality || {},
            
            viewingZones: [],
            
            instructions: activityData.instructions || [],
            tips: activityData.tips || [],
            safetyInfo: activityData.safetyInfo || [],
            alternatives: activityData.alternatives || []
        };

        stop.activities.push(activity);
        this.updateStopMetadata(stop);
        return activity;
    }

    /**
     * Add a viewing zone to an activity
     */
    addViewingZone(activity, zoneData) {
        const zone = {
            id: this.generateId('zone'),
            activityId: activity.id,
            name: zoneData.name || 'Viewing Zone',
            description: zoneData.description || '',
            
            coordinates: zoneData.coordinates || {},
            bounds: zoneData.bounds || {},
            area: zoneData.area || 0,
            
            type: zoneData.type || 'feeding_zone',
            waterDepth: zoneData.waterDepth || 0,
            substrate: zoneData.substrate || '',
            currentFlow: zoneData.currentFlow || {},
            
            probability: zoneData.probability || 0,
            confidence: zoneData.confidence || 0,
            recentSightings: zoneData.recentSightings || [],
            historicalData: zoneData.historicalData || {},
            
            environmental: zoneData.environmental || {},
            prey: zoneData.prey || {},
            humanActivity: zoneData.humanActivity || {},
            
            expectedBehaviors: zoneData.expectedBehaviors || [],
            optimalConditions: zoneData.optimalConditions || {},
            timeWindows: zoneData.timeWindows || [],
            
            vectorEmbedding: zoneData.vectorEmbedding || new Array(128).fill(0),
            similarity: zoneData.similarity || {},
            content: zoneData.content || {},
            
            liveData: zoneData.liveData || {},
            alerts: zoneData.alerts || [],
            lastUpdated: new Date().toISOString()
        };

        activity.viewingZones.push(zone);
        this.updateActivityMetadata(activity);
        return zone;
    }

    /**
     * Utility methods
     */
    generateId(type) {
        return `${type}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    calculateEndDate(startDate, duration) {
        const start = new Date(startDate);
        start.setDate(start.getDate() + duration - 1);
        return start.toISOString().split('T')[0];
    }

    calculateDayDate(tripStartDate, dayIndex) {
        const start = new Date(tripStartDate);
        start.setDate(start.getDate() + dayIndex);
        return start.toISOString().split('T')[0];
    }

    calculateDuration(startTime, endTime) {
        const [startHour, startMin] = startTime.split(':').map(Number);
        const [endHour, endMin] = endTime.split(':').map(Number);
        return (endHour * 60 + endMin) - (startHour * 60 + startMin);
    }

    updateTripMetadata(trip) {
        trip.totalCost = trip.days.reduce((sum, day) => 
            sum + day.dayTrips.reduce((daySum, dt) => 
                daySum + dt.cost + dt.stops.reduce((stopSum, stop) => 
                    stopSum + stop.cost + stop.activities.reduce((actSum, act) => 
                        actSum + act.cost, 0), 0), 0), 0);
        
        trip.overallProbability = this.calculateOverallProbability(trip);
        trip.confidence = this.calculateOverallConfidence(trip);
        trip.updatedAt = new Date().toISOString();
    }

    updateDayMetadata(day) {
        day.estimatedCost = day.dayTrips.reduce((sum, dt) => sum + dt.cost, 0);
        day.probabilityScore = this.calculateDayProbability(day);
    }

    updateDayTripMetadata(dayTrip) {
        // Update metadata calculations
    }

    updateStopMetadata(stop) {
        // Update metadata calculations
    }

    updateActivityMetadata(activity) {
        // Update metadata calculations
    }

    calculateOverallProbability(trip) {
        // Calculate weighted probability across all zones
        let totalProbability = 0;
        let zoneCount = 0;

        trip.days.forEach(day => {
            day.dayTrips.forEach(dayTrip => {
                dayTrip.stops.forEach(stop => {
                    stop.activities.forEach(activity => {
                        activity.viewingZones.forEach(zone => {
                            totalProbability += zone.probability * zone.confidence;
                            zoneCount++;
                        });
                    });
                });
            });
        });

        return zoneCount > 0 ? totalProbability / zoneCount : 0;
    }

    calculateOverallConfidence(trip) {
        // Calculate overall confidence
        let totalConfidence = 0;
        let zoneCount = 0;

        trip.days.forEach(day => {
            day.dayTrips.forEach(dayTrip => {
                dayTrip.stops.forEach(stop => {
                    stop.activities.forEach(activity => {
                        activity.viewingZones.forEach(zone => {
                            totalConfidence += zone.confidence;
                            zoneCount++;
                        });
                    });
                });
            });
        });

        return zoneCount > 0 ? totalConfidence / zoneCount : 0;
    }

    calculateDayProbability(day) {
        // Calculate day-level probability
        return 0.75; // Placeholder
    }

    /**
     * Validation methods
     */
    validateTrip(trip) {
        if (!trip.id || !trip.title || !trip.duration) {
            throw new Error('Trip validation failed: missing required fields');
        }
        return true;
    }

    validateDay(day) {
        if (!day.id || !day.tripId || !day.dayNumber) {
            throw new Error('Day validation failed: missing required fields');
        }
        return true;
    }

    validateDayTrip(dayTrip) {
        if (!dayTrip.id || !dayTrip.dayId || !dayTrip.title) {
            throw new Error('DayTrip validation failed: missing required fields');
        }
        return true;
    }

    validateStop(stop) {
        if (!stop.id || !stop.dayTripId || !stop.name) {
            throw new Error('Stop validation failed: missing required fields');
        }
        return true;
    }

    validateActivity(activity) {
        if (!activity.id || !activity.stopId || !activity.title) {
            throw new Error('Activity validation failed: missing required fields');
        }
        return true;
    }

    validateViewingZone(zone) {
        if (!zone.id || !zone.activityId || !zone.name) {
            throw new Error('ViewingZone validation failed: missing required fields');
        }
        return true;
    }

    /**
     * Export/Import methods
     */
    exportTrip(trip) {
        return JSON.stringify(trip, null, 2);
    }

    importTrip(tripJson) {
        const trip = JSON.parse(tripJson);
        this.validateTrip(trip);
        return trip;
    }

    /**
     * Search and query methods
     */
    findViewingZonesByProbability(trip, minProbability = 0.5) {
        const zones = [];
        
        trip.days.forEach(day => {
            day.dayTrips.forEach(dayTrip => {
                dayTrip.stops.forEach(stop => {
                    stop.activities.forEach(activity => {
                        activity.viewingZones.forEach(zone => {
                            if (zone.probability >= minProbability) {
                                zones.push({
                                    ...zone,
                                    path: {
                                        day: day.dayNumber,
                                        dayTrip: dayTrip.title,
                                        stop: stop.name,
                                        activity: activity.title
                                    }
                                });
                            }
                        });
                    });
                });
            });
        });

        return zones.sort((a, b) => b.probability - a.probability);
    }

    findActivitiesByType(trip, activityType) {
        const activities = [];
        
        trip.days.forEach(day => {
            day.dayTrips.forEach(dayTrip => {
                dayTrip.stops.forEach(stop => {
                    stop.activities.forEach(activity => {
                        if (activity.type === activityType) {
                            activities.push({
                                ...activity,
                                path: {
                                    day: day.dayNumber,
                                    dayTrip: dayTrip.title,
                                    stop: stop.name
                                }
                            });
                        }
                    });
                });
            });
        });

        return activities;
    }
}

// Export the model
window.TripHierarchyModel = TripHierarchyModel; 