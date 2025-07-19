/**
 * BlueSky Whale Sightings Importer
 * Fetches confirmed orca sightings from BlueSky social media
 */

const axios = require('axios');
const fs = require('fs');

const BLUESKY_API_BASE = 'https://bsky.social/xrpc';
const WHALE_KEYWORDS = ['orca', 'killer whale', 'whale sighting', 'j pod', 'k pod', 'l pod'];

class BlueSkyImporter {
    constructor() {
        this.session = null;
        this.rateLimitDelay = 1000; // 1 second between requests
    }

    async authenticate() {
        // Public API - no authentication needed for public posts
        console.log('✅ BlueSky public API ready');
        return true;
    }

    async searchWhalePosts(limit = 100) {
        try {
            const allPosts = [];
            
            for (const keyword of WHALE_KEYWORDS) {
                console.log(`🔍 Searching BlueSky for: "${keyword}"`);
                
                try {
                    const response = await axios.get(`${BLUESKY_API_BASE}/app.bsky.feed.searchPosts`, {
                        params: {
                            q: keyword,
                            limit: Math.floor(limit / WHALE_KEYWORDS.length),
                            sort: 'latest'
                        },
                        timeout: 10000
                    });

                    if (response.data && response.data.posts) {
                        console.log(`📝 Found ${response.data.posts.length} posts for "${keyword}"`);
                        allPosts.push(...response.data.posts);
                    }
                } catch (searchError) {
                    console.warn(`⚠️ Search failed for "${keyword}":`, searchError.message);
                }

                // Rate limiting
                await new Promise(resolve => setTimeout(resolve, this.rateLimitDelay));
            }

            return allPosts;
        } catch (error) {
            console.error('❌ BlueSky search failed:', error.message);
            return [];
        }
    }

    filterConfirmedSightings(posts) {
        const confirmedSightings = [];
        const confirmationKeywords = ['confirmed', 'verified', 'spotted', 'seen', 'sighting'];
        const locationKeywords = ['san juan', 'puget sound', 'seattle', 'tacoma', 'vancouver', 'victoria'];

        for (const post of posts) {
            const text = post.record?.text?.toLowerCase() || '';
            
            // Check for confirmation language and location
            const hasConfirmation = confirmationKeywords.some(keyword => text.includes(keyword));
            const hasLocation = locationKeywords.some(keyword => text.includes(keyword));
            
            if (hasConfirmation || hasLocation) {
                // Extract approximate location (simplified)
                let location = this.extractLocation(text);
                
                const sighting = {
                    id: post.uri,
                    text: post.record.text,
                    author: post.author?.handle || 'unknown',
                    timestamp: new Date(post.record.createdAt).getTime(),
                    location: location,
                    source: 'bluesky',
                    confidence: hasConfirmation && hasLocation ? 'high' : 'medium',
                    verified: hasConfirmation,
                    originalPost: post.uri
                };

                confirmedSightings.push(sighting);
            }
        }

        return confirmedSightings;
    }

    extractLocation(text) {
        // Simple location extraction - could be enhanced with NLP
        const locations = {
            'san juan islands': { lat: 48.5465, lng: -123.0307, name: 'San Juan Islands' },
            'puget sound': { lat: 47.6062, lng: -122.3321, name: 'Puget Sound' },
            'seattle': { lat: 47.6062, lng: -122.3321, name: 'Seattle Waterfront' },
            'vancouver': { lat: 49.2827, lng: -123.1207, name: 'Vancouver' },
            'victoria': { lat: 48.4284, lng: -123.3656, name: 'Victoria' },
            'tacoma': { lat: 47.2529, lng: -122.4443, name: 'Tacoma' }
        };

        for (const [key, location] of Object.entries(locations)) {
            if (text.includes(key)) {
                return location;
            }
        }

        // Default to San Juan Islands area
        return { lat: 48.5465, lng: -123.0307, name: 'Pacific Northwest' };
    }

    async importWhaleSightings(options = {}) {
        const { limit = 100, saveToFile = true } = options;
        
        console.log('🐋 Starting BlueSky whale sightings import...');
        
        try {
            await this.authenticate();
            
            const posts = await this.searchWhalePosts(limit);
            console.log(`📊 Retrieved ${posts.length} total posts`);
            
            const confirmedSightings = this.filterConfirmedSightings(posts);
            console.log(`✅ Found ${confirmedSightings.length} confirmed whale sightings`);
            
            const result = {
                source: 'BlueSky Social Media',
                timestamp: new Date().toISOString(),
                totalPosts: posts.length,
                confirmedSightings: confirmedSightings,
                metadata: {
                    searchKeywords: WHALE_KEYWORDS,
                    confidenceLevels: ['high', 'medium'],
                    locationCoverage: 'Pacific Northwest'
                }
            };

            if (saveToFile) {
                if (!fs.existsSync('./data')) {
                    fs.mkdirSync('./data', { recursive: true });
                }
                
                fs.writeFileSync('./data/bluesky_whale_sightings.json', JSON.stringify(result, null, 2));
                console.log('💾 Saved to ./data/bluesky_whale_sightings.json');
            }

            return result;
        } catch (error) {
            console.error('❌ BlueSky import failed:', error);
            return { confirmedSightings: [], error: error.message };
        }
    }
}

// Export for use
module.exports = BlueSkyImporter;

// CLI usage
if (require.main === module) {
    const importer = new BlueSkyImporter();
    importer.importWhaleSightings({ limit: 200 })
        .then(result => {
            console.log(`\n🎉 BlueSky import complete: ${result.confirmedSightings?.length || 0} sightings`);
        })
        .catch(error => {
            console.error('💥 Import failed:', error);
        });
} 