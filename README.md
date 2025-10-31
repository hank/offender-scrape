# Idaho Sex Offender Registry Scraper

A Python web scraper that extracts public information from the Idaho Sex Offender Registry (SOR) database for any Idaho county. This tool downloads offender data, photos, and detailed information, organizing everything into a structured JSON format and generating printable PDF reports.

## Features

- 📊 **Complete Data Extraction**: Scrapes all offender information including names, addresses, KNO numbers, and compliance status
- 🖼️ **Image Downloading**: Automatically downloads full-resolution offender photos
- 📄 **Detailed Records**: Visits each offender's profile page to extract:
  - Complete identification information
  - Criminal offense descriptions, dates, and locations
- 🔄 **Automatic Pagination**: Processes all pages of results automatically
- 💾 **JSON Export**: Saves all data in a well-structured JSON format
- 📑 **PDF Generation**: Creates professional 8.5x11" printable reports with photos
- 🏷️ **Offense Classification**: Automatically categorizes offenses (CP, CHILD SA, RAPE, SA, etc.)
- 🗺️ **Multi-County Support**: Scrape and generate reports for any Idaho county
- ⏱️ **Rate Limiting**: Includes respectful delays between requests to avoid overwhelming the server

## Requirements

- Python 3.6+
- `requests` library
- `beautifulsoup4` library
- `reportlab` library
- `pillow` library

## Installation

1. Clone this repository or download the scripts:
```bash
git clone <repository-url>
cd idaho-sor-scraper
```

2. Install required dependencies:
```bash
pip install requests beautifulsoup4 reportlab pillow
```

Or use the requirements file:
```bash
pip install -r requirements.txt
```

## Usage

### Scraping Data

**Scrape Bonner County (default):**
```bash
python scraper.py
```

**Scrape a specific county:**
```bash
python scraper.py BOUNDARY
python scraper.py KOOTENAI
python scraper.py ADA
```

The scraper will:
1. Connect to the Idaho SOR database
2. Submit a POST request for the specified county
3. Parse each page of results
4. Download offender photos to `offender_images/<county>/`
5. Visit each offender's detail page for additional information
6. Save everything to `<county>_county_offenders.json`

### Generating PDF Reports

**Generate PDF for Bonner County (default):**
```bash
python generate_pdf.py
```

**Generate PDF for a specific county:**
```bash
python generate_pdf.py BOUNDARY
python generate_pdf.py KOOTENAI
```

The PDF generator will:
1. Read the JSON file for the specified county
2. Create an 8.5x11" PDF with photo grid layout
3. Display photos (~1.5" wide) with names and offense classifications
4. Save to `<county>_county_offenders.pdf`

## Output

### Directory Structure

```
.
├── scraper.py
├── generate_pdf.py
├── offender_images/
│   ├── bonner/
│   │   ├── 8001234_DOE_JOHN_MICHAEL.jpg
│   │   ├── 8001235_SMITH_JAMES_LEE.jpg
│   │   └── ...
│   ├── boundary/
│   │   └── ...
│   └── kootenai/
│       └── ...
├── bonner_county_offenders.json
├── bonner_county_offenders.pdf
├── boundary_county_offenders.json
├── boundary_county_offenders.pdf
└── README.md
```

### JSON File Structure

The script generates `<county>_county_offenders.json` with the following structure:

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
    "local_image_path": "offender_images/bonner/8001234_DOE_JOHN_MICHAEL.jpg",
    "identification": {
      "Reg ID": "SX12345",
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
        "offense": "18-1508",
        "description": "LEWD CONDUCT WITH A MINOR",
        "date": "03/15/2015",
        "location": "BONNER COUNTY, ID"
      }
    ]
  }
]
```

### PDF Report Layout

The PDF report features:
- **Header**: County name and generation date on each page
- **Photo Grid**: 5 columns × 3 rows (15 offenders per page)
- **Each Entry Shows**:
  - Full-resolution photo (~1.5" wide)
  - Full name
  - Offense classification (in red, bold)
  - City of residence
- **Page Numbers**: Bottom right of each page

### Offense Classifications

The system automatically categorizes offenses into the following types:

- **CP** - Child Pornography (possession of materials)
- **CHILD SA** - Child Sexual Assault/Abuse (offenses against minors)
- **RAPE** - Rape (adult victims)
- **SA** - Sexual Assault (adult victims)
- **EXPLOIT** - Exploitation/Enticement of minors
- **ASSAULT** - Assault with intent/Kidnapping
- **EXPOSURE** - Indecent Exposure
- **OTHER-SEX** - Other sexual offenses
- **OTHER** - Non-sexual offenses

The classification is based on analyzing offense descriptions for keywords related to:
- Age indicators (U/16, UNDER 14, MINOR, CHILD, etc.)
- Offense types (LEWD, MOLESTATION, RAPE, etc.)
- Material possession (PORNOGRAPHY, EXPLICIT IMAGES, etc.)

## Configuration

### Changing the County

Both scripts accept a county name as a command-line argument:

```bash
# Scrape data
python scraper.py <COUNTY_NAME>

# Generate PDF
python generate_pdf.py <COUNTY_NAME>
```

### Valid Idaho Counties

Some common Idaho counties:
- ADA
- BANNOCK
- BONNER
- BONNEVILLE
- BOUNDARY
- CANYON
- KOOTENAI
- LATAH
- NEZ PERCE
- TWIN FALLS

(The system accepts any valid Idaho county name)

### Customizing the PDF Layout

You can modify these values in `generate_pdf.py`:

```python
self.photo_width = 1.5 * inch        # Width of each photo
self.photo_height = 2 * inch         # Height of each photo
self.photos_per_row = 5              # Photos per row
```

The script automatically calculates how many rows fit on each page based on available space.

## Data Fields

### Basic Information
- **name**: Full legal name of the offender
- **kno**: Idaho offender identification number
- **address**: Street address
- **city**: City of residence
- **county**: County of residence
- **zip**: ZIP code
- **status**: Compliance status (COMPLIANT, NON COMP, PENDING, etc.)

### Additional Fields
- **profile_url**: Direct link to the offender's detail page
- **image_url**: URL of the full-resolution photo
- **local_image_path**: Path to downloaded image file (county-specific directory)

### Identification Details
Physical characteristics and biographical information extracted from the offender's detail page:
- Reg ID
- Height, Weight
- Hair Color, Eye Color
- Race, Sex
- Date of Birth
- Aliases

### Offenses
Array of criminal offenses including:
- **offense**: Idaho code or statute number
- **description**: Type of offense
- **date**: Date of conviction/offense
- **location**: County/state where offense occurred

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
- Consider the privacy and safety implications of distributing this information

## Legal Disclaimer

This tool is provided for informational and research purposes only. The data scraped is publicly available from the Idaho Sex Offender Registry maintained by Idaho State Police. 

**Users are responsible for:**
- Complying with all applicable federal, state, and local laws
- Using the data ethically and legally
- Not using the data for harassment, discrimination, or any illegal purpose
- Respecting the terms of service of the Idaho SOR website
- Understanding that this information is public record but should be used responsibly

The authors of this tool are not responsible for misuse of the data or the tool itself.

**Warning:** Misuse of sex offender registry information may be a criminal offense under Idaho Code § 18-8329.

## Troubleshooting

### No data returned
- Check your internet connection
- Verify the website is accessible: https://apps.isp.idaho.gov/sor_id/SOR
- Ensure the county name is spelled correctly and is a valid Idaho county
- The website structure may have changed (HTML parsing may need updates)

### Images not downloading
- Some offenders may not have photos
- Check the `offender_images/<county>` directory permissions
- Verify image URLs are accessible
- Check your internet connection

### JSON parsing errors
- Ensure you have the latest version of BeautifulSoup4
- Check that the HTML structure hasn't changed on the source website
- Verify the JSON file isn't corrupted

### PDF generation fails
- Ensure the JSON file exists for the specified county
- Check that ReportLab and Pillow are installed correctly
- Verify image files exist in the correct directory
- Check available disk space

### County-specific issues
- Verify the county name is correct (use uppercase)
- Some counties may have no registered offenders
- Check the Idaho SOR website to confirm data exists for that county

## Example Workflow

**Complete workflow for multiple counties:**

```bash
# Scrape multiple counties
python scraper.py BONNER
python scraper.py BOUNDARY
python scraper.py KOOTENAI

# Generate PDFs for all counties
python generate_pdf.py BONNER
python generate_pdf.py BOUNDARY
python generate_pdf.py KOOTENAI
```

This will create:
- 3 JSON files with complete data
- 3 PDF reports ready for printing
- Organized image directories for each county

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with multiple counties
5. Submit a pull request

## License

This project is provided as-is for educational and research purposes. Please check local regulations regarding web scraping and data usage.

## Acknowledgments

Data source: [Idaho Sex Offender Registry](https://isp.idaho.gov/BCI/OffenderSearch.html)

---

**Disclaimer**: This is an unofficial tool and is not affiliated with, endorsed by, or connected to Idaho State Police or any government agency.
