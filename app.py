#!/usr/bin/env python3
"""
eXcelerate CRM - eXp Realty Recruiting Assistant
Built specifically for Jay Kinder's eXp recruiting workflow
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


# eXp Realty Pipeline Knowledge Base
EXP_PIPELINE_STAGES = {
    "send live call invite": {
        "name": "Send Live Call Invite",
        "description": "Triggers SMS + Email to register for Thursday 12pm CST live call",
        "keywords": ["live call", "live invite", "thursday call", "weekly call"]
    },
    "send invite": {
        "name": "Send Invite",
        "description": "Triggers SMS + Email to watch recorded partner webinar",
        "keywords": ["partner webinar", "recorded webinar", "webinar invite", "partner invite"]
    },
    "registered": {
        "name": "Registered",
        "description": "Agent registered for live call OR partner webinar",
        "keywords": ["registered", "signed up"]
    },
    "watched webinar": {
        "name": "Watched Webinar",
        "description": "Agent attended live call OR watched partner webinar",
        "keywords": ["watched", "attended", "showed up"]
    },
    "discovery call scheduled": {
        "name": "Discovery Call Scheduled",
        "description": "Agent booked discovery call to learn more",
        "keywords": ["discovery", "first call", "learning call"]
    },
    "three way call scheduled": {
        "name": "Three Way Call Scheduled",
        "description": "Agent booked 3-way call with upline leader",
        "keywords": ["three way", "3 way", "leadership call"]
    },
    "red zone": {
        "name": "Red Zone",
        "description": "Agent is 80% committed, very close to joining",
        "keywords": ["red zone", "almost there", "80%"]
    },
    "verbally committed": {
        "name": "Verbally Committed",
        "description": "Agent ready to start - triggers email with application next steps",
        "keywords": ["committed", "verbally", "ready to start"]
    },
    "application appt complete": {
        "name": "Application Appt Complete",
        "description": "Agent completed application appointment",
        "keywords": ["application complete", "app complete"]
    },
    "exp onboarding app complete": {
        "name": "eXp Onboarding App Complete",
        "description": "Agent showed up and completed application",
        "keywords": ["onboarding complete", "onboarded"]
    },
    "license transfer scheduled": {
        "name": "License Transfer Scheduled / Welcome Call",
        "description": "Agent officially licensed and transferred - DONE!",
        "keywords": ["welcome call", "license transfer", "completed", "done"]
    }
}


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
    
    def get_contact_notes(self, contact_id):
        """Get all notes for a contact"""
        url = f"{self.base_url}/contacts/{contact_id}/notes"
        response = requests.get(url, headers=self.headers)
        return response.json()
    
    def add_tag_to_contact(self, contact_id, tags):
        """Add tags to a contact"""
        url = f"{self.base_url}/contacts/{contact_id}"
        payload = {"tags": tags if isinstance(tags, list) else [tags]}
        response = requests.put(url, headers=self.headers, json=payload)
        return response.json()
    
    def create_opportunity(self, data):
        """Create a new opportunity"""
        url = f"{self.base_url}/opportunities/"
        payload = {"locationId": self.location_id, **data}
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json()
    
    def get_opportunities(self, contact_id=None, limit=500):
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
    
    def get_pipelines(self):
        """Get all pipelines"""
        url = f"{self.base_url}/opportunities/pipelines"
        params = {"locationId": self.location_id}
        response = requests.get(url, headers=self.headers, params=params)
        return response.json()
    
    def find_exp_pipeline_and_stage(self, stage_keyword):
        """Find the eXp Realty pipeline and match stage by keyword"""
        pipelines = self.get_pipelines()
        
        # Find eXp Realty pipeline
        exp_pipeline = None
        for pipeline in pipelines.get("pipelines", []):
            if "exp" in pipeline["name"].lower() and "realty" in pipeline["name"].lower():
                exp_pipeline = pipeline
                break
        
        if not exp_pipeline:
            return None
        
        # Match stage by keyword
        search_term = stage_keyword.lower().strip()
        
        # First check our knowledge base
        for key, stage_info in EXP_PIPELINE_STAGES.items():
            if search_term in key or any(kw in search_term for kw in stage_info["keywords"]):
                # Now find this stage in the actual pipeline
                for stage in exp_pipeline.get("stages", []):
                    if key in stage["name"].lower() or stage["name"].lower() in key:
                        return {
                            "pipeline_id": exp_pipeline["id"],
                            "pipeline_name": exp_pipeline["name"],
                            "stage_id": stage["id"],
                            "stage_name": stage["name"],
                            "description": stage_info["description"]
                        }
        
        # Fallback: fuzzy match on actual stages
        for stage in exp_pipeline.get("stages", []):
            if search_term in stage["name"].lower() or stage["name"].lower() in search_term:
                return {
                    "pipeline_id": exp_pipeline["id"],
                    "pipeline_name": exp_pipeline["name"],
                    "stage_id": stage["id"],
                    "stage_name": stage["name"],
                    "description": "Stage matched"
                }
        
        return None
    
    def move_or_create_opportunity(self, contact_id, stage_keyword):
        """Move existing opportunity or create new one in specified stage"""
        # Find the stage info
        stage_info = self.find_exp_pipeline_and_stage(stage_keyword)
        if not stage_info:
            return {"error": f"Could not find stage matching '{stage_keyword}' in eXp Realty pipeline"}
        
        # Check if contact already has an opportunity
        opps = self.get_opportunities(contact_id=contact_id)
        existing_opps = opps.get("opportunities", [])
        
        # Filter for eXp Realty pipeline opportunities
        exp_opps = [o for o in existing_opps if o.get("pipelineId") == stage_info["pipeline_id"]]
        
        if exp_opps:
            # Update existing opportunity
            opp_id = exp_opps[0]["id"]
            result = self.update_opportunity(opp_id, {"pipelineStageId": stage_info["stage_id"]})
            return {
                "action": "updated",
                "opportunity_id": opp_id,
                **stage_info
            }
        else:
            # Create new opportunity
            opp_data = {
                "pipelineId": stage_info["pipeline_id"],
                "pipelineStageId": stage_info["stage_id"],
                "contactId": contact_id,
                "name": f"eXp Recruiting",
                "status": "open"
            }
            result = self.create_opportunity(opp_data)
            return {
                "action": "created",
                "opportunity_id": result.get("opportunity", {}).get("id"),
                **stage_info
            }
    
    def get_contact_summary(self, contact_id):
        """Get complete contact summary with history"""
        contact_result = self.get_contact(contact_id)
        contact = contact_result.get("contact", {})
        
        # Get notes
        notes_result = self.get_contact_notes(contact_id)
        notes = notes_result.get("notes", [])
        
        # Get opportunities
        opps_result = self.get_opportunities(contact_id=contact_id)
        opps = opps_result.get("opportunities", [])
        
        # Get current stage
        current_stage = "No opportunity yet"
        if opps:
            latest_opp = opps[0]
            pipelines = self.get_pipelines()
            for pipeline in pipelines.get("pipelines", []):
                for stage in pipeline.get("stages", []):
                    if stage["id"] == latest_opp.get("pipelineStageId"):
                        current_stage = stage["name"]
                        break
        
        return {
            "contact": contact,
            "current_stage": current_stage,
            "notes": notes,
            "opportunities": opps,
            "tags": contact.get("tags", [])
        }
    
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


class RecruitingAssistant:
    """Conversational AI Assistant for eXp Recruiting"""
    
    def __init__(self, ghl_api):
        self.ghl = ghl_api
        self.conversation_context = {}
    
    def interpret_command(self, user_command, session_id="default"):
        """Use Claude to interpret recruiting commands with conversation context"""
        
        if not anthropic_client:
            return {
                "action": "error",
                "parameters": {},
                "confirmation_message": "AI service not configured.",
                "needs_clarification": False
            }
        
        # Get conversation context
        context = self.conversation_context.get(session_id, {})
        
        system_prompt = f"""You are a recruiting assistant for eXp Realty. You help manage the recruiting pipeline conversationally.

CRITICAL: Return ONLY valid JSON. No markdown, no code blocks.

EXP REALTY PIPELINE STAGES (in order):
1. "Send Live Call Invite" - Triggers SMS+Email for Thursday 12pm CST live call registration
2. "Send Invite" - Triggers SMS+Email for recorded partner webinar
3. "Registered" - Agent registered for live call OR webinar
4. "Watched Webinar" - Agent attended live call OR watched webinar
5. "Discovery Call Scheduled" - Agent booked discovery call
6. "Three Way Call Scheduled" - Agent booked 3-way with upline leader
7. "Red Zone" - Agent 80% committed
8. "Verbally Committed" - Agent ready to start (triggers application email)
9. "Application Appt Complete" - Completed application appointment
10. "eXp Onboarding App Complete" - Application fully done
11. "License Transfer Scheduled / Welcome Call" - DONE! Agent joined!

CONVERSATION CONTEXT:
{json.dumps(context, indent=2) if context else "No previous context"}

NEW PHASE 1 FEATURES - TIME TRACKING & SMART LISTS:

TIME-BASED QUERIES:
- "who registered this week" → search stage + date filter
- "who registered today" → search stage + today filter
- "agents stuck in discovery over 2 weeks" → time in stage > 14 days
- "who watched webinar yesterday" → stage + yesterday filter
- "agents who haven't moved in 30 days" → time in stage > 30 days
- "who's been in red zone for a week" → specific stage time check

QUICK STATS BY PERSON:
- "when did jeff register" → find stage entry date
- "how long has sarah been in discovery" → calculate days in current stage
- "last time i talked to mike" → most recent note date
- "jeff's timeline" → full journey with dates
- "sarah's journey" → complete history

SMART LISTS:
- "show me hot leads" → Red Zone + Verbally Committed
- "who needs follow up" → in stage > 7 days OR no note in 5 days
- "ready to close" → Verbally Committed + App Complete
- "my top priorities" → hot leads + overdue follow-ups
- "agents about to fall off" → in stage > 14 days
- "cold leads" → in stage > 30 days

BULK MOVEMENTS:
- "move everyone in registered to watched" → bulk stage change
- "push all discovery to 3-way" → bulk update
- "everyone in red zone to verbally committed" → mass promotion
- ALWAYS confirm before bulk action with count

YOUR JOB:
- Understand recruiting language naturally
- Ask clarifying questions when needed
- Track conversation context
- Provide detailed confirmations
- Calculate time periods correctly
- Flag stuck opportunities with warnings

COMMANDS YOU UNDERSTAND:
- "send jeff live invite" → move to "Send Live Call Invite"
- "send partner webinar" → move to "Send Invite"  
- "resend invite" → needs clarification: which invite?
- "jeff committed" → move to "Verbally Committed"
- "jeff signed" or "jeff done" → move to "License Transfer Scheduled"
- "who's committed" → search stage "Verbally Committed"
- "how many in discovery" → count opps in "Discovery Call Scheduled"
- "summary of jeff" → get full contact history
- "hows my pipeline" → pipeline_overview (shows opportunity counts per stage)
- "who registered this week" → time-filtered stage search
- "jeff's timeline" → person's journey with dates
- "show hot leads" → smart filtered list
- "move everyone in X to Y" → bulk stage movement

WHEN TO ASK FOR CLARIFICATION:
- "send invite" alone → ask: who? which invite (live call or partner webinar)?
- "resend invite to jeff" → ask: which invite?
- Ambiguous names → ask which person
- Unclear stage → ask which stage
- Bulk movements → CONFIRM with count first

Response format:
{{
    "action": "action_name",
    "parameters": {{}},
    "confirmation_message": "what you'll do",
    "needs_clarification": true/false,
    "clarification_question": "question to ask" (if needed),
    "clarification_options": ["option1", "option2"] (if needed),
    "context_update": {{}} (info to remember)
}}

NEW ACTION TYPES:

"search_by_stage_and_time"
{{
    "action": "search_by_stage_and_time",
    "parameters": {{"stage": "registered", "time_period": "this_week"}},
    "confirmation_message": "Finding agents who registered this week"
}}

"get_person_timeline"
{{
    "action": "get_person_timeline",
    "parameters": {{"contact_name": "jeff"}},
    "confirmation_message": "Getting Jeff's complete timeline"
}}

"smart_list"
{{
    "action": "smart_list",
    "parameters": {{"list_type": "hot_leads"}},
    "confirmation_message": "Showing your hot leads"
}}

"bulk_move"
{{
    "action": "bulk_move_confirm",
    "parameters": {{"from_stage": "registered", "to_stage": "watched webinar"}},
    "confirmation_message": "Checking how many to move from Registered to Watched",
    "needs_clarification": true,
    "clarification_question": "I found X agents in Registered. Move them all to Watched Webinar?"
}}

EXAMPLES:

"send jeff the live call invite"
{{
    "action": "move_to_stage",
    "parameters": {{"contact_name": "jeff", "stage": "send live call invite"}},
    "confirmation_message": "Moving Jeff to Send Live Call Invite",
    "needs_clarification": false
}}

"send the live call invite to jeff quiane"
{{
    "action": "move_to_stage",
    "parameters": {{"contact_name": "jeff quiane", "stage": "send live call invite"}},
    "confirmation_message": "Moving Jeff Quiane to Send Live Call Invite",
    "needs_clarification": false
}}

"send jeff partner webinar invite"
{{
    "action": "move_to_stage",
    "parameters": {{"contact_name": "jeff", "stage": "send invite"}},
    "confirmation_message": "Moving Jeff to Send Invite (partner webinar)",
    "needs_clarification": false
}}

"who registered this week"
{{
    "action": "search_by_stage_and_time",
    "parameters": {{"stage": "registered", "time_period": "this_week"}},
    "confirmation_message": "Finding agents who registered this week",
    "needs_clarification": false
}}

"jeff's timeline"
{{
    "action": "get_person_timeline",
    "parameters": {{"contact_name": "jeff"}},
    "confirmation_message": "Getting Jeff's complete journey",
    "needs_clarification": false
}}

"show hot leads"
{{
    "action": "smart_list",
    "parameters": {{"list_type": "hot_leads"}},
    "confirmation_message": "Showing Red Zone + Verbally Committed agents",
    "needs_clarification": false
}}

"move everyone in registered to watched"
{{
    "action": "bulk_move_confirm",
    "parameters": {{"from_stage": "registered", "to_stage": "watched webinar"}},
    "confirmation_message": "Preparing to bulk move from Registered to Watched Webinar",
    "needs_clarification": true
}}

"hows my pipeline" OR "pipeline overview" OR "show my pipeline" OR "pipeline report" OR "how many people in pipeline"
{{
    "action": "pipeline_overview",
    "parameters": {{}},
    "confirmation_message": "Getting pipeline overview with opportunity counts",
    "needs_clarification": false
}}

"how many people are in the exp realty pipeline" OR "total people in pipeline"
{{
    "action": "pipeline_overview",
    "parameters": {{}},
    "confirmation_message": "Counting all opportunities in eXp Realty pipeline",
    "needs_clarification": false
}}

REMEMBER: Return ONLY JSON, nothing else."""

        try:
            message = anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_command}]
            )
            
            response_text = message.content[0].text.strip()
            
            # Clean markdown if present
            response_text = re.sub(r'^```json\s*', '', response_text)
            response_text = re.sub(r'^```\s*', '', response_text)
            response_text = re.sub(r'\s*```$', '', response_text)
            response_text = response_text.strip()
            
            try:
                result = json.loads(response_text)
                
                # Update conversation context
                if result.get("context_update"):
                    if session_id not in self.conversation_context:
                        self.conversation_context[session_id] = {}
                    self.conversation_context[session_id].update(result["context_update"])
                
                # Clear context if action completed
                if not result.get("needs_clarification"):
                    self.conversation_context[session_id] = {}
                
                return result
                
            except json.JSONDecodeError as e:
                print(f"JSON Parse Error: {e}")
                print(f"Response was: {response_text}")
                return {
                    "action": "error",
                    "parameters": {},
                    "confirmation_message": "Sorry, I couldn't understand that. Can you rephrase?",
                    "needs_clarification": False
                }
                
        except Exception as e:
            print(f"AI Error: {str(e)}")
            return {
                "action": "error",
                "parameters": {},
                "confirmation_message": f"Error: {str(e)}",
                "needs_clarification": False
            }
    
    def execute_command(self, command_data):
        """Execute the interpreted command"""
        
        action = command_data.get("action")
        params = command_data.get("parameters", {})
        
        # If needs clarification, return the question
        if command_data.get("needs_clarification"):
            return {
                "success": True,
                "message": f"❓ {command_data.get('clarification_question')}",
                "clarification_options": command_data.get("clarification_options"),
                "needs_input": True
            }
        
        # If confirmation required for bulk move
        if command_data.get("confirmation_required"):
            return {
                "success": True,
                "message": command_data.get("message"),
                "needs_input": True,
                "clarification_question": "Type 'yes' to confirm or 'no' to cancel",
                "pending_bulk_action": True
            }
        
        try:
            # Move to stage (core recruiting action)
            if action == "move_to_stage":
                contact_name = params.get("contact_name")
                stage = params.get("stage")
                
                # Find contact
                contacts = self.ghl.search_contacts(contact_name)
                if not contacts.get("contacts"):
                    return {"success": False, "message": f"❌ Contact '{contact_name}' not found"}
                
                contact = contacts["contacts"][0]
                contact_id = contact["id"]
                contact_full_name = f"{contact.get('firstName', '')} {contact.get('lastName', '')}".strip()
                
                # Move or create opportunity
                result = self.ghl.move_or_create_opportunity(contact_id, stage)
                
                if result.get("error"):
                    return {"success": False, "message": f"❌ {result['error']}"}
                
                # Build detailed confirmation
                action_taken = "Created new opportunity" if result["action"] == "created" else "Updated opportunity"
                
                confirmation = {
                    "success": True,
                    "message": f"✅ Done! Here's what I did:",
                    "data": [{
                        "contact": contact_full_name,
                        "action": action_taken,
                        "pipeline": result["pipeline_name"],
                        "stage": result["stage_name"],
                        "what_happens": result["description"]
                    }]
                }
                
                return confirmation
            
            # Get contact summary
            elif action == "get_summary":
                contact_name = params.get("contact_name")
                
                contacts = self.ghl.search_contacts(contact_name)
                if not contacts.get("contacts"):
                    return {"success": False, "message": f"❌ Contact '{contact_name}' not found"}
                
                contact_id = contacts["contacts"][0]["id"]
                summary = self.ghl.get_contact_summary(contact_id)
                
                contact = summary["contact"]
                contact_full_name = f"{contact.get('firstName', '')} {contact.get('lastName', '')}".strip()
                
                # Format notes
                notes_list = []
                for note in summary["notes"][:10]:  # Last 10 notes
                    notes_list.append({
                        "date": note.get("dateAdded", "Unknown date"),
                        "note": note.get("body", "")
                    })
                
                return {
                    "success": True,
                    "message": f"📋 Summary for {contact_full_name}",
                    "summary": {
                        "name": contact_full_name,
                        "email": contact.get("email", "No email"),
                        "phone": contact.get("phone", "No phone"),
                        "current_stage": summary["current_stage"],
                        "tags": summary["tags"],
                        "total_notes": len(summary["notes"]),
                        "recent_notes": notes_list
                    }
                }
            
            # Search by stage
            elif action == "search_by_stage":
                stage = params.get("stage")
                
                # Get stage info
                stage_info = self.ghl.find_exp_pipeline_and_stage(stage)
                if not stage_info:
                    return {"success": False, "message": f"❌ Stage '{stage}' not found"}
                
                # Get all opportunities in this stage
                all_opps = self.ghl.get_opportunities(limit=500)
                stage_opps = [o for o in all_opps.get("opportunities", []) 
                             if o.get("pipelineStageId") == stage_info["stage_id"]]
                
                if not stage_opps:
                    return {
                        "success": True,
                        "message": f"✅ No one currently in '{stage_info['stage_name']}' stage"
                    }
                
                # Get contact details
                contact_list = []
                for opp in stage_opps[:20]:
                    try:
                        contact_result = self.ghl.get_contact(opp["contactId"])
                        contact = contact_result.get("contact", {})
                        contact_list.append({
                            "name": f"{contact.get('firstName', '')} {contact.get('lastName', '')}".strip(),
                            "email": contact.get("email", "No email"),
                            "phone": contact.get("phone", "No phone")
                        })
                    except:
                        pass
                
                return {
                    "success": True,
                    "message": f"✅ Found {len(contact_list)} agents in '{stage_info['stage_name']}'",
                    "data": contact_list
                }
            
            # Count by stage
            elif action == "count_by_stage":
                stage = params.get("stage")
                
                stage_info = self.ghl.find_exp_pipeline_and_stage(stage)
                if not stage_info:
                    return {"success": False, "message": f"❌ Stage '{stage}' not found"}
                
                all_opps = self.ghl.get_opportunities(limit=500)
                stage_count = len([o for o in all_opps.get("opportunities", []) 
                                  if o.get("pipelineStageId") == stage_info["stage_id"]])
                
                return {
                    "success": True,
                    "message": f"✅ {stage_count} opportunities in '{stage_info['stage_name']}'"
                }
            
            # Pipeline overview (also handles pipeline_report and get_pipeline_summary)
            elif action == "pipeline_overview" or action == "pipeline_report" or action == "get_pipeline_summary":
                pipelines = self.ghl.get_pipelines()
                all_opps = self.ghl.get_opportunities(limit=500)
                
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
                    stage_counts.append({
                        "stage": stage["name"],
                        "count": count
                    })
                
                total_opps = sum(s["count"] for s in stage_counts)
                
                return {
                    "success": True,
                    "message": f"📊 Pipeline Overview - Total: {total_opps} opportunities",
                    "data": stage_counts
                }
            
            # NEW: Search by stage and time period
            elif action == "search_by_stage_and_time":
                stage = params.get("stage")
                time_period = params.get("time_period", "all")
                
                # Get stage info
                stage_info = self.ghl.find_exp_pipeline_and_stage(stage)
                if not stage_info:
                    return {"success": False, "message": f"❌ Stage '{stage}' not found"}
                
                # Get all opportunities in this stage
                all_opps = self.ghl.get_opportunities(limit=500)
                stage_opps = [o for o in all_opps.get("opportunities", []) 
                             if o.get("pipelineStageId") == stage_info["stage_id"]]
                
                # Filter by time period
                now = datetime.now()
                filtered_opps = []
                
                for opp in stage_opps:
                    date_updated = opp.get("dateUpdated")
                    if not date_updated:
                        continue
                    
                    opp_date = datetime.fromisoformat(date_updated.replace('Z', '+00:00'))
                    days_in_stage = (now - opp_date).days
                    
                    # Apply time filter
                    include = False
                    if time_period == "today":
                        include = days_in_stage == 0
                    elif time_period == "yesterday":
                        include = days_in_stage == 1
                    elif time_period == "this_week":
                        include = days_in_stage <= 7
                    elif time_period == "this_month":
                        include = days_in_stage <= 30
                    elif time_period == "over_2_weeks":
                        include = days_in_stage > 14
                    elif time_period == "over_30_days":
                        include = days_in_stage > 30
                    else:
                        include = True
                    
                    if include:
                        opp["days_in_stage"] = days_in_stage
                        filtered_opps.append(opp)
                
                if not filtered_opps:
                    return {
                        "success": True,
                        "message": f"✅ No agents found in '{stage_info['stage_name']}' for {time_period}"
                    }
                
                # Get contact details
                contact_list = []
                for opp in filtered_opps[:20]:
                    try:
                        contact_result = self.ghl.get_contact(opp["contactId"])
                        contact = contact_result.get("contact", {})
                        
                        warning = "⚠️ " if opp["days_in_stage"] > 7 else ""
                        
                        contact_list.append({
                            "name": f"{warning}{contact.get('firstName', '')} {contact.get('lastName', '')}".strip(),
                            "email": contact.get("email", "No email"),
                            "phone": contact.get("phone", "No phone"),
                            "days_in_stage": f"{opp['days_in_stage']} days"
                        })
                    except:
                        pass
                
                return {
                    "success": True,
                    "message": f"✅ Found {len(contact_list)} agents in '{stage_info['stage_name']}' ({time_period})",
                    "data": contact_list
                }
            
            # NEW: Get person timeline
            elif action == "get_person_timeline":
                contact_name = params.get("contact_name")
                
                contacts = self.ghl.search_contacts(contact_name)
                if not contacts.get("contacts"):
                    return {"success": False, "message": f"❌ Contact '{contact_name}' not found"}
                
                contact_id = contacts["contacts"][0]["id"]
                contact = contacts["contacts"][0]
                contact_full_name = f"{contact.get('firstName', '')} {contact.get('lastName', '')}".strip()
                
                # Get opportunities to see stage history
                opps = self.ghl.get_opportunities(contact_id=contact_id)
                
                if not opps.get("opportunities"):
                    return {
                        "success": True,
                        "message": f"📋 {contact_full_name} - No opportunity history yet"
                    }
                
                latest_opp = opps["opportunities"][0]
                
                # Get current stage info
                pipelines = self.ghl.get_pipelines()
                current_stage_name = "Unknown"
                days_in_stage = 0
                
                for pipeline in pipelines.get("pipelines", []):
                    for stage in pipeline.get("stages", []):
                        if stage["id"] == latest_opp.get("pipelineStageId"):
                            current_stage_name = stage["name"]
                            
                            # Calculate days in current stage
                            date_updated = latest_opp.get("dateUpdated")
                            if date_updated:
                                opp_date = datetime.fromisoformat(date_updated.replace('Z', '+00:00'))
                                days_in_stage = (datetime.now() - opp_date).days
                            break
                
                # Get notes for activity
                notes_result = self.ghl.get_contact_notes(contact_id)
                notes = notes_result.get("notes", [])
                
                last_contact = "No recent contact"
                if notes:
                    last_note_date = notes[0].get("dateAdded", "")
                    if last_note_date:
                        note_date = datetime.fromisoformat(last_note_date.replace('Z', '+00:00'))
                        days_ago = (datetime.now() - note_date).days
                        last_contact = f"{days_ago} days ago" if days_ago > 0 else "Today"
                
                # Build timeline
                warning = "⚠️ Needs follow-up" if days_in_stage > 7 else "✅ On track"
                
                timeline = {
                    "name": contact_full_name,
                    "current_stage": current_stage_name,
                    "days_in_stage": f"{days_in_stage} days",
                    "last_contact": last_contact,
                    "status": warning,
                    "total_notes": len(notes)
                }
                
                return {
                    "success": True,
                    "message": f"📊 Timeline for {contact_full_name}",
                    "data": [timeline]
                }
            
            # NEW: Smart lists
            elif action == "smart_list":
                list_type = params.get("list_type")
                
                pipelines = self.ghl.get_pipelines()
                all_opps = self.ghl.get_opportunities(limit=500)
                
                # Find eXp pipeline
                exp_pipeline = None
                for p in pipelines.get("pipelines", []):
                    if "exp" in p["name"].lower() and "realty" in p["name"].lower():
                        exp_pipeline = p
                        break
                
                if not exp_pipeline:
                    return {"success": False, "message": "❌ eXp Realty pipeline not found"}
                
                # Get stage IDs for filtering
                stage_map = {}
                for stage in exp_pipeline.get("stages", []):
                    stage_map[stage["name"].lower()] = stage["id"]
                
                filtered_opps = []
                now = datetime.now()
                
                for opp in all_opps.get("opportunities", []):
                    if opp.get("pipelineId") != exp_pipeline["id"]:
                        continue
                    
                    # Calculate days in stage
                    days_in_stage = 0
                    date_updated = opp.get("dateUpdated")
                    if date_updated:
                        opp_date = datetime.fromisoformat(date_updated.replace('Z', '+00:00'))
                        days_in_stage = (now - opp_date).days
                    
                    opp["days_in_stage"] = days_in_stage
                    
                    # Filter by list type
                    include = False
                    stage_id = opp.get("pipelineStageId")
                    
                    if list_type == "hot_leads":
                        # Red Zone + Verbally Committed
                        red_zone_id = stage_map.get("red zone")
                        committed_id = stage_map.get("verbally committed")
                        include = stage_id in [red_zone_id, committed_id]
                    
                    elif list_type == "needs_follow_up":
                        # In stage > 7 days
                        include = days_in_stage > 7
                    
                    elif list_type == "ready_to_close":
                        # Verbally Committed + App Complete
                        committed_id = stage_map.get("verbally committed")
                        app_complete_id = stage_map.get("application appt complete")
                        include = stage_id in [committed_id, app_complete_id]
                    
                    elif list_type == "falling_off":
                        # In stage > 14 days
                        include = days_in_stage > 14
                    
                    elif list_type == "cold_leads":
                        # In stage > 30 days
                        include = days_in_stage > 30
                    
                    if include:
                        filtered_opps.append(opp)
                
                if not filtered_opps:
                    list_names = {
                        "hot_leads": "hot leads",
                        "needs_follow_up": "agents needing follow-up",
                        "ready_to_close": "agents ready to close",
                        "falling_off": "agents falling off",
                        "cold_leads": "cold leads"
                    }
                    return {
                        "success": True,
                        "message": f"✅ No {list_names.get(list_type, 'agents')} found"
                    }
                
                # Get contact details
                contact_list = []
                for opp in filtered_opps[:20]:
                    try:
                        contact_result = self.ghl.get_contact(opp["contactId"])
                        contact = contact_result.get("contact", {})
                        
                        # Get stage name
                        stage_name = "Unknown"
                        for stage in exp_pipeline.get("stages", []):
                            if stage["id"] == opp.get("pipelineStageId"):
                                stage_name = stage["name"]
                                break
                        
                        warning = "⚠️ " if opp["days_in_stage"] > 7 else ""
                        
                        contact_list.append({
                            "name": f"{warning}{contact.get('firstName', '')} {contact.get('lastName', '')}".strip(),
                            "stage": stage_name,
                            "days_in_stage": f"{opp['days_in_stage']} days",
                            "email": contact.get("email", "No email"),
                            "phone": contact.get("phone", "No phone")
                        })
                    except:
                        pass
                
                list_icons = {
                    "hot_leads": "🔥",
                    "needs_follow_up": "⚠️",
                    "ready_to_close": "🎯",
                    "falling_off": "📉",
                    "cold_leads": "❄️"
                }
                
                list_titles = {
                    "hot_leads": "Hot Leads",
                    "needs_follow_up": "Needs Follow-Up",
                    "ready_to_close": "Ready to Close",
                    "falling_off": "Falling Off",
                    "cold_leads": "Cold Leads"
                }
                
                icon = list_icons.get(list_type, "📋")
                title = list_titles.get(list_type, "List")
                
                return {
                    "success": True,
                    "message": f"{icon} {title} - Found {len(contact_list)} agents",
                    "data": contact_list
                }
            
            # NEW: Bulk move confirmation
            elif action == "bulk_move_confirm":
                from_stage = params.get("from_stage")
                to_stage = params.get("to_stage")
                
                # Get stage infos
                from_stage_info = self.ghl.find_exp_pipeline_and_stage(from_stage)
                to_stage_info = self.ghl.find_exp_pipeline_and_stage(to_stage)
                
                if not from_stage_info or not to_stage_info:
                    return {"success": False, "message": "❌ Could not find one or both stages"}
                
                # Count how many would be moved
                all_opps = self.ghl.get_opportunities(limit=500)
                to_move = [o for o in all_opps.get("opportunities", []) 
                          if o.get("pipelineStageId") == from_stage_info["stage_id"]]
                
                count = len(to_move)
                
                if count == 0:
                    return {
                        "success": True,
                        "message": f"✅ No agents in '{from_stage_info['stage_name']}' to move"
                    }
                
                # Store in session for actual execution
                self.conversation_context[session.get('session_id', 'default')] = {
                    "pending_bulk_move": {
                        "from_stage_id": from_stage_info["stage_id"],
                        "to_stage_id": to_stage_info["stage_id"],
                        "from_stage_name": from_stage_info["stage_name"],
                        "to_stage_name": to_stage_info["stage_name"],
                        "opportunity_ids": [o["id"] for o in to_move[:50]]  # Limit to 50
                    }
                }
                
                return {
                    "success": True,
                    "message": f"⚠️ Ready to move {min(count, 50)} agents from '{from_stage_info['stage_name']}' to '{to_stage_info['stage_name']}'",
                    "confirmation_required": True,
                    "needs_input": True
                }
            
            # NEW: Execute bulk move
            elif action == "bulk_move_execute":
                session_id = session.get('session_id', 'default')
                context = self.conversation_context.get(session_id, {})
                bulk_data = context.get("pending_bulk_move")
                
                if not bulk_data:
                    return {"success": False, "message": "❌ No pending bulk move found"}
                
                # Execute the moves
                moved_count = 0
                for opp_id in bulk_data["opportunity_ids"]:
                    try:
                        self.ghl.update_opportunity(opp_id, {
                            "pipelineStageId": bulk_data["to_stage_id"]
                        })
                        moved_count += 1
                    except:
                        pass
                
                # Clear context
                self.conversation_context[session_id] = {}
                
                return {
                    "success": True,
                    "message": f"✅ Moved {moved_count} agents from '{bulk_data['from_stage_name']}' to '{bulk_data['to_stage_name']}'"
                }
            
            # Error
            elif action == "error":
                return {
                    "success": False,
                    "message": command_data.get('confirmation_message', 'Unknown error')
                }
            
            # Clarify (shouldn't reach here)
            elif action == "clarify":
                return {
                    "success": True,
                    "message": command_data.get('clarification_question'),
                    "needs_input": True
                }
            
            # Unknown action
            else:
                return {
                    "success": False,
                    "message": f"❌ I don't know how to: {action}"
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
assistant = RecruitingAssistant(ghl_api)


@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')


@app.route('/api/command', methods=['POST'])
def process_command():
    """Process user commands"""
    data = request.json
    user_command = data.get('command', '')
    session_id = session.get('session_id')
    
    if not session_id:
        session_id = secrets.token_hex(8)
        session['session_id'] = session_id
    
    if not user_command:
        return jsonify({
            "success": False,
            "message": "No command provided"
        })
    
    try:
        # Check if this is a confirmation for bulk move
        if user_command.lower() in ["yes", "y", "do it", "go ahead", "confirm"]:
            context = assistant.conversation_context.get(session_id, {})
            if context.get("pending_bulk_move"):
                result = assistant.execute_command({"action": "bulk_move_execute", "parameters": {}})
                return jsonify({
                    "success": result.get("success", False),
                    "message": result.get("message", ""),
                    "data": result.get("data")
                })
        
        # Interpret command with AI
        command_data = assistant.interpret_command(user_command, session_id)
        
        # Execute the command
        result = assistant.execute_command(command_data)
        
        return jsonify({
            "success": result.get("success", False),
            "message": result.get("message", ""),
            "data": result.get("data"),
            "summary": result.get("summary"),
            "clarification_options": result.get("clarification_options"),
            "needs_input": result.get("needs_input", False),
            "clarification_question": result.get("clarification_question"),
            "plan": command_data.get("confirmation_message", "")
        })
        
    except Exception as e:
        print(f"API Error: {str(e)}")
        import traceback
        traceback.print_exc()
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
            "message": "✅ Connected - eXcelerate Recruiting Assistant",
            "contact_count": len(contacts.get("contacts", []))
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"❌ Connection error: {str(e)}"
        })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
