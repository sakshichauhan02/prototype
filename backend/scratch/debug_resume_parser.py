import re
import json

# Define the pasted text as a single line to simulate the user's input
pasted_text = (
    "SAKSHI CHAUHAN (+91)-7017400147  |  India  |  sakshichauhan64771@gmail.com "
    "linkedin.com/in/sakshi-chauhan-704973326  |  github.com/sakshichauhan02 "
    "PROFESSIONAL SUMMARY "
    "Motivated IT/CS graduate with foundational knowledge in Windows OS, networking basics, and technical troubleshooting. Strong problem-solving mindset with excellent communication skills and a passion for helping users resolve technical issues. Quick learner, adaptable, and eager to gain hands-on experience in desktop support and IT operations. Seeking to contribute as an IT Intern, providing reliable user support while growing technical expertise in a collaborative environment. "
    "TECHNICAL SKILLS "
    "Web Technologies: HTML5, JavaScript (Basic), React.js, Next.js "
    "Backend & API: SQL, API Design & Integration, RESTful Services, JSON, Data Handling "
    "Development Tools: VS Code, Browser Developer Tools (Chrome DevTools), Git, Cursor AI "
    "QA & Debugging: Technical Troubleshooting, Issue Identification, Root Cause Analysis, QA Testing "
    "Analytics & SEO: Google Analytics Basics, SEO Fundamentals, Performance Monitoring "
    "Documentation: SRS, BRD, FRD, Technical Specifications, Implementation Guides, Process Flows "
    "Collaboration Tools: Agile Workflows, Cross-Functional Communication, Client-Facing Support "
    "PROFESSIONAL EXPERIENCE "
    "AI Operations Engineer  | Sars Digital, Gurugram  |  June 2025 – July 2025 "
    "Automated operational workflows using low-code AI tools, reducing manual task execution time by 40%. "
    "Supported backend architecture for data integration pipelines, ensuring 99% uptime for operational processes. "
    "Identified and resolved system bottlenecks in data flow, improving end-to-end process efficiency. "
    "Collaborated with operations and product teams to gather requirements and translate them into scalable technical solutions. "
    "Maintained technical documentation and process manuals (SOPs, BRDs) for all automated workflows. "
    "KEY PROJECTS "
    "Smart Parking System (IoT) | Arduino, HTML/CSS/JS, Real-Time Data Integration "
    "Engineered an IoT-based parking solution integrating sensor data with a web interface; performed QA validation to ensure accurate real-time slot display. "
    "Debugged frontend-backend communication issues using browser tools and serial monitoring, demonstrating systematic problem-solving. "
    "Route Mapping & Logistics Web App | React.js, Google Maps API, Responsive Design "
    "Built a responsive logistics application featuring real-time route optimization; implemented cross-browser compatibility checks and performance debugging. "
    "Collaborated with hypothetical stakeholders to refine requirements, ensuring technical execution matched business goals and user expectations. "
    "Face Mask Detection System | Python, TensorFlow, OpenCV, Model Validation "
    "Implemented a CNN-based classification model achieving 95% accuracy; conducted rigorous testing and validation to ensure reliable, production-ready outputs. "
    "Documented technical architecture and deployment steps, supporting reproducibility and knowledge transfer. "
    "CRM Dashboard with AI Chatbot | Next.js, JavaScript, API Integration, QA Testing "
    "Developed a scalable CRM platform with an AI chatbot for automated customer query handling; performed end-to-end testing and debugging using Chrome DevTools. "
    "Integrated RESTful APIs for real-time data flow; conducted QA checks to ensure feature reliability and alignment with user requirements. "
    "Documented implementation steps and troubleshooting guides to support future iterations and team knowledge sharing. "
    "EDUCATION "
    "Master of Computer Application – Machine Learning & AI (Pursuing)  |  UPES, Dehradun  |  2024 - 2026 "
    "Bachelor of Computer Science  |  HNB Garhwal University, Haridwar  |  2021 - 2024 "
    "yeh template use krna hai"
)

def run_debug():
    raw_msg = pasted_text
    
    # Simulate Attempt 2
    name = re.search(r"(?i)\bname\b\s*:\s*(.*?)(?=\s*(?:\b(?:name|contact|education|experience|skills)\b\s*:|$))", raw_msg, re.DOTALL)
    contact = re.search(r"(?i)\bcontact\b\s*:\s*(.*?)(?=\s*(?:\b(?:name|contact|education|experience|skills)\b\s*:|$))", raw_msg, re.DOTALL)
    edu = re.search(r"(?i)\beducation\b\s*:\s*(.*?)(?=\s*(?:\b(?:name|contact|education|experience|skills)\b\s*:|$))", raw_msg, re.DOTALL)
    exp = re.search(r"(?i)\bexperience\b\s*:\s*(.*?)(?=\s*(?:\b(?:name|contact|education|experience|skills)\b\s*:|$))", raw_msg, re.DOTALL)
    skills = re.search(r"(?i)\bskills\b\s*:\s*(.*?)(?=\s*(?:\b(?:name|contact|education|experience|skills)\b\s*:|$))", raw_msg, re.DOTALL)

    def clean_val(match):
        if not match:
            return None
        val = match.group(1).strip()
        if val.startswith("[") and val.endswith("]"):
            return None
        if val.lower() in ["", "null", "undefined"]:
            return None
        return val

    fields = {
        "name": clean_val(name),
        "contact": clean_val(contact),
        "education": clean_val(edu),
        "experience": clean_val(exp),
        "skills": clean_val(skills)
    }
    
    print("After Attempt 2:")
    print(json.dumps(fields, indent=2))

    # Simulate Attempt 3 (Offset-based parsing)
    if not fields.get("name") or not fields.get("contact") or not fields.get("skills"):
        normalized_text = " ".join(raw_msg.split())
        
        headers = {}
        patterns = {
            "summary": r"\bPROFESSIONAL SUMMARY\b|\bSUMMARY\b",
            "skills": r"\bTECHNICAL SKILLS\b|\bTECHNICAL SKILL\b|\bSKILLS\b",
            "experience": r"\bPROFESSIONAL EXPERIENCE\b|\bEXPERIENCE\b|\bWORK EXPERIENCE\b",
            "education": r"\bEDUCATION\b",
            "projects": r"\bKEY PROJECTS\b|\bPROJECTS\b"
        }
        
        # Try case-sensitive search first to avoid matching lowercase words in sentences
        for key, pattern in patterns.items():
            match = re.search(pattern, normalized_text)
            if match:
                headers[key] = (match.start(), match.end())
        
        # If we didn't find enough headers, fallback to case-insensitive
        if len(headers) < 3:
            headers = {}
            for key, pattern in patterns.items():
                match = re.search(pattern, normalized_text, re.IGNORECASE)
                if match:
                    headers[key] = (match.start(), match.end())
        
        sorted_headers = sorted(headers.items(), key=lambda x: x[1][0])
        print("\nSorted Headers Offset Map:")
        for k, val in sorted_headers:
            print(f"  {k}: start={val[0]}, end={val[1]}")

        # Extract Name and Contact from the text BEFORE the first header
        header_start = sorted_headers[0][1][0] if sorted_headers else len(normalized_text)
        intro_text = normalized_text[:header_start].strip()
        print(f"\nIntro Text: {intro_text}")

        # Name extraction
        name_val = None
        words = intro_text.split()
        if words and not any(re.search(rf"\b{w}\b", words[0].lower()) for w in ["build", "create", "generate", "resume", "cv", "hello", "hi", "hey"]):
            candidate_name = " ".join(words[:3])
            email_idx = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", candidate_name)
            phone_pattern_regex = r"\(?\+?\d[\d\-\s\(\)]{6,}\d"
            phone_idx = re.search(phone_pattern_regex, candidate_name)
            cut_idx = min([idx for idx in [email_idx.start() if email_idx else None, phone_idx.start() if phone_idx else None] if idx is not None], default=len(candidate_name))
            name_val = candidate_name[:cut_idx].strip(" |,-.").strip()

        # Contact extraction
        contact_val = None
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        phone_pattern = r"\(?\+?\d[\d\-\s\(\)]{6,}\d"
        
        # Clean links from intro text for phone search to avoid matching digits in URLs
        clean_intro = intro_text
        for word in intro_text.split():
            if any(w in word.lower() for w in ["linkedin.com", "github.com", "http", "www", "git"]):
                clean_intro = clean_intro.replace(word, "")
        
        emails = re.findall(email_pattern, intro_text)
        phones = []
        for m in re.finditer(phone_pattern, clean_intro):
            phone = m.group().strip().strip(" |,-.")
            if phone and not any(w in phone for w in ["2024", "2026", "2021", "2025"]) and len(re.sub(r'\D', '', phone)) >= 7:
                phones.append(phone)
                
        links = [w for w in words if "linkedin.com" in w.lower() or "github.com" in w.lower()]
        
        contact_parts = []
        if phones:
            contact_parts.extend(phones)
        if emails:
            contact_parts.extend(emails)
        if links:
            contact_parts.extend(links)
            
        if contact_parts:
            contact_val = " | ".join(contact_parts)
        else:
            contact_val = intro_text

        # Section extraction
        def get_section_content(header_key):
            if header_key not in headers:
                return None
            start_offset = headers[header_key][1]
            end_offset = len(normalized_text)
            for k, (h_start, h_end) in sorted_headers:
                if h_start > headers[header_key][0]:
                    end_offset = h_start
                    break
            return normalized_text[start_offset:end_offset].strip()

        def clean_trailing_prompt(text: str) -> str:
            if not text:
                return text
            text_lower = text.lower()
            earliest_idx = len(text)
            for pattern in ["template use", "use krna", "use karna", "yeh template", "template", "use krna hai"]:
                if pattern in text_lower:
                    idx = text_lower.find(pattern)
                    if idx < earliest_idx:
                        earliest_idx = idx
            if earliest_idx < len(text):
                text = text[:earliest_idx].strip()
            return text.strip(" |,-")

        edu_val = clean_trailing_prompt(get_section_content("education"))
        exp_val = clean_trailing_prompt(get_section_content("experience"))
        skills_val = clean_trailing_prompt(get_section_content("skills"))
        proj_val = clean_trailing_prompt(get_section_content("projects"))
        
        if proj_val and exp_val:
            exp_val += "\n\nProjects:\n" + proj_val
        elif proj_val:
            exp_val = "Projects:\n" + proj_val

        fields = {
            "name": fields.get("name") or name_val,
            "contact": fields.get("contact") or contact_val,
            "education": fields.get("education") or edu_val,
            "experience": fields.get("experience") or exp_val,
            "skills": fields.get("skills") or skills_val
        }

    print("\nAfter Attempt 3 (Offset Segmented):")
    print(json.dumps(fields, indent=2))

if __name__ == "__main__":
    run_debug()
