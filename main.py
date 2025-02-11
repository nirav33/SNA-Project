import csv
from scholarly import scholarly

def fetch_citation_data(scholar_ids, output_file):
    """
    Fetch citation data for a list of Google Scholar IDs and save it to a CSV file.
    
    Args:
        scholar_ids (list): List of Google Scholar IDs.
        output_file (str): Path to the output CSV file.
    """
    data = []

    for scholar_id in scholar_ids:
        print(f"Fetching data for Google Scholar ID: {scholar_id}")
        try:
            # Fetch author profile
            author = scholarly.search_author_id(scholar_id)
            scholarly.fill(author)
            
            # Extract relevant data
            author_data = {
                "Name": author.get("name", ""),
                "Affiliation": author.get("affiliation", ""),
                "Citations": author.get("citedby", 0),
                "H-Index": author.get("hindex", 0),
                "i10-Index": author.get("i10index", 0),
                "ID": scholar_id
            }
            data.append(author_data)
        except Exception as e:
            print(f"Error fetching data for {scholar_id}: {e}")
    
    # Write data to CSV
    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["ID", "Name", "Affiliation", "Citations", "H-Index", "i10-Index"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    print(f"Data saved to {output_file}")

# Example usage
scholar_ids = ["YOUR_GOOGLE_SCHOLAR_ID1", "YOUR_GOOGLE_SCHOLAR_ID2"]  # Replace with actual IDs
output_file = "google_scholar_data.csv"
fetch_citation_data(scholar_ids, output_file)
