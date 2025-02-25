from scholarly import scholarly
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

professor_urls = [
    "https://scholar.google.com/citations?user=W4lc9bUAAAAJ",  
    "https://scholar.google.com/citations?user=OGQm6cwAAAAJ"    
]


# Dictionary to store professor data
professor_data = {}

# Function to extract data from scholarly
def get_professor_basic_data(scholar_url):
    scholar_id = scholar_url.split("user=")[-1].split("&")[0]
    author = scholarly.search_author_id(scholar_id)
    author = scholarly.fill(author, sections=["basics", "indices"])  # Get basic details

    name = author.get("name", "Unknown")
    interests = ", ".join(author.get("interests", []))  # Convert list to string
    citedby = author.get("citedby", 0)

    return name, interests, citedby

# Function to scrape additional data (co-authors, h-index, i10-index)
def scrape_google_scholar_profile(profile_url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(profile_url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to retrieve {profile_url}")
            return set(), 0, 0

        soup = BeautifulSoup(response.text, "lxml")

        # Get h-index and i10-index
        indices = soup.find_all("td", class_="gsc_rsb_std")
        h_index = int(indices[2].text) if len(indices) > 2 else 0
        i10_index = int(indices[4].text) if len(indices) > 4 else 0

        # Get co-authors from publications
        coauthors_set = set()
        papers = soup.find_all("tr", class_="gsc_a_tr")

        for paper in papers:
            paper_authors = paper.find("div", class_="gs_gray")
            if paper_authors:
                authors_list = paper_authors.text.split(", ")
                coauthors_set.update(authors_list)

        return coauthors_set, h_index, i10_index

    except Exception as e:
        print(f"Error scraping {profile_url}: {e}")
        return set(), 0, 0

# Fetch data for all professors
for url in professor_urls:
    print(f"Processing: {url}")
    name, interests, citedby = get_professor_basic_data(url)
    coauthors, h_index, i10_index = scrape_google_scholar_profile(url)

    professor_data[name] = {
        "Interests": interests,
        "Citations": citedby,
        "H-Index": h_index,
        "i10-Index": i10_index,
        "Coauthors": list(coauthors)
    }

    time.sleep(3)  # To avoid rate limiting

# Convert to DataFrame
df = pd.DataFrame.from_dict(professor_data, orient="index")
print(df)

# Save to CSV
df.to_csv("nit_professor_citation_data.csv", index=True)
print("Data saved to nit_professor_citation_data.csv")