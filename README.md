# Idaho Sex Offender Registry Scraper

A Python web scraper that extracts public information from the Idaho Sex Offender Registry (SOR) database for Bonner County. This tool downloads offender data, photos, and detailed information, organizing everything into a structured JSON format.

## Features

- 📊 **Complete Data Extraction**: Scrapes all offender information including names, addresses, KNO numbers, and compliance status
- 🖼️ **Image Downloading**: Automatically downloads full-resolution offender photos
- 📄 **Detailed Records**: Visits each offender's profile page to extract:
  - Complete identification information
  - Criminal offense descriptions, dates, and locations
- 🔄 **Automatic Pagination**: Processes all pages of results automatically
- 💾 **JSON Export**: Saves all data in a well-structured JSON format
- ⏱️ **Rate Limiting**: Includes respectful delays between requests to avoid overwhelming the server

## Requirements

- Python 3.6+
- `requests` library
- `beautifulsoup4` library

## Installation

1. Clone this repository or download the script:
```bash
git clone <repository-url>
cd idaho-sor-scraper
```

2. Install required dependencies:
```bash
pip install requests beautifulsoup4
```

Or use the requirements file:
```bash
pip install -r requirements.txt
```

## Usage

Run the scraper:
```bash
python scraper.py
```

The script will:
1. Connect to the Idaho SOR database
2. Submit a POST request for Bonner County offenders
3. Parse each page of results
4. Download offender photos
5. Visit each offender's detail page for additional information
6. Save everything to `idaho_sex_offenders.json`

## Output

### JSON File Structure

The script generates `idaho_sex_offenders.json` with the following structure:

```json
[
  {
    "name": "DOE, JOHN MICHAEL",
    "kno": "8001234",
    "address": "123 MAIN ST",
    "city": "SANDPOINT",
    "county": "BONNER",
    "zip": "83864",
    "status": "COMPLIANT",
    "profile_url": "https://apps.isp.idaho.gov/sor_id/SOR?id=12345&sz=2814",
    "image_url": "https://apps.isp.idaho.gov/sorFiles/photos/DOEJ_8001234_01-01-2024.jpg",
    "local_image_path": "offender_images/8001234_DOE_JOHN_MICHAEL.jpg",
    "identification": {
      "Height": "6'2\"",
      "Weight": "200",
      "Hair Color": "BROWN",
      "Eye Color": "BLUE",
      "Race": "WHITE",
      "Sex": "MALE",
      "Date of Birth": "01/01/1980"
    },
    "offenses": [
      {
        "description": "LEWD CONDUCT WITH A MINOR",
        "date": "03/15/2015",
        "location": "BONNER COUNTY, ID"
      }
    ]
  }
]
```

### Directory Structure

```
.
├── scraper.py
├── idaho_sex_offenders.json
├── offender_images/
│   ├── 8001234_DOE_JOHN_MICHAEL.jpg
│   ├── 8001235_SMITH_JAMES_LEE.jpg
│   └── ...
└── README.md
```

## Configuration

You can modify the search parameters in the `make_post_request()` method:

```python
data = {
    'cnt': 'BONNER',     # County name
    'rad': 'A',          # Radius (A = All)
    'sz': '2814',        # Size parameter
    'form': '4'          # Form type
}
```

To scrape a different county, change the `cnt` parameter to another Idaho county name (e.g., 'ADA', 'KOOTENAI', etc.).

## Data Fields

### Basic Information
- **name**: Full legal name of the offender
- **kno**: Idaho offender identification number
- **address**: Street address
- **city**: City of residence
- **county**: County of residence
- **zip**: ZIP code
- **status**: Compliance status (COMPLIANT, NON COMP, etc.)

### Additional Fields
- **profile_url**: Direct link to the offender's detail page
- **image_url**: URL of the full-resolution photo
- **local_image_path**: Path to downloaded image file

### Identification Details
Physical characteristics and biographical information extracted from the offender's detail page.

### Offenses
Array of criminal offenses including:
- **description**: Type of offense
- **date**: Date of conviction/offense
- **location**: Location where offense occurred

## Rate Limiting & Ethics

This scraper includes built-in delays:
- 0.5 seconds between detail page requests
- 1 second between pagination requests

**Important Notes:**
- This tool accesses **publicly available** information only
- The data is already published by Idaho State Police
- Please use responsibly and in accordance with local laws
- Do not use for harassment, discrimination, or illegal purposes
- Respect the server by not removing rate limiting

## Legal Disclaimer

This tool is provided for informational and research purposes only. The data scraped is publicly available from the Idaho Sex Offender Registry maintained by Idaho State Police. 

**Users are responsible for:**
- Complying with all applicable federal, state, and local laws
- Using the data ethically and legally
- Not using the data for harassment, discrimination, or any illegal purpose
- Respecting the terms of service of the Idaho SOR website

The authors of this tool are not responsible for misuse of the data or the tool itself.

## Troubleshooting

### No data returned
- Check your internet connection
- Verify the website is accessible: https://apps.isp.idaho.gov/sor_id/SOR
- The website structure may have changed (HTML parsing may need updates)

### Images not downloading
- Some offenders may not have photos
- Check the `offender_images` directory permissions
- Verify image URLs are accessible

### JSON parsing errors
- Ensure you have the latest version of BeautifulSoup4
- Check that the HTML structure hasn't changed on the source website

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is provided as-is for educational and research purposes. Please check local regulations regarding web scraping and data usage.

## Acknowledgments

Data source: [Idaho Sex Offender Registry](https://isp.idaho.gov/BCI/OffenderSearch.html)

---

**Disclaimer**: This is an unofficial tool and is not affiliated with, endorsed by, or connected to Idaho State Police or any government agency.
