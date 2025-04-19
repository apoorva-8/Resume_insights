# app.py
from flask import Flask, request, jsonify, render_template
import os
import tempfile
from werkzeug.utils import secure_filename
from resume_analyzer import ResumeAnalyzer
from ats_analyzer import ATSScoreAnalyzer
from flask_cors import CORS

# Allow only the specific frontend origin

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
CORS(app, resources={r"/*": {"origins": [
    "https://campusconnectkrmu.onrender.com",
    "http://localhost:5173",
    "http://127.0.0.1:5500"  
]}})

# Ensure upload directory exists
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_resume():
    if 'resume' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed, please upload a PDF'}), 400
    
    target_industry = request.form.get('industry', None)
    job_description = request.form.get('job_description', None)
    
    # Save file to temporary location
    temp_dir = tempfile.mkdtemp()
    filename = secure_filename(file.filename)
    filepath = os.path.join(temp_dir, filename)
    file.save(filepath)
    
    try:
        # Initialize analyzers
        resume_analyzer = ResumeAnalyzer()
        ats_analyzer = ATSScoreAnalyzer()
        
        # Get ATS score and recommendations
        ats_result = ats_analyzer.calculate_ats_score(
            filepath, 
            job_description=job_description,
            target_industry=target_industry
        )
        
        # Format response
        response = {
            "success": True,
            "ats_score": ats_result['ats_score'],
            "recommendations": ats_result['recommendations'],
            "metrics": {
                "wordCount": ats_result['base_analysis']['metrics']['word_count'],
                "actionVerbCount": ats_result['base_analysis']['metrics']['action_verbs']['count'],
                "weakPhraseCount": ats_result['base_analysis']['metrics']['weak_phrases']['count'],
                "sectionsFound": ats_result['base_analysis']['sections_found'],
                "formattingIssues": ats_result['formatting_issues']
            },
            "keywordAnalysis": {
                "industryKeywords": ats_result['base_analysis']['industry_keywords']
            },
            "factorScores": ats_result['factor_scores']
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # Clean up temp file
        try:
            os.remove(filepath)
            os.rmdir(temp_dir)
        except:
            pass

@app.route('/health')
def health_check():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)


