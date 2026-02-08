#!/usr/bin/env python3
"""
GoHighLevel AI Agent - FULL FEATURED (V2 API)
Complete CRM control with opportunities, calls, SMS, and more!
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
GHL_BASE_URL = "https://services.leadconnectorhq.com"
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
    
    # CONTACTS
    def create_contact(self, data):
        """Create a new contact"""
        url = f"{self.base_url}/contacts/"
        payload = {"locationId": self.location_id, **data}
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json()
    
    def search_contacts(self, query):
        """Search for contacts"""
        url = f"{self.base_url}/contacts/"
        params = {"locationId": self.location_id, "query": query}
        response = requests.get(url, headers=self.headers, params=params)
        return response.json()
    
    def update_contact(self, contact_id, data):
        """Update a contact"""
        url = f"{self.base_url}/contacts/{contact_id}"
        response = requests.put(url, headers=self.headers, json=data)
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
    
    # OPPORTUNITIES
    def create_opportunity(self, data):
        """Create an opportunity"""
        url = f"{self.base_url}/opportunities/"
        payload = {"locationId": self.location_id, **data}
        print(f"Creating opportunity: {payload}")
        response = requests.post(url, headers=self.headers, json=payload)
        print(f"Opportunity response: {response.status_code} - {response.text}")
        return response.json()
    
    def get_opportunities(self, contact_id=None, pipeline_id=None):
        """Get opportunities"""
        url = f"{self.base_url}/opportunities/search"
        params = {"location_id": self.location_id}
        if contact_id:
            params["contact_id"] = contact_id
        if pipeline_id:
            params["pipelineId"] = pipeline_id
        response = requests.get(url, headers=self.headers, params=params)
        return response.json()
    
    def update_opportunity(self, opportunity_id, data):
        """Update opportunity (move stages, update value, etc)"""
        url = f"{self.base_url}/opportunities/{opportunity_id}"
        print(f"Updating opportunity {opportunity_id}: {data}")
        response = requests.put(url, headers=self.headers, json=data)
        print(f"Update response: {response.status_code} - {response.text}")
        return response.json()
    
    def delete_opportunity(self, opportunity_id):
        """Delete an opportunity"""
        url = f"{self.base_url}/opportunities/{opportunity_id}"
        response = requests.delete(url, headers=self.headers)
        return response.json()
    
    # PIPELINES
    def get_pipelines(self):
        """Get all pipelines"""
        url = f"{self.base_url}/opportunities/pipelines"
        params = {"locationId": self.location_id}
        response = requests.get(url, headers=self.headers, params=params)
        return response.json()
    
    # APPOINTMENTS
    def create_appointment(self, data):
        """Create an appointment"""
        url = f"{self.base_url}/calendars/events/appointments"
        payload = {"locationId": self.location_id, **data}
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json()
    
    def get_appointments(self, contact_id=None):
        """Get appointments"""
        url = f"{self.base_url}/calendars/events/appointments"
        params = {"locationId": self.location_id}
        if contact_id:
            params["contactId"] = contact_id
        response = requests.get(url, headers=self.headers, params=params)
        return response.json()
    
    # TASKS
    def create_task(self, data):
        """Create a task"""
        url = f"{self.base_url}/contacts/{data['contactId']}/tasks"
        response = requests.post(url, headers=self.headers, json=data)
        return response.json()
    
    # COMMUNICATIONS
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
    
    # CAMPAIGNS
    def add_to_campaign(self, contact_id, campaign_id):
        """Add contact to a campaign"""
        url = f"{self.base_url}/contacts/{contact_id}/campaigns/{campaign_id}"
        response = requests.post(url, headers=self.headers)
        return response.json()


class GHLAIAgent:
    """AI Agent with FULL CRM capabilities"""
    
    def __init__(self, ghl_api):
        self.ghl = ghl_api
    
    def interpret_command(self, user_command):
        """Use Claude to interpret commands"""
        
        if not anthropic_client:
            return {"action": "error", "parameters": {}, "confirmation_message": "Anthropic API key not configured."}
        
        system_prompt = """You are an AI assistant for GoHighLevel CRM with FULL capabilities.

Available actions:
1. create_contact - Create a contact
2. update_contact - Update contact details
3. search_contact - Search for contacts
4. add_note - Add note to contact
5. add_tag - Add tags to contact
6. create_opportunity - Create a new deal/opportunity
7. update_opportunity - Update opportunity (change stage, value, status)
8. move_opportunity - Move opportunity to different stage
9. get_opportunities - List opportunities
10. get_pipelines - List all pipelines and stages
11. create_appointment - Schedule an appointment
12. create_task - Create a task
13. send_sms - Send SMS to contact
14. send_email - Send email to contact
15. add_to_campaign - Add contact to a campaign

Return JSON:
{
    "action": "action_name",
    "parameters": {...},
    "confirmation_message": "description"
}

Examples:

"Create opportunity for John Doe worth $50000 in Sales pipeline"
{
    "action": "create_opportunity",
    "parameters": {
        "contact_name": "John Doe",
        "name": "John Doe - $50000 Deal",
        "monetaryValue": 50000,
        "pipelineName": "Sales"
    },
    "confirmation_message": "Creating $50000 opportunity for John Doe in Sales pipeline"
}

"Move John's deal to Contract Signed"
{
    "action": "move_opportunity",
    "parameters": {
        "contact_name": "John Doe",
        "stage_name": "Contract Signed"
    },
    "confirmation_message": "Moving John Doe's opportunity to Contract Signed stage"
}

"Send SMS to John saying thanks for the meeting"
{
    "action": "send_sms",
    "parameters": {
        "contact_name": "John",
        "message": "Thanks for the meeting!"
    },
    "confirmation_message": "Sending SMS to John"
}

"Show me all pipelines"
{
    "action": "get_pipelines",
    "parameters": {},
    "confirmation_message": "Getting all pipelines and stages"
}

Return ONLY JSON."""

        try:
            message = anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_command}]
            )
            
            response_text = message.content[0].text
            return json.loads(response_text)
        except Exception as e:
            return {"action": "error", "parameters": {}, "confirmation_message": f"Error: {str(e)}"}
    
    def execute_command(self, command_data):
        """Execute ANY command"""
        
        action = command_data.get("action")
        params = command_data.get("parameters", {})
        
        try:
            # CONTACTS
            if action == "create_contact":
                result = self.ghl.create_contact(params)
                if result.get("contact"):
                    contact = result["contact"]
                    name = f"{contact.get('firstName', '')} {contact.get('lastName', '')}".strip()
                    return {"success": True, "message": f"✅ Created contact: {name}", "data": contact}
                return {"success": False, "message": f"❌ Error: {result.get('message', 'Unknown')}"}
            
            elif action == "search_contact":
                result = self.ghl.search_contacts(params.get("query"))
                contacts = result.get("contacts", [])
                if contacts:
                    contact_list = [{
                        "name": f"{c.get('firstName', '')} {c.get('lastName', '')}".strip(),
                        "email": c.get('email', 'No email'),
                        "phone": c.get('phone', 'No phone'),
                        "tags": c.get('tags', [])
                    } for c in contacts[:10]]
                    return {"success": True, "message": f"✅ Found {len(contacts)} contact(s)", "data": contact_list}
                return {"success": False, "message": f"❌ No contacts found"}
            
            elif action == "add_note":
                contacts = self.ghl.search_contacts(params.get("contact_name"))
                if contacts.get("contacts"):
                    contact_id = contacts["contacts"][0]["id"]
                    self.ghl.add_note_to_contact(contact_id, params["note"])
                    return {"success": True, "message": f"✅ Added note to {params.get('contact_name')}"}
                return {"success": False, "message": f"❌ Contact not found"}
            
            elif action == "add_tag":
                contacts = self.ghl.search_contacts(params.get("contact_name"))
                if contacts.get("contacts"):
                    contact_id = contacts["contacts"][0]["id"]
                    self.ghl.add_tag_to_contact(contact_id, params["tags"])
                    return {"success": True, "message": f"✅ Added tags to {params.get('contact_name')}"}
                return {"success": False, "message": f"❌ Contact not found"}
            
            # OPPORTUNITIES
            elif action == "create_opportunity":
                # First find the contact
                contacts = self.ghl.search_contacts(params.get("contact_name", ""))
                if not contacts.get("contacts"):
                    return {"success": False, "message": f"❌ Contact not found: {params.get('contact_name')}"}
                
                contact_id = contacts["contacts"][0]["id"]
                
                # Get pipelines to find the right one
                pipelines = self.ghl.get_pipelines()
                pipeline = None
                stage_id = None
                
                if pipelines.get("pipelines"):
                    # Find pipeline by name or use first one
                    pipeline_name = params.get("pipelineName", "").lower()
                    for p in pipelines["pipelines"]:
                        if pipeline_name in p.get("name", "").lower() or not pipeline_name:
                            pipeline = p
                            # Use first stage
                            if p.get("stages"):
                                stage_id = p["stages"][0]["id"]
                            break
                
                if not pipeline or not stage_id:
                    return {"success": False, "message": "❌ Could not find pipeline or stage"}
                
                opp_data = {
                    "pipelineId": pipeline["id"],
                    "pipelineStageId": stage_id,
                    "contactId": contact_id,
                    "name": params.get("name", f"Opportunity for {params.get('contact_name')}"),
                    "monetaryValue": params.get("monetaryValue", 0),
                    "status": "open"
                }
                
                result = self.ghl.create_opportunity(opp_data)
                if result.get("opportunity"):
                    return {"success": True, "message": f"✅ Created opportunity: {opp_data['name']}"}
                return {"success": False, "message": f"❌ Error creating opportunity: {result.get('message')}"}
            
            elif action == "move_opportunity" or action == "update_opportunity":
                # Find contact's opportunity
                contacts = self.ghl.search_contacts(params.get("contact_name", ""))
                if not contacts.get("contacts"):
                    return {"success": False, "message": "❌ Contact not found"}
                
                contact_id = contacts["contacts"][0]["id"]
                opps = self.ghl.get_opportunities(contact_id=contact_id)
                
                if not opps.get("opportunities"):
                    return {"success": False, "message": "❌ No opportunities found for this contact"}
                
                opp = opps["opportunities"][0]
                opp_id = opp["id"]
                
                # If moving to a stage, find the stage ID
                update_data = {}
                if params.get("stage_name"):
                    pipelines = self.ghl.get_pipelines()
                    for pipeline in pipelines.get("pipelines", []):
                        for stage in pipeline.get("stages", []):
                            if params["stage_name"].lower() in stage["name"].lower():
                                update_data["pipelineStageId"] = stage["id"]
                                break
                
                if params.get("monetaryValue"):
                    update_data["monetaryValue"] = params["monetaryValue"]
                if params.get("status"):
                    update_data["status"] = params["status"]
                
                result = self.ghl.update_opportunity(opp_id, update_data)
                return {"success": True, "message": f"✅ Updated opportunity"}
            
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
                    return {"success": True, "message": f"✅ Found {len(pipeline_info)} pipeline(s)", "data": pipeline_info}
                return {"success": False, "message": "❌ No pipelines found"}
            
            elif action == "get_opportunities":
                contact_name = params.get("contact_name")
                if contact_name:
                    contacts = self.ghl.search_contacts(contact_name)
                    if contacts.get("contacts"):
                        contact_id = contacts["contacts"][0]["id"]
                        result = self.ghl.get_opportunities(contact_id=contact_id)
                    else:
                        return {"success": False, "message": "❌ Contact not found"}
                else:
                    result = self.ghl.get_opportunities()
                
                opps = result.get("opportunities", [])
                return {"success": True, "message": f"✅ Found {len(opps)} opportunities", "data": opps[:10]}
            
            # COMMUNICATIONS
            elif action == "send_sms":
                contacts = self.ghl.search_contacts(params.get("contact_name"))
                if contacts.get("contacts"):
                    contact_id = contacts["contacts"][0]["id"]
                    result = self.ghl.send_sms(contact_id, params["message"])
                    return {"success": True, "message": f"✅ SMS sent to {params.get('contact_name')}"}
                return {"success": False, "message": "❌ Contact not found"}
            
            elif action == "send_email":
                contacts = self.ghl.search_contacts(params.get("contact_name"))
                if contacts.get("contacts"):
                    contact_id = contacts["contacts"][0]["id"]
                    result = self.ghl.send_email(contact_id, params.get("subject", ""), params.get("body", ""))
                    return {"success": True, "message": f"✅ Email sent to {params.get('contact_name')}"}
                return {"success": False, "message": "❌ Contact not found"}
            
            # TASKS & APPOINTMENTS
            elif action == "create_task":
                contacts = self.ghl.search_contacts(params.get("contact_name"))
                if contacts.get("contacts"):
                    contact_id = contacts["contacts"][0]["id"]
                    task_data = {"contactId": contact_id, "title": params.get("title"), "dueDate": params.get("dueDate")}
                    result = self.ghl.create_task(task_data)
                    return {"success": True, "message": f"✅ Task created"}
                return {"success": False, "message": "❌ Contact not found"}
            
            elif action == "create_appointment":
                result = self.ghl.create_appointment(params)
                return {"success": True, "message": "✅ Appointment created"}
            
            elif action == "error":
                return {"success": False, "message": command_data.get('confirmation_message')}
            
            else:
                return {"success": False, "message": f"❌ Action not implemented: {action}"}
        
        except Exception as e:
            print(f"Execute error: {str(e)}")
            return {"success": False, "message": f"❌ Error: {str(e)}"}


# Initialize
ghl_api = GoHighLevelAPI(GHL_API_KEY, GHL_LOCATION_ID)
agent = GHLAIAgent(ghl_api)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/command', methods=['POST'])
def process_command():
    data = request.json
    user_command = data.get('command', '')
    
    if not user_command:
        return jsonify({"success": False, "message": "No command provided"})
    
    command_data = agent.interpret_command(user_command)
    result = agent.execute_command(command_data)
    
    return jsonify({
        "success": result.get("success", False),
        "message": result.get("message", ""),
        "data": result.get("data"),
        "plan": command_data.get("confirmation_message", "")
    })


@app.route('/api/test', methods=['GET'])
def test_api():
    try:
        contacts = ghl_api.search_contacts("")
        return jsonify({
            "success": True,
            "message": "✅ Connected to GoHighLevel V2",
            "contact_count": len(contacts.get("contacts", []))
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"❌ Error: {str(e)}"})


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 GoHighLevel AI Agent - FULL FEATURED")
    print("=" * 60)
    print("\n📱 V2 API | Opportunities | SMS | Email | Tasks")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
