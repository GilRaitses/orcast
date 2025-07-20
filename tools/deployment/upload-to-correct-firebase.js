/**
 * Upload All Whale Data to CORRECT Firebase Project (orca-904de)
 * Uses the correct service account key for the orca-904de project
 */

const admin = require('firebase-admin');
const fs = require('fs');

// Initialize with the CORRECT service account for orca-904de
const serviceAccount = require('./config/orca-904de-firebase-adminsdk-fbsvc-19b853cc6d.json');
admin.initializeApp({
    credential: admin.credential.cert(serviceAccount),
    databaseURL: "https://orca-904de-default-rtdb.firebaseio.com",
    projectId: 'orca-904de'
});

const db = admin.firestore();

async function uploadToCorrectFirebase() {
    console.log('🔥 Uploading whale data to CORRECT Firebase project: orca-904de');
    console.log('📊 Target: https://console.firebase.google.com/project/orca-904de/firestore');
    
    try {
        let totalUploaded = 0;
        
        // Upload BlueSky data
        if (fs.existsSync('./data/bluesky_whale_sightings.json')) {
            const blueSkyData = JSON.parse(fs.readFileSync('./data/bluesky_whale_sightings.json', 'utf8'));
            const sightings = blueSkyData.confirmedSightings || [];
            
            console.log(`🐦 Uploading ${sightings.length} BlueSky confirmed sightings...`);
            await uploadBatch('whale_sightings', sightings, 'bluesky');
            totalUploaded += sightings.length;
        }
        
        // Upload Orcasound data
        if (fs.existsSync('./data/orcasound_whale_detections.json')) {
            const orcasoundData = JSON.parse(fs.readFileSync('./data/orcasound_whale_detections.json', 'utf8'));
            const detections = orcasoundData.processedSightings || [];
            
            console.log(`🎧 Uploading ${detections.length} Orcasound acoustic detections...`);
            await uploadBatch('whale_sightings', detections, 'orcasound');
            totalUploaded += detections.length;
        }
        
        // Upload OBIS data
        if (fs.existsSync('./data/obis_orca_observations.json')) {
            const obisData = JSON.parse(fs.readFileSync('./data/obis_orca_observations.json', 'utf8'));
            const observations = obisData.validatedSightings || [];
            
            console.log(`🔬 Uploading ${observations.length} OBIS expert observations...`);
            await uploadBatch('whale_sightings', observations, 'obis');
            totalUploaded += observations.length;
        }
        
        console.log(`\n🎉 Successfully uploaded ${totalUploaded} whale records to orca-904de Firestore!`);
        console.log('🔍 Verify at: https://console.firebase.google.com/project/orca-904de/firestore/data');
        
        // Test query to verify upload
        await testFirestoreAccess();
        
    } catch (error) {
        console.error('❌ Upload failed:', error);
    }
}

async function uploadBatch(collection, documents, sourceType) {
    const batchSize = 500; // Firestore batch limit
    
    for (let i = 0; i < documents.length; i += batchSize) {
        const batch = db.batch();
        const batchDocuments = documents.slice(i, i + batchSize);
        
        for (const doc of batchDocuments) {
            const docId = sanitizeDocumentId(`${sourceType}_${doc.id || Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
            const docRef = db.collection(collection).doc(docId);
            
            const firestoreDoc = {
                ...doc,
                source: sourceType,
                uploadedAt: admin.firestore.FieldValue.serverTimestamp(),
                location: new admin.firestore.GeoPoint(doc.location.lat, doc.location.lng),
                timestamp: new Date(doc.timestamp)
            };
            
            batch.set(docRef, firestoreDoc);
        }
        
        await batch.commit();
        console.log(`  ✅ Batch ${Math.floor(i/batchSize) + 1}: ${batchDocuments.length} documents uploaded`);
    }
}

function sanitizeDocumentId(id) {
    // Remove forbidden characters from Firestore document IDs
    return id.replace(/[\/\\\.\#\$\[\]]/g, '_').substring(0, 1500);
}

async function testFirestoreAccess() {
    console.log('\n🔍 Testing Firestore access...');
    
    try {
        const snapshot = await db.collection('whale_sightings').limit(5).get();
        console.log(`✅ Query successful: Found ${snapshot.size} documents`);
        
        snapshot.forEach(doc => {
            const data = doc.data();
            console.log(`  📍 ${data.source}: ${data.locationName} (${new Date(data.timestamp.seconds * 1000).toLocaleDateString()})`);
        });
        
        // Get total count by source
        const sources = ['bluesky', 'orcasound', 'obis'];
        for (const source of sources) {
            const sourceSnapshot = await db.collection('whale_sightings').where('source', '==', source).get();
            console.log(`📊 ${source.toUpperCase()}: ${sourceSnapshot.size} records`);
        }
        
    } catch (error) {
        console.error('❌ Firestore test failed:', error);
    }
}

// Import whale data first if needed
async function importAndUpload() {
    console.log('🔄 Importing fresh whale data...');
    
    try {
        // Import BlueSky data
        console.log('📱 Importing BlueSky data...');
        const BlueSkyImporter = require('./data-importers/bluesky-importer');
        const blueSky = new BlueSkyImporter();
        await blueSky.importWhaleSightings({ limit: 200 });
        
        // Import Orcasound data
        console.log('🎧 Importing Orcasound data...');
        const OrcasoundImporter = require('./data-importers/orcasound-importer');
        const orcasound = new OrcasoundImporter();
        await orcasound.importWhaleDetections({ limit: 1000 });
        
        // Import OBIS data
        console.log('🔬 Importing OBIS data...');
        const OBISImporter = require('./data-importers/obis-importer');
        const obis = new OBISImporter();
        await obis.importOrcaObservations({ limit: 500 });
        
        console.log('✅ Data import completed, now uploading to Firestore...');
        
        // Upload to Firestore
        await uploadToCorrectFirebase();
        
    } catch (error) {
        console.error('❌ Import and upload failed:', error);
    }
}

// Export functions
module.exports = {
    uploadToCorrectFirebase,
    importAndUpload,
    testFirestoreAccess
};

// CLI usage
if (require.main === module) {
    const args = process.argv.slice(2);
    
    if (args.includes('--import')) {
        importAndUpload();
    } else {
        uploadToCorrectFirebase();
    }
} 