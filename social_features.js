// OrCast Social Features Module
// Handles content feeds, interactions, and social networking features

class OrCastSocial {
    constructor() {
        this.currentUser = null;
        this.contentFeed = [];
        this.followingList = [];
        this.userProfiles = {};
        this.currentTrip = null;
        
        // Initialize Firebase references
        this.database = firebase.database();
        this.storage = firebase.storage();
        this.auth = firebase.auth();
        
        this.setupEventListeners();
    }
    
    // === CONTENT FEED MANAGEMENT ===
    
    async loadContentFeed(limit = 20) {
        try {
            const feedRef = this.database.ref('contentFeed')
                .orderByChild('timestamp')
                .limitToLast(limit);
            
            feedRef.on('value', (snapshot) => {
                this.contentFeed = [];
                snapshot.forEach((child) => {
                    this.contentFeed.unshift({
                        id: child.key,
                        ...child.val()
                    });
                });
                this.renderContentFeed();
            });
        } catch (error) {
            console.error('Error loading content feed:', error);
        }
    }
    
    async uploadOrcaContent(contentData) {
        try {
            const contentId = this.database.ref('contentFeed').push().key;
            
            // Upload media files to Firebase Storage
            const mediaUrls = await this.uploadMediaFiles(contentData.media, contentId);
            
            // Get precise location metadata
            const locationMetadata = await this.getLocationMetadata(contentData.location);
            
            // Create content object
            const content = {
                id: contentId,
                userId: this.currentUser.uid,
                username: this.currentUser.displayName || 'Anonymous',
                userPhoto: this.currentUser.photoURL,
                timestamp: new Date().toISOString(),
                type: contentData.type, // 'photo', 'video', 'story'
                
                // Orca-specific data
                orcaData: {
                    count: contentData.orcaCount,
                    behavior: contentData.behavior,
                    confidence: contentData.confidence,
                    podType: contentData.podType // 'single', 'small', 'medium', 'large'
                },
                
                // Location with secure metadata
                location: {
                    lat: locationMetadata.lat,
                    lng: locationMetadata.lng,
                    name: locationMetadata.name,
                    waterBody: locationMetadata.waterBody,
                    visibility: contentData.locationVisibility || 'public' // 'public', 'followers', 'private'
                },
                
                // Media content
                media: mediaUrls,
                caption: contentData.caption || '',
                tags: contentData.tags || [],
                
                // Environmental context
                environment: {
                    waterConditions: contentData.waterConditions,
                    weather: contentData.weather,
                    vesselTraffic: contentData.vesselTraffic,
                    visibility: contentData.visibility
                },
                
                // Trip context
                tripId: this.currentTrip?.id || null,
                tripDay: this.currentTrip?.currentDay || null,
                
                // Social engagement
                likes: 0,
                comments: 0,
                shares: 0,
                bookmarks: 0,
                
                // Content safety
                verified: false,
                aiAnalysis: contentData.aiAnalysis || null,
                moderationStatus: 'pending'
            };
            
            // Save to database
            await this.database.ref(`contentFeed/${contentId}`).set(content);
            
            // Update user's content count
            await this.updateUserStats('postsCount', 1);
            
            return contentId;
            
        } catch (error) {
            console.error('Error uploading orca content:', error);
            throw error;
        }
    }
    
    async uploadMediaFiles(mediaFiles, contentId) {
        const urls = [];
        
        for (let i = 0; i < mediaFiles.length; i++) {
            const file = mediaFiles[i];
            const fileRef = this.storage.ref(`content/${contentId}/${Date.now()}_${i}`);
            
            try {
                const snapshot = await fileRef.put(file);
                const url = await snapshot.ref.getDownloadURL();
                
                urls.push({
                    url: url,
                    type: file.type.startsWith('video') ? 'video' : 'image',
                    size: file.size,
                    timestamp: new Date().toISOString()
                });
            } catch (error) {
                console.error('Error uploading media:', error);
            }
        }
        
        return urls;
    }
    
    async getLocationMetadata(location) {
        try {
            // Use Google Maps Reverse Geocoding
            const response = await fetch(
                `https://maps.googleapis.com/maps/api/geocode/json?latlng=${location.lat},${location.lng}&key=${window.ORCA_CONFIG.apiKeys.GOOGLE_MAPS}`
            );
            
            const data = await response.json();
            
            if (data.results && data.results.length > 0) {
                const result = data.results[0];
                return {
                    lat: location.lat,
                    lng: location.lng,
                    name: this.extractLocationName(result),
                    waterBody: this.extractWaterBody(result),
                    fullAddress: result.formatted_address
                };
            }
            
            return {
                lat: location.lat,
                lng: location.lng,
                name: 'Unknown Location',
                waterBody: 'Unknown Waters'
            };
            
        } catch (error) {
            console.error('Error getting location metadata:', error);
            return {
                lat: location.lat,
                lng: location.lng,
                name: 'Unknown Location',
                waterBody: 'Unknown Waters'
            };
        }
    }
    
    extractLocationName(geocodeResult) {
        const components = geocodeResult.address_components;
        
        // Look for specific marine location names
        for (const component of components) {
            if (component.types.includes('establishment') || 
                component.types.includes('point_of_interest')) {
                return component.long_name;
            }
        }
        
        // Fall back to locality
        for (const component of components) {
            if (component.types.includes('locality')) {
                return component.long_name;
            }
        }
        
        return 'Unknown Location';
    }
    
    extractWaterBody(geocodeResult) {
        const formatted = geocodeResult.formatted_address;
        
        // Common water bodies in the region
        const waterBodies = [
            'Puget Sound', 'San Juan Islands', 'Strait of Georgia', 
            'Haro Strait', 'Rosario Strait', 'Admiralty Inlet',
            'Hood Canal', 'Salish Sea'
        ];
        
        for (const waterBody of waterBodies) {
            if (formatted.includes(waterBody)) {
                return waterBody;
            }
        }
        
        return 'Pacific Northwest Waters';
    }
    
    // === SOCIAL INTERACTIONS ===
    
    async likeContent(contentId) {
        try {
            const likeRef = this.database.ref(`contentLikes/${contentId}/${this.currentUser.uid}`);
            const snapshot = await likeRef.once('value');
            
            if (snapshot.exists()) {
                // Unlike
                await likeRef.remove();
                await this.updateContentStat(contentId, 'likes', -1);
                return false;
            } else {
                // Like
                await likeRef.set({
                    userId: this.currentUser.uid,
                    timestamp: new Date().toISOString()
                });
                await this.updateContentStat(contentId, 'likes', 1);
                return true;
            }
        } catch (error) {
            console.error('Error liking content:', error);
        }
    }
    
    async commentOnContent(contentId, comment) {
        try {
            const commentRef = this.database.ref(`contentComments/${contentId}`).push();
            
            await commentRef.set({
                userId: this.currentUser.uid,
                username: this.currentUser.displayName || 'Anonymous',
                userPhoto: this.currentUser.photoURL,
                comment: comment,
                timestamp: new Date().toISOString(),
                likes: 0
            });
            
            await this.updateContentStat(contentId, 'comments', 1);
            
        } catch (error) {
            console.error('Error commenting on content:', error);
        }
    }
    
    async shareContent(contentId, shareNote = '') {
        try {
            const shareRef = this.database.ref(`contentShares/${contentId}`).push();
            
            await shareRef.set({
                userId: this.currentUser.uid,
                username: this.currentUser.displayName || 'Anonymous',
                shareNote: shareNote,
                timestamp: new Date().toISOString()
            });
            
            await this.updateContentStat(contentId, 'shares', 1);
            
            // Add to user's shared content
            await this.database.ref(`userShares/${this.currentUser.uid}/${contentId}`).set({
                shareNote: shareNote,
                timestamp: new Date().toISOString()
            });
            
        } catch (error) {
            console.error('Error sharing content:', error);
        }
    }
    
    async bookmarkContent(contentId) {
        try {
            const bookmarkRef = this.database.ref(`userBookmarks/${this.currentUser.uid}/${contentId}`);
            const snapshot = await bookmarkRef.once('value');
            
            if (snapshot.exists()) {
                // Remove bookmark
                await bookmarkRef.remove();
                await this.updateContentStat(contentId, 'bookmarks', -1);
                return false;
            } else {
                // Add bookmark
                await bookmarkRef.set({
                    timestamp: new Date().toISOString()
                });
                await this.updateContentStat(contentId, 'bookmarks', 1);
                return true;
            }
        } catch (error) {
            console.error('Error bookmarking content:', error);
        }
    }
    
    // === TRIP DOCUMENTATION ===
    
    async startTrip(tripData) {
        try {
            const tripId = this.database.ref('userTrips').push().key;
            
            this.currentTrip = {
                id: tripId,
                userId: this.currentUser.uid,
                title: tripData.title,
                description: tripData.description,
                startDate: new Date().toISOString(),
                endDate: tripData.endDate,
                currentDay: 1,
                locations: [],
                content: [],
                stats: {
                    orcaEncounters: 0,
                    photosShared: 0,
                    videosShared: 0,
                    distanceTraveled: 0
                }
            };
            
            await this.database.ref(`userTrips/${this.currentUser.uid}/${tripId}`).set(this.currentTrip);
            
            // Set active trip
            await this.database.ref(`users/${this.currentUser.uid}/activeTrip`).set(tripId);
            
            return tripId;
            
        } catch (error) {
            console.error('Error starting trip:', error);
        }
    }
    
    async addToTrip(contentId) {
        if (!this.currentTrip) return;
        
        try {
            await this.database.ref(`userTrips/${this.currentUser.uid}/${this.currentTrip.id}/content/${contentId}`).set({
                day: this.currentTrip.currentDay,
                timestamp: new Date().toISOString()
            });
            
            // Update trip stats
            await this.updateTripStats();
            
        } catch (error) {
            console.error('Error adding to trip:', error);
        }
    }
    
    async updateTripStats() {
        // This would calculate trip statistics based on content added
        // Implementation would depend on specific requirements
    }
    
    // === USER PROFILES & FOLLOWING ===
    
    async followUser(userId) {
        try {
            const followRef = this.database.ref(`userFollows/${this.currentUser.uid}/${userId}`);
            const snapshot = await followRef.once('value');
            
            if (snapshot.exists()) {
                // Unfollow
                await followRef.remove();
                await this.database.ref(`userFollowers/${userId}/${this.currentUser.uid}`).remove();
                return false;
            } else {
                // Follow
                await followRef.set({
                    timestamp: new Date().toISOString()
                });
                await this.database.ref(`userFollowers/${userId}/${this.currentUser.uid}`).set({
                    timestamp: new Date().toISOString()
                });
                return true;
            }
        } catch (error) {
            console.error('Error following user:', error);
        }
    }
    
    async updateUserStats(stat, increment) {
        try {
            const userRef = this.database.ref(`users/${this.currentUser.uid}/stats/${stat}`);
            const snapshot = await userRef.once('value');
            const currentValue = snapshot.val() || 0;
            await userRef.set(currentValue + increment);
        } catch (error) {
            console.error('Error updating user stats:', error);
        }
    }
    
    async updateContentStat(contentId, stat, increment) {
        try {
            const statRef = this.database.ref(`contentFeed/${contentId}/${stat}`);
            const snapshot = await statRef.once('value');
            const currentValue = snapshot.val() || 0;
            await statRef.set(currentValue + increment);
        } catch (error) {
            console.error('Error updating content stat:', error);
        }
    }
    
    // === UI RENDERING ===
    
    renderContentFeed() {
        const feedContainer = document.getElementById('contentFeed');
        if (!feedContainer) return;
        
        feedContainer.innerHTML = '';
        
        this.contentFeed.forEach(content => {
            const contentElement = this.createContentElement(content);
            feedContainer.appendChild(contentElement);
        });
    }
    
    createContentElement(content) {
        const element = document.createElement('div');
        element.className = 'content-item';
        element.innerHTML = `
            <div class="content-header">
                <img src="${content.userPhoto || '/default-avatar.png'}" class="user-avatar">
                <div class="user-info">
                    <div class="username">${content.username}</div>
                    <div class="location">${content.location.name}</div>
                    <div class="timestamp">${this.formatTimestamp(content.timestamp)}</div>
                </div>
                <div class="orca-badge">
                    ORCA ${content.orcaData.count} ${content.orcaData.behavior}
                </div>
            </div>
            
            <div class="content-media">
                ${this.renderMedia(content.media)}
            </div>
            
            <div class="content-actions">
                <button class="like-btn ${content.userLiked ? 'liked' : ''}" onclick="orcastSocial.likeContent('${content.id}')">
                    ❤️ ${content.likes}
                </button>
                <button class="comment-btn" onclick="orcastSocial.showComments('${content.id}')">
                    💬 ${content.comments}
                </button>
                <button class="share-btn" onclick="orcastSocial.shareContent('${content.id}')">
                    📤 ${content.shares}
                </button>
                <button class="bookmark-btn ${content.userBookmarked ? 'bookmarked' : ''}" onclick="orcastSocial.bookmarkContent('${content.id}')">
                    🔖 ${content.bookmarks}
                </button>
            </div>
            
            <div class="content-caption">
                ${content.caption}
            </div>
            
            <div class="content-metadata">
                <div class="environmental-data">
                    WATER ${content.environment.waterConditions} | 
                    VESSEL ${content.environment.vesselTraffic} | 
                    CONFIDENCE ${content.orcaData.confidence}
                </div>
            </div>
        `;
        
        return element;
    }
    
    renderMedia(mediaArray) {
        return mediaArray.map(media => {
            if (media.type === 'video') {
                return `<video src="${media.url}" controls class="content-video"></video>`;
            } else {
                return `<img src="${media.url}" class="content-image">`;
            }
        }).join('');
    }
    
    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        if (diff < 60000) return 'Just now';
        if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
        return `${Math.floor(diff / 86400000)}d ago`;
    }
    
    // === EVENT LISTENERS ===
    
    setupEventListeners() {
        // Set up auth state listener
        this.auth.onAuthStateChanged((user) => {
            this.currentUser = user;
            if (user) {
                this.loadContentFeed();
                this.loadUserTrips();
            }
        });
        
        // Set up real-time listeners for social features
        this.setupRealtimeListeners();
    }
    
    setupRealtimeListeners() {
        // Listen for new content
        this.database.ref('contentFeed').on('child_added', (snapshot) => {
            // Handle new content in real-time
            this.handleNewContent(snapshot.val());
        });
        
        // Listen for engagement updates
        this.database.ref('contentLikes').on('value', (snapshot) => {
            this.updateEngagementUI(snapshot.val());
        });
    }
    
    handleNewContent(content) {
        // Show notification for new content from followed users
        if (this.followingList.includes(content.userId)) {
            this.showNotification(`${content.username} shared a new orca encounter!`);
        }
    }
    
    updateEngagementUI(likesData) {
        // Update like counts in real-time
        Object.keys(likesData).forEach(contentId => {
            const likeCount = Object.keys(likesData[contentId]).length;
            const likeBtn = document.querySelector(`[data-content-id="${contentId}"] .like-btn`);
            if (likeBtn) {
                likeBtn.textContent = `❤️ ${likeCount}`;
            }
        });
    }
    
    showNotification(message) {
        // Show in-app notification
        const notification = document.createElement('div');
        notification.className = 'notification';
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
}

// Initialize the social system
const orcastSocial = new OrCastSocial(); 