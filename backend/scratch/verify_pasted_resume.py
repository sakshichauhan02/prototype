import httpx
import asyncio
import re
import sys

# Force UTF-8 encoding on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def test_pasted_resume():
    base_url = "http://127.0.0.1:8000/api/v1"
    
    # 1. Login to get JWT Token
    login_data = {
        "username": "jane.dev2@example.com",
        "password": "aetheria-local-dev"
    }
    
    async with httpx.AsyncClient(timeout=20.0) as client:
        print("Logging in to Aetheria Local Instance...")
        res = await client.post(f"{base_url}/auth/login", data=login_data)
        if res.status_code != 200:
            print("Login failed! Please check if backend is running.")
            return
            
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Create a new thread in professional mode
        thread_payload = {
            "title": "Pasted Resume Test",
            "companion_id": "aria",
            "session_mode": "professional"
        }
        
        print("\nCreating thread...")
        res = await client.post(f"{base_url}/chat/threads", json=thread_payload, headers=headers)
        if res.status_code != 201:
            print(f"Failed to create thread: {res.text}")
            return
            
        thread_id = res.json()["id"]
        print(f"Created chat thread ID: {thread_id}")
        
        # 3. Send raw pasted resume text
        print("\n--- Sending raw pasted resume text ---")
        pasted_text = (
            "SAKSHI CHAUHAN\n"
            "(+91)-7017400147  |  India  |  sakshichauhan64771@gmail.com\n"
            "linkedin.com/in/sakshi-chauhan-704973326  |  github.com/sakshichauhan02\n"
            "PROFESSIONAL SUMMARY\n"
            "Motivated IT/CS graduate with foundational knowledge in Windows OS, networking basics, and technical troubleshooting. Strong problem-solving mindset with excellent communication skills and a passion for helping users resolve technical issues. Quick learner, adaptable, and eager to gain hands-on experience in desktop support and IT operations. Seeking to contribute as an IT Intern, providing reliable user support while growing technical expertise in a collaborative environment.\n"
            "TECHNICAL SKILLS\n"
            "Web Technologies: HTML5, JavaScript (Basic), React.js, Next.js\n"
            "Backend & API: SQL, API Design & Integration, RESTful Services, JSON, Data Handling\n"
            "Development Tools: VS Code, Browser Developer Tools (Chrome DevTools), Git, Cursor AI\n"
            "QA & Debugging: Technical Troubleshooting, Issue Identification, Root Cause Analysis, QA Testing\n"
            "Analytics & SEO: Google Analytics Basics, SEO Fundamentals, Performance Monitoring\n"
            "Documentation: SRS, BRD, FRD, Technical Specifications, Implementation Guides, Process Flows\n"
            "Collaboration Tools: Agile Workflows, Cross-Functional Communication, Client-Facing Support\n"
            "PROFESSIONAL EXPERIENCE\n"
            "AI Operations Engineer  | Sars Digital, Gurugram  |  June 2025 – July 2025\n"
            "Automated operational workflows using low-code AI tools, reducing manual task execution time by 40%.\n"
            "Supported backend architecture for data integration pipelines, ensuring 99% uptime for operational processes.\n"
            "Identified and resolved system bottlenecks in data flow, improving end-to-end process efficiency.\n"
            "Collaborated with operations and product teams to gather requirements and translate them into scalable technical solutions.\n"
            "Maintained technical documentation and process manuals (SOPs, BRDs) for all automated workflows.\n"
            "KEY PROJECTS\n"
            "Smart Parking System (IoT) | Arduino, HTML/CSS/JS, Real-Time Data Integration\n"
            "Engineered an IoT-based parking solution integrating sensor data with a web interface; performed QA validation to ensure accurate real-time slot display.\n"
            "Debugged frontend-backend communication issues using browser tools and serial monitoring, demonstrating systematic problem-solving.\n"
            "Route Mapping & Logistics Web App | React.js, Google Maps API, Responsive Design\n"
            "Built a responsive logistics application featuring real-time route optimization; implemented cross-browser compatibility checks and performance debugging.\n"
            "Collaborated with hypothetical stakeholders to refine requirements, ensuring technical execution matched business goals and user expectations. \n"
            "Face Mask Detection System | Python, TensorFlow, OpenCV, Model Validation\n"
            "Implemented a CNN-based classification model achieving 95% accuracy; conducted rigorous testing and validation to ensure reliable, production-ready outputs.\n"
            "Documented technical architecture and deployment steps, supporting reproducibility and knowledge transfer. \n"
            "CRM Dashboard with AI Chatbot | Next.js, JavaScript, API Integration, QA Testing\n"
            "Developed a scalable CRM platform with an AI chatbot for automated customer query handling; performed end-to-end testing and debugging using Chrome DevTools.\n"
            "Integrated RESTful APIs for real-time data flow; conducted QA checks to ensure feature reliability and alignment with user requirements.\n"
            "Documented implementation steps and troubleshooting guides to support future iterations and team knowledge sharing. \n"
            "EDUCATION\n"
            "Master of Computer Application – Machine Learning & AI (Pursuing)  |  UPES, Dehradun  |  2024 - 2026\n"
            "Bachelor of Computer Science  |  HNB Garhwal University, Haridwar  |  2021 - 2024\n"
            "yeh template use krna hai"
        )
        
        msg_payload = {
            "content": pasted_text
        }
        res = await client.post(f"{base_url}/chat/threads/{thread_id}/messages", json=msg_payload, headers=headers)
        if res.status_code != 200:
            print(f"Error sending message: {res.text}")
            return
            
        reply = res.json()["content"]
        print("AI Reply:")
        print(reply)
        
        # Validation
        if "📄 **[Resume Agent Active]**" in reply and "resume_url:" in reply:
            print("\n✅ SUCCESS: Raw resume successfully parsed and generated!")
            url_match = re.search(r"resume_url:\s*(https?://[^\s]+)", reply)
            if url_match:
                print(f"Generated URL: {url_match.group(1)}")
        else:
            print("\n❌ FAILURE: Unexpected AI response.")

if __name__ == "__main__":
    asyncio.run(test_pasted_resume())
