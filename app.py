#!/usr/bin/env python3
"""
eXcelerate CRM - Clean Working Version
Core recruiting functions only - tested and reliable
"""

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import os
import json
import re
import requests
from datetime import datetime
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
anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None


class GoHighLevelAPI:
    """Simple GHL API Wrapper"""
    
    def __init__(self, api_key, location_id):
        self.api_key = api_key
        self.location_id = location_id
        self.base_url = GHL_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Version": "2021-07-28"
        }
    
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
    
    def add_note(self, contact_id, note):
        """Add a note to a contact"""
        url = f"{self.base_url}/contacts/{contact_id}/notes"
        payload = {"body": note}
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json()
    
    def add_tag(self, contact_id, tag):
        """Add tag to a contact"""
        url = f"{self.base_url}/contacts/{contact_id}/tags"
        payload = {"tags": [tag] if isinstance(tag, str) else tag}
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json()
    
    def get_pipelines(self):
        """Get all pipelines"""
        url = f"{self.base_url}/opportunities/pipelines"
        params = {"locationId": self.location_id}
        response = requests.get(url, headers=self.headers, params=params)
        return response.json()
    
    def get_opportunities(self, contact_id=None, limit=500):
        """Get opportunities"""
        url = f"{self.base_url}/opportunities/search"
        params = {"locationId": self.location_id, "limit": limit}
        if contact_id:
            params["contactId"] = contact_id
        response = requests.get(url, headers=self.headers, params=params)
        return response.json()
    
    def create_opportunity(self, contact_id, pipeline_id, stage_id):
        """Create a new opportunity"""
        url = f"{self.base_url}/opportunities/"
        payload = {
            "locationId": self.location_id,
            "pipelineId": pipeline_id,
            "pipelineStageId": stage_id,
            "contactId": contact_id,
            "name": "eXp Recruiting",
            "status": "open"
        }
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json()
    
    def update_opportunity(self, opportunity_id, stage_id):
        """Update opportunity stage"""
        url = f"{self.base_url}/opportunities/{opportunity_id}"
        payload = {"pipelineStageId": stage_id}
        response = requests.put(url, headers=self.headers, json=payload)
        return response.json()
    
    def find_stage(self, stage_keyword):
        """Find stage in eXp pipeline"""
        pipelines = self.get_pipelines()
        
        # Find eXp Realty pipeline
        exp_pipeline = None
        for p in pipelines.get("pipelines", []):
            if "exp" in p["name"].lower() and "realty" in p["name"].lower():
                exp_pipeline = p
                break
        
        if not exp_pipeline:
            return None
        
        # Match stage
        search_term = stage_keyword.lower()
        for stage in exp_pipeline.get("stages", []):
            stage_name = stage["name"].lower()
            
            # Direct match
            if search_term in stage_name or stage_name in search_term:
                return {
                    "pipeline_id": exp_pipeline["id"],
                    "pipeline_name": exp_pipeline["name"],
                    "stage_id": stage["id"],
                    "stage_name": stage["name"]
                }
        
        return None
    
    def move_to_stage(self, contact_id, stage_keyword):
        """Move or create opportunity in stage"""
        stage_info = self.find_stage(stage_keyword)
        if not stage_info:
            return {"error": f"Stage '{stage_keyword}' not found"}
        
        # Check for existing opportunity
        opps = self.get_opportunities(contact_id=contact_id)
        exp_opps = [o for o in opps.get("opportunities", []) 
                   if o.get("pipelineId") == stage_info["pipeline_id"]]
        
        if exp_opps:
            # Update existing
            self.update_opportunity(exp_opps[0]["id"], stage_info["stage_id"])
            return {"action": "updated", **stage_info}
        else:
            # Create new
            self.create_opportunity(contact_id, stage_info["pipeline_id"], stage_info["stage_id"])
            return {"action": "created", **stage_info}


class SimpleAssistant:
    """Simple AI assistant - crystal clear commands"""
    
    def __init__(self, ghl):
        self.ghl = ghl
    
    def understand(self, command):
        """Use AI to understand command"""
        
        if not anthropic_client:
            return {"action": "error", "message": "AI not configured"}
        
        prompt = f"""You interpret eXp recruiting commands. Return ONLY valid JSON.

AVAILABLE ACTIONS:
- search_contact: "find jeff", "search sarah"
- add_note: "note on jeff: interested", "add note jeff called today"
- add_tag: "tag sarah hot lead", "tag jeff vip"
- move_stage: "send jeff live call invite", "jeff committed", "sarah send partner webinar"
- show_pipeline: "hows my pipeline", "show stages"
- search_stage: "who's in registered", "show me verbally committed"

STAGE KEYWORDS:
- "live call invite" or "live invite" → Send Live Call Invite
- "partner webinar" or "send invite" → Send Invite
- "registered" → Registered
- "watched" → Watched Webinar
- "discovery" → Discovery Call Scheduled
- "3 way" or "three way" → Three Way Call Scheduled
- "red zone" → Red Zone
- "committed" or "verbally" → Verbally Committed
- "application" → Application Appt Complete

Return JSON:
{{
    "action": "action_name",
    "contact": "name" (if applicable),
    "stage": "stage" (if applicable),
    "note": "note text" (if applicable),
    "tag": "tag" (if applicable)
}}

EXAMPLES:

"find jeff" → {{"action": "search_contact", "contact": "jeff"}}
"note on jeff: very interested" → {{"action": "add_note", "contact": "jeff", "note": "very interested"}}
"tag sarah hot lead" → {{"action": "add_tag", "contact": "sarah", "tag": "hot lead"}}
"send jeff live call invite" → {{"action": "move_stage", "contact": "jeff", "stage": "live call invite"}}
"jeff committed" → {{"action": "move_stage", "contact": "jeff", "stage": "committed"}}
"hows my pipeline" → {{"action": "show_pipeline"}}
"who's in registered" → {{"action": "search_stage", "stage": "registered"}}

User: {command}
Return ONLY JSON:"""

        try:
            message = anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text.strip()
            response_text = re.sub(r'```json\s*|\s*```', '', response_text).strip()
            
            return json.loads(response_text)
            
        except Exception as e:
            print(f"AI Error: {e}")
            return {"action": "error", "message": str(e)}
    
    def execute(self, command_data):
        """Execute the command"""
        
        action = command_data.get("action")
        
        try:
            # Search contact
            if action == "search_contact":
                contact_name = command_data.get("contact")
                result = self.ghl.search_contacts(contact_name)
                contacts = result.get("contacts", [])
                
                if not contacts:
                    return {"success": False, "message": f"❌ No contact found for '{contact_name}'"}
                
                contact = contacts[0]
                return {
                    "success": True,
                    "message": f"✅ Found {contact.get('firstName', '')} {contact.get('lastName', '')}",
                    "data": [{
                        "name": f"{contact.get('firstName', '')} {contact.get('lastName', '')}".strip(),
                        "email": contact.get("email", "No email"),
                        "phone": contact.get("phone", "No phone"),
                        "tags": contact.get("tags", [])
                    }]
                }
            
            # Add note
            elif action == "add_note":
                contact_name = command_data.get("contact")
                note_text = command_data.get("note")
                
                # Find contact
                result = self.ghl.search_contacts(contact_name)
                contacts = result.get("contacts", [])
                if not contacts:
                    return {"success": False, "message": f"❌ Contact '{contact_name}' not found"}
                
                contact_id = contacts[0]["id"]
                self.ghl.add_note(contact_id, note_text)
                
                return {
                    "success": True,
                    "message": f"✅ Note added to {contacts[0].get('firstName', contact_name)}: {note_text}"
                }
            
            # Add tag
            elif action == "add_tag":
                contact_name = command_data.get("contact")
                tag = command_data.get("tag")
                
                # Find contact
                result = self.ghl.search_contacts(contact_name)
                contacts = result.get("contacts", [])
                if not contacts:
                    return {"success": False, "message": f"❌ Contact '{contact_name}' not found"}
                
                contact_id = contacts[0]["id"]
                self.ghl.add_tag(contact_id, tag)
                
                return {
                    "success": True,
                    "message": f"✅ Tagged {contacts[0].get('firstName', contact_name)} as '{tag}'"
                }
            
            # Move to stage
            elif action == "move_stage":
                contact_name = command_data.get("contact")
                stage = command_data.get("stage")
                
                # Find contact
                result = self.ghl.search_contacts(contact_name)
                contacts = result.get("contacts", [])
                if not contacts:
                    return {"success": False, "message": f"❌ Contact '{contact_name}' not found"}
                
                contact_id = contacts[0]["id"]
                contact_full_name = f"{contacts[0].get('firstName', '')} {contacts[0].get('lastName', '')}".strip()
                
                # Move to stage
                result = self.ghl.move_to_stage(contact_id, stage)
                
                if result.get("error"):
                    return {"success": False, "message": f"❌ {result['error']}"}
                
                action_word = "Moved" if result["action"] == "updated" else "Created opportunity and moved"
                
                return {
                    "success": True,
                    "message": f"✅ {action_word} {contact_full_name} to '{result['stage_name']}'"
                }
            
            # Show pipeline
            elif action == "show_pipeline":
                pipelines = self.ghl.get_pipelines()
                all_opps = self.ghl.get_opportunities()
                
                # Find eXp pipeline
                exp_pipeline = None
                for p in pipelines.get("pipelines", []):
                    if "exp" in p["name"].lower() and "realty" in p["name"].lower():
                        exp_pipeline = p
                        break
                
                if not exp_pipeline:
                    return {"success": False, "message": "❌ eXp Realty pipeline not found"}
                
                # Count opps per stage
                stage_counts = []
                for stage in exp_pipeline.get("stages", []):
                    count = len([o for o in all_opps.get("opportunities", []) 
                                if o.get("pipelineStageId") == stage["id"]])
                    if count > 0:  # Only show stages with opportunities
                        stage_counts.append({
                            "stage": stage["name"],
                            "count": count
                        })
                
                total = sum(s["count"] for s in stage_counts)
                
                return {
                    "success": True,
                    "message": f"📊 Pipeline Overview - {total} total opportunities",
                    "data": stage_counts
                }
            
            # Search by stage
            elif action == "search_stage":
                stage = command_data.get("stage")
                
                stage_info = self.ghl.find_stage(stage)
                if not stage_info:
                    return {"success": False, "message": f"❌ Stage '{stage}' not found"}
                
                # Get all opps in this stage
                all_opps = self.ghl.get_opportunities()
                stage_opps = [o for o in all_opps.get("opportunities", []) 
                             if o.get("pipelineStageId") == stage_info["stage_id"]]
                
                if not stage_opps:
                    return {
                        "success": True,
                        "message": f"✅ No one in '{stage_info['stage_name']}' stage"
                    }
                
                # Get contact details
                contact_list = []
                for opp in stage_opps[:20]:
                    try:
                        contact = self.ghl.get_contact(opp["contactId"])
                        c = contact.get("contact", {})
                        contact_list.append({
                            "name": f"{c.get('firstName', '')} {c.get('lastName', '')}".strip(),
                            "email": c.get("email", "No email"),
                            "phone": c.get("phone", "No phone")
                        })
                    except:
                        pass
                
                return {
                    "success": True,
                    "message": f"✅ Found {len(contact_list)} in '{stage_info['stage_name']}'",
                    "data": contact_list
                }
            
            # Error
            else:
                return {
                    "success": False,
                    "message": f"❌ I don't know how to: {action}"
                }
        
        except Exception as e:
            print(f"Execute error: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"❌ Error: {str(e)}"}


# Initialize
ghl = GoHighLevelAPI(GHL_API_KEY, GHL_LOCATION_ID)
assistant = SimpleAssistant(ghl)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/command', methods=['POST'])
def process_command():
    data = request.json
    command = data.get('command', '')
    
    if not command:
        return jsonify({"success": False, "message": "No command provided"})
    
    try:
        # Understand command
        command_data = assistant.understand(command)
        
        # Execute it
        result = assistant.execute(command_data)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"API Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"❌ Error: {str(e)}"})


@app.route('/api/test', methods=['GET'])
def test_api():
    try:
        contacts = ghl.search_contacts("", limit=5)
        return jsonify({
            "success": True,
            "message": f"✅ Connected - Found {len(contacts.get('contacts', []))} contacts"
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"❌ Error: {str(e)}"})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
