import os
import re
import json
import nltk
import PyPDF2
import spacy
from collections import Counter

# Download necessary NLTK resources
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)

# Load spaCy model
try:
    nlp = spacy.load('en_core_web_sm')
except:
    # If model not found, download it
    print("Downloading spaCy model...")
    import subprocess
    subprocess.call(['python', '-m', 'spacy', 'download', 'en_core_web_sm'])
    nlp = spacy.load('en_core_web_sm')

class ResumeAnalyzer:
    def __init__(self):
        self.stopwords = set(nltk.corpus.stopwords.words('english'))
        self.lemmatizer = nltk.stem.WordNetLemmatizer()
        
        # Keywords for different sections - expanded with more variations
        self.section_keywords = {
            'education': ['education', 'academic background', 'degree', 'university', 'college', 'school',
                         'graduation', 'diploma', 'bachelor', 'master', 'phd', 'doctorate'],
            'experience': ['experience', 'work history', 'employment', 'job', 'position', 'career',
                          'professional background', 'work experience', 'internship', 'intern'],
            'skills': ['skills', 'abilities', 'competencies', 'expertise', 'proficiencies', 'technical skills',
                      'soft skills', 'hard skills', 'qualifications', 'technical'],
            'projects': ['projects', 'portfolio', 'personal projects', 'academic projects', 'project experience'],
            'achievements': ['achievements', 'accomplishments', 'awards', 'honors', 'recognitions', 'accolades'],
            'certifications': ['certifications', 'certificates', 'licenses', 'accreditations', 'credentials'],
            'languages': ['languages', 'language proficiency', 'multilingual', 'fluent in'],
            'contact': ['contact', 'email', 'phone', 'address', 'linkedin', 'github', 'website', 'portfolio']
        }
        
        # Action verbs that make resumes stronger
        self.action_verbs = [
            'achieved', 'improved', 'developed', 'created', 'implemented', 'managed', 'led', 
            'designed', 'analyzed', 'reduced', 'increased', 'negotiated', 'streamlined', 'optimized',
            'coordinated', 'launched', 'executed', 'generated', 'delivered', 'resolved', 'spearheaded',
            'produced', 'transformed', 'built', 'established', 'pioneered', 'innovated', 'administered',
            'modernized', 'engineered', 'directed', 'accelerated', 'formulated', 'restructured',
            'gained', 'partnered', 'assisted', 'maintained', 'deployed', 'contributed', 'served',
            'volunteered', 'organized', 'ranked', 'streamlined'
        ]
        
        # Common weak phrases to avoid
        self.weak_phrases = [
            'responsible for', 'duties included', 'worked on', 'involved in', 'helped with',
            'assisted with', 'participated in', 'was tasked with', 'was asked to'
        ]
        
        # Industry keywords (expand these based on your target industries)
        self.industry_keywords = {
            'software_development': ['python', 'java', 'javascript', 'react', 'node', 'aws', 'cloud', 'api', 
                                    'database', 'frontend', 'backend', 'fullstack', 'devops', 'agile',
                                    'scrum', 'ci/cd', 'testing', 'git', 'docker', 'kubernetes', 'microservices',
                                    'express', 'mongodb', 'typescript', 'next.js', 'html5', 'css3', 'redux',
                                    'websockets', 'jwt', 'rest', 'api', 'mern', 'c++', 'algorithms'],
            'data_science': ['machine learning', 'artificial intelligence', 'data analysis', 'statistics',
                            'python', 'r', 'sql', 'pandas', 'numpy', 'tensorflow', 'pytorch', 'scikit-learn',
                            'data visualization', 'big data', 'nlp', 'computer vision', 'deep learning'],
            'marketing': ['digital marketing', 'seo', 'sem', 'content strategy', 'social media', 'analytics',
                         'campaign management', 'google analytics', 'conversion optimization', 'a/b testing',
                         'customer acquisition', 'funnel optimization', 'brand management'],
            'finance': ['financial analysis', 'accounting', 'budgeting', 'forecasting', 'risk assessment',
                       'portfolio management', 'investment', 'banking', 'excel', 'financial modeling'],
            'project_management': ['project management', 'agile', 'scrum', 'kanban', 'jira', 'stakeholder',
                                 'timeline', 'resource allocation', 'risk management', 'project planning']
        }
    
    def extract_text_from_pdf(self, pdf_path):
        """Extract text from a PDF file"""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num in range(len(pdf_reader.pages)):
                    text += pdf_reader.pages[page_num].extract_text()
            return text
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""
    
    def preprocess_text(self, text):
        """Clean and preprocess the resume text"""
        # Remove special characters and extra whitespace
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Lowercase
        text = text.lower()
        
        return text
    
    def identify_sections(self, text):
        """Identify different sections in the resume with improved logic"""
        sections = {}
        
        # Split text into lines
        lines = text.split('\n')
        current_section = 'header'
        section_content = []
        
        # Improved logic to detect section headers
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            line_lower = line.lower()
            section_match = None
            
            # Check if line contains a section header
            for section, keywords in self.section_keywords.items():
                # Direct match for section headers (e.g., "Work Experience", "Projects", etc.)
                for keyword in keywords:
                    # Check for exact section header matches or with adjacent words
                    if (re.search(r'\b' + re.escape(keyword) + r'\b', line_lower) and len(line) < 50) or \
                       line_lower == keyword or \
                       line_lower.startswith(keyword + ' ') or \
                       line_lower.endswith(' ' + keyword):
                        if current_section:
                            sections[current_section] = ' '.join(section_content)
                        current_section = section
                        section_content = []
                        section_match = True
                        break
                
                # Special case for common resume section headers
                if not section_match and section == 'experience' and re.search(r'\bwork\s+experience\b', line_lower):
                    if current_section:
                        sections[current_section] = ' '.join(section_content)
                    current_section = 'experience'
                    section_content = []
                    section_match = True
                
                # Special case for projects
                if not section_match and section == 'projects' and (line_lower == 'projects' or line_lower.startswith('project')):
                    if current_section:
                        sections[current_section] = ' '.join(section_content)
                    current_section = 'projects'
                    section_content = []
                    section_match = True
                
                # Special case for achievements
                if not section_match and section == 'achievements' and (line_lower == 'achievements' or line_lower.startswith('achievement')):
                    if current_section:
                        sections[current_section] = ' '.join(section_content)
                    current_section = 'achievements'
                    section_content = []
                    section_match = True
                
                if section_match:
                    break
            
            # Format detection for section headers (e.g., all caps, followed by a blank line)
            if not section_match and i > 0 and i < len(lines) - 1:
                if line.isupper() or (line[0].isupper() and line[-1].isupper() and len(line) < 30):
                    line_lower = line.lower()
                    for section, keywords in self.section_keywords.items():
                        for keyword in keywords:
                            if keyword in line_lower:
                                if current_section:
                                    sections[current_section] = ' '.join(section_content)
                                current_section = section
                                section_content = []
                                section_match = True
                                break
                        if section_match:
                            break
            
            if not section_match:
                section_content.append(line)
        
        # Add the last section
        if current_section and section_content:
            sections[current_section] = ' '.join(section_content)
        
        # Special case for GitHub detection in projects section
        if 'header' in sections and 'github' in sections['header'].lower():
            if 'projects' not in sections:
                sections['projects'] = 'GitHub project entries found in header'
        
        # Check for achievements/awards keywords in the entire text
        full_text = text.lower()
        if 'achievements' not in sections:
            for achievement_keyword in ['ranked', 'award', 'star', 'achievement', 'volunteer', 'recognition', 'honor']:
                if achievement_keyword in full_text:
                    # Extract the surrounding content for context
                    pattern = r"[^.]*\b" + re.escape(achievement_keyword) + r"\b[^.]*\."
                    matches = re.findall(pattern, full_text, re.IGNORECASE)
                    if matches:
                        sections['achievements'] = ' '.join(matches)
                        break
        
        return sections
    
    def extract_entities(self, text):
        """Extract named entities from text using spaCy"""
        doc = nlp(text)
        entities = {}
        
        for ent in doc.ents:
            if ent.label_ not in entities:
                entities[ent.label_] = []
            entities[ent.label_].append(ent.text)
            
        return entities
    
    def count_action_verbs(self, text):
        """Count action verbs used in the resume"""
        words = nltk.word_tokenize(text.lower())
        lemmatized_words = [self.lemmatizer.lemmatize(word, 'v') for word in words if word.isalpha()]
        
        action_verbs_used = set()
        for word in lemmatized_words:
            if word in self.action_verbs:
                action_verbs_used.add(word)
                
        return list(action_verbs_used)
    
    def detect_weak_phrases(self, text):
        """Detect weak phrases in the resume"""
        text_lower = text.lower()
        found_phrases = []
        
        for phrase in self.weak_phrases:
            if phrase in text_lower:
                found_phrases.append(phrase)
                
        return found_phrases
    
    def identify_industry_keywords(self, text, industries=None):
        """Identify industry-specific keywords in the resume"""
        text_lower = text.lower()
        found_keywords = {}
        
        # If specific industries are provided, only check those
        if industries:
            industry_list = [ind for ind in industries if ind in self.industry_keywords]
        else:
            industry_list = list(self.industry_keywords.keys())
            
        for industry in industry_list:
            found = []
            for keyword in self.industry_keywords[industry]:
                if keyword in text_lower:
                    found.append(keyword)
            if found:
                found_keywords[industry] = found
                
        return found_keywords
    
    def calculate_metrics(self, text, sections):
        """Calculate various metrics about the resume"""
        metrics = {}
        
        # Word count
        words = nltk.word_tokenize(text)
        metrics['word_count'] = len(words)
        
        # Section presence and length
        section_metrics = {}
        for section, section_keywords in self.section_keywords.items():
            if section in sections:
                section_words = nltk.word_tokenize(sections[section])
                section_metrics[section] = {
                    'present': True,
                    'word_count': len(section_words)
                }
            else:
                section_metrics[section] = {
                    'present': False,
                    'word_count': 0
                }
        metrics['sections'] = section_metrics
        
        # Action verb metrics
        action_verbs = self.count_action_verbs(text)
        metrics['action_verbs'] = {
            'count': len(action_verbs),
            'verbs': action_verbs
        }
        
        # Weak phrases
        weak_phrases = self.detect_weak_phrases(text)
        metrics['weak_phrases'] = {
            'count': len(weak_phrases),
            'phrases': weak_phrases
        }
        
        return metrics
    
    def generate_recommendations(self, metrics, sections, industry_keywords, target_industry=None):
        """Generate recommendations based on resume analysis"""
        recommendations = {
            'overall': [],
            'sections': {},
            'language_use': [],
            'industry_alignment': []
        }
        
        # Overall recommendations
        if metrics['word_count'] < 300:
            recommendations['overall'].append("Your resume is quite short. Consider adding more details about your achievements and experience.")
        elif metrics['word_count'] > 1000:
            recommendations['overall'].append("Your resume is relatively long. Consider condensing it to highlight your most relevant accomplishments.")
        
        # Section-specific recommendations
        for section, data in metrics['sections'].items():
            section_recs = []
            
            # Only recommend adding a section if it's truly missing
            # Skip certain checks if we've already identified the content elsewhere
            if not data['present']:
                # Additional check for projects section
                if section == 'projects' and any('github' in s.lower() for s in sections.values()):
                    continue
                # Additional check for achievements section
                if section == 'achievements' and any('ranked' in s.lower() or 'award' in s.lower() or 'recognition' in s.lower() for s in sections.values()):
                    continue
                    
                section_recs.append(f"Add a {section.replace('_', ' ').title()} section to your resume.")
            elif data['word_count'] < 30 and section not in ['contact', 'languages']:
                section_recs.append(f"Expand your {section.replace('_', ' ').title()} section with more details.")
            
            if section_recs:
                recommendations['sections'][section] = section_recs
        
        # Experience section specific recommendations
        if 'experience' in sections:
            exp_text = sections['experience'].lower()
            if not re.search(r'\d{4}', exp_text):
                if 'experience' not in recommendations['sections']:
                    recommendations['sections']['experience'] = []
                recommendations['sections']['experience'].append("Add dates to your work experience entries.")
            
            if not any(verb in exp_text for verb in self.action_verbs):
                if 'experience' not in recommendations['sections']:
                    recommendations['sections']['experience'] = []
                recommendations['sections']['experience'].append("Use strong action verbs to describe your responsibilities and achievements.")
        
        # Language use recommendations
        if metrics['action_verbs']['count'] < 5:
            recommendations['language_use'].append("Use more action verbs to make your achievements stand out. Examples include: achieved, implemented, developed, etc.")
        
        if metrics['weak_phrases']['count'] > 0:
            weak_phrase_examples = ', '.join(metrics['weak_phrases']['phrases'][:3])
            recommendations['language_use'].append(f"Replace weak phrases like '{weak_phrase_examples}' with strong action verbs.")
        
        # Industry alignment recommendations
        if target_industry and target_industry in self.industry_keywords:
            relevant_keywords = set(self.industry_keywords[target_industry])
            found_keywords = set()
            
            for industry, keywords in industry_keywords.items():
                found_keywords.update(keywords)
            
            missing_important_keywords = relevant_keywords - found_keywords
            
            if missing_important_keywords:
                sample_keywords = list(missing_important_keywords)[:5]
                recommendations['industry_alignment'].append(f"Consider adding industry-relevant keywords such as: {', '.join(sample_keywords)}")
        
        return recommendations
    
    def analyze_resume(self, pdf_path, target_industry=None):
        """Main function to analyze a resume and generate recommendations"""
        # Extract text from PDF
        raw_text = self.extract_text_from_pdf(pdf_path)
        if not raw_text:
            return {"error": "Could not extract text from the PDF"}
        
        # Preprocess text
        processed_text = self.preprocess_text(raw_text)
        
        # Debug raw text extraction
        print("PDF Text (First 200 chars):", raw_text[:200])
        
        # Identify sections
        sections = self.identify_sections(raw_text)
        
        # Debug sections found
        print("Sections found:", list(sections.keys()))
        
        # Extract entities
        entities = self.extract_entities(processed_text)
        
        # Identify industry keywords
        industry_keywords = self.identify_industry_keywords(processed_text)
        
        # Calculate metrics
        metrics = self.calculate_metrics(processed_text, sections)
        
        # Generate recommendations
        recommendations = self.generate_recommendations(metrics, sections, industry_keywords, target_industry)
        
        # Prepare analysis result
        analysis = {
            'sections_found': list(sections.keys()),
            'metrics': metrics,
            'industry_keywords': industry_keywords,
            'recommendations': recommendations
        }
        
        return analysis

    def generate_api_response(self, analysis):
        """Format the analysis results for API response"""
        response = {
            "success": True,
            "recommendations": [],
            "metrics": {
                "wordCount": analysis['metrics']['word_count'],
                "actionVerbCount": analysis['metrics']['action_verbs']['count'],
                "weakPhraseCount": analysis['metrics']['weak_phrases']['count'],
                "sectionsFound": analysis['sections_found']
            },
            "keywordAnalysis": {
                "industryKeywords": analysis['industry_keywords']
            }
        }
        
        # Compile all recommendations into a flat list for easier frontend consumption
        all_recs = []
        
        # Overall recommendations
        for rec in analysis['recommendations']['overall']:
            all_recs.append({
                "category": "Overall",
                "recommendation": rec
            })
        
        # Section recommendations
        for section, recs in analysis['recommendations']['sections'].items():
            for rec in recs:
                all_recs.append({
                    "category": section.replace('_', ' ').title(),
                    "recommendation": rec
                })
        
        # Language use recommendations
        for rec in analysis['recommendations']['language_use']:
            all_recs.append({
                "category": "Language",
                "recommendation": rec
            })
        
        # Industry alignment recommendations
        for rec in analysis['recommendations']['industry_alignment']:
            all_recs.append({
                "category": "Industry Alignment",
                "recommendation": rec
            })
        
        response["recommendations"] = all_recs
        return response

# Add a test function to help with debugging
def test_resume_analyzer(pdf_path, target_industry=None):
    analyzer = ResumeAnalyzer()
    analysis = analyzer.analyze_resume(pdf_path, target_industry)
    
    print("\n--- RESUME ANALYSIS RESULTS ---")
    print(f"Sections found: {analysis['sections_found']}")
    print(f"Word count: {analysis['metrics']['word_count']}")
    print(f"Action verbs: {len(analysis['metrics']['action_verbs']['verbs'])}")
    print(f"Weak phrases: {len(analysis['metrics']['weak_phrases']['phrases'])}")
    
    print("\n--- RECOMMENDATIONS ---")
    if analysis['recommendations']['overall']:
        print("Overall:")
        for rec in analysis['recommendations']['overall']:
            print(f"- {rec}")
    
    if analysis['recommendations']['sections']:
        print("\nSection-specific:")
        for section, recs in analysis['recommendations']['sections'].items():
            print(f"{section.replace('_', ' ').title()}:")
            for rec in recs:
                print(f"- {rec}")
    
    if analysis['recommendations']['language_use']:
        print("\nLanguage use:")
        for rec in analysis['recommendations']['language_use']:
            print(f"- {rec}")
    
    if analysis['recommendations']['industry_alignment']:
        print("\nIndustry alignment:")
        for rec in analysis['recommendations']['industry_alignment']:
            print(f"- {rec}")
    
    print("\n--- INDUSTRY KEYWORDS ---")
    for industry, keywords in analysis['industry_keywords'].items():
        print(f"{industry}: {keywords}")
    
    return analysis

# Example usage:
if __name__ == "__main__":
    test_resume_analyzer("example_resume.pdf", "software_development")