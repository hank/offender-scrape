import requests
from bs4 import BeautifulSoup
import json
import os
import re
from urllib.parse import urljoin, urlparse
import time
import sys

class IdahoSORScraper:
    def __init__(self, county='BONNER'):
        self.base_url = "https://apps.isp.idaho.gov/sor_id/"
        self.county = county.upper()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.offenders_data = []
        
        # County-specific directories and files
        self.images_dir = os.path.join("offender_images", self.county.lower())
        self.output_file = f'{self.county.lower()}_county_offenders.json'
        
        os.makedirs(self.images_dir, exist_ok=True)
        
        print(f"Scraping {self.county} County")
        print(f"Images will be saved to: {self.images_dir}")
        print(f"Data will be saved to: {self.output_file}")

    def make_post_request(self, page=None):
        """Make POST request to the SOR page"""
        url = urljoin(self.base_url, "SOR")
        data = {
            'cnt': self.county,
            'rad': 'A',
            'sz': '2814',
            'form': '4'
        }
        if page:
            data['page'] = str(page)
            data['srt'] = '1'
        
        response = self.session.post(url, data=data)
        response.raise_for_status()
        return response.text

    def download_image(self, img_url, offender_name, kno):
        """Download image and return local filename"""
        try:
            # Remove /thumbs/ from the URL
            full_img_url = img_url.replace('/thumbs/', '/')
            full_img_url = urljoin(self.base_url, full_img_url)
            
            response = self.session.get(full_img_url, timeout=10)
            response.raise_for_status()
            
            # Create filename from KNO and name
            safe_name = re.sub(r'[^\w\-_]', '_', offender_name)
            filename = f"{kno}_{safe_name}.jpg"
            filepath = os.path.join(self.images_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            print(f"Downloaded image: {filename}")
            return filepath
        except Exception as e:
            print(f"Error downloading image for {offender_name}: {e}")
            return None

    def get_offender_details(self, offender_url):
        """Scrape detailed information from offender's page"""
        try:
            full_url = urljoin(self.base_url, offender_url)
            response = self.session.get(full_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            details = {
                'identification': {},
                'offenses': []
            }
            
            # Extract Offender Identification section
            tables = soup.find_all('table')
            
            for table in tables:
                table_text = table.get_text()
                
                # Check if this is the offenses table
                if 'Offenses Requiring Registration' in table_text:
                    rows = table.find_all('tr')
                    
                    # Find the header row
                    header_idx = -1
                    for idx, row in enumerate(rows):
                        cells = row.find_all(['th', 'td'])
                        cell_texts = [c.get_text(strip=True) for c in cells]
                        
                        # Check if this is the header row with all required columns
                        has_offense = any('Offense' in text for text in cell_texts)
                        has_description = any('Description' in text for text in cell_texts)
                        has_date = any('Date' in text for text in cell_texts)
                        has_place = any('Place' in text or 'Conviction' in text for text in cell_texts)
                        
                        if has_offense and has_description and has_date and has_place:
                            header_idx = idx
                            break
                    
                    # Process data rows after the header
                    if header_idx >= 0:
                        for row in rows[header_idx + 1:]:
                            cells = row.find_all('td')
                            
                            # Must have exactly 4 cells for valid offense row
                            if len(cells) != 4:
                                continue
                            
                            # Extract individual cell values
                            offense_code = cells[0].get_text(strip=True)
                            description = cells[1].get_text(strip=True)
                            date = cells[2].get_text(strip=True)
                            location = cells[3].get_text(strip=True)
                            
                            # Validate that this looks like a real offense code (not concatenated data)
                            if not offense_code:
                                continue
                            
                            # Skip if offense_code contains the description (means it's concatenated)
                            if description and description in offense_code:
                                continue
                            
                            # Skip if the offense code is too long (concatenated data)
                            if len(offense_code) > 50:
                                continue
                            
                            offense = {
                                'offense': offense_code,
                                'description': description,
                                'date': date,
                                'location': location
                            }
                            
                            # Add only if not already in list
                            if offense not in details['offenses']:
                                details['offenses'].append(offense)
                    
                    # Once we've processed the offenses table, skip to next table
                    continue
                
                # Extract identification info from non-offense tables
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    
                    # Look for label-value pairs
                    if len(cells) == 2:
                        label = cells[0].get_text(strip=True).rstrip(':')
                        value = cells[1].get_text(strip=True)
                        
                        # Skip offense-related fields and empty values
                        skip_keywords = ['offense', 'description', 'date', 'place', 'conviction', 'requiring', 'registration']
                        if label and value and not any(keyword in label.lower() for keyword in skip_keywords):
                            # Don't overwrite if already exists
                            if label not in details['identification']:
                                details['identification'][label] = value
            
            time.sleep(0.5)  # Be respectful to the server
            return details
            
        except Exception as e:
            print(f"Error getting offender details from {offender_url}: {e}")
            import traceback
            traceback.print_exc()
            return {'identification': {}, 'offenses': []}

    def parse_table(self, html):
        """Parse the offenders table and extract data"""
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table', {'id': 'data_tbl'})
        
        if not table:
            print("Table not found")
            return []
        
        offenders = []
        rows = table.find_all('tr')
        
        for row in rows:
            # Skip header rows and spacer rows
            if row.find('th') or not row.find('td', {'id': 'nam_field'}):
                continue
            
            try:
                # Extract basic information
                name_cell = row.find('td', {'id': 'nam_field'})
                name_link = name_cell.find('a') if name_cell else None
                name = name_link.get_text(strip=True) if name_link else ''
                offender_url = name_link.get('href') if name_link else ''
                
                kno_cell = row.find('td', {'id': 'kno_field'})
                kno = kno_cell.get_text(strip=True) if kno_cell else ''
                
                address_cell = row.find('td', {'id': 'adr_field'})
                address = address_cell.get_text(strip=True) if address_cell else ''
                
                city_cell = row.find('td', {'id': 'cty_field'})
                city = city_cell.get_text(strip=True) if city_cell else ''
                
                # Get county (second cty_field)
                county_cells = row.find_all('td', {'id': 'cty_field'})
                county = county_cells[1].get_text(strip=True) if len(county_cells) > 1 else ''
                
                zip_cell = row.find('td', {'id': 'zip_field'})
                zip_code = zip_cell.get_text(strip=True) if zip_cell else ''
                
                status_cell = row.find('td', {'id': 'stat_field'})
                status = status_cell.get_text(strip=True) if status_cell else ''
                
                # Extract image URL
                img_cell = row.find('td', {'id': 'off_img'})
                img_tag = img_cell.find('img') if img_cell else None
                img_url = img_tag.get('src') if img_tag else None
                
                # Download image
                image_path = None
                if img_url:
                    image_path = self.download_image(img_url, name, kno)
                
                # Get detailed information from offender page
                print(f"Fetching details for {name}...")
                details = self.get_offender_details(offender_url) if offender_url else {}
                
                offender_data = {
                    'name': name,
                    'kno': kno,
                    'address': address,
                    'city': city,
                    'county': county,
                    'zip': zip_code,
                    'status': status,
                    'profile_url': urljoin(self.base_url, offender_url) if offender_url else '',
                    'image_url': urljoin(self.base_url, img_url.replace('/thumbs/', '/')) if img_url else '',
                    'local_image_path': image_path,
                    'identification': details.get('identification', {}),
                    'offenses': details.get('offenses', [])
                }
                
                offenders.append(offender_data)
                print(f"Processed: {name} - Found {len(details.get('offenses', []))} offense(s)")
                
            except Exception as e:
                print(f"Error parsing row: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        return offenders

    def get_next_pages(self, html):
        """Extract pagination links"""
        soup = BeautifulSoup(html, 'html.parser')
        pages = []
        
        # Find the pagination div
        pagination = soup.find('div', class_='np')
        if pagination:
            links = pagination.find_all('a')
            for link in links:
                href = link.get('href')
                if href and 'page=' in href:
                    # Extract page number
                    match = re.search(r'page=(\d+)', href)
                    if match:
                        page_num = int(match.group(1))
                        if page_num not in pages:
                            pages.append(page_num)
        
        return sorted(pages)

    def scrape_all(self):
        """Main scraping function"""
        print(f"\nStarting scrape for {self.county} County...")
        
        # Get first page
        print("Fetching page 1...")
        html = self.make_post_request()
        self.offenders_data.extend(self.parse_table(html))
        
        # Get all page numbers
        all_pages = self.get_next_pages(html)
        
        # Process remaining pages
        for page_num in all_pages:
            if page_num == 1:
                continue
            
            print(f"\nFetching page {page_num}...")
            try:
                html = self.make_post_request(page=page_num)
                self.offenders_data.extend(self.parse_table(html))
                time.sleep(1)  # Be respectful to the server
            except Exception as e:
                print(f"Error fetching page {page_num}: {e}")
        
        # Save to JSON
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(self.offenders_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n\nScraping complete!")
        print(f"Total offenders: {len(self.offenders_data)}")
        print(f"Data saved to: {self.output_file}")
        print(f"Images saved to: {self.images_dir}/")

def main():
    # Default to BONNER county, but allow command-line parameter
    county = 'BONNER'
    
    if len(sys.argv) > 1:
        county = sys.argv[1].upper()
    
    scraper = IdahoSORScraper(county=county)
    scraper.scrape_all()

if __name__ == "__main__":
    main()
