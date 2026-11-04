from flask import Flask, request, jsonify, render_template_string
import requests

app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Instant Maps Lead Scraper</title>
    <style>
        body { font-family: sans-serif; background: #0f172a; color: #f8fafc; padding: 30px; }
        .box { max-width: 900px; margin: auto; background: #1e293b; padding: 25px; border-radius: 8px; }
        h2 { color: #38bdf8; margin-top: 0; }
        .input-row { display: flex; gap: 10px; margin: 20px 0; }
        input { flex: 1; padding: 12px; border-radius: 6px; border: 1px solid #334155; background: #0f172a; color: #fff; font-size: 15px; }
        button { background: #0284c7; color: white; border: none; padding: 12px 24px; border-radius: 6px; font-weight: bold; cursor: pointer; }
        button:disabled { opacity: 0.5; }
        table { width: 100%; border-collapse: collapse; margin-top: 25px; }
        th, td { padding: 12px; border-bottom: 1px solid #334155; text-align: left; font-size: 14px; }
        th { background: #0f172a; color: #94a3b8; }
        a { color: #38bdf8; text-decoration: none; }
        #status { margin-top: 15px; color: #38bdf8; display: none; }
    </style>
</head>
<body>
<div class="box">
    <h2>Instant Maps Lead Scraper</h2>
    <p style="color: #94a3b8;">Location aur business type dalein (e.g. <i>dentists in Dallas</i>)</p>
    <div class="input-row">
        <input type="text" id="query" placeholder="Enter keyword and city...">
        <button id="btn" onclick="startScrape()">Extract Leads</button>
    </div>
    <div id="status">Scraping live places data... Kripya intezar karein.</div>
    <table id="resultsTable" style="display:none;">
        <thead>
            <tr>
                <th>Business Name</th>
                <th>Phone</th>
                <th>Website</th>
                <th>Full Address</th>
            </tr>
        </thead>
        <tbody id="tableBody"></tbody>
    </table>
</div>

<script>
async function startScrape() {
    const q = document.getElementById('query').value.trim();
    if (!q) return alert('Keyword enter karein');
    
    const btn = document.getElementById('btn');
    const status = document.getElementById('status');
    const table = document.getElementById('resultsTable');
    const tbody = document.getElementById('tableBody');

    btn.disabled = true;
    status.style.display = 'block';
    table.style.display = 'none';
    tbody.innerHTML = '';

    try {
        const res = await fetch('/api/scrape?query=' + encodeURIComponent(q));
        const data = await res.json();
        
        status.style.display = 'none';
        btn.disabled = false;

        if (data.status === 'success' && data.leads.length > 0) {
            table.style.display = 'table';
            data.leads.forEach(lead => {
                const site = lead.website !== 'N/A' ? `<a href="${lead.website}" target="_blank">${lead.website}</a>` : 'N/A';
                tbody.innerHTML += `<tr>
                    <td><b>${lead.name}</b></td>
                    <td>${lead.phone}</td>
                    <td>${site}</td>
                    <td>${lead.address}</td>
                </tr>`;
            });
        } else {
            alert('Koi leads nahi mili. Doosra keyword try karein.');
        }
    } catch (err) {
        status.style.display = 'none';
        btn.disabled = false;
        alert('Extraction failed: ' + err.message);
    }
}
</script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/api/scrape', methods=['GET'])
def scrape():
    query = request.args.get('query', '')
    if not query:
        return jsonify({"status": "error", "message": "Query missing"}), 400

    url = f"https://nominatim.openstreetmap.org/search?format=json&q={query}&addressdetails=1&extratags=1&limit=20"
    headers = {"User-Agent": "LeadPipelineScraper/1.0"}
    
    try:
        r = requests.get(url, headers=headers, timeout=10)
        items = r.json()
        leads = []
        for item in items:
            name = item.get('display_name', '').split(',')[0]
            extratags = item.get('extratags', {})
            website = extratags.get('website', extratags.get('contact:website', 'N/A'))
            phone = extratags.get('phone', extratags.get('contact:phone', 'N/A'))
            
            leads.append({
                "name": name,
                "phone": phone,
                "website": website,
                "address": item.get('display_name', '')
            })
        return jsonify({"status": "success", "total": len(leads), "leads": leads})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
