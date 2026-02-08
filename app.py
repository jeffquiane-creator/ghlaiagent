#!/usr/bin/env python3
"""
GoHighLevel AI Agent - Web Server (V2 API)
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

# Configuration - V2 API
GHL_API_KEY = os.environ.get("GHL_API_KEY", "pit-08e43a3b-311c-4eca-85ed-5aa15cf9c9ed")
GHL_LOCATION_ID = os.environ.get("GHL_LOCATION_ID", "oRAdNjgqsxfmfcoNLmAG")
GHL_BASE_URL = "https://services.leadconnectorhq.com"  # V2 API endpoint
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# Initialize Anthropic client
if ANTHROPIC_API_KEY:
    anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)
else:
    anthropic_client = None


class GoHighLevelAPI:
    """Wrapper for GoHighLevel V2 API calls"""
    
    def __init__(self, api_key, location_id):
        self.api_key = api_key
        self.location_id = location_id
        self.base_url = GHL_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Version": "2021-07-28"
        }
    
    def create_contact(self, data):
        """Create a new contact"""
        url = f"{self.base_url}/contacts/"
        payload = {
            "locationId": self.location_id,
            **data
        }
        print(f"Creating contact at: {url}")
        print(f"Payload: {payload}")
        response = requests.post(url, headers=self.headers, json=payload)
        print(f"Response status: {response.status_code}")
        print(f"Response: {response.text}")
        return response.json()
    
    def search_contacts(self, query):
        """Search for contacts"""
        url = f"{self.base_url}/contacts/"
        params = {
            "locationId": self.location_id,
            "query": query
        }
        print(f"Searching contacts at: {url}")
        print(f"Params: {params}")
        response = requests.get(url, headers=self.headers, params=params)
        print(f"Response status: {response.status_code}")
        print(f"Response: {response.text[:200]}")  # First 200 chars
        return response.json()
    
    def add_note_to_contact(self, contact_id, note):
        """Add a note to a contact"""
        url = f"{self.base_url}/contacts/{contact_id}/notes"
        payload = {
            "body": note
        }
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json()
    
    def add_tag_to_contact(self, contact_id, tags):
        """Add tags to a contact"""
        url = f"{self.base_url}/contacts/{contact_id}"
        payload = {
            "tags": tags if isinstance(tags, list) else [tags]
        }
        response = requests.put(url, headers=self.headers, json=payload)
        return response.json()


class GHLAIAgent:
    """AI Agent that interprets commands and executes them via GHL API"""
    
    def __init__(self, ghl_api):
        self.ghl = ghl_api
    
    def interpret_command(self, user_command):
        """Use Claude to interpret the user's natural language command"""
        
        if not anthropic_client:
            return {
                "action": "error",
                "parameters": {},
                "confirmation_message": "Anthropic API key not configured."
            }
        
        system_prompt = """You are an AI assistant that helps users control their GoHighLevel CRM through natural language commands.

Your job is to interpret user commands and return a JSON object with the action to take and the parameters needed.

Available actions:
1. create_contact - Create a new contact
2. add_note - Add a note to a contact
3. add_tag - Add tags to a contact
4. search_contact - Search for a contact

For each command, return a JSON object with this structure:
{
    "action": "action_name",
    "parameters": {
        // relevant parameters for the action
    },
    "confirmation_message": "Human-readable description of what will be done"
}

Examples:

User: "Add contact John Doe, email john@example.com, phone 555-1234, tag him as Facebook Lead"
Response:
{
    "action": "create_contact",
    "parameters": {
        "firstName": "John",
        "lastName": "Doe",
        "email": "john@example.com",
        "phone": "555-1234",
        "tags": ["Facebook Lead"]
    },
    "confirmation_message": "Creating contact John Doe with email john@example.com, phone 555-1234, and tag 'Facebook Lead'"
}

User: "Add note to John Doe saying he's interested in downtown properties"
Response:
{
    "action": "add_note",
    "parameters": {
        "contact_name": "John Doe",
        "note": "Interested in downtown properties"
    },
    "confirmation_message": "Adding note to John Doe: 'Interested in downtown properties'"
}

User: "Search for Mike"
Response:
{
    "action": "search_contact",
    "parameters": {
        "query": "Mike"
    },
    "confirmation_message": "Searching for contacts matching 'Mike'"
}

Return ONLY the JSON object, no other text."""

        try:
            message = anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_command}
                ]
            )
            
            response_text = message.content[0].text
            command_data = json.loads(response_text)
            return command_data
        except json.JSONDecodeError:
            return {
                "action": "error",
                "parameters": {},
                "confirmation_message": f"Could not understand command."
            }
        except Exception as e:
            return {
                "action": "error",
                "parameters": {},
                "confirmation_message": f"Error: {str(e)}"
            }
    
    def execute_command(self, command_data):
        """Execute the interpreted command"""
        
        action = command_data.get("action")
        params = command_data.get("parameters", {})
        
        try:
            if action == "create_contact":
                result = self.ghl.create_contact(params)
                if result.get("contact"):
                    contact = result["contact"]
                    name = f"{contact.get('firstName', '')} {contact.get('lastName', '')}".strip()
                    return {
                        "success": True,
                        "message": f"✅ Created contact: {name}",
                        "data": contact
                    }
                return {"success": False, "message": f"❌ Error creating contact: {result.get('message', 'Unknown error')}"}
            
            elif action == "add_note":
                contact_name = params.get("contact_name")
                contacts = self.ghl.search_contacts(contact_name)
                
                if contacts.get("contacts") and len(contacts["contacts"]) > 0:
                    contact_id = contacts["contacts"][0]["id"]
                    result = self.ghl.add_note_to_contact(contact_id, params["note"])
                    return {
                        "success": True,
                        "message": f"✅ Added note to {contact_name}",
                        "data": result
                    }
                else:
                    return {"success": False, "message": f"❌ Could not find contact: {contact_name}"}
            
            elif action == "add_tag":
                contact_name = params.get("contact_name")
                contacts = self.ghl.search_contacts(contact_name)
                
                if contacts.get("contacts") and len(contacts["contacts"]) > 0:
                    contact_id = contacts["contacts"][0]["id"]
                    result = self.ghl.add_tag_to_contact(contact_id, params["tags"])
                    return {
                        "success": True,
                        "message": f"✅ Added tags to {contact_name}",
                        "data": result
                    }
                else:
                    return {"success": False, "message": f"❌ Could not find contact: {contact_name}"}
            
            elif action == "search_contact":
                query = params.get("query")
                result = self.ghl.search_contacts(query)
                contacts = result.get("contacts", [])
                
                if contacts:
                    contact_list = []
                    for c in contacts[:10]:
                        contact_list.append({
                            "name": f"{c.get('firstName', '')} {c.get('lastName', '')}".strip(),
                            "email": c.get('email', 'No email'),
                            "phone": c.get('phone', 'No phone'),
                            "tags": c.get('tags', [])
                        })
                    
                    return {
                        "success": True,
                        "message": f"✅ Found {len(contacts)} contact(s)",
                        "data": contact_list
                    }
                else:
                    return {"success": False, "message": f"❌ No contacts found for: {query}"}
            
            elif action == "error":
                return {"success": False, "message": command_data.get('confirmation_message')}
            
            else:
                return {"success": False, "message": f"❌ Action not yet implemented: {action}"}
        
        except Exception as e:
            print(f"Execute error: {str(e)}")
            return {"success": False, "message": f"❌ Error: {str(e)}"}


# Initialize GHL API
ghl_api = GoHighLevelAPI(GHL_API_KEY, GHL_LOCATION_ID)
agent = GHLAIAgent(ghl_api)


@app.route('/')
def index():
    """Serve the main web interface"""
    return render_template('index.html')


@app.route('/api/command', methods=['POST'])
def process_command():
    """Process a natural language command"""
    data = request.json
    user_command = data.get('command', '')
    
    if not user_command:
        return jsonify({
            "success": False,
            "message": "No command provided"
        })
    
    # Interpret the command
    command_data = agent.interpret_command(user_command)
    
    # Execute the command
    result = agent.execute_command(command_data)
    
    return jsonify({
        "success": result.get("success", False),
        "message": result.get("message", ""),
        "data": result.get("data"),
        "plan": command_data.get("confirmation_message", "")
    })


@app.route('/api/test', methods=['GET'])
def test_api():
    """Test the GHL API connection"""
    try:
        contacts = ghl_api.search_contacts("")
        return jsonify({
            "success": True,
            "message": "✅ Connected to GoHighLevel",
            "contact_count": len(contacts.get("contacts", []))
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"❌ Connection error: {str(e)}"
        })


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 GoHighLevel AI Agent - Web Server (V2 API)")
    print("=" * 60)
    print("\n📱 Starting server...")
    print("💡 Using GHL V2 API endpoint\n")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
