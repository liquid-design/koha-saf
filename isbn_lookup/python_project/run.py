from app import create_app

app = create_app()

def lookup_isbn(isbn):
    """Gebruik dit vanuit Flask: haalt en merged API-data"""
    ol_data = fetch_openlibrary(isbn)
    gb_data = fetch_googlebooks(isbn)
    merged = merge_results(ol_data, gb_data)
    return merged

if __name__ == "__main__":
    # host 0.0.0.0 zodat je app bereikbaar is op http://<server-ip>:5000
    app.run(host="0.0.0.0", port=5000, debug=True)
