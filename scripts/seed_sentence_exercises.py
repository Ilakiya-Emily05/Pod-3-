import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config.settings import get_settings
from app.models.sentence_framing import SentenceExercise

# -----------------------------------------------------------------------------
# EXERCISE DATA (50 Exercises)
# -----------------------------------------------------------------------------

EXERCISES = [
    # --- PROFESSIONAL EMAILS (20) ---
    # Client Communication (5)
    {
        "category": "Professional Emails",
        "subcategory": "Client Communication",
        "exercise_type": "fill_in_blank",
        "difficulty": "Professional",
        "industry": "IT",
        "scenario": "Update a client on a minor delay in the front-end development phase.",
        "context": {"sender_role": "Project Manager", "recipient": "Client", "tone": "Professional and Apologetic"},
        "template": "Dear {client_name},\n\nI am writing to share a brief update. Due to _________________, we are experiencing a slight delay in the _________________. We expect to have this resolved by _________________.\n\nBest regards,\n[Your Name]",
        "hints": ["State the reason clearly", "Provide a revised timeline", "Maintain a confident tone"],
        "example_answer": "Dear Mr. Miller, I am writing to share a brief update. Due to unexpected API integration issues, we are experiencing a slight delay in the front-end development phase. We expect to have this resolved by Friday afternoon. Best regards, Jane.",
        "points": 10
    },
    {
        "category": "Professional Emails",
        "subcategory": "Client Communication",
        "exercise_type": "free_form",
        "difficulty": "Executive",
        "industry": "Consulting",
        "scenario": "Negotiate a scope extension for a strategic roadmap project.",
        "context": {"sender_role": "Senior Partner", "recipient": "CEO of Client", "tone": "Strategic and Persuasive"},
        "hints": ["Value-driven approach", "Address ROI", "Call to action"],
        "example_answer": "Dear [CEO], following our recent audit, we've identified significant growth opportunities that warrant an extension of our current roadmap phase...",
        "points": 20
    },
    {
        "category": "Professional Emails",
        "subcategory": "Client Communication",
        "exercise_type": "reorder",
        "difficulty": "Basic",
        "industry": "Banking",
        "scenario": "Welcome a new corporate client and introduce their account manager.",
        "context": {"sender_role": "Relationship Manager", "recipient": "New Client", "tone": "Welcoming"},
        "template": "1. We are delighted to have you with us. | 2. Welcome to Global Bank. | 3. Your account manager, Sarah, will contact you shortly. | 4. Please let us know if you need assistance.",
        "hints": ["Start with a greeting", "Introduce the contact", "End with a helpful offer"],
        "example_answer": "Welcome to Global Bank. We are delighted to have you with us. Your account manager, Sarah, will contact you shortly. Please let us know if you need assistance.",
        "points": 10
    },
    {
        "category": "Professional Emails",
        "subcategory": "Client Communication",
        "exercise_type": "fill_in_blank",
        "difficulty": "Professional",
        "industry": "IT",
        "scenario": "Requesting feedback on a delivered prototype.",
        "context": {"sender_role": "UX Lead", "recipient": "Product Owner", "tone": "Inquisitive"},
        "template": "Hi team,\n\nWe would value your _________________ on the _________________ we shared yesterday. Specifically, does the _________________ meet your expectations?\n\nBest,\n[Your Name]",
        "hints": ["Be specific about what feedback you need", "Reference the delivery time", "Keep it concise"],
        "points": 10
    },
    {
        "category": "Professional Emails",
        "subcategory": "Client Communication",
        "exercise_type": "free_form",
        "difficulty": "Basic",
        "industry": "Consulting",
        "scenario": "Scheduling a follow-up call after an initial discovery session.",
        "context": {"sender_role": "Analyst", "recipient": "Project Lead", "tone": "Polite"},
        "hints": ["Mention the previous meeting", "Offer 2-3 time slots", "Be helpful"],
        "points": 10
    },

    # Manager Updates (5)
    {
        "category": "Professional Emails",
        "subcategory": "Manager Updates",
        "exercise_type": "fill_in_blank",
        "difficulty": "Basic",
        "industry": "IT",
        "scenario": "Informing your manager that you've completed your assigned tasks early.",
        "context": {"sender_role": "Developer", "recipient": "Team Lead", "tone": "Proactive"},
        "template": "Hi [Manager],\n\nI've finished _________________ ahead of schedule. I'm now available to _________________ or _________________ if needed.\n\nThanks,\n[Your Name]",
        "hints": ["Be specific about the tasks", "Offer to help with others", "Stay professional"],
        "points": 10
    },
    {
        "category": "Professional Emails",
        "subcategory": "Manager Updates",
        "exercise_type": "free_form",
        "difficulty": "Professional",
        "industry": "Banking",
        "scenario": "Escalating a potential compliance risk found during an internal audit.",
        "context": {"sender_role": "Risk Analyst", "recipient": "Head of Compliance", "tone": "Urgent and Serious"},
        "hints": ["Identify the risk clearly", "Mention the audit findings", "Request immediate review"],
        "points": 15
    },
    {
        "category": "Professional Emails",
        "subcategory": "Manager Updates",
        "exercise_type": "reorder",
        "difficulty": "Professional",
        "industry": "Consulting",
        "scenario": "Summarizing the key takeaways from a high-level stakeholder interview.",
        "context": {"sender_role": "Associate", "recipient": "Project Manager", "tone": "Concise"},
        "template": "1. Overall, they support the vision. | 2. I interviewed the CTO today. | 3. However, they are concerned about the budget. | 4. Here are the key takeaways.",
        "hints": ["State the event first", "Summarize the general sentiment", "Detail the specific concern"],
        "points": 10
    },
    {
        "category": "Professional Emails",
        "subcategory": "Manager Updates",
        "exercise_type": "fill_in_blank",
        "difficulty": "Executive",
        "industry": "IT",
        "scenario": "Providing a high-level summary of the quarterly cloud migration progress.",
        "context": {"sender_role": "Director of Engineering", "recipient": "CTO", "tone": "Strategic"},
        "template": "Quarterly Update:\n\nWe have successfully migrated _________________% of our _________________. The primary challenge remains _________________, but we are _________________ to address it.\n\nRegards,\n[Your Name]",
        "hints": ["Use metrics", "Be honest about blockers", "Show leadership"],
        "points": 20
    },
    {
        "category": "Professional Emails",
        "subcategory": "Manager Updates",
        "exercise_type": "free_form",
        "difficulty": "Basic",
        "industry": "General",
        "scenario": "Requesting a one-on-one meeting to discuss career development.",
        "context": {"sender_role": "Employee", "recipient": "Manager", "tone": "Professional"},
        "hints": ["Be clear about the purpose", "Keep it positive", "Suggest a timeframe"],
        "points": 10
    },

    # Team Coordination (5)
    {
        "category": "Professional Emails",
        "subcategory": "Team Coordination",
        "exercise_type": "fill_in_blank",
        "difficulty": "Basic",
        "industry": "IT",
        "scenario": "Setting a deadline for the team to submit their sprint reports.",
        "context": {"sender_role": "Scrum Master", "recipient": "Dev Team", "tone": "Direct"},
        "template": "Hi everyone,\n\nPlease ensure your _________________ are submitted by _________________ today. This is crucial for _________________.\n\nThanks,\n[Your Name]",
        "hints": ["State the 'what'", "State the 'when'", "State the 'why'"],
        "points": 10
    },
    {
        "category": "Professional Emails",
        "subcategory": "Team Coordination",
        "exercise_type": "reorder",
        "difficulty": "Professional",
        "industry": "Banking",
        "scenario": "Organizing a brief lunch-and-learn session on new banking regulations.",
        "context": {"sender_role": "Senior Analyst", "recipient": "Team", "tone": "Informal but Professional"},
        "template": "1. I'm hosting a lunch-and-learn on Tuesday. | 2. Let me know if you can join. | 3. We'll cover the latest KYC rules. | 4. Pizza will be provided!",
        "hints": ["Announce the event", "Specify the topic", "Add an incentive", "Ask for RSVP"],
        "points": 10
    },
    {
        "category": "Professional Emails",
        "subcategory": "Team Coordination",
        "exercise_type": "free_form",
        "difficulty": "Professional",
        "industry": "Consulting",
        "scenario": "Resolving a conflict between two analysts regarding data ownership.",
        "context": {"sender_role": "Team Lead", "recipient": "Consultancy Team", "tone": "Diplomatic"},
        "hints": ["Acknowledge the confusion", "Set clear guidelines", "Promote collaboration"],
        "points": 15
    },
    {
        "category": "Professional Emails",
        "subcategory": "Team Coordination",
        "exercise_type": "fill_in_blank",
        "difficulty": "Executive",
        "industry": "IT",
        "scenario": "Announcing a major shift in technical strategy to the entire department.",
        "context": {"sender_role": "VP of Product", "recipient": "Engineering Dept", "tone": "Inspiring and Clear"},
        "template": "Team,\n\nTo better serve our _________________, we are pivoting our _________________ strategy towards _________________. This move represents _________________ for us.\n\nBest,\n[Your Name]",
        "hints": ["Focus on the 'why'", "Acknowledge the effort involved", "Look forward"],
        "points": 20
    },
    {
        "category": "Professional Emails",
        "subcategory": "Team Coordination",
        "exercise_type": "free_form",
        "difficulty": "Basic",
        "industry": "General",
        "scenario": "Asking for a volunteer to take notes during the next team meeting.",
        "context": {"sender_role": "Moderator", "recipient": "Team Members", "tone": "Polite"},
        "hints": ["Request clearly", "Explain why it's needed", "Keep it light"],
        "points": 10
    },

    # Escalation Emails (5)
    {
        "category": "Professional Emails",
        "subcategory": "Escalation Emails",
        "exercise_type": "fill_in_blank",
        "difficulty": "Professional",
        "industry": "IT",
        "scenario": "Escalating a recurring server performance issue that remains unresolved after three tickets.",
        "context": {"sender_role": "Operations Manager", "recipient": "IT Support Lead", "tone": "Firm and Urgent"},
        "template": "Dear [Lead],\n\nI am escalating _________________ (tickets #12, #45, #67) as the _________________ continues to impact our _________________. We require a _________________ by EOD.\n\nRegards,\n[Your Name]",
        "hints": ["Cite previous attempts", "Impact on business", "Give a clear deadline"],
        "points": 15
    },
    {
        "category": "Professional Emails",
        "subcategory": "Escalation Emails",
        "exercise_type": "free_form",
        "difficulty": "Executive",
        "industry": "Banking",
        "scenario": "Escalating a significant delay in the KYC approval process for a major institutional client.",
        "context": {"sender_role": "Director of Client Onboarding", "recipient": "Head of Compliance", "tone": "Executive and Decisive"},
        "hints": ["Client impact", "Revenue risk", "Demand a priority review"],
        "points": 20
    },
    {
        "category": "Professional Emails",
        "subcategory": "Escalation Emails",
        "exercise_type": "reorder",
        "difficulty": "Professional",
        "industry": "Consulting",
        "scenario": "Escalating a lack of response from a sub-contractor on a critical project milestone.",
        "context": {"sender_role": "Project Director", "recipient": "Sub-contractor Lead", "tone": "Serious and Demanding"},
        "template": "1. This has put our milestone at risk. | 2. I've sent three follow-ups with no reply. | 3. Please call me immediately to discuss. | 4. We are still waiting for the Phase 2 report.",
        "hints": ["Identify what is missing", "Recap failed follow-ups", "State project risk", "Next action"],
        "points": 15
    },
    {
        "category": "Professional Emails",
        "subcategory": "Escalation Emails",
        "exercise_type": "fill_in_blank",
        "difficulty": "Basic",
        "industry": "General",
        "scenario": "Escalating a travel reimbursement that is 30 days overdue.",
        "context": {"sender_role": "Employee", "recipient": "Finance Lead", "tone": "Polite but Persistent"},
        "template": "Hello,\n\nMy _________________ is now _________________ days overdue. I've already checked with _________________, but haven't received an update.\n\nBest,\n[Your Name]",
        "hints": ["Be factual", "Mention previous check-ins", "Ask for a status update"],
        "points": 10
    },
    {
        "category": "Professional Emails",
        "subcategory": "Escalation Emails",
        "exercise_type": "free_form",
        "difficulty": "Executive",
        "industry": "Consulting",
        "scenario": "Escalating an internal resource conflict between two high-priority projects.",
        "context": {"sender_role": "Principal Consultant", "recipient": "VP of Operations", "tone": "Strategic"},
        "hints": ["Balance priorities", "Highlight cost of delay", "Propose a solution"],
        "points": 20
    },

    # --- REPORT WRITING (15) ---
    # Status Reports (5)
    {
        "category": "Report Writing",
        "subcategory": "Status Reports",
        "exercise_type": "fill_in_blank",
        "difficulty": "Professional",
        "industry": "IT",
        "scenario": "Weekly status update for a software development project.",
        "context": {"sender_role": "Lead Dev", "recipient": "Project Manager", "tone": "Factual"},
        "template": "Project Status: _________________\n\nAchievements: _________________\nBlockers: _________________\nNext Steps: _________________",
        "hints": ["Use clear headers", "Be concise", "Focus on results"],
        "points": 10
    },
    {
        "category": "Report Writing",
        "subcategory": "Status Reports",
        "exercise_type": "reorder",
        "difficulty": "Basic",
        "industry": "General",
        "scenario": "Quick end-of-day update report.",
        "context": {"sender_role": "Trainee", "recipient": "Supervisor", "tone": "Informative"},
        "template": "1. I will continue the audit tomorrow. | 2. Today I scanned 50 files. | 3. No issues were found. | 4. Summary of Work:",
        "hints": ["Header first", "Achievement next", "Status", "Future plan"],
        "points": 10
    },
    {
        "category": "Report Writing",
        "subcategory": "Status Reports",
        "exercise_type": "free_form",
        "difficulty": "Executive",
        "industry": "Banking",
        "scenario": "Monthly executive summary of digital transformation progress.",
        "context": {"sender_role": "Digital Lead", "recipient": "EXCO", "tone": "Strategic and Data-driven"},
        "hints": ["High-level metrics", "Highlight strategic alignment", "Address budget"],
        "points": 20
    },
    {
        "category": "Report Writing",
        "subcategory": "Status Reports",
        "exercise_type": "fill_in_blank",
        "difficulty": "Professional",
        "industry": "Consulting",
        "scenario": "Status update report for a client engagement audit.",
        "context": {"sender_role": "Manager", "recipient": "Client Sponsor", "tone": "Reassuring"},
        "template": "Audit Progress:\n\nWe have completed _________________ of the required interviews. Preliminary findings indicate _________________. We are on track for _________________.",
        "hints": ["Progress percentage", "Initial insights", "Deadline confirmation"],
        "points": 15
    },
    {
        "category": "Report Writing",
        "subcategory": "Status Reports",
        "exercise_type": "free_form",
        "difficulty": "Basic",
        "industry": "IT",
        "scenario": "Reporting the status of a specific bug fix to the QA team.",
        "context": {"sender_role": "Developer", "recipient": "QA Team", "tone": "Technical"},
        "hints": ["Bug ID", "Current status", "Expected fix date"],
        "points": 10
    },

    # Incident Reports (5)
    {
        "category": "Report Writing",
        "subcategory": "Incident Reports",
        "exercise_type": "fill_in_blank",
        "difficulty": "Professional",
        "industry": "IT",
        "scenario": "Reporting a data center outage that occurred last night.",
        "context": {"sender_role": "SRE", "recipient": "Tech Org", "tone": "Serious and Detailed"},
        "template": "INCIDENT REPORT\n\nIncident: _________________\nDuration: _________________\nRoot Cause: _________________\nImpact: _________________\nResolution: _________________",
        "hints": ["Be precise with times", "Be technical in root cause", "Quantify impact"],
        "points": 15
    },
    {
        "category": "Report Writing",
        "subcategory": "Incident Reports",
        "exercise_type": "reorder",
        "difficulty": "Professional",
        "industry": "Banking",
        "scenario": "Reporting a potential phishing attempt targeting the branch staff.",
        "context": {"sender_role": "Branch Head", "recipient": "InfoSec Dept", "tone": "Urgent"},
        "template": "1. Three staff members clicked the link. | 2. A suspicious email was received at 9 AM. | 3. We've locked their accounts. | 4. The sender posed as 'IT Support'.",
        "hints": ["Time of detection", "Method", "Impact", "Action taken"],
        "points": 15
    },
    {
        "category": "Report Writing",
        "subcategory": "Incident Reports",
        "exercise_type": "free_form",
        "difficulty": "Executive",
        "industry": "Consulting",
        "scenario": "Writing an incident report for an accidental sensitive data leak in a client report.",
        "context": {"sender_role": "Partner", "recipient": "Client Legal Counsel", "tone": "Highly Professional and Apologetic"},
        "hints": ["Full transparency", "Immediate mitigation steps", "Future prevention"],
        "points": 20
    },
    {
        "category": "Report Writing",
        "subcategory": "Incident Reports",
        "exercise_type": "fill_in_blank",
        "difficulty": "Basic",
        "industry": "General",
        "scenario": "Reporting a minor office safety incident (a trip over a loose cable).",
        "context": {"sender_role": "Employee", "recipient": "HR/Facilities", "tone": "Descriptive"},
        "template": "Incident: _________________\nLocation: _________________\nDetails: _________________\nAction Needed: _________________",
        "hints": ["Clear location", "Detailed sequence of events", "Suggested fix"],
        "points": 10
    },
    {
        "category": "Report Writing",
        "subcategory": "Incident Reports",
        "exercise_type": "free_form",
        "difficulty": "Professional",
        "industry": "IT",
        "scenario": "Writing a Post-Mortem incident report for a failed software deployment.",
        "context": {"sender_role": "DevOps Lead", "recipient": "Engineering Team", "tone": "Analytical"},
        "hints": ["What went wrong", "Why it wasn't caught", "Action items"],
        "points": 15
    },

    # Project Summaries (5)
    {
        "category": "Report Writing",
        "subcategory": "Project Summaries",
        "exercise_type": "fill_in_blank",
        "difficulty": "Basic",
        "industry": "Consulting",
        "scenario": "Briefly summarizing a completed market research project.",
        "context": {"sender_role": "Research Associate", "recipient": "Senior Manager", "tone": "Informative"},
        "template": "The [Project Name] is complete. We found that _________________. The client has _________________ our findings.",
        "hints": ["Key takeaway first", "Client reaction", "Next steps"],
        "points": 10
    },
    {
        "category": "Report Writing",
        "subcategory": "Project Summaries",
        "exercise_type": "reorder",
        "difficulty": "Professional",
        "industry": "Banking",
        "scenario": "Structuring a project summary for a new loan processing system.",
        "context": {"sender_role": "BA", "recipient": "Operations Head", "tone": "Clear and Results-focused"},
        "template": "1. We reduced processing time by 20%. | 2. The project was completed in 6 months. | 3. Our goal was system modernization. | 4. ROI is estimated at $1M.",
        "hints": ["State the goal", "Mention duration", "Show key result", "End with ROI"],
        "points": 15
    },
    {
        "category": "Report Writing",
        "subcategory": "Project Summaries",
        "exercise_type": "free_form",
        "difficulty": "Executive",
        "industry": "IT",
        "scenario": "Writing a project wrap-up summary for a multi-year ERP implementation.",
        "context": {"sender_role": "Program Director", "recipient": "CIO", "tone": "Reflective and Strategic"},
        "hints": ["Strategic impact", "Major milestones", "Future landscape"],
        "points": 20
    },
    {
        "category": "Report Writing",
        "subcategory": "Project Summaries",
        "exercise_type": "fill_in_blank",
        "difficulty": "Professional",
        "industry": "IT",
        "scenario": "Drafting an abstract for a technical feasibility study final report.",
        "context": {"sender_role": "Technical Lead", "recipient": "Steering Committee", "tone": "Formal"},
        "template": "Conclusion: The proposed solution is _________________. While _________________ exists, the benefits of _________________ outweigh the risks.",
        "hints": ["Be definitive", "Balance pros and cons", "Professional phrasing"],
        "points": 15
    },
    {
        "category": "Report Writing",
        "subcategory": "Project Summaries",
        "exercise_type": "free_form",
        "difficulty": "Basic",
        "industry": "General",
        "scenario": "Summarizing a small internal process improvement project.",
        "context": {"sender_role": "Team Assistant", "recipient": "Team", "tone": "Helpful"},
        "hints": ["Old process vs new", "How it helps the team", "Where to find docs"],
        "points": 10
    },

    # --- MEETING COMMUNICATION (15) ---
    # Meeting Invites (5)
    {
        "category": "Meeting Communication",
        "subcategory": "Meeting Invites",
        "exercise_type": "fill_in_blank",
        "difficulty": "Basic",
        "industry": "IT",
        "scenario": "Inviting the team to a daily stand-up meeting.",
        "context": {"sender_role": "Scrum Master", "recipient": "Dev Team", "tone": "Concise"},
        "template": "Daily Stand-up:\n\nWhen: _________________\nWhere: _________________\nPurpose: _________________",
        "hints": ["Be brief", "Include a link/room", "Mention the quick 15-min nature"],
        "points": 10
    },
    {
        "category": "Meeting Communication",
        "subcategory": "Meeting Invites",
        "exercise_type": "reorder",
        "difficulty": "Professional",
        "industry": "Banking",
        "scenario": "Inviting senior management to a critical budget approval meeting.",
        "context": {"sender_role": "Finance Manager", "recipient": "GMs", "tone": "Formal and Clear"},
        "template": "1. I've attached the budget draft. | 2. You are invited to the Q3 Budget Review. | 3. We will finalize sub-dept allocations. | 4. The meeting is in the Boardroom at 2 PM.",
        "hints": ["State the invitation", "Mention the time/place", "Define the objective", "Reference docs"],
        "points": 15
    },
    {
        "category": "Meeting Communication",
        "subcategory": "Meeting Invites",
        "exercise_type": "free_form",
        "difficulty": "Executive",
        "industry": "Consulting",
        "scenario": "Drafting an invitation for a high-stakes partnership kickoff meeting.",
        "context": {"sender_role": "Managing Director", "recipient": "External Partners", "tone": "Professional and Welcoming"},
        "hints": ["Mutual value prop", "Clear agenda overview", "Next steps for RSVP"],
        "points": 20
    },
    {
        "category": "Meeting Communication",
        "subcategory": "Meeting Invites",
        "exercise_type": "fill_in_blank",
        "difficulty": "Professional",
        "industry": "IT",
        "scenario": "Inviting external vendors for a technical RFP overview session.",
        "context": {"sender_role": "Procurement Lead", "recipient": "Vendors", "tone": "Formal"},
        "template": "RFP Overview:\n\nWe are hosting _________________ on _________________. This session will provide _________________ for the _________________ project.",
        "hints": ["Explicit purpose", "Context of the RFP", "Time/Link"],
        "points": 15
    },
    {
        "category": "Meeting Communication",
        "subcategory": "Meeting Invites",
        "exercise_type": "free_form",
        "difficulty": "Basic",
        "industry": "General",
        "scenario": "Inviting colleagues to a casual Friday after-work social.",
        "context": {"sender_role": "Social Committee Member", "recipient": "All Staff", "tone": "Casual and Fun"},
        "hints": ["Light tone", "Time/Place", "Encourage attendance"],
        "points": 10
    },

    # Minutes Writing (5)
    {
        "category": "Meeting Communication",
        "subcategory": "Minutes Writing",
        "exercise_type": "fill_in_blank",
        "difficulty": "Professional",
        "industry": "IT",
        "scenario": "Recording action items from a technical sprint planning meeting.",
        "context": {"sender_role": "Dev Lead", "recipient": "Team", "tone": "Direct and Clear"},
        "template": "Action item 1: _________________ (Assigned to: _________________)\nAction item 2: _________________ (Assigned to: _________________)\nDeadline: _________________",
        "hints": ["Focus on the 'who' and 'what'", "Be very specific", "Set clear deadlines"],
        "points": 15
    },
    {
        "category": "Meeting Communication",
        "subcategory": "Minutes Writing",
        "exercise_type": "reorder",
        "difficulty": "Basic",
        "industry": "General",
        "scenario": "Organizing the summary of a quick weekly sync meeting.",
        "context": {"sender_role": "Team lead", "recipient": "Team", "tone": "Concise"},
        "template": "1. Next meeting is scheduled for Monday. | 2. We discussed the marketing delay. | 3. Weekly Sync Summary: | 4. Jane will follow up with the creative team.",
        "hints": ["Header first", "Topic overview", "Action item", "Next meeting"],
        "points": 10
    },
    {
        "category": "Meeting Communication",
        "subcategory": "Minutes Writing",
        "exercise_type": "free_form",
        "difficulty": "Executive",
        "industry": "Banking",
        "scenario": "Writing high-level minutes for a board-level risk committee meeting.",
        "context": {"sender_role": "Company Secretary", "recipient": "Board Members", "tone": "Formal and Precise"},
        "hints": ["Summarize key decisions", "Maintain confidentiality", "Record formal approvals"],
        "points": 20
    },
    {
        "category": "Meeting Communication",
        "subcategory": "Minutes Writing",
        "exercise_type": "fill_in_blank",
        "difficulty": "Professional",
        "industry": "Consulting",
        "scenario": "Finalizing the 'Key Decisions' section of a client workshop minute notes.",
        "context": {"sender_role": "Senior Consultant", "recipient": "Client Team", "tone": "Confident"},
        "template": "Decision A: _________________. Decision B: _________________. Both parties agreed to _________________ by _________________.",
        "hints": ["Be unambiguous", "Confirm the agreement", "State the dates"],
        "points": 15
    },
    {
        "category": "Meeting Communication",
        "subcategory": "Minutes Writing",
        "exercise_type": "free_form",
        "difficulty": "Basic",
        "industry": "IT",
        "scenario": "Writing brief notes for an ad-hoc debugging session.",
        "context": {"sender_role": "QA Engineer", "recipient": "Devs", "tone": "Technical"},
        "hints": ["Reproduced steps", "Confirmed fix approach", "Assigned dev"],
        "points": 10
    },

    # Follow-up Emails (5)
    {
        "category": "Meeting Communication",
        "subcategory": "Follow-up",
        "exercise_type": "fill_in_blank",
        "difficulty": "Professional",
        "industry": "IT",
        "scenario": "Follow-up email after a product demo session with a client.",
        "context": {"sender_role": "Sales Eng", "recipient": "Lead Buyer", "tone": "Helpful and Persuasive"},
        "template": "Hi [Name],\n\nThank you for _________________ today. As promised, I've attached _________________. I look forward to _________________.",
        "hints": ["Personalize the thank-you", "Deliver on promises", "Nudge for the next step"],
        "points": 15
    },
    {
        "category": "Meeting Communication",
        "subcategory": "Follow-up",
        "exercise_type": "reorder",
        "difficulty": "Basic",
        "industry": "General",
        "scenario": "Following up with a colleague after a quick coffee chat about a project idea.",
        "context": {"sender_role": "Idea Owner", "recipient": "Colleague", "tone": "Enthusiastic"},
        "template": "1. Let's touch base again next week. | 2. It was great chatting today. | 3. I really liked your suggestion about [topic]. | 4. I'll send over a draft soon.",
        "hints": ["Personal touch", "Specific compliment/recap", "Commit to action", "Next sync"],
        "points": 10
    },
    {
        "category": "Meeting Communication",
        "subcategory": "Follow-up",
        "exercise_type": "free_form",
        "difficulty": "Executive",
        "industry": "Banking",
        "scenario": "Following up after a high-level strategic partnership discussion with another bank's executive.",
        "context": {"sender_role": "VP", "recipient": "Counterpart VP", "tone": "Professional and Visionary"},
        "hints": ["Recap strategic alignment", "Define next formal step", "Professional networking touch"],
        "points": 20
    },
    {
        "category": "Meeting Communication",
        "subcategory": "Follow-up",
        "exercise_type": "fill_in_blank",
        "difficulty": "Professional",
        "industry": "Consulting",
        "scenario": "Following up on outstanding requests after a project status call.",
        "context": {"sender_role": "Associate", "recipient": "Analyst", "tone": "Persistent but Polite"},
        "template": "Following up on our _________________ call. We still need _________________ to proceed with _________________. Could you please _________________?",
        "hints": ["Reference a specific meeting", "State the blocker clearly", "Direct request"],
        "points": 15
    },
    {
        "category": "Meeting Communication",
        "subcategory": "Follow-up",
        "exercise_type": "free_form",
        "difficulty": "Basic",
        "industry": "General",
        "scenario": "Sending a 'thank you' email to a guest speaker after an internal event.",
        "context": {"sender_role": "Organizer", "recipient": "Speaker", "tone": "Appreciative"},
        "hints": ["Specific highlight from the talk", "Feedback from the audience", "Professional closure"],
        "points": 10
    }
]

# -----------------------------------------------------------------------------
# SEEDING EXECUTION
# -----------------------------------------------------------------------------

async def seed():
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    async_session = session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # Clear existing exercises (optional, for clean seeding)
        # await session.execute("DELETE FROM sentence_exercises")
        
        for data in EXERCISES:
            exercise = SentenceExercise(
                id=uuid.uuid4(),
                category=data["category"],
                subcategory=data["subcategory"],
                exercise_type=data["exercise_type"],
                difficulty=data["difficulty"],
                industry=data.get("industry", "General Professional"),
                scenario=data["scenario"],
                context=data["context"],
                template=data.get("template"),
                hints=data.get("hints", []),
                example_answer=data.get("example_answer"),
                time_limit_secs=300,
                points=data.get("points", 10)
            )
            session.add(exercise)
        
        await session.commit()
        print(f"Successfully seeded {len(EXERCISES)} exercises.")

if __name__ == "__main__":
    asyncio.run(seed())
