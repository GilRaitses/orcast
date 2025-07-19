#!/usr/bin/env python3
"""
Sample User Sightings Data Generator
Creates realistic orca sighting reports for demonstration purposes
"""

import json
import random
from datetime import datetime, timedelta
import uuid

def generate_sample_sightings():
    """Generate sample user-reported orca sightings for San Juan Islands"""
    
    # San Juan Islands key locations
    locations = [
        {"name": "Lime Kiln Point", "lat": 48.5155, "lng": -123.1522},
        {"name": "Cattle Point", "lat": 48.4518, "lng": -122.9618},
        {"name": "Turn Point", "lat": 48.6895, "lng": -123.2447},
        {"name": "Pile Point", "lat": 48.6034, "lng": -123.1147},
        {"name": "Rosario Strait", "lat": 48.6756, "lng": -122.8234},
        {"name": "Haro Strait", "lat": 48.5523, "lng": -123.1890},
        {"name": "President Channel", "lat": 48.6456, "lng": -123.0123},
        {"name": "Boundary Pass", "lat": 48.7234, "lng": -123.0567},
        {"name": "San Juan Channel", "lat": 48.5345, "lng": -123.0789},
        {"name": "Lopez Sound", "lat": 48.4567, "lng": -122.8890},
    ]
    
    # Possible behaviors
    behaviors = ["foraging", "traveling", "socializing", "resting", "playing"]
    
    # Possible orca counts
    orca_counts = ["1", "2", "3", "4", "5", "6-10", "11-20"]
    
    # Water and vessel conditions
    water_conditions = ["calm", "light", "moderate", "rough"]
    vessel_traffic = ["none", "light", "moderate", "heavy"]
    confidence_levels = ["high", "medium", "low"]
    
    # Sample users
    users = [
        {"uid": "user1", "email": "whale_watcher@example.com"},
        {"uid": "user2", "email": "researcher@marine.org"},
        {"uid": "user3", "email": "captain@orcatours.com"},
        {"uid": "user4", "email": "anonymous", "anonymous": True},
        {"uid": "user5", "email": "scientist@noaa.gov"},
    ]
    
    # Sample notes
    sample_notes = [
        "Beautiful pod with juvenile! Moving slowly northbound.",
        "Saw them surface feeding on salmon. Amazing to watch!",
        "Large male with distinctive dorsal fin leading the group.",
        "Pod was very playful, lots of breaching and tail slapping.",
        "Quiet group, seemed to be resting in the kelp beds.",
        "Fast-moving pod heading toward Canadian waters.",
        "Heard lots of vocalizations, very active group.",
        "Single orca, possibly T137A based on saddle patch.",
        "Family group with new calf staying close to mother.",
        "Foraging behavior observed, lots of diving activity.",
        "",  # Some sightings have no notes
        "",
        ""
    ]
    
    sightings = {}
    
    # Generate sightings over the past 30 days
    base_time = datetime.now()
    
    for i in range(75):  # Generate 75 sample sightings
        sighting_id = f"sample_{uuid.uuid4().hex[:8]}"
        
        # Random time in past 30 days
        days_ago = random.randint(0, 30)
        hours_ago = random.randint(0, 23)
        minutes_ago = random.randint(0, 59)
        
        timestamp = base_time - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
        
        # Random location with some variation
        base_location = random.choice(locations)
        lat_variation = random.uniform(-0.01, 0.01)  # ~1km variation
        lng_variation = random.uniform(-0.01, 0.01)
        
        # Select user (bias toward certain users for more realistic data)
        user = random.choices(users, weights=[3, 2, 4, 1, 2])[0]
        
        # Generate realistic combinations
        orca_count = random.choice(orca_counts)
        behavior = random.choice(behaviors) if random.random() > 0.2 else ""
        confidence = random.choices(confidence_levels, weights=[4, 3, 1])[0]  # Bias toward high confidence
        
        # Environmental conditions correlate somewhat
        if random.random() > 0.7:  # 30% chance of difficult conditions
            water_condition = random.choice(["moderate", "rough"])
            vessel_traffic_level = random.choice(["moderate", "heavy"])
            if confidence == "high":
                confidence = random.choice(["medium", "low"])
        else:
            water_condition = random.choice(["calm", "light"])
            vessel_traffic_level = random.choice(["none", "light"])
        
        # Some sightings have photos (simulate with placeholder URLs)
        photo_url = None
        if random.random() > 0.6:  # 40% of sightings have photos
            photo_url = f"https://example.com/orca_photos/{sighting_id}.jpg"
        
        sighting = {
            "userId": user["uid"],
            "userEmail": user["email"],
            "timestamp": int(timestamp.timestamp() * 1000),  # Firebase timestamp format
            "location": {
                "lat": base_location["lat"] + lat_variation,
                "lng": base_location["lng"] + lng_variation
            },
            "orcaCount": orca_count,
            "behavior": behavior,
            "waterConditions": water_condition,
            "vesselTraffic": vessel_traffic_level,
            "notes": random.choice(sample_notes),
            "confidence": confidence,
            "verified": random.random() > 0.8,  # 20% verified by experts
            "photoUrl": photo_url,
            "locationName": base_location["name"]  # For reference
        }
        
        sightings[sighting_id] = sighting
    
    return sightings

def main():
    """Generate and save sample sightings data"""
    print("🐋 Generating sample orca sightings data...")
    
    sightings = generate_sample_sightings()
    
    # Create complete Firebase data structure
    firebase_data = {
        "userSightings": sightings
    }
    
    # Save to JSON file
    output_file = "sample_user_sightings.json"
    with open(output_file, 'w') as f:
        json.dump(firebase_data, f, indent=2)
    
    print(f"✅ Generated {len(sightings)} sample sightings")
    print(f"📁 Saved to {output_file}")
    
    # Statistics
    verified_count = sum(1 for s in sightings.values() if s.get("verified", False))
    with_photos = sum(1 for s in sightings.values() if s.get("photoUrl"))
    
    print(f"\n📊 Statistics:")
    print(f"   • Total sightings: {len(sightings)}")
    print(f"   • Verified: {verified_count}")
    print(f"   • With photos: {with_photos}")
    
    # Confidence breakdown
    confidence_counts = {}
    for sighting in sightings.values():
        conf = sighting["confidence"]
        confidence_counts[conf] = confidence_counts.get(conf, 0) + 1
    
    print(f"   • Confidence: {confidence_counts}")
    
    print(f"\n💡 To use this data:")
    print(f"   1. Upload to Firebase: firebase database:set /userSightings {output_file}")
    print(f"   2. Or import manually in Firebase Console")
    print(f"   3. The app will automatically display these sightings on the map")

if __name__ == "__main__":
    main() 