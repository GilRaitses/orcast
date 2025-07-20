#!/usr/bin/env python3
"""
ORCAST Production Backend - Real ML Service
"""

import os
from orcast_firestore_ml_service import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False) 