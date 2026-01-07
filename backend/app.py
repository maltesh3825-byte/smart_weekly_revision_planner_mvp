
import os
import json
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-pro")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


def build_summary_prompt(payload):
        chapter_text = payload.get('text') or ''
        prompt = f"""
You are an educational assistant creating a concise 30-minute revision summary for Class 8 students.

Input:
Subject: {payload.get('subject')}
Chapter: {payload.get('chapter')}
Pages covered: {payload.get('pages')}
Exam type: {payload.get('examType')}

Chapter Text:
{chapter_text}

Task:
Provide a clear, simple 30-minute revision summary suitable for a Class 8 student. Use 3-6 short bullet points or short paragraphs.

Return ONLY the summary as plain text (no JSON, no markdown, no extra commentary).
"""
        return prompt


def build_questions_prompt(payload):
    chapter_text = payload.get('text') or ''
    prompt = f"""Generate exactly 10 exam questions in JSON format from this text.

Text:
{chapter_text}

Return ONLY valid JSON. Be very strict with JSON formatting - all property names MUST be enclosed in double quotes. No unquoted keys.

{{"mcqs": [{{"question": "MCQ 1?", "options": ["A", "B", "C", "D"], "answer": 0}}, {{"question": "MCQ 2?", "options": ["A", "B", "C", "D"], "answer": 1}}, {{"question": "MCQ 3?", "options": ["A", "B", "C", "D"], "answer": 0}}, {{"question": "MCQ 4?", "options": ["A", "B", "C", "D"], "answer": 2}}, {{"question": "MCQ 5?", "options": ["A", "B", "C", "D"], "answer": 1}}, {{"question": "MCQ 6?", "options": ["A", "B", "C", "D"], "answer": 3}}], "short_questions": [{{"question": "Short answer 1?", "answer": "Sample answer"}}, {{"question": "Short answer 2?", "answer": "Sample answer"}}], "long_questions": [{{"question": "Essay question 1?", "answer": "Long sample answer"}}, {{"question": "Essay question 2?", "answer": "Long sample answer"}}]}}
"""
    return prompt


def call_gemini(prompt):
    # Call Google Generative AI (Gemini) using the official SDK
    if not GEMINI_API_KEY:
        raise RuntimeError("Missing GEMINI_API_KEY")

    try:
        model = genai.GenerativeModel(GEMINI_MODEL)  # Use model from env or default
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=3000,
            )
        )
        if response.text:
            return response.text
        else:
            raise RuntimeError("Gemini returned empty response")
    except Exception as e:
        print(f"[ERROR] Gemini API call failed: {str(e)}")
        raise RuntimeError(f"Gemini API error: {str(e)}")


@app.route('/list-models', methods=['GET'])
def list_models():
    """Utility route to list models available to the configured API key.
    Use this to discover which models and methods your key supports.
    """
    if not GEMINI_API_KEY:
        return jsonify({"error": "Missing GEMINI_API_KEY in environment"}), 400
    try:
        models = genai.list_models()
        # Return a compact list of model ids and supported methods if present
        simplified = []
        for m in models.get('models', models) if isinstance(models, dict) else models:
            try:
                mid = m.get('name') or m.get('id') or str(m)
            except Exception:
                mid = str(m)
            simplified.append(mid)
        return jsonify({"models": simplified})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def dummy_response(payload):
    # Provide a friendly dummy response when no Gemini key is present.
    chapter_text = payload.get('text') or ''
    intro = f"Quick 30-min revision for {payload.get('subject')} - {payload.get('chapter')}:\n"
    if chapter_text:
        # Show the first 400 characters of pasted text in the dummy summary to indicate processing
        excerpt = chapter_text.strip()[:400]
        summary = intro + "Based on pasted chapter text:\n" + excerpt + "\n\nStudy tips:\n1) Highlight main concepts.\n2) Make flashcards for key terms.\n3) Solve example problems.\n4) Quick recap."
    else:
        summary = (
            intro +
            "1) Skim pages covered and highlight main concepts.\n"
            "2) Create 5 flashcards for key terms.\n"
            "3) Solve 2 practice problems from the chapter.\n"
            "4) Quick recap and formula list."
        )

    mcqs = [
        {"question": f"Sample MCQ {i+1} for {payload.get('chapter')}", "options": ["A","B","C","D"], "answer": 0}
        for i in range(6)
    ]
    short_questions = [
        {"question": f"Sample short question {i+1} on {payload.get('chapter')}", "answer": "Short answer here."}
        for i in range(2)
    ]
    long_questions = [
        {"question": f"Sample long question {i+1} on {payload.get('chapter')}", "answer": "Long answer paragraph here."}
        for i in range(2)
    ]
    return {"summary": summary, "mcqs": mcqs, "short_questions": short_questions, "long_questions": long_questions}


def extract_json_from_text(text: str):
    """Attempt to extract the first balanced JSON object from a raw text string.
    This handles stray text before/after the JSON and tries to ignore braces inside strings.
    Returns the JSON string if found, otherwise None.
    """
    if not text or '{' not in text:
        return None

    start = text.find('{')
    i = start
    depth = 0
    in_str = False
    escape = False

    while i < len(text):
        ch = text[i]
        if in_str:
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    # return substring from first '{' to this '}' inclusive
                    return text[start:i+1]
        i += 1

    return None


def escape_invalid_json_escapes(s: str):
    """Escape backslashes that introduce invalid JSON escape sequences.
    Converts single backslashes followed by non-standard escape chars into escaped backslashes.
    Example: "\\(2Mg" -> "\\\\(2Mg" so JSON parser sees a literal backslash.
    """
    if not s:
        return s
    # Replace a single backslash not followed by valid JSON escape characters with a double backslash
    try:
        return re.sub(r'\\(?![\"\\/bfnrtu])', lambda m: "\\\\", s)
    except Exception:
        return s


def repair_json_string(s: str):
    """Attempt common repairs on a malformed JSON string to make it parseable.
    Returns repaired string or None if no reasonable repair possible.
    """
    if not s:
        return None

    candidate = s.strip()
    
    # 0) Remove markdown code block markers
    if candidate.startswith('```json'):
        candidate = candidate[7:].strip()
    elif candidate.startswith('```'):
        candidate = candidate[3:].strip()
    if candidate.endswith('```'):
        candidate = candidate[:-3].strip()

    # 1) Trim to first {...} block if present
    j = extract_json_from_text(candidate)
    if j:
        candidate = j

    # 2) Replace smart quotes with straight quotes
    candidate = candidate.replace('\u201c', '"').replace('\u201d', '"')
    candidate = candidate.replace('\u2018', "'").replace('\u2019', "'")

    # 3) Close any unterminated strings by tracking quote state
    # This handles truncated JSON where a string is left open
    in_str = False
    escape_next = False
    fixed = []
    
    for i, ch in enumerate(candidate):
        if escape_next:
            fixed.append(ch)
            escape_next = False
        elif ch == '\\':
            fixed.append(ch)
            escape_next = True
        elif ch == '"':
            in_str = not in_str
            fixed.append(ch)
        elif in_str and ch in '\n\r\t':
            fixed.append(' ')  # Replace newlines/tabs with spaces inside strings
        else:
            fixed.append(ch)
    
    candidate = ''.join(fixed)
    
    # 4) If we end with an unclosed string, close it
    if in_str:
        candidate = candidate + '"'
        print(f"[DEBUG] Closed unterminated string")

    # 5) Remove trailing commas and incomplete key-value pairs
    candidate = re.sub(r':\s*$', ': ""', candidate)  # "key": at EOF -> "key": ""
    candidate = re.sub(r',\s*$', '', candidate)  # Trailing comma at EOF

    # 6) Remove trailing commas before } or ]
    candidate = re.sub(r',\s*([}\]])', r'\1', candidate)

    # 7) Quote unquoted keys
    candidate = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', candidate)
    
    # 8) Quote unquoted string values
    candidate = re.sub(r':\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*([,}\]])', r': "\1"\2', candidate)

    # 9) Close truncated/incomplete JSON by counting open structures
    open_braces = 0
    open_brackets = 0
    in_str = False
    escape_next = False
    
    for ch in candidate:
        if escape_next:
            escape_next = False
        elif ch == '\\':
            escape_next = True
        elif ch == '"':
            in_str = not in_str
        elif not in_str:
            if ch == '{':
                open_braces += 1
            elif ch == '}':
                open_braces -= 1
            elif ch == '[':
                open_brackets += 1
            elif ch == ']':
                open_brackets -= 1
    
    print(f"[DEBUG] Before closing: open_braces={open_braces}, open_brackets={open_brackets}")
    
    # Add closing brackets and braces in correct order
    if open_brackets > 0:
        candidate = candidate + (']' * open_brackets)
    if open_braces > 0:
        candidate = candidate + ('}' * open_braces)
    
    if open_braces > 0 or open_brackets > 0:
        print(f"[DEBUG] Closed with {open_braces} braces and {open_brackets} brackets")

    # 10) Final cleanup
    candidate = re.sub(r',(\s*,+)', r'\1', candidate)  # Remove duplicate commas
    candidate = re.sub(r',(\s*[}\]])', r'\1', candidate)  # Remove trailing commas again
    
    # Validate
    try:
        parsed = json.loads(candidate)
        print(f"[DEBUG] ✓ Repair successful!")
        return candidate
    except json.JSONDecodeError as e:
        print(f"[DEBUG] Repair still fails: {e}")
        return None


@app.route("/generate-revision", methods=["POST"])
def generate_revision():
    data = request.get_json() or {}
    subject = data.get("subject")
    chapter = data.get("chapter")
    pages = data.get("pages")
    examType = data.get("examType")
    text = data.get("text")
    mode = data.get("mode", "summary")

    payload = {"subject": subject, "chapter": chapter, "pages": pages, "examType": examType, "text": text}
    # Choose prompt based on requested mode
    try:
        if mode == 'summary':
            # Request only a plain-text summary
            prompt = build_summary_prompt(payload)
            if GEMINI_API_KEY:
                print(f"[INFO] Calling Gemini for SUMMARY subject={subject}, chapter={chapter}")
                try:
                    raw = call_gemini(prompt)
                    print(f"[INFO] Gemini raw summary length: {len(raw)}")
                    # raw is expected to be plain text summary
                    result = {"summary": raw, "mcqs": [], "short_questions": [], "long_questions": []}
                except Exception as e:
                    print(f"[WARN] Gemini API failed for summary: {e}, using dummy")
                    d = dummy_response(payload)
                    result = {"summary": d.get('summary',''), "mcqs": [], "short_questions": [], "long_questions": []}
            else:
                print("[INFO] No GEMINI_API_KEY, using dummy summary")
                d = dummy_response(payload)
                result = {"summary": d.get('summary',''), "mcqs": [], "short_questions": [], "long_questions": []}
        elif mode == 'questions':
            prompt = build_questions_prompt(payload)
            if GEMINI_API_KEY:
                print(f"[INFO] Calling Gemini for QUESTIONS subject={subject}, chapter={chapter}")
                raw = call_gemini(prompt)
                print(f"[INFO] Gemini raw response length: {len(raw)}")
                print(f"[DEBUG] Raw response (first 500 chars): {raw[:500]}")
                
                # Attempt to parse JSON from raw
                parsed = None
                
                # Strategy 1: Extract from code blocks FIRST
                if "```json" in raw or "```" in raw:
                    try:
                        # Extract content between ```json and ```
                        if "```json" in raw:
                            json_str = raw.split("```json")[1].split("```")[0].strip()
                        else:
                            json_str = raw.split("```")[1].split("```")[0].strip()

                        print(f"[DEBUG] Extracted from code block (len={len(json_str)})")
                        # Escape invalid backslash sequences before parsing
                        json_str_fixed = escape_invalid_json_escapes(json_str)
                        parsed = json.loads(json_str_fixed)
                        print("[INFO] ✓ Successfully parsed JSON from code block")
                    except json.JSONDecodeError as e:
                        print(f"[WARN] Code-block JSON parse failed: {e}")
                        # Try to repair the extracted string (use escaped version first)
                        repaired = repair_json_string(json_str_fixed if 'json_str_fixed' in locals() else json_str)
                        if repaired:
                            try:
                                repaired_fixed = escape_invalid_json_escapes(repaired)
                                parsed = json.loads(repaired_fixed)
                                print("[INFO] ✓ Successfully repaired code-block JSON")
                            except Exception as e2:
                                print(f"[WARN] Repair of code-block JSON failed: {e2}")
                
                # Strategy 2: Direct parse
                if parsed is None:
                    try:
                        raw_fixed = escape_invalid_json_escapes(raw)
                        parsed = json.loads(raw_fixed)
                        print("[INFO] ✓ Parsed questions JSON directly")
                    except json.JSONDecodeError as e:
                        print(f"[WARN] Direct JSON parse failed: {e}")
                
                # Strategy 3: Balanced extraction
                if parsed is None:
                    json_str = extract_json_from_text(raw)
                    if json_str:
                        try:
                            json_str_fixed = escape_invalid_json_escapes(json_str)
                            parsed = json.loads(json_str_fixed)
                            print("[INFO] ✓ Extracted and parsed balanced JSON")
                        except Exception as e:
                            print(f"[WARN] Failed to parse extracted JSON: {e}")
                            # Try repair
                            repaired = repair_json_string(json_str_fixed if 'json_str_fixed' in locals() else json_str)
                            if repaired:
                                try:
                                    repaired_fixed = escape_invalid_json_escapes(repaired)
                                    parsed = json.loads(repaired_fixed)
                                    print("[INFO] ✓ Successfully repaired extracted JSON")
                                except Exception as e2:
                                    print(f"[WARN] Repair of extracted JSON failed: {e2}")
                
                # Strategy 4: Repair raw response
                if parsed is None:
                    # Try escaping invalid escapes in raw first
                    raw_fixed = escape_invalid_json_escapes(raw)
                    repaired = repair_json_string(raw_fixed)
                    if repaired:
                        try:
                            repaired_fixed = escape_invalid_json_escapes(repaired)
                            parsed = json.loads(repaired_fixed)
                            print("[INFO] ✓ Successfully repaired raw response JSON")
                        except Exception as e:
                            print(f"[WARN] Repair of raw response failed: {e}")
                
                # Fallback if all parsing failed
                if parsed is None:
                    print(f"[WARN] All parsing attempts failed; using dummy questions")
                    print(f"[DEBUG] Raw response (full): {raw}")
                    d = dummy_response(payload)
                    parsed = {"mcqs": d['mcqs'], "short_questions": d['short_questions'], "long_questions": d['long_questions']}
                
                # Ensure keys
                result = {
                    "summary": "",
                    "mcqs": parsed.get('mcqs', parsed.get('mcq', [])),
                    "short_questions": parsed.get('short_questions', parsed.get('short_questions', [])),
                    "long_questions": parsed.get('long_questions', parsed.get('long_questions', []))
                }
            else:
                print("[INFO] No GEMINI_API_KEY, using dummy questions")
                # dummy_response contains both summary and questions; return only questions
                d = dummy_response(payload)
                result = {"summary": "", "mcqs": d['mcqs'], "short_questions": d['short_questions'], "long_questions": d['long_questions']}
        else:
            # default: full mode (summary + questions in one response)
            prompt = build_questions_prompt(payload)  # reuse questions prompt but include summary field in parsing
            if GEMINI_API_KEY:
                raw = call_gemini(prompt)
                # attempt to parse as JSON then fallback
                try:
                    parsed = json.loads(raw)
                except Exception:
                    json_str = extract_json_from_text(raw)
                    parsed = json.loads(json_str) if json_str else {"summary": raw}
                result = parsed
            else:
                result = dummy_response(payload)

        # Ensure result has required keys
        for k in ["summary", "mcqs", "short_questions", "long_questions"]:
            if k not in result:
                result[k] = [] if k != "summary" else ""

        return jsonify(result)

    except RuntimeError as e:
        error_msg = str(e)
        print(f"[ERROR] RuntimeError: {error_msg}")
        return jsonify({"error": "Gemini API error", "details": error_msg}), 502
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] Unexpected error: {error_msg}")
        return jsonify({"error": "Server error", "details": error_msg}), 500


if __name__ == "__main__":
    # Use the PORT environment variable provided by hosting platforms (e.g., Railway)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)


@app.route("/", methods=["GET"]) 
def index():
    return jsonify({"status": "ok", "message": "Revision backend is running"}), 200
