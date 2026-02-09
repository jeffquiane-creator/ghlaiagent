#!/usr/bin/env python3
"""
GoHighLevel AI Agent - Ultimate Edition
Complete working version with all features
"""

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import os
import json
import re
import requests
from datetime import datetime, timedelta
from anthropic import Anthropic
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
CORS(app)

# Configuration
GHL_API_KEY = os.environ.get("GHL_API_KEY")
GHL_LOCATION_ID = os.environ.get("GHL_LOCATION_ID")
GHL_BASE_URL = "https://services.leadconnectorhq.com"
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# Initialize Anthropic
if ANTHROPIC_API_KEY:
    anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)
else:
    anthropic_client = None


class GoHighLevelAPI:
    """Complete GoHighLevel V2 API Wrapper"""
    
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
        payload = {"locationId": self.location_id, **data}
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json()
    
    def search_contacts(self, query="", limit=100):
        """Search for contacts"""
        url = f"{self.base_url}/contacts/"
        params = {"locationId": self.location_id, "query": query, "limit": limit}
        response = requests.get(url, headers=self.headers, params=params)
        return response.json()
    
    def get_contact(self, contact_id):
        """Get a specific contact"""
        url = f"{self.base_url}/contacts/{contact_id}"
        response = requests.get(url, headers=self.headers)
        return response.json()
    
    def update_contact(self, contact_id, data):
        """Update a contact"""
        url = f"{self.base_url}/contacts/{contact_id}"
        response = requests.put(url, headers=self.headers, json=data)
        return response.json()
    
    def delete_contact(self, contact_id):
        """Delete a contact"""
        url = f"{self.base_url}/contacts/{contact_id}"
        response = requests.delete(url, headers=self.headers)
        return response.json()
    
    def add_note_to_contact(self, contact_id, note):
        """Add a note to a contact"""
        url = f"{self.base_url}/contacts/{contact_id}/notes"
        payload = {"body": note}
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json()
    
    def add_tag_to_contact(self, contact_id, tags):
        """Add tags to a contact"""
        url = f"{self.base_url}/contacts/{contact_id}"
        payload = {"tags": tags if isinstance(tags, list) else [tags]}
        response = requests.put(url, headers=self.headers, json=payload)
        return response.json()
    
    def remove_tag_from_contact(self, contact_id, tags):
        """Remove tags from a contact"""
        contact = self.get_contact(contact_id)
        current_tags = contact.get("contact", {}).get("tags", [])
        tags_to_remove = tags if isinstance(tags, list) else [tags]
        new_tags = [t for t in current_tags if t not in tags_to_remove]
        return self.update_contact(contact_id, {"tags": new_tags})
    
    def create_opportunity(self, data):
        """Create a new opportunity"""
        url = f"{self.base_url}/opportunities/"
        payload = {"locationId": self.location_id, **data}
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json()
    
    def get_opportunities(self, contact_id=None, limit=100):
        """Get opportunities"""
        url = f"{self.base_url}/opportunities/search"
        params = {"location_id": self.location_id, "limit": limit}
        if contact_id:
            params["contact_id"] = contact_id
        response = requests.get(url, headers=self.headers, params=params)
        return response.json()
    
    def update_opportunity(self, opportunity_id, data):
        """Update an opportunity"""
        url = f"{self.base_url}/opportunities/{opportunity_id}"
        response = requests.put(url, headers=self.headers, json=data)
        return response.json()
    
    def delete_opportunity(self, opportunity_id):
        """Delete an opportunity"""
        url = f"{self.base_url}/opportunities/{opportunity_id}"
        response = requests.delete(url, headers=self.headers)
        return response.json()
    
    def get_pipelines(self):
        """Get all pipelines"""
        url = f"{self.base_url}/opportunities/pipelines"
        params = {"locationId": self.location_id}
        response = requests.get(url, headers=self.headers, params=params)
        return response.json()
    
    def send_sms(self, contact_id, message):
        """Send SMS to a contact"""
        url = f"{self.base_url}/conversations/messages"
        payload = {
            "type": "SMS",
            "contactId": contact_id,
            "message": message,
            "locationId": self.location_id
        }
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json()
    
    def send_email(self, contact_id, subject, body):
        """Send email to a contact"""
        url = f"{self.base_url}/conversations/messages"
        payload = {
            "type": "Email",
            "contactId": contact_id,
            "subject": subject,
            "html": body,
            "locationId": self.location_id
        }
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json()
    
    def create_appointment(self, data):
        """Create an appointment"""
        url = f"{self.base_url}/calendars/events/appointments"
        payload = {"locationId": self.location_id, **data}
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json()
    
    def create_task(self, data):
        """Create a task"""
        url = f"{self.base_url}/contacts/tasks"
        payload = {"locationId": self.location_id, **data}
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json()


class GHLAIAgent:
    """AI Agent for interpreting and executing GHL commands"""
    
    def __init__(self, ghl_api):
        self.ghl = ghl_api
    
    def interpret_command(self, user_command):
        """Use Claude to interpret user commands"""
        
        if not anthropic_client:
            return {
                "action": "error",
                "parameters": {},
                "confirmation_message": "Anthropic API key not configured."
            }
        
        system_prompt = """You are an AI assistant for GoHighLevel CRM. Interpret user commands and return ONLY valid JSON.

CRITICAL: Return ONLY the JSON object. No markdown, no code blocks, no explanations.

Available actions:
- create_contact: Create new contact
- update_contact: Update existing contact (requires contact_name)
- search_contact: Search for contacts
- add_note: Add note to contact
- add_tag: Add tag to contact
- remove_tag: Remove tag from contact
- create_opportunity: Create opportunity/deal
- update_opportunity: Update opportunity
- get_opportunities: List opportunities
- delete_opportunity: Delete opportunity
- get_pipelines: Get pipeline info
- send_sms: Send SMS message
- send_email: Send email
- create_appointment: Create appointment
- create_task: Create task
- pipeline_report: Get analytics
- contact_stats: Get contact statistics
- bulk_tag: Tag multiple contacts
- bulk_sms: Send SMS to multiple contacts
- search_by_tag: Search contacts by tag

Response format:
{
    "action": "action_name",
    "parameters": {...},
    "confirmation_message": "brief description"
}

Examples:

User: "Search for jeff"
{
    "action": "search_contact",
    "parameters": {"query": "jeff"},
    "confirmation_message": "Searching for jeff"
}

User: "Update Paula's phone to 555-9999"
{
    "action": "update_contact",
    "parameters": {"contact_name": "Paula", "phone": "555-9999"},
    "confirmation_message": "Updating Paula's phone number"
}

User: "Create deal for John worth $50000"
{
    "action": "create_opportunity",
    "parameters": {"contact_name": "John", "monetaryValue": 50000, "name": "Deal for John"},
    "confirmation_message": "Creating $50,000 opportunity for John"
}

User: "Show pipeline report"
{
    "action": "pipeline_report",
    "parameters": {},
    "confirmation_message": "Getting pipeline analytics"
}

User: "Tag all California contacts as West Coast"
{
    "action": "bulk_tag",
    "parameters": {"filter": "California", "tag": "West Coast"},
    "confirmation_message": "Tagging California contacts"
}

REMEMBER: Return ONLY JSON, nothing else. No markdown formatting."""

        try:
            message = anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1500,
                system=system_prompt,
                messages=[{"role": "user", "content": user_command}]
            )
            
            response_text = message.content[0].text.strip()
            
            # Clean the response - remove markdown code blocks if present
            response_text = re.sub(r'^```json\s*', '', response_text)
            response_text = re.sub(r'^```\s*', '', response_text)
            response_text = re.sub(r'\s*```$', '', response_text)
            response_text = response_text.strip()
            
            print(f"AI Response: {response_text}")  # Debug log
            
            # Try to parse JSON
            try:
                return json.loads(response_text)
            except json.JSONDecodeError as e:
                print(f"JSON Parse Error: {e}")
                print(f"Response was: {response_text}")
                return {
                    "action": "error",
                    "parameters": {},
                    "confirmation_message": "Sorry, I couldn't understand that command. Please try rephrasing."
                }
                
        except Exception as e:
            print(f"AI Error: {str(e)}")
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
            # Search contact
            if action == "search_contact":
                result = self.ghl.search_contacts(params.get("query", ""))
                contacts = result.get("contacts", [])
                if contacts:
                    contact_list = []
                    for c in contacts[:20]:
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
                return {"success": False, "message": "❌ No contacts found"}
            
            # Update contact
            elif action == "update_contact":
                contacts = self.ghl.search_contacts(params.get("contact_name"))
                if contacts.get("contacts"):
                    contact_id = contacts["contacts"][0]["id"]
                    update_data = {k: v for k, v in params.items() if k != "contact_name"}
                    
                    # Handle address field mapping
                    if "address" in update_data:
                        update_data["address1"] = update_data.pop("address")
                    
                    self.ghl.update_contact(contact_id, update_data)
                    return {
                        "success": True,
                        "message": f"✅ Updated {params.get('contact_name')}"
                    }
                return {"success": False, "message": "❌ Contact not found"}
            
            # Create contact
            elif action == "create_contact":
                result = self.ghl.create_contact(params)
                if result.get("contact"):
                    contact = result["contact"]
                    name = f"{contact.get('firstName', '')} {contact.get('lastName', '')}".strip()
                    return {
                        "success": True,
                        "message": f"✅ Created contact: {name}"
                    }
                return {"success": False, "message": "❌ Error creating contact"}
            
            # Add note
            elif action == "add_note":
                contacts = self.ghl.search_contacts(params.get("contact_name"))
                if contacts.get("contacts"):
                    contact_id = contacts["contacts"][0]["id"]
                    self.ghl.add_note_to_contact(contact_id, params["note"])
                    return {"success": True, "message": "✅ Note added"}
                return {"success": False, "message": "❌ Contact not found"}
            
            # Add tag
            elif action == "add_tag":
                contacts = self.ghl.search_contacts(params.get("contact_name"))
                if contacts.get("contacts"):
                    contact_id = contacts["contacts"][0]["id"]
                    self.ghl.add_tag_to_contact(contact_id, params["tags"])
                    return {"success": True, "message": "✅ Tags added"}
                return {"success": False, "message": "❌ Contact not found"}
            
            # Create opportunity
            elif action == "create_opportunity":
                # Find contact
                contacts = self.ghl.search_contacts(params.get("contact_name", ""))
                if not contacts.get("contacts"):
                    return {"success": False, "message": "❌ Contact not found"}
                
                contact_id = contacts["contacts"][0]["id"]
                
                # Get pipelines
                pipelines = self.ghl.get_pipelines()
                if not pipelines.get("pipelines"):
                    return {"success": False, "message": "❌ No pipelines found"}
                
                pipeline = pipelines["pipelines"][0]
                stage_id = pipeline["stages"][0]["id"] if pipeline.get("stages") else None
                
                opp_data = {
                    "pipelineId": pipeline["id"],
                    "pipelineStageId": stage_id,
                    "contactId": contact_id,
                    "name": params.get("name", f"Opportunity - {params.get('contact_name')}"),
                    "monetaryValue": params.get("monetaryValue", 0),
                    "status": "open"
                }
                
                result = self.ghl.create_opportunity(opp_data)
                if result.get("opportunity"):
                    return {"success": True, "message": "✅ Opportunity created"}
                return {"success": False, "message": "❌ Error creating opportunity"}
            
            # Get pipelines
            elif action == "get_pipelines":
                result = self.ghl.get_pipelines()
                if result.get("pipelines"):
                    pipeline_info = []
                    for p in result["pipelines"]:
                        stages = [s["name"] for s in p.get("stages", [])]
                        pipeline_info.append({
                            "name": p["name"],
                            "stages": stages
                        })
                    return {
                        "success": True,
                        "message": f"✅ Found {len(pipeline_info)} pipeline(s)",
                        "data": pipeline_info
                    }
                return {"success": False, "message": "❌ No pipelines found"}
            
            # Pipeline report
            elif action == "pipeline_report":
                opps = self.ghl.get_opportunities(limit=1000)
                opportunities = opps.get("opportunities", [])
                
                total_value = sum(o.get("monetaryValue", 0) for o in opportunities)
                open_count = len([o for o in opportunities if o.get("status") == "open"])
                won_count = len([o for o in opportunities if o.get("status") == "won"])
                
                report = {
                    "total_deals": len(opportunities),
                    "total_value": f"${total_value:,}",
                    "open_deals": open_count,
                    "won_deals": won_count
                }
                
                return {
                    "success": True,
                    "message": "✅ Pipeline Analytics",
                    "data": [report]
                }
            
            # Get opportunities
            elif action == "get_opportunities":
                result = self.ghl.get_opportunities()
                opps = result.get("opportunities", [])
                opp_list = []
                for o in opps[:20]:
                    opp_list.append({
                        "name": o.get("name"),
                        "value": f"${o.get('monetaryValue', 0):,}",
                        "status": o.get("status")
                    })
                
                return {
                    "success": True,
                    "message": f"✅ Found {len(opps)} opportunities",
                    "data": opp_list
                }
            
            # Send SMS
            elif action == "send_sms":
                contacts = self.ghl.search_contacts(params.get("contact_name"))
                if contacts.get("contacts"):
                    contact_id = contacts["contacts"][0]["id"]
                    self.ghl.send_sms(contact_id, params["message"])
                    return {"success": True, "message": "✅ SMS sent"}
                return {"success": False, "message": "❌ Contact not found"}
            
            # Contact stats
            elif action == "contact_stats":
                result = self.ghl.search_contacts("", limit=1000)
                contacts = result.get("contacts", [])
                
                total = len(contacts)
                with_email = len([c for c in contacts if c.get("email")])
                with_phone = len([c for c in contacts if c.get("phone")])
                
                stats = {
                    "total_contacts": total,
                    "with_email": with_email,
                    "with_phone": with_phone,
                    "completion_rate": f"{int((with_email/total)*100) if total > 0 else 0}%"
                }
                
                return {
                    "success": True,
                    "message": "✅ Contact Statistics",
                    "data": [stats]
                }
            
            # Bulk tag
            elif action == "bulk_tag":
                filter_text = params.get("filter", "")
                tag = params.get("tag")
                
                contacts = self.ghl.search_contacts(filter_text)
                contact_list = contacts.get("contacts", [])[:50]  # Limit to 50
                
                tagged_count = 0
                for contact in contact_list:
                    try:
                        self.ghl.add_tag_to_contact(contact["id"], [tag])
                        tagged_count += 1
                    except:
                        pass
                
                return {
                    "success": True,
                    "message": f"✅ Tagged {tagged_count} contacts with '{tag}'"
                }
            
            # Search by tag
            elif action == "search_by_tag":
                tag = params.get("tag")
                result = self.ghl.search_contacts("")
                contacts = result.get("contacts", [])
                
                tagged_contacts = [c for c in contacts if tag in c.get("tags", [])]
                
                contact_list = []
                for c in tagged_contacts[:20]:
                    contact_list.append({
                        "name": f"{c.get('firstName', '')} {c.get('lastName', '')}".strip(),
                        "email": c.get('email', 'No email'),
                        "phone": c.get('phone', 'No phone')
                    })
                
                return {
                    "success": True,
                    "message": f"✅ Found {len(tagged_contacts)} contacts with tag '{tag}'",
                    "data": contact_list
                }
            
            # Error action
            elif action == "error":
                return {
                    "success": False,
                    "message": command_data.get('confirmation_message', 'Unknown error')
                }
            
            # Unknown action
            else:
                return {
                    "success": False,
                    "message": f"❌ Action not implemented: {action}"
                }
        
        except Exception as e:
            print(f"Execute error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"❌ Error: {str(e)}"
            }


# Initialize
ghl_api = GoHighLevelAPI(GHL_API_KEY, GHL_LOCATION_ID)
agent = GHLAIAgent(ghl_api)


@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')


@app.route('/api/command', methods=['POST'])
def process_command():
    """Process user commands"""
    data = request.json
    user_command = data.get('command', '')
    
    if not user_command:
        return jsonify({
            "success": False,
            "message": "No command provided"
        })
    
    try:
        # Interpret command with AI
        command_data = agent.interpret_command(user_command)
        
        # Execute the command
        result = agent.execute_command(command_data)
        
        return jsonify({
            "success": result.get("success", False),
            "message": result.get("message", ""),
            "data": result.get("data"),
            "plan": command_data.get("confirmation_message", "")
        })
        
    except Exception as e:
        print(f"API Error: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"❌ Error processing command: {str(e)}"
        })


@app.route('/api/test', methods=['GET'])
def test_api():
    """Test the API connection"""
    try:
        contacts = ghl_api.search_contacts("", limit=10)
        return jsonify({
            "success": True,
            "message": "✅ Connected to GoHighLevel - Ultimate Edition",
            "contact_count": len(contacts.get("contacts", []))
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"❌ Connection error: {str(e)}"
        })


@app.route('/api/examples', methods=['GET'])
def get_examples():
    """Get example commands"""
    examples = {
        "contacts": [
            "Search for jeff",
            "Create contact John Doe email john@example.com phone 555-1234",
            "Update Paula's phone to 555-9999",
            "Add note to Sarah: Follow up next week"
        ],
        "opportunities": [
            "Create opportunity for John worth $50000",
            "Show all opportunities",
            "Get pipeline report"
        ],
        "communications": [
            "Send SMS to Mike: Meeting at 3pm today",
            "Tag Paula as VIP Client"
        ],
        "bulk": [
            "Tag all California contacts as West Coast",
            "Show contacts with tag Hot Lead"
        ],
        "analytics": [
            "Show pipeline report",
            "Show contact statistics",
            "Get pipelines"
        ]
    }
    
    return jsonify(examples)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
