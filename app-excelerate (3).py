#!/usr/bin/env python3
"""
eXcelerate CRM AI Agent by Jay Kinder
Complete AI-powered CRM control for eXp Realty
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
    
    def find_stage_by_name(self, stage_name):
        """Find a stage ID by name (fuzzy matching for eXp Realty stages)"""
        pipelines = self.get_pipelines()
        
        # Normalize search term
        search_term = stage_name.lower().strip()
        
        for pipeline in pipelines.get("pipelines", []):
            for stage in pipeline.get("stages", []):
                stage_name_lower = stage["name"].lower()
                
                # Exact match
                if search_term == stage_name_lower:
                    return {
                        "stage_id": stage["id"],
                        "stage_name": stage["name"],
                        "pipeline_id": pipeline["id"],
                        "pipeline_name": pipeline["name"]
                    }
                
                # Partial match (e.g., "verbally" matches "Verbally Committed")
                if search_term in stage_name_lower or stage_name_lower in search_term:
                    return {
                        "stage_id": stage["id"],
                        "stage_name": stage["name"],
                        "pipeline_id": pipeline["id"],
                        "pipeline_name": pipeline["name"]
                    }
        
        return None
    
    def move_opportunity_to_stage(self, opportunity_id, stage_name):
        """Move an opportunity to a stage by name"""
        stage_info = self.find_stage_by_name(stage_name)
        
        if not stage_info:
            return {"error": f"Stage '{stage_name}' not found in any pipeline"}
        
        update_data = {
            "pipelineStageId": stage_info["stage_id"]
        }
        
        result = self.update_opportunity(opportunity_id, update_data)
        result["stage_info"] = stage_info
        return result
    
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
                "confirmation_message": "AI service not configured."
            }
        
        system_prompt = """You are an AI assistant for eXcelerate CRM - eXp Realty recruiting system. Understand REAL recruiting language - how recruiters actually talk. Return ONLY valid JSON.

CRITICAL: Return ONLY the JSON object. No markdown, no code blocks, no explanations.

REAL RECRUITING LANGUAGE:
- "send jeff the live call invite" = move Jeff to "Send Live Invite" stage
- "resend jeff the invite" = move Jeff to "Send Live Invite" stage (or send snippet)
- "show me who is verbally committed" = search contacts in "Verbally Committed" stage
- "who's ready to close" = show contacts in final stages
- "set appt with jeff friday at 3" = create appointment with Jeff
- "schedule call with sarah tuesday 2pm" = create appointment
- "jeff signed" = move to "Contract Signed"
- "sarah committed" = move to "Verbally Committed"
- "put mike in nurture" = tag as nurture or move to appropriate stage

PHONE NUMBER HANDLING:
- "text 555-1234 thanks" = send SMS directly to that phone number
- "text 2142903350 here's the link" = send to phone number
- Phone numbers: 555-1234, (214)290-3350, 214-290-3350

UNDERSTAND NATURAL SPEECH:
- People say "find john" not "search for contact named john"
- People say "jeff committed" not "move jeff's opportunity to verbally committed stage"
- People say "who's in contract" not "show contacts in contract signed stage"
- People use pronouns: "move her deal", "text him", "set appt with her"
- People make typos: "comitted", "wendesday", "febuary"
- People are vague: "show me my hot leads", "who's ready", "send the invite"

Available actions:
- search_contact: "find john", "who is sarah", "lookup mike"
- search_by_stage: "who's verbally committed", "show me send invite stage", "who's in contract"
- create_contact: "add john 555-1234", "new contact sarah"
- update_contact: "change his phone", "update sarah's email"
- add_note: "note on john: called today", "jeff said he's interested"
- add_tag: "tag sarah hot lead", "mark as nurture", "label john vip"
- move_opportunity: "send jeff the invite", "jeff committed", "sarah signed", "put mike in contract"
- create_opportunity: "new deal john", "create opportunity sarah 50k"
- send_sms: "text john thanks", "message sarah"
- send_sms_to_number: "text 555-1234 hello" (direct to phone)
- create_appointment: "set appt with jeff friday 3pm", "schedule call sarah tuesday"
- pipeline_report: "how's my pipeline", "show stats"
- get_pipelines: "show stages", "what stages"
- contact_stats: "how many contacts"

Response format:
{
    "action": "action_name",
    "parameters": {...},
    "confirmation_message": "brief description"
}

REAL EXAMPLES:

"send jeff the live call invite"
{"action": "move_opportunity", "parameters": {"contact_name": "jeff", "stage_name": "send live invite"}, "confirmation_message": "Moving jeff to send live invite"}

"resend jeff the invite"
{"action": "move_opportunity", "parameters": {"contact_name": "jeff", "stage_name": "send live invite"}, "confirmation_message": "Moving jeff to send live invite"}

"show me who is verbally committed"
{"action": "search_by_stage", "parameters": {"stage_name": "verbally committed"}, "confirmation_message": "Finding contacts in verbally committed"}

"who's in contract"
{"action": "search_by_stage", "parameters": {"stage_name": "contract signed"}, "confirmation_message": "Finding contacts in contract signed"}

"jeff signed"
{"action": "move_opportunity", "parameters": {"contact_name": "jeff", "stage_name": "contract signed"}, "confirmation_message": "Moving jeff to contract signed"}

"sarah committed"
{"action": "move_opportunity", "parameters": {"contact_name": "sarah", "stage_name": "verbally committed"}, "confirmation_message": "Moving sarah to verbally committed"}

"set appt with jeff friday at 3"
{"action": "create_appointment", "parameters": {"contact_name": "jeff", "date": "friday", "time": "3pm"}, "confirmation_message": "Scheduling appointment with jeff"}

"schedule call with sarah tuesday 2pm"
{"action": "create_appointment", "parameters": {"contact_name": "sarah", "date": "tuesday", "time": "2pm"}, "confirmation_message": "Scheduling call with sarah"}

"text 2142903350 here's the link"
{"action": "send_sms_to_number", "parameters": {"phone": "2142903350", "message": "here's the link"}, "confirmation_message": "Texting 2142903350"}

"find john"
{"action": "search_contact", "parameters": {"query": "john"}, "confirmation_message": "Looking for john"}

"johns phone is 555-9999"
{"action": "update_contact", "parameters": {"contact_name": "john", "phone": "555-9999"}, "confirmation_message": "Updating john's phone"}

"who's ready to close"
{"action": "search_by_stage", "parameters": {"stage_name": "contract signed"}, "confirmation_message": "Finding contacts ready to close"}

"show my hot leads"
{"action": "search_by_tag", "parameters": {"tag": "hot lead"}, "confirmation_message": "Finding hot leads"}

"hows my pipeline"
{"action": "pipeline_report", "parameters": {}, "confirmation_message": "Getting pipeline stats"}

"tag everyone in cali west coast"
{"action": "bulk_tag", "parameters": {"filter": "california", "tag": "west coast"}, "confirmation_message": "Tagging california contacts"}

BE SMART:
- "send/resend invite" = move to "Send Live Invite" stage
- "jeff committed/verbally" = move to "Verbally Committed"
- "jeff signed/contract" = move to "Contract Signed"
- "show who's in X" = search by stage X
- "set appt" = create appointment
- If unclear, make best guess - don't refuse

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
                    pipeline_data = []
                    for p in result["pipelines"]:
                        stages = p.get("stages", [])
                        stage_names = [s["name"] for s in stages]
                        
                        # Create a clear display for each pipeline
                        pipeline_data.append({
                            "pipeline": p["name"],
                            "total_stages": len(stages),
                            "stages": " → ".join(stage_names)
                        })
                    
                    return {
                        "success": True,
                        "message": f"✅ Found {len(result['pipelines'])} pipeline(s) with stages",
                        "data": pipeline_data
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
            
            # Move opportunity to stage
            elif action == "move_opportunity":
                contact_name = params.get("contact_name")
                stage_name = params.get("stage_name")
                
                # Find contact first
                contacts = self.ghl.search_contacts(contact_name)
                if not contacts.get("contacts"):
                    return {"success": False, "message": f"❌ Contact '{contact_name}' not found"}
                
                contact_id = contacts["contacts"][0]["id"]
                
                # Get their opportunities
                opps = self.ghl.get_opportunities(contact_id=contact_id)
                opportunities = opps.get("opportunities", [])
                
                if not opportunities:
                    return {"success": False, "message": f"❌ No opportunities found for {contact_name}"}
                
                # Get the most recent opportunity (or first one)
                opportunity_id = opportunities[0]["id"]
                
                # Move to the stage
                result = self.ghl.move_opportunity_to_stage(opportunity_id, stage_name)
                
                if result.get("error"):
                    return {"success": False, "message": f"❌ {result['error']}"}
                
                stage_info = result.get("stage_info", {})
                return {
                    "success": True,
                    "message": f"✅ Moved {contact_name}'s opportunity to '{stage_info.get('stage_name')}' in {stage_info.get('pipeline_name')} pipeline"
                }
            
            # Send SMS
            elif action == "send_sms":
                contacts = self.ghl.search_contacts(params.get("contact_name"))
                if contacts.get("contacts"):
                    contact_id = contacts["contacts"][0]["id"]
                    self.ghl.send_sms(contact_id, params["message"])
                    return {"success": True, "message": "✅ SMS sent"}
                return {"success": False, "message": "❌ Contact not found"}
            
            # Send SMS to phone number directly
            elif action == "send_sms_to_number":
                phone = params.get("phone")
                message = params.get("message")
                
                # Try to find contact by phone number first
                contacts = self.ghl.search_contacts(phone)
                
                if contacts.get("contacts"):
                    # Found a contact with this number
                    contact_id = contacts["contacts"][0]["id"]
                    self.ghl.send_sms(contact_id, message)
                    return {"success": True, "message": f"✅ SMS sent to {phone}"}
                else:
                    # No contact found - need to create one first
                    # GHL requires a contact to send SMS
                    return {
                        "success": False, 
                        "message": f"❌ No contact found with number {phone}. Create the contact first with: add contact {phone}"
                    }
            
            # Create appointment - "set appt with jeff friday 3pm"
            elif action == "create_appointment":
                contact_name = params.get("contact_name")
                date_str = params.get("date", "")
                time_str = params.get("time", "")
                
                # Find the contact
                contacts = self.ghl.search_contacts(contact_name)
                if not contacts.get("contacts"):
                    return {"success": False, "message": f"❌ Contact '{contact_name}' not found"}
                
                contact_id = contacts["contacts"][0]["id"]
                
                # For now, just add a note about the appointment
                # Full calendar integration would require calendar ID which we don't have
                note_text = f"Appointment requested: {date_str} at {time_str}"
                self.ghl.add_note_to_contact(contact_id, note_text)
                
                return {
                    "success": True,
                    "message": f"✅ Appointment note added for {contact_name} - {date_str} at {time_str}. (Note: Full calendar integration requires calendar setup)"
                }
            
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
            
            # Search by stage - "who's verbally committed", "show me who's in contract"
            elif action == "search_by_stage":
                stage_name = params.get("stage_name")
                
                # Get all opportunities
                opps_result = self.ghl.get_opportunities(limit=500)
                opportunities = opps_result.get("opportunities", [])
                
                # Get pipelines to match stage names
                pipelines = self.ghl.get_pipelines()
                stage_id = None
                
                # Find the stage ID by fuzzy matching
                for pipeline in pipelines.get("pipelines", []):
                    for stage in pipeline.get("stages", []):
                        if stage_name.lower() in stage["name"].lower() or stage["name"].lower() in stage_name.lower():
                            stage_id = stage["id"]
                            break
                    if stage_id:
                        break
                
                if not stage_id:
                    return {"success": False, "message": f"❌ Stage '{stage_name}' not found"}
                
                # Filter opportunities by this stage
                matching_opps = [o for o in opportunities if o.get("pipelineStageId") == stage_id]
                
                if not matching_opps:
                    return {"success": True, "message": f"✅ No one currently in '{stage_name}' stage"}
                
                # Get contact details for each opportunity
                contact_list = []
                for opp in matching_opps[:20]:
                    contact_id = opp.get("contactId")
                    if contact_id:
                        try:
                            contact_result = self.ghl.get_contact(contact_id)
                            contact = contact_result.get("contact", {})
                            contact_list.append({
                                "name": f"{contact.get('firstName', '')} {contact.get('lastName', '')}".strip(),
                                "email": contact.get('email', 'No email'),
                                "phone": contact.get('phone', 'No phone'),
                                "deal_value": f"${opp.get('monetaryValue', 0):,}"
                            })
                        except:
                            pass
                
                return {
                    "success": True,
                    "message": f"✅ Found {len(contact_list)} people in '{stage_name}' stage",
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
            "message": "✅ Connected - eXcelerate CRM by Jay Kinder",
            "contact_count": len(contacts.get("contacts", []))
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"❌ Connection error: {str(e)}"
        })


@app.route('/api/examples', methods=['GET'])
def get_examples():
    """Get natural, conversational example commands"""
    examples = {
        "contacts": [
            "find mike",
            "add sarah 555-1234",
            "johns phone is 555-9999",
            "note on mike: interested"
        ],
        "pipeline": [
            "sarah is committed",
            "move john to send invite",
            "put mike in contract signed",
            "new deal sarah 50k"
        ],
        "actions": [
            "text john thanks!",
            "tag mike hot lead",
            "tag everyone in texas"
        ],
        "status": [
            "hows my pipeline",
            "show stats",
            "what stages"
        ]
    }
    
    return jsonify(examples)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
