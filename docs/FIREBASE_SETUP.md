# Firebase Setup Instructions

## 1. Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Create a project"
3. Name: `orca-behavior-tracker` (or your preferred name)
4. Disable Google Analytics (or enable if you want usage stats)
5. Click "Create project"

## 2. Enable Required Services

### Enable Realtime Database
1. In Firebase Console → "Realtime Database"
2. Click "Create Database"
3. Choose "Start in test mode" (we'll update rules later)
4. Select region (us-central1 recommended)

### Enable Authentication
1. In Firebase Console → "Authentication"
2. Click "Get started"
3. Go to "Sign-in method" tab
4. Enable "Email/Password"
5. Enable "Anonymous" (for quick reporting without signup)

### Enable Storage
1. In Firebase Console → "Storage"
2. Click "Get started"
3. Choose "Start in test mode"
4. Select same region as database

## 3. Get Firebase Configuration

1. In Firebase Console → Project Settings (gear icon)
2. Scroll down to "Your apps"
3. Click "Web" icon (</>) to add web app
4. App nickname: `orca-tracker-web`
5. Don't check "Firebase Hosting" yet
6. Click "Register app"
7. **Copy the config object** - you'll need this!

It looks like:
```javascript
const firebaseConfig = {
  apiKey: "your-api-key",
  authDomain: "your-project.firebaseapp.com",
  databaseURL: "https://your-project-default-rtdb.firebaseapp.com/",
  projectId: "your-project-id",
  storageBucket: "your-project.appspot.com",
  messagingSenderId: "123456789",
  appId: "your-app-id"
};
```

## 4. Update Configuration

Replace the placeholder config in `index.html` with your actual config.

## 5. Deploy (Optional)

### Option A: Firebase Hosting
```bash
npm install -g firebase-tools
firebase login
firebase init hosting
firebase deploy
```

### Option B: Local Testing
Just open `index.html` in a web browser - it will work locally!

## 6. Security Rules

The app will automatically update the database rules. For storage, you'll need to set:

```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    match /sightings/{allPaths=**} {
      allow read: if true;
      allow write: if request.auth != null;
    }
  }
}
```

## Current Status
- ✅ Database rules configured
- ✅ App structure ready
- ⏳ Need your Firebase config
- ⏳ Need to enable Auth & Storage 