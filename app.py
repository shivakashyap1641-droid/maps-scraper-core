from flask import Flask, request, jsonify, render_template_string
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse

app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Live Maps & Web Lead Scraper</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; padding: 30px; }
        .box { max-width: 1000px; margin: auto; background: #1e293b; padding: 25px; border-radius: 8px; }
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
    <h2>Live Maps & Business Lead Scraper</h2>
    <p style="color: #94a3b8;">Format: <code>Keyword in City</code> (e.g. <b>Gyms in Ohio</b> ya <b>Roofing in Dallas</b>)</p>
    <div class="input-row">
        <input type="text" id="query" placeholder="e.g. Gyms in Ohio">
        <button id="btn" onclick="startScrape()">Extract Leads</button>
    </div>
    <div id="status">Scraping live data... Kripya intezar karein.</div>
    <table id="resultsTable" style="display:none;">
        <thead>
            <tr>
                <th>Business Name</th>
                <th>Website</th>
                <th>Snippet / Details</th>
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
                    <td>${site}</td>
                    <td>${lead.snippet}</td>
                </tr>`;
            });
        } else {
            alert('Data fetch nahi hua. Format simple rakhein jaise: Gyms in Ohio');
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

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # Live Search Engine Request
    search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    
    try:
        r = requests.post(search_url, headers=headers, timeout=12)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        leads = []
        for result in soup.find_all('div', class_='result'):
            title_tag = result.find('a', class_='result__a')
            snippet_tag = result.find('a', class_='result__snippet')
            
            if not title_tag:
                continue
                
            raw_url = title_tag.get('href', '')
            actual_url = raw_url
            if "uddg=" in raw_url:
                try:
                    actual_url = urllib.parse.unquote(raw_url.split("uddg=")[1].split("&")[0])
                except:
                    actual_url = raw_url

            # Social media / Wikipedia filter
            if any(x in actual_url for x in ['wikipedia.org', 'youtube.com', 'facebook.com', 'instagram.com']):
                continue

            name = title_tag.get_text(strip=True)
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else 'N/A'

            leads.append({
                "name": name,
                "website": actual_url,
                "snippet": snippet
            })
            
            if len(leads) >= 15:
                break

        return jsonify({"status": "success", "total": len(leads), "leads": leads})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
