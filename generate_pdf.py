from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib import colors
from reportlab.pdfgen import canvas
import json
import os
from datetime import datetime
from PIL import Image as PILImage
import sys

class OffenderPDFGenerator:
    def __init__(self, county='BONNER'):
        self.county = county.upper()
        self.json_file = f'{self.county.lower()}_county_offenders.json'
        self.images_dir = os.path.join('offender_images', self.county.lower())
        self.output_file = f'{self.county.lower()}_county_offenders.pdf'
        
        # Page setup
        self.page_width = 8.5 * inch
        self.page_height = 11 * inch
        self.margin = 0.5 * inch
        self.top_margin = 1.1 * inch  # Space for header
        self.bottom_margin = 0.5 * inch
        
        # Calculate available height
        self.available_height = self.page_height - self.top_margin - self.bottom_margin
        
        # Photo settings
        self.photo_width = 1.5 * inch
        self.photo_height = 2 * inch
        self.photos_per_row = 5
        
        # Cell settings (photo + text below)
        self.cell_height = self.photo_height + 0.6 * inch  # Space for photo + name + classification + city
        
        # Calculate how many rows fit on a page
        self.rows_per_page = int(self.available_height / self.cell_height)
        print(f"Available height: {self.available_height / inch:.2f} inches")
        print(f"Cell height: {self.cell_height / inch:.2f} inches")
        print(f"Rows per page: {self.rows_per_page}")
        
        # Load data
        with open(self.json_file, 'r', encoding='utf-8') as f:
            self.offenders = json.load(f)
        
        print(f"\nGenerating PDF for {self.county} County")
        print(f"Reading from: {self.json_file}")
        print(f"Output will be: {self.output_file}")

    def classify_offense(self, offender):
        """Classify offenses into broad categories"""
        if not offender.get('offenses'):
            return "UNKNOWN"
        
        # Collect all offense descriptions
        descriptions = []
        for offense in offender['offenses']:
            desc = offense.get('description', '').upper()
            descriptions.append(desc)
        
        combined = ' '.join(descriptions)
        
        # Classification rules (order matters - more specific first)
        
        # Child Pornography
        if any(keyword in combined for keyword in ['CHILD PORN', 'PORNOGRAPHY', 'SEXUALLY EXPLICIT IMAGES', 
                                                     'DEPICTIONS OF MINOR', 'OBSCENE MATTER', 'CHILD PORNOGRAPHY']):
            return "CP"
        
        # Child Sexual Assault - check for minor-specific keywords
        child_keywords = [
            'U/16', 'UNDER 16', 'U/14', 'UNDER 14', 'U/18', 'UNDER 18',
            'MINOR', 'CHILD', 'JUVENILE', 'U 16', 'U 14', 'U 18',
            'CHLD', 'MINOR CHILD', 'WITH A MINOR', 'OF A MINOR',
            'CHILD MOLESTATION', 'RAPE OF A CHILD', 'RAPE OF CHILD',
            '16/17', 'AGE 16/17', 'PERSON UNDER', 'PERSON U/',
            'INVOLVING A CHILD', 'INVOLVING MINOR'
        ]
        
        if any(keyword in combined for keyword in child_keywords):
            # Check if it's not just pornography (already caught above)
            if any(sa_keyword in combined for sa_keyword in ['LEWD', 'SEXUAL ABUSE', 'SEX ABUSE', 
                                                               'SEXUAL ASSAULT', 'SEXUAL BATTERY', 
                                                               'MOLESTATION', 'MOLEST', 'SODOMY',
                                                               'ORAL COPULATION', 'INDECENT LIBERTIES', 
                                                               'SEXUAL INTERCOURSE', 'RAPE',
                                                               'LASCIVIOUS', 'UNLAWFUL SEXUAL']):
                return "CHILD SA"
        
        # Regular Rape (not involving children - already caught above)
        if 'RAPE' in combined and not any(keyword in combined for keyword in child_keywords):
            return "RAPE"
        
        # General Sexual Assault (adult victims)
        if any(keyword in combined for keyword in ['SEXUAL ASSAULT', 'SEXUAL BATTERY', 
                                                     'SEXUAL INTERCOURSE WITHOUT CONSENT',
                                                     'SODOMY', 'ORAL COPULATION']) and \
           not any(keyword in combined for keyword in child_keywords):
            return "SA"
        
        # Exploitation/Enticement
        if any(keyword in combined for keyword in ['EXPLOITATION', 'ENTICEMENT', 'COERCION', 
                                                     'COMMUNICATION WITH MINOR', 'ENTICEMENT OF A MINOR']):
            return "EXPLOIT"
        
        # Assault with intent
        if any(keyword in combined for keyword in ['KIDNAP', 'ASSAULT WITH INTENT']):
            return "ASSAULT"
        
        # Indecent Exposure
        if 'INDECENT EXPOSURE' in combined or 'LEWDNESS' in combined:
            return "EXPOSURE"
        
        # Catch remaining sexual offenses
        if any(keyword in combined for keyword in ['SEXUAL', 'SEX', 'LEWD', 'LASCIVIOUS']):
            return "OTHER-SEX"
        
        return "OTHER"

    def create_header(self, canvas, doc):
        """Create header for each page"""
        canvas.saveState()
        
        # Title
        canvas.setFont('Helvetica-Bold', 18)
        canvas.drawCentredString(self.page_width / 2, self.page_height - 0.5 * inch, 
                                f"{self.county.title()} County Sex Offenders")
        
        # Date
        canvas.setFont('Helvetica', 10)
        date_str = datetime.now().strftime("%B %d, %Y")
        canvas.drawCentredString(self.page_width / 2, self.page_height - 0.75 * inch, 
                                f"Generated: {date_str}")
        
        # Page number
        canvas.setFont('Helvetica', 9)
        canvas.drawRightString(self.page_width - self.margin, 0.3 * inch, 
                              f"Page {doc.page}")
        
        canvas.restoreState()

    def resize_image(self, image_path, target_width, target_height):
        """Resize image maintaining aspect ratio"""
        try:
            img = PILImage.open(image_path)
            
            # Calculate aspect ratio
            img_width, img_height = img.size
            aspect = img_height / float(img_width)
            
            # Calculate new dimensions
            if aspect > target_height / target_width:
                # Height is the limiting factor
                new_height = target_height
                new_width = target_height / aspect
            else:
                # Width is the limiting factor
                new_width = target_width
                new_height = target_width * aspect
            
            return image_path, new_width, new_height
        except Exception as e:
            print(f"Error processing image {image_path}: {e}")
            return None, target_width, target_height

    def create_photo_grid(self):
        """Create PDF with photo grid"""
        doc = SimpleDocTemplate(
            self.output_file,
            pagesize=letter,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.top_margin,
            bottomMargin=self.bottom_margin
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        # Custom style for names
        name_style = ParagraphStyle(
            'OffenderName',
            parent=styles['Normal'],
            fontSize=7,
            alignment=TA_CENTER,
            spaceAfter=0,
            spaceBefore=2,
            leading=8
        )
        
        # Custom style for classification
        classification_style = ParagraphStyle(
            'Classification',
            parent=styles['Normal'],
            fontSize=7,
            alignment=TA_CENTER,
            textColor=colors.red,
            spaceAfter=0,
            spaceBefore=0,
            leading=7,
            fontName='Helvetica-Bold'
        )
        
        # Custom style for city
        city_style = ParagraphStyle(
            'City',
            parent=styles['Normal'],
            fontSize=6,
            alignment=TA_CENTER,
            textColor=colors.grey,
            spaceAfter=0,
            spaceBefore=0,
            leading=7
        )
        
        # Process offenders in groups
        photos_per_page = self.photos_per_row * self.rows_per_page
        total_pages = (len(self.offenders) + photos_per_page - 1) // photos_per_page
        
        print(f"\nGenerating {total_pages} pages with {self.rows_per_page} rows of {self.photos_per_row} photos each...")
        
        for page_num, page_start in enumerate(range(0, len(self.offenders), photos_per_page), 1):
            page_offenders = self.offenders[page_start:page_start + photos_per_page]
            
            print(f"Page {page_num}: {len(page_offenders)} offenders")
            
            # Create table data
            table_data = []
            current_row = []
            
            for idx, offender in enumerate(page_offenders):
                # Create cell content
                cell_content = []
                
                # Add photo
                image_path = offender.get('local_image_path')
                if image_path and os.path.exists(image_path):
                    img_path, img_width, img_height = self.resize_image(
                        image_path, 
                        self.photo_width, 
                        self.photo_height
                    )
                    if img_path:
                        try:
                            img = Image(img_path, width=img_width, height=img_height)
                            cell_content.append(img)
                        except Exception as e:
                            print(f"Error adding image for {offender['name']}: {e}")
                            cell_content.append(Paragraph("No Photo", name_style))
                else:
                    cell_content.append(Paragraph("No Photo", name_style))
                
                # Add name
                name = offender.get('name', 'UNKNOWN')
                # Wrap long names
                if len(name) > 25:
                    name = name[:22] + "..."
                cell_content.append(Paragraph(name, name_style))
                
                # Add offense classification
                classification = self.classify_offense(offender)
                cell_content.append(Paragraph(classification, classification_style))
                
                # Add city
                city = offender.get('city', '')
                if city:
                    cell_content.append(Paragraph(city, city_style))
                
                current_row.append(cell_content)
                
                # Check if row is complete
                if len(current_row) == self.photos_per_row:
                    table_data.append(current_row)
                    current_row = []
            
            # Add partially filled row
            if current_row:
                # Fill remaining cells with empty content
                while len(current_row) < self.photos_per_row:
                    current_row.append([])
                table_data.append(current_row)
            
            # Create table with fixed row height
            if table_data:
                col_width = (self.page_width - 2 * self.margin) / self.photos_per_row
                row_height = self.cell_height
                
                table = Table(
                    table_data, 
                    colWidths=[col_width] * self.photos_per_row,
                    rowHeights=[row_height] * len(table_data)
                )
                table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('LEFTPADDING', (0, 0), (-1, -1), 5),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ]))
                
                story.append(table)
                
                # Add page break if not last page
                if page_start + photos_per_page < len(self.offenders):
                    story.append(PageBreak())
        
        # Build PDF with header
        doc.build(story, onFirstPage=self.create_header, onLaterPages=self.create_header)
        print(f"\nPDF generated: {self.output_file}")
        print(f"Total offenders: {len(self.offenders)}")
        print(f"Total pages: {total_pages}")
        
        # Print classification statistics
        classifications = {}
        for offender in self.offenders:
            cls = self.classify_offense(offender)
            classifications[cls] = classifications.get(cls, 0) + 1
        
        print("\nOffense Classifications:")
        for cls, count in sorted(classifications.items(), key=lambda x: x[1], reverse=True):
            print(f"  {cls}: {count}")

def main():
    # Default to BONNER county, but allow command-line parameter
    county = 'BONNER'
    
    if len(sys.argv) > 1:
        county = sys.argv[1].upper()
    
    generator = OffenderPDFGenerator(county=county)
    generator.create_photo_grid()

if __name__ == "__main__":
    main()
