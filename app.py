from flask import Flask, request, jsonify
import os
import tempfile
from resume_analyzer import ResumeAnalyzer

app = Flask(__name__)
analyzer = ResumeAnalyzer()

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "online",
        "message": "Resume Analyzer API is running",
        "endpoints": {
            "analyze": "/analyze - POST request with 'resume' file and optional 'target_industry'"
        }
    })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})

@app.route('/analyze', methods=['POST'])
def analyze_resume():
    # Check if request has the file part
    if 'resume' not in request.files:
        return jsonify({"error": "No resume file provided"}), 400
    
    file = request.files['resume']
    
    # If user does not select file, browser might submit an empty file
    if file.filename == '':
        return jsonify({"error": "No resume file selected"}), 400
    
    # Get target industry if provided
    target_industry = request.form.get('target_industry', None)
    
    try:
        # Save the uploaded file temporarily
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, file.filename)
        file.save(temp_file_path)
        
        # Analyze the resume
        analysis = analyzer.analyze_resume(temp_file_path, target_industry)
        
        # Generate API response
        response = analyzer.generate_api_response(analysis)
        
        # Clean up the temp file
        os.remove(temp_file_path)
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)