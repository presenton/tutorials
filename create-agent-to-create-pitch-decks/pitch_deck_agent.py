"""
Pitch Deck Generator using Presenton API
This script generates pitch decks by:
1. Fetching company info from URL
2. Using OpenAI to generate questions
3. Creating pitch deck structure
4. Generating presentation via Presenton API
"""

import requests
import json
import os
import sys
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import openai
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class QuestionsResponse(BaseModel):
    """Structured response for questions"""
    questions: List[str] = Field(description="List of exactly 3 questions to ask the user about their business")


class PitchDeckGenerator:
    def __init__(self):
        self.presenton_base_url = "http://localhost:5000"
        self.openai_client = None
        self.last_questions = []  # Store the generated questions
        self.setup_openai()
    
    def setup_openai(self):
        """Setup OpenAI client with API key"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("❌ Error: OPENAI_API_KEY environment variable not set")
            print("Please set your OpenAI API key: export OPENAI_API_KEY='your-key-here'")
            sys.exit(1)
        
        self.openai_client = openai.OpenAI(api_key=api_key)
    
    def fetch_company_info(self, url: str) -> Dict[str, str]:
        """Fetch company information from URL"""
        print(f"🔍 Fetching information from: {url}")
        
        try:
            # Add protocol if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else "No title found"
            
            # Extract meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            description = meta_desc.get('content', '') if meta_desc else ""
            
            # Extract h1 if available
            h1 = soup.find('h1')
            h1_text = h1.get_text().strip() if h1 else ""
            
            # Extract first paragraph
            first_p = soup.find('p')
            first_p_text = first_p.get_text().strip() if first_p else ""
            
            company_info = {
                'url': url,
                'title': title_text,
                'description': description,
                'h1': h1_text,
                'first_paragraph': first_p_text
            }
            
            print(f"✅ Successfully fetched company information")
            print(f"   Title: {title_text}")
            print(f"   Description: {description[:100]}...")
            
            return company_info
            
        except Exception as e:
            print(f"❌ Error fetching company information: {str(e)}")
            return {'url': url, 'title': '', 'description': '', 'h1': '', 'first_paragraph': ''}
    
    def generate_questions(self, company_info: Dict[str, str]) -> List[str]:
        """Generate questions using OpenAI based on company information"""
        print("🤖 Generating questions using OpenAI...")
        
        prompt = f"""
Based on this company information, generate exactly 3 relevant questions to ask the user to better understand their business for creating a pitch deck:

Company URL: {company_info['url']}
Company Title: {company_info['title']}
Company Description: {company_info['description']}
H1: {company_info['h1']}
First Paragraph: {company_info['first_paragraph']}

Generate 3 specific, relevant questions that will help create a compelling pitch deck. 
Focus on understanding their business model, target market, unique value proposition, and growth plans.

The questions should be clear, specific, and designed to gather essential information for creating a professional pitch deck.
"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                tools=[{
                    "type": "function",
                    "function": {
                        "name": "get_questions",
                        "description": "Get exactly 3 questions to ask the user about their business",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "questions": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of exactly 3 questions to ask the user about their business"
                                }
                            },
                            "required": ["questions"]
                        }
                    }
                }],
                tool_choice={"type": "function", "function": {"name": "get_questions"}},
                max_tokens=300,
                temperature=0.7
            )
            
            # Extract questions from the tool call response
            tool_call = response.choices[0].message.tool_calls[0]
            arguments = json.loads(tool_call.function.arguments)
            questions = arguments.get('questions', [])
            
            # Ensure we have exactly 3 questions
            if len(questions) < 3:
                # Fallback questions if AI didn't provide enough
                fallback_questions = [
                    "What is your company's main product or service?",
                    "Who is your target market?",
                    "What makes your solution unique?"
                ]
                questions = questions + fallback_questions[:3-len(questions)]
            else:
                questions = questions[:3]  # Take first 3 if more provided
            
            print("✅ Generated questions:")
            for i, question in enumerate(questions, 1):
                print(f"   {i}. {question}")
            
            # Store the questions for later use in structure generation
            self.last_questions = questions
            
            return questions
            
        except Exception as e:
            print(f"❌ Error generating questions: {str(e)}")
            return [
                "What is your company's main product or service?",
                "Who is your target market?",
                "What makes your solution unique?"
            ]
    
    def get_user_answers(self, questions: List[str]) -> List[str]:
        """Get user answers to the generated questions"""
        print("\n📝 Please answer the following questions:")
        answers = []
        
        for i, question in enumerate(questions, 1):
            print(f"\nQuestion {i}: {question}")
            answer = input("Your answer: ").strip()
            answers.append(answer)
        
        return answers
    
    def generate_pitch_deck_structure(self, company_info: Dict[str, str], answers: List[str]) -> str:
        """Generate pitch deck structure using OpenAI"""
        print("🤖 Generating pitch deck structure...")
        
        prompt = f"""
Create a comprehensive pitch deck structure in markdown format for this company:

Company Information:
- URL: {company_info['url']}
- Title: {company_info['title']}
- Description: {company_info['description']}
- H1: {company_info['h1']}

Questions Asked and User Answers:
{chr(10).join([f"Q: {question}\nA: {answer}\n" for question, answer in zip(self.last_questions, answers)])}

Generate a pitch deck structure with 8-12 slides covering:
1. Title slide with company name and tagline
2. Problem statement
3. Solution overview
4. Market opportunity
5. Business model
6. Competitive advantage
7. Go-to-market strategy
8. Financial projections
9. Team
10. Funding ask (if applicable)
11. Contact information

Use the questions and answers provided to create a more targeted and relevant pitch deck structure.
Format as markdown with clear slide titles and bullet points for content.
"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.7
            )
            
            structure = response.choices[0].message.content.strip()
            print("✅ Generated pitch deck structure")
            return structure
            
        except Exception as e:
            print(f"❌ Error generating structure: {str(e)}")
            return self.get_default_structure(company_info)
    
    def get_default_structure(self, company_info: Dict[str, str]) -> str:
        """Fallback default structure"""
        return f"""
# {company_info['title']} - Pitch Deck

## Slide 1: Title Slide
- Company Name: {company_info['title']}
- Tagline: {company_info['description'][:50]}...

## Slide 2: Problem Statement
- [To be filled based on user input]

## Slide 3: Our Solution
- [To be filled based on user input]

## Slide 4: Market Opportunity
- [To be filled based on user input]

## Slide 5: Business Model
- [To be filled based on user input]

## Slide 6: Competitive Advantage
- [To be filled based on user input]

## Slide 7: Go-to-Market Strategy
- [To be filled based on user input]

## Slide 8: Financial Projections
- [To be filled based on user input]

## Slide 9: Team
- [To be filled based on user input]

## Slide 10: Funding Ask
- [To be filled based on user input]

## Slide 11: Contact Information
- Website: {company_info['url']}
- [Additional contact details]
"""
    
    def generate_presentation(self, company_info: Dict[str, str], structure: str) -> Optional[Dict]:
        """Generate presentation using Presenton API"""
        print("🎨 Generating presentation using Presenton API...")
        
        # Create a comprehensive prompt for the presentation
        presentation_prompt = f"""
Create a professional pitch deck for {company_info['title']}.

Company Information:
- Website: {company_info['url']}
- Description: {company_info['description']}

Pitch Deck Structure:
{structure}

Create a compelling pitch deck with professional slides, clear messaging, and engaging visuals.
Focus on storytelling and making the business case compelling.
"""
        
        try:
            url = f"{self.presenton_base_url}/api/v1/ppt/generate/presentation"
            
            data = {
                'prompt': presentation_prompt,
                'n_slides': 10,
                'language': 'English',
                'theme': 'light',
                'export_as': 'pdf'
            }
            print("Presentation generation can take a couple of minutes, please wait...")
            
            response = requests.post(url, data=data, timeout=500)
            response.raise_for_status()
            
            result = response.json()
            print("✅ Presentation generated successfully!")
            print(f"   Presentation ID: {result.get('presentation_id')}")
            print(f"   Download path: {result.get('path')}")
            print(f"   Edit URL: {self.presenton_base_url}{result.get('edit_path')}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error connecting to Presenton API: {str(e)}")
            print("Make sure Presenton is running on localhost:5000")
            return None
        except Exception as e:
            print(f"❌ Error generating presentation: {str(e)}")
            return None
    
    def run(self):
        """Main execution flow"""
        print("🚀 Pitch Deck Generator")
        print("=" * 50)
        
        # Get company URL
        company_url = input("Enter the company website URL: ").strip()
        if not company_url:
            print("❌ No URL provided. Exiting.")
            return
        
        # Fetch company information
        company_info = self.fetch_company_info(company_url)
        
        # Generate questions
        questions = self.generate_questions(company_info)
        
        # Get user answers
        answers = self.get_user_answers(questions)
        
        # Generate pitch deck structure
        structure = self.generate_pitch_deck_structure(company_info, answers)
        
        # Generate presentation
        result = self.generate_presentation(company_info, structure)
        
        if result:
            print("\n🎉 Pitch deck generation completed!")
            print(f"📄 You can download the presentation from: {self.presenton_base_url}{result.get('path')}")
            print(f"✏️  Edit the pitch deck at: {self.presenton_base_url}{result.get('edit_path')}")
        else:
            print("\n❌ Failed to generate presentation. Please check your setup.")

def main():
    """Main entry point"""
    generator = PitchDeckGenerator()
    generator.run()

if __name__ == "__main__":
    main()
