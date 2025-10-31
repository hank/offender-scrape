import requests
from bs4 import BeautifulSoup
import json
import os
import re
from urllib.parse import urljoin, urlparse
import time

class IdahoSORScraper:
    def __init__(self):
        self.base_url = "https://apps.isp.idaho.gov/sor_id/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.offenders_data = []
        self.images_dir = "offender_images"
        os.makedirs(self.images_dir, exist_ok=True)

    def make_post_request(self, page=None):
        """Make POST request to the SOR page"""
        url = urljoin(self.base_url, "SOR")
        data = {
            'cnt': 'BONNER',
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
            # Look for the identification table/section
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True).rstrip(':')
                        value = cells[1].get_text(strip=True)
                        if label and value:
                            details['identification'][label] = value
            
            # Extract offenses - look for offense-related sections
            # Common pattern: tables or divs containing offense information
            offense_headers = soup.find_all(text=re.compile(r'offense|conviction', re.I))
            
            for header in offense_headers:
                parent_table = header.find_parent('table')
                if parent_table:
                    rows = parent_table.find_all('tr')
                    current_offense = {}
                    
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            label = cells[0].get_text(strip=True).rstrip(':')
                            value = cells[1].get_text(strip=True)
                            
                            if 'description' in label.lower() or 'offense' in label.lower():
                                if current_offense:
                                    details['offenses'].append(current_offense)
                                current_offense = {'description': value}
                            elif 'date' in label.lower():
                                current_offense['date'] = value
                            elif 'location' in label.lower() or 'county' in label.lower():
                                current_offense['location'] = value
                    
                    if current_offense and current_offense not in details['offenses']:
                        details['offenses'].append(current_offense)
            
            # Alternative parsing for offenses in different format
            if not details['offenses']:
                # Look for any structured data that might contain offense info
                for table in tables:
                    text = table.get_text()
                    if any(keyword in text.lower() for keyword in ['offense', 'conviction', 'crime']):
                        rows = table.find_all('tr')
                        for i, row in enumerate(rows):
                            cells = row.find_all('td')
                            if len(cells) >= 3:
                                offense = {
                                    'description': cells[0].get_text(strip=True),
                                    'date': cells[1].get_text(strip=True) if len(cells) > 1 else '',
                                    'location': cells[2].get_text(strip=True) if len(cells) > 2 else ''
                                }
                                if offense['description']:
                                    details['offenses'].append(offense)
            
            time.sleep(0.5)  # Be respectful to the server
            return details
            
        except Exception as e:
            print(f"Error getting offender details from {offender_url}: {e}")
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
                print(f"Processed: {name}")
                
            except Exception as e:
                print(f"Error parsing row: {e}")
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
        print("Starting scrape...")
        
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
        output_file = 'idaho_sex_offenders.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.offenders_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n\nScraping complete!")
        print(f"Total offenders: {len(self.offenders_data)}")
        print(f"Data saved to: {output_file}")
        print(f"Images saved to: {self.images_dir}/")

if __name__ == "__main__":
    scraper = IdahoSORScraper()
    scraper.scrape_all()
