#!/usr/bin/env python3
"""
GoHighLevel AI Agent - Web Server
Flask backend that powers the web interface
"""

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import os
import json
import requests
from datetime import datetime, timedelta
from anthropic import Anthropic
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
CORS(app)

# Configuration
GHL_API_KEY = os.environ.get("GHL_API_KEY", "pit-08e43a3b-311c-4eca-85ed-5aa15cf9c9ed")
GHL_LOCATION_ID = os.environ.get("GHL_LOCATION_ID", "oRAdNjgqsxfmfcoNLmAG")
GHL_BASE_URL = "https://rest.gohighlevel.com/v1"
ANTHROPIC_API_KEY
