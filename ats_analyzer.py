# ats_analyzer.py
import re
import string
from collections import Counter
from resume_analyzer import ResumeAnalyzer

class ATSScoreAnalyzer:
    def __init__(self):
        self.resume_analyzer = ResumeAnalyzer()
        
        # ATS compatibility factors and their weights
        self.ats_factors = {
            'keyword_match': 0.35,       # Keyword matching with job description
            'format_score': 0.25,        # Clean formatting, standard sections
            'word_count': 0.10,          # Appropriate length
            'action_verbs': 0.10,        # Strong action verbs  
            'file_format': 0.10,         # PDF format is standard
            'contact_info': 0.05,        # Complete contact information
            'education_format': 0.05     # Properly formatted education
        }
        
        # Common ATS-unfriendly elements
        self.ats_unfriendly_elements = [
            'tables',              # Many ATS systems struggle with tables
            'columns',             # Multi-column layouts can cause parsing issues
            'headers/footers',     # Often ignored by ATS
            'images',              # Can't be parsed by ATS
            'charts',              # Visual elements get lost
            'text boxes',          # Often parsed incorrectly
            'special characters',  # Can cause parsing errors
            'custom fonts',        # May render incorrectly
            'uncommon file formats' # Non-standard formats may not parse correctly
        ]
        
        # Keywords frequently used in job descriptions by industry
        self.common_ats_keywords = {
            'software_development': [
                'javascript', 'python', 'java', 'react', 'angular', 'vue', 'node.js', 
                'api', 'rest', 'git', 'aws', 'cloud', 'agile', 'scrum', 'ci/cd',
                'full-stack', 'backend', 'frontend', 'database', 'sql', 'nosql',
                'devops', 'docker', 'kubernetes', 'testing', 'microservices'
            ],
            'data_science': [
                'machine learning', 'deep learning', 'neural networks', 'ai', 'data analysis',
                'python', 'r', 'sql', 'pandas', 'numpy', 'scikit-learn', 'tensorflow',
                'pytorch', 'statistics', 'big data', 'data visualization', 'nlp',
                'computer vision', 'predictive modeling', 'data mining', 'feature engineering'
            ],
            'marketing': [
                'digital marketing', 'social media', 'content marketing', 'seo', 'sem',
                'google analytics', 'campaign management', 'market research', 'brand strategy',
                'email marketing', 'crm', 'customer journey', 'analytics', 'kpis',
                'conversion rate optimization', 'a/b testing', 'marketing automation'
            ],
            'finance': [
                'financial analysis', 'accounting', 'budgeting', 'forecasting', 'risk assessment',
                'financial reporting', 'investment analysis', 'portfolio management', 'excel',
                'financial modeling', 'valuation', 'cfa', 'bloomberg', 'financial statements',
                'compliance', 'regulatory reporting', 'audit', 'tax'
            ],
            'project_management': [
                'project management', 'agile', 'scrum', 'kanban', 'waterfall', 'prince2',
                'pmp', 'project planning', 'risk management', 'stakeholder management',
                'resource allocation', 'gantt', 'jira', 'ms project', 'project lifecycle',
                'change management', 'budget management', 'timeline', 'kpis'
            ]
        }
    
    def check_file_format(self, file_path):
        """Check if the file is in ATS-friendly format (PDF)"""
        return file_path.lower().endswith('.pdf')
    
    def detect_formatting_issues(self, text):
        """Detect potential ATS unfriendly formatting"""
        issues = []
        
        # Check for potential tables (rows of similar format)
        lines = text.split('\n')
        for i in range(1, len(lines)-1):
            if (len(lines[i-1]) > 0 and len(lines[i]) > 0 and len(lines[i+1]) > 0 and
                '|' in lines[i-1] and '|' in lines[i] and '|' in lines[i+1]):
                issues.append('tables')
                break
        
        # Check for potential columns (multiple sections on same horizontal line)
        for line in lines:
            if len(line) > 50:  # Reasonable minimum line length
                tab_or_spaces = len(re.findall(r'\t|\s{4,}', line))
                if tab_or_spaces > 2:  # Multiple tabs or large spaces suggest columns
                    issues.append('columns')
                    break
        
        # Check for special characters that might confuse ATS
        special_chars = set(string.punctuation) - set('-_.,@:()/')  # Common acceptable punctuation
        unusual_chars = []
        for char in text:
            if char in special_chars:
                unusual_chars.append(char)
        
        if unusual_chars:
            issues.append('special characters')
        
        # Check for potential text boxes (short isolated text segments)
        isolated_segments = re.findall(r'\n\s*\S{1,20}\s*\n', text)
        if len(isolated_segments) > 3:  # Multiple isolated short segments suggest text boxes
            issues.append('text boxes')
        
        return list(set(issues))  # Remove duplicates
    
    def analyze_contact_info(self, text):
        """Check for complete contact information"""
        has_email = bool(re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text))
        has_phone = bool(re.search(r'(\+\d{1,3}\s?)?(\()?\d{3}(\))?[\s.-]?\d{3}[\s.-]?\d{4}', text))
        has_linkedin = bool(re.search(r'linkedin\.com|linkedin', text.lower()))
        
        missing_info = []
        if not has_email:
            missing_info.append('email')
        if not has_phone:
            missing_info.append('phone number')
        if not has_linkedin:
            missing_info.append('LinkedIn profile')
            
        return {
            'complete': len(missing_info) == 0,
            'missing': missing_info
        }
    
    def check_education_format(self, education_text):
        """Check if education section follows ATS-friendly format"""
        if not education_text:
            return {'properly_formatted': False, 'issues': ['education section missing']}
        
        issues = []
        
        # Check for degree mention
        if not re.search(r'\b(bachelor|master|phd|doctor|mba|bs|ba|ms|ma|btech|mtech)\b', education_text.lower()):
            issues.append('degree not clearly stated')
        
        # Check for graduation year
        if not re.search(r'\b20\d{2}\b', education_text):
            issues.append('graduation year not mentioned')
        
        # Check for institution name
        if not re.search(r'\b(university|college|institute|school)\b', education_text.lower()):
            issues.append('institution not clearly stated')
            
        return {
            'properly_formatted': len(issues) == 0,
            'issues': issues
        }
    
    def calculate_keyword_match(self, text, job_description=None, target_industry=None):
        """Calculate keyword match score with job description or industry standards"""
        if job_description:
            # Prepare job description
            job_desc_words = self._extract_keywords(job_description)
            
            # Prepare resume text
            resume_words = self._extract_keywords(text)
            
            # Calculate match percentage
            total_keywords = len(job_desc_words)
            if total_keywords == 0:
                return 0
                
            matches = sum(1 for word in job_desc_words if word in resume_words)
            return matches / total_keywords
        elif target_industry and target_industry in self.common_ats_keywords:
            # Use industry-specific keywords if no job description provided
            industry_keywords = self.common_ats_keywords[target_industry]
            resume_words = self._extract_keywords(text)
            
            # Calculate match percentage
            total_keywords = len(industry_keywords)
            matches = sum(1 for word in industry_keywords if word in resume_words)
            return matches / total_keywords
        else:
            # Default to industry keywords from resume analyzer
            industry_keywords = self.resume_analyzer.identify_industry_keywords(text)
            if not industry_keywords:
                return 0.3  # Default moderate score if no clear industry detected
                
            # Use the industry with most matches
            best_industry = max(industry_keywords.keys(), key=lambda k: len(industry_keywords[k]))
            standard_keywords = self.common_ats_keywords.get(best_industry, [])
            
            if not standard_keywords:
                return 0.3
                
            resume_words = self._extract_keywords(text)
            total_keywords = len(standard_keywords)
            matches = sum(1 for word in standard_keywords if word in resume_words)
            return matches / total_keywords
    
    def _extract_keywords(self, text):
        """Extract important keywords from text"""
        text = text.lower()
        # Remove punctuation
        text = re.sub(r'[^\w\s]', ' ', text)
        # Tokenize
        words = text.split()
        # Remove stopwords (simplified)
        stopwords = {'and', 'the', 'to', 'of', 'for', 'in', 'on', 'at', 'with', 'by', 'a', 'an'}
        keywords = [word for word in words if word not in stopwords and len(word) > 2]
        return set(keywords)
    
    def calculate_ats_score(self, pdf_path, job_description=None, target_industry=None):
        """Calculate overall ATS compatibility score"""
        # Extract text and analyze resume using base analyzer
        raw_text = self.resume_analyzer.extract_text_from_pdf(pdf_path)
        if not raw_text:
            return {"error": "Could not extract text from the PDF"}
            
        processed_text = self.resume_analyzer.preprocess_text(raw_text)
        sections = self.resume_analyzer.identify_sections(raw_text)
        
        # Get base analysis
        base_analysis = self.resume_analyzer.analyze_resume(pdf_path, target_industry)
        
        # Calculate individual factor scores
        scores = {}
        
        # 1. Keyword match score
        scores['keyword_match'] = self.calculate_keyword_match(raw_text, job_description, target_industry)
        
        # 2. Format score
        formatting_issues = self.detect_formatting_issues(raw_text)
        format_score = 1.0 - (len(formatting_issues) / len(self.ats_unfriendly_elements))
        scores['format_score'] = max(0, format_score)  # Ensure non-negative
        
        # 3. Word count score - penalize if too short or too long
        word_count = base_analysis['metrics']['word_count']
        if word_count < 300:
            scores['word_count'] = word_count / 300  # Linearly scale up to 300
        elif word_count > 1000:
            scores['word_count'] = 1.0 - ((word_count - 1000) / 1000)  # Penalize for being too long
            scores['word_count'] = max(0, scores['word_count'])  # Ensure non-negative
        else:
            scores['word_count'] = 1.0  # Optimal range
            
        # 4. Action verbs score
        action_verb_count = base_analysis['metrics']['action_verbs']['count']
        scores['action_verbs'] = min(1.0, action_verb_count / 10)  # Cap at 10 action verbs
        
        # 5. File format score - binary PDF check
        scores['file_format'] = 1.0 if self.check_file_format(pdf_path) else 0.5
        
        # 6. Contact info score
        contact_info = self.analyze_contact_info(raw_text)
        contact_score = 1.0 if contact_info['complete'] else 0.7 - (0.1 * len(contact_info['missing']))
        scores['contact_info'] = max(0, contact_score)
        
        # 7. Education format score
        education_text = sections.get('education', '')
        education_check = self.check_education_format(education_text)
        education_score = 1.0 if education_check['properly_formatted'] else 0.7 - (0.2 * len(education_check['issues']))
        scores['education_format'] = max(0, education_score)
        
        # Calculate weighted score
        weighted_score = sum(scores[factor] * weight for factor, weight in self.ats_factors.items())
        
        # Round to nearest percent
        ats_score = round(weighted_score * 100)
        
        # Cap at 100%
        ats_score = min(100, ats_score)
        
        # Generate recommendations
        recommendations = self.generate_ats_recommendations(scores, formatting_issues, 
                                                           contact_info, education_check, 
                                                           base_analysis, target_industry)
        
        return {
            'ats_score': ats_score,
            'factor_scores': scores,
            'recommendations': recommendations,
            'formatting_issues': formatting_issues,
            'base_analysis': base_analysis
        }
        
    def generate_ats_recommendations(self, scores, formatting_issues, contact_info, 
                                    education_check, base_analysis, target_industry):
        """Generate specific recommendations to improve ATS compatibility"""
        recommendations = []
        
        # 1. Keyword recommendations
        if scores['keyword_match'] < 0.6:
            if target_industry and target_industry in self.common_ats_keywords:
                missing_keywords = [kw for kw in self.common_ats_keywords[target_industry] 
                                   if kw not in ' '.join(base_analysis['industry_keywords'].get(target_industry, []))]
                if missing_keywords:
                    top_missing = missing_keywords[:5]
                    recommendations.append({
                        'category': 'Keywords',
                        'recommendation': f"Add more industry-specific keywords such as: {', '.join(top_missing)}",
                        'priority': 'High'
                    })
            else:
                recommendations.append({
                    'category': 'Keywords',
                    'recommendation': "Add more relevant keywords from the job description to increase your match rate.",
                    'priority': 'High'
                })
        
        # 2. Formatting recommendations
        if formatting_issues:
            for issue in formatting_issues:
                recommendations.append({
                    'category': 'Formatting',
                    'recommendation': f"Remove {issue} from your resume as they can confuse ATS systems.",
                    'priority': 'High' if issue in ['tables', 'columns', 'text boxes'] else 'Medium'
                })
        
        # 3. Word count recommendations
        if scores['word_count'] < 0.7:
            if base_analysis['metrics']['word_count'] < 300:
                recommendations.append({
                    'category': 'Content',
                    'recommendation': "Your resume is too short. Add more relevant details about your experience and achievements.",
                    'priority': 'Medium'
                })
            elif base_analysis['metrics']['word_count'] > 1000:
                recommendations.append({
                    'category': 'Content',
                    'recommendation': "Your resume is too long. Trim it down to 1-2 pages focusing on the most relevant information.",
                    'priority': 'Medium'
                })
        
        # 4. Action verb recommendations
        if scores['action_verbs'] < 0.5:
            recommendations.append({
                'category': 'Language',
                'recommendation': "Use more strong action verbs like 'achieved', 'implemented', 'developed' to describe your accomplishments.",
                'priority': 'Medium'
            })
        
        # 5. File format recommendations
        if scores['file_format'] < 1.0:
            recommendations.append({
                'category': 'File Format',
                'recommendation': "Save your resume as a PDF to ensure consistent formatting when parsed by ATS.",
                'priority': 'High'
            })
        
        # 6. Contact info recommendations
        if not contact_info['complete']:
            missing = ', '.join(contact_info['missing'])
            recommendations.append({
                'category': 'Contact Information',
                'recommendation': f"Add missing contact information: {missing}.",
                'priority': 'High'
            })
        
        # 7. Education recommendations
        if not education_check['properly_formatted']:
            for issue in education_check['issues']:
                recommendations.append({
                    'category': 'Education',
                    'recommendation': f"Fix education section: {issue}.",
                    'priority': 'Medium'
                })
        
        # 8. Section recommendations
        missing_sections = [section for section, data in base_analysis['metrics']['sections'].items() 
                          if not data['present'] and section in ['experience', 'education', 'skills']]
        if missing_sections:
            for section in missing_sections:
                recommendations.append({
                    'category': 'Structure',
                    'recommendation': f"Add a {section.replace('_', ' ').title()} section - this is a standard section expected by ATS.",
                    'priority': 'High'
                })
        
        # 9. General ATS recommendations
        recommendations.append({
            'category': 'ATS Optimization',
            'recommendation': "Use a simple, clean layout with standard section headings like 'Experience', 'Education', and 'Skills'.",
            'priority': 'Medium'
        })
        
        # Sort by priority
        priority_order = {'High': 0, 'Medium': 1, 'Low': 2}
        recommendations.sort(key=lambda x: priority_order[x['priority']])
        
        return recommendations

# Example usage if this file is run directly
if __name__ == "__main__":
    analyzer = ATSScoreAnalyzer()
    result = analyzer.calculate_ats_score("example_resume.pdf", target_industry="software_development")
    
    print(f"ATS Score: {result['ats_score']}%")
    print("\nRecommendations:")
    for rec in result['recommendations']:
        print(f"[{rec['priority']}] {rec['category']}: {rec['recommendation']}")