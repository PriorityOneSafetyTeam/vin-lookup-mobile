import os
import requests
from flask import Flask, request, jsonify, render_template_string, send_from_directory

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>POST Vehicle Inquiry Service</title>
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#1e40af">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #f1f5f9; color: #0f172a; margin: 0; padding: 20px; }
        .card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); max-width: 500px; margin: 0 auto; }
        h2 { margin-top: 0; color: #1e40af; font-size: 22px; }
        label { font-weight: bold; color: #475569; font-size: 14px; display: block; margin-bottom: 6px; }
        input { width: 100%; padding: 12px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 16px; box-sizing: border-box; text-transform: uppercase; margin-bottom: 16px; }
        .btn-row { display: flex; gap: 10px; }
        button { flex: 1; padding: 12px; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; }
        .btn-search { background-color: #1e40af; color: white; }
        .btn-clear { background-color: #e2e8f0; color: #475569; }
        .results { margin-top: 20px; border-top: 1px solid #e2e8f0; padding-top: 15px; }
        .section-title { font-weight: bold; color: #1e40af; margin: 10px 0; }
        .data-row { display: flex; margin-bottom: 6px; font-size: 15px; }
        .data-key { font-weight: bold; color: #475569; width: 150px; flex-shrink: 0; }
        .data-val { color: black; }
        .debug-box { margin-top: 15px; background: #f8fafc; border: 1px solid #e2e8f0; padding: 10px; border-radius: 6px; font-family: monospace; font-size: 11px; white-space: pre-wrap; color: #dc2626; max-height: 150px; overflow-y: auto; }
    </style>
</head>
<body>
<div class="card">
    <h2>POST Vehicle Inquiry</h2>
    <label for="vin">Enter 17-Digit VIN Number:</label>
    <input type="text" id="vin" maxlength="17" placeholder="17 ALPHANUMERIC CHARACTERS">
    <div class="btn-row">
        <button class="btn-search" onclick="lookupVin()">Search Database</button>
        <button class="btn-clear" onclick="clearAll()">Clear</button>
    </div>
    <div class="results" id="output">
        <p style="text-align:center; font-style:italic; color:#475569;">Please enter a vehicle VIN above to query technical specification data.</p>
    </div>
</div>

<script>
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js').catch(err => console.log("PWA init"));
    });
}

function clearAll() {
    document.getElementById('vin').value = '';
    document.getElementById('output').innerHTML = '<p style="text-align:center; font-style:italic; color:#475569;">Please enter a vehicle VIN above to query technical specification data.</p>';
}

async function lookupVin() {
    const vinInput = document.getElementById('vin').value.trim().toUpperCase();
    const output = document.getElementById('output');
    if (vinInput.length !== 17) { alert("Invalid VIN Length: A standard VIN must be exactly 17 characters."); return; }
    output.innerHTML = '<p style="text-align:center; color:#1e40af; font-weight:bold;">Connecting to server...</p>';
    
    try {
        const response = await fetch(`/api/lookup?vin=${vinInput}`);
        const data = await response.json();
        
        if (data.error) { 
            // In case of a backend mapping issue, this exposes the inner system log tracking notes on your screen
            let errHtml = `<p style="text-align:center; color:#dc2626; font-weight:bold;">${data.error}</p>`;
            if(data.details) {
                errHtml += `<div class="section-title">Diagnostic Trace:</div><div class="debug-box">${data.details}</div>`;
            }
            output.innerHTML = errHtml; 
            return; 
        }
        
        let html = '<div class="section-title">Core Identity Overview</div>';
        const primary = ["ModelYear", "Make", "Model", "Trim", "BodyClass"];
        primary.forEach(metric => {
            if (data[metric]) {
                let displayKey = metric.replace(/([A-Z])/g, ' \$1').trim();
                html += `<div class="data-row"><div class="data-key">${displayKey}:</div><div class="data-val">${data[metric]}</div></div>`;
                delete data[metric];
            }
        });

        html += '<div class="section-title" style="margin-top:15px;">Additional Engine Specs</div>';
        for (const [key, val] of Object.entries(data)) {
            let displayKey = key.replace(/([A-Z])/g, ' \$1').trim();
            html += `<div class="data-row"><div class="data-key">${displayKey}:</div><div class="data-val">${val}</div></div>`;
        }
        output.innerHTML = html;
    } catch (e) {
        output.innerHTML = `<p style="text-align:center; color:#dc2626; font-weight:bold;">Connection Error: Server layout processing fault.</p>`;
    }
}
</script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory(os.getcwd(), 'manifest.json')

@app.route('/sw.js')
def serve_sw():
    return send_from_directory(os.getcwd(), 'sw.js')

@app.route('/api/lookup')
def lookup():
    vin = request.args.get('vin', '').strip().upper()
    if len(vin) != 17:
        return jsonify({"error": "VIN must be exactly 17 characters."}), 400
    
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/{vin}?format=json"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=12)
        raw_json = res.json()
        
        # Core fix: Secure extraction of index 0 from the returned list object mapping array wrapper
        results_list = raw_json.get('Results', [])
        results = results_list[0] if (results_list and len(results_list) > 0) else None
        
        if not results or results.get("ErrorCode") == "1":
            return jsonify({"error": "No vehicle database records match this VIN number."}), 404
            
        clean_data = {}
        for key, val in results.items():
            if val and str(val).strip() and str(val).lower().strip() not in ["not applicable", "none", "null", "0"]:
                clean_data[key] = str(val).strip()
        return jsonify(clean_data)
    except Exception as e:
        # If an upstream structure change occurs, this tracks and reflects it safely on your phone interface
        return jsonify({
            "error": "Failed to map government database parameters.",
            "details": str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
