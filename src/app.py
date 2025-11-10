"""
Flask app using LangGraph for contract analysis
"""
import os
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import pdfplumber
from datetime import date
import re
from werkzeug.security import check_password_hash

# Import the LangGraph workflow
from graph.legal_graph import run_legal_analysis

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or "dev-secret-key-change-in-production"

# Load hashed password
APP_PASSWORD_HASH = os.getenv("APP_PASSWORD_HASH")
if not APP_PASSWORD_HASH:
    raise RuntimeError("APP_PASSWORD_HASH is not set in the environment.")

# -------------------------
# Session Configuration
# -------------------------
@app.before_request
def before_request():
    """Initialize session with default values"""
    if 'mode' not in session:
        session['mode'] = 'legal'
    session.modified = True

# -------------------------
# Helper Functions
# -------------------------

# -------------------------
# Authentication
# -------------------------
def login_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login", next=request.path))
        return fn(*args, **kwargs)
    return wrapper

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if check_password_hash(APP_PASSWORD_HASH, password):
            session.clear()
            session["logged_in"] = True
            session["mode"] = "legal"
            next_url = request.args.get("next") or url_for("index")
            return redirect(next_url)
        else:
            return render_template("login.html", error="Invalid password"), 403
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# -------------------------
# Protected Routes
# -------------------------
@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/set_mode/<mode>", methods=["POST"])
@login_required
def set_mode(mode):
    if mode not in ["legal", "creator"]:
        return jsonify({"success": False, "message": "Invalid mode"}), 400
    session["mode"] = mode
    session.modified = True
    print(f"🔄 Switched mode to: {mode}")
    return jsonify({"success": True, "mode": mode})

@app.route("/get_mode", methods=["GET"])
@login_required
def get_mode():
    return jsonify({"mode": session.get("mode", "legal")})

@app.route("/upload", methods=["POST"])
@login_required
def upload():
    """Handle contract upload and analysis using LangGraph"""
    mode = session.get("mode", "legal")
    contract_file = request.files.get("contract")
    user_email = request.form.get("user_email")
    
    if not contract_file or not user_email:
        return jsonify({"success": False, "message": "Missing file or email"}), 400
    
    try:
        # Extract text from PDF
        with pdfplumber.open(contract_file.stream) as pdf:
            contract_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        
        # Determine which mode to use
        analysis_mode = "creator" if mode == "creator" else "legal"
        print(f"🔍 Running {analysis_mode} mode analysis")
        
        # Run the LangGraph workflow
        final_state = run_legal_analysis(
            contract_text=contract_text,
            user_email=user_email,
            mode=analysis_mode
        )
        
        # Log extracted company name
        company_name = final_state.get("company_name", "Unknown")
        extraction_method = final_state.get("company_extraction_method", "unknown")
        print(f"🏢 Company: {company_name} (method: {extraction_method})")
        
        # Check for errors
        if final_state.get("error"):
            return jsonify({
                "success": False,
                "message": f"Analysis error: {final_state['error']}"
            }), 500
        
        # Build success message
        notification_results = final_state.get("notification_results", [])
        message = f"Contract processed! Check your email ({user_email})."
        
        # Add calendar info if available
        calendar_results = [r for r in notification_results if "Calendar" in r or "📅" in r]
        if calendar_results:
            message += f" {calendar_results[0]}"
        
        print("✅ Analysis completed successfully")
        return jsonify({"success": True, "message": message})
        
    except Exception as e:
        print(f"❌ Error in upload: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Processing error: {str(e)}"
        }), 500


if __name__ == "__main__":
    app.run(debug=True)


# if __name__ == "__main__":
#     port = int(os.environ.get("PORT", 5000))
#     app.run(host="0.0.0.0", port=port)