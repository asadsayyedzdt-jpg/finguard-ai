"""
OCR Service for Document Text Extraction

This service handles:
1. Image preprocessing (cleaning, enhancing)
2. Text extraction using Tesseract OCR
3. Pattern matching for specific document types
4. Confidence scoring
"""

import cv2
import numpy as np
from PIL import Image
import pytesseract
import re
import os
from datetime import datetime

# Set Tesseract path (adjust if needed)
# For Windows, Tesseract is usually installed here:
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class OCRService:
    """
    OCR Service for extracting text from document images
    """
    
    def __init__(self):
        """Initialize OCR service"""
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
        
        # Regex patterns for Indian documents
        self.patterns = {
            'pan': r'[A-Z]{5}[0-9]{4}[A-Z]',
            'aadhaar': r'\d{4}\s?\d{4}\s?\d{4}',
            'date': r'\d{2}[/-]\d{2}[/-]\d{4}',
            'pincode': r'\d{6}'
        }
    
    def preprocess_image(self, image_path):
        """
        Preprocess image for better OCR accuracy
        
        This is like cleaning glasses before reading - makes everything clearer!
        
        Steps:
        1. Read image
        2. Convert to grayscale
        3. Remove noise
        4. Increase contrast
        5. Sharpen text
        """
        
        print(f"📷 Preprocessing image: {image_path}")
        
        # Read image
        img = cv2.imread(image_path)
        
        if img is None:
            raise ValueError("Could not read image file")
        
        # Get original dimensions
        height, width = img.shape[:2]
        print(f"   Original size: {width}x{height}")
        
        # Step 1: Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        print("   ✓ Converted to grayscale")
        
        # Step 2: Resize if too small (OCR works better on larger images)
        if width < 1000:
            scale_factor = 1000 / width
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            print(f"   ✓ Resized to: {new_width}x{new_height}")
        
        # Step 3: Denoise (remove tiny dots and artifacts)
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        print("   ✓ Removed noise")
        
        # Step 4: Increase contrast using CLAHE
        # (Contrast Limited Adaptive Histogram Equalization - fancy name, simple concept!)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        contrast = clahe.apply(denoised)
        print("   ✓ Enhanced contrast")
        
        # Step 5: Threshold - make it pure black text on white background
        # We try two methods and pick the better one
        
        # Method 1: Otsu's thresholding (automatic threshold selection)
        _, thresh1 = cv2.threshold(contrast, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Method 2: Adaptive thresholding (works better for uneven lighting)
        thresh2 = cv2.adaptiveThreshold(
            contrast, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Use adaptive threshold (usually better for documents)
        thresh = thresh2
        print("   ✓ Applied thresholding")
        
        # Step 6: Morphological operations to clean up
        # This removes small noise and connects broken characters
        kernel = np.ones((1, 1), np.uint8)
        processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        print("   ✓ Applied morphological operations")
        
        # Save preprocessed image for debugging
        preprocessed_path = image_path.replace('.', '_preprocessed.')
        cv2.imwrite(preprocessed_path, processed)
        print(f"   ✓ Saved preprocessed image: {preprocessed_path}")
        
        return processed, preprocessed_path
    
    def extract_text(self, image_path):
        """
        Extract all text from image using Tesseract OCR
        
        Returns both raw text and structured data
        """
        
        print(f"\n🔍 Extracting text from: {image_path}")
        
        try:
            # Preprocess image
            processed_img, preprocessed_path = self.preprocess_image(image_path)
            
            # Convert numpy array to PIL Image (Tesseract needs PIL format)
            pil_image = Image.fromarray(processed_img)
            
            # Extract text with detailed data
            # PSM 6 = Assume a single uniform block of text
            custom_config = r'--oem 3 --psm 6'
            
            print("\n🤖 Running Tesseract OCR...")
            
            # Get detailed OCR data
            ocr_data = pytesseract.image_to_data(
                pil_image, 
                config=custom_config,
                output_type=pytesseract.Output.DICT
            )
            
            # Get plain text
            raw_text = pytesseract.image_to_string(pil_image, config=custom_config)
            
            print("   ✓ OCR completed")
            print(f"\n📄 Extracted Text:\n{'-'*50}")
            print(raw_text)
            print('-'*50)
            
            # Calculate average confidence
            confidences = [int(conf) for conf in ocr_data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            print(f"\n📊 OCR Confidence: {avg_confidence:.1f}%")
            
            return {
                'raw_text': raw_text,
                'ocr_data': ocr_data,
                'confidence': round(avg_confidence, 2),
                'preprocessed_image': preprocessed_path
            }
        
        except Exception as e:
            print(f"❌ Error during OCR: {str(e)}")
            raise Exception(f"OCR failed: {str(e)}")
    
    def extract_pan_details(self, text):
        """
        Extract PAN card specific information
        
        PAN Card typically contains:
        - PAN Number (ABCDE1234F)
        - Name
        - Father's Name
        - Date of Birth
        """
        
        print("\n🔎 Extracting PAN details...")
        
        details = {
            'document_type': 'PAN',
            'pan_number': None,
            'name': None,
            'father_name': None,
            'date_of_birth': None
        }
        
        # Extract PAN number
        pan_match = re.search(self.patterns['pan'], text)
        if pan_match:
            details['pan_number'] = pan_match.group(0)
            print(f"   ✓ Found PAN: {details['pan_number']}")
        
        # Extract date of birth
        date_matches = re.findall(self.patterns['date'], text)
        if date_matches:
            details['date_of_birth'] = date_matches[0]
            print(f"   ✓ Found DOB: {details['date_of_birth']}")
        
        # Extract name (usually appears after "Name" keyword)
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if 'name' in line.lower() and i + 1 < len(lines):
                # Next line likely contains the name
                potential_name = lines[i + 1].strip()
                if len(potential_name) > 3 and potential_name.replace(' ', '').isalpha():
                    details['name'] = potential_name
                    print(f"   ✓ Found Name: {details['name']}")
                    break
        
        # Extract father's name
        for i, line in enumerate(lines):
            if 'father' in line.lower() and i + 1 < len(lines):
                potential_father = lines[i + 1].strip()
                if len(potential_father) > 3 and potential_father.replace(' ', '').isalpha():
                    details['father_name'] = potential_father
                    print(f"   ✓ Found Father's Name: {details['father_name']}")
                    break
        
        return details
    
    def extract_aadhaar_details(self, text):
        """
        Extract Aadhaar card specific information
        
        Aadhaar Card typically contains:
        - Aadhaar Number (1234 5678 9012)
        - Name
        - Date of Birth
        - Gender
        - Address
        """
        
        print("\n🔎 Extracting Aadhaar details...")
        
        details = {
            'document_type': 'AADHAAR',
            'aadhaar_number': None,
            'name': None,
            'date_of_birth': None,
            'gender': None,
            'address': None
        }
        
        # Extract Aadhaar number
        aadhaar_match = re.search(self.patterns['aadhaar'], text)
        if aadhaar_match:
            details['aadhaar_number'] = aadhaar_match.group(0).replace(' ', '')
            print(f"   ✓ Found Aadhaar: {details['aadhaar_number']}")
        
        # Extract date of birth
        date_matches = re.findall(self.patterns['date'], text)
        if date_matches:
            details['date_of_birth'] = date_matches[0]
            print(f"   ✓ Found DOB: {details['date_of_birth']}")
        
        # Extract gender
        if 'male' in text.lower():
            details['gender'] = 'Male' if 'female' not in text.lower() else 'Female'
            print(f"   ✓ Found Gender: {details['gender']}")
        
        # Extract name (first substantial line of text)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        for line in lines:
            if len(line) > 5 and line.replace(' ', '').isalpha():
                details['name'] = line
                print(f"   ✓ Found Name: {details['name']}")
                break
        
        return details
    
    def process_document(self, image_path, document_type='auto'):
        """
        Main function to process a document image
        Now supports: PAN, Aadhaar, Passport, Driver's License, Voter ID
        
        Args:
            image_path: Path to document image
            document_type: 'pan', 'aadhaar', 'passport', 'drivers_license', 'voter_id', or 'auto'
        
        Returns:
            Complete extraction results with confidence scores
        """
        
        print(f"\n{'='*60}")
        print(f"🚀 PROCESSING DOCUMENT")
        print(f"{'='*60}")
        print(f"File: {image_path}")
        print(f"Type: {document_type}")
        
        # Extract text
        ocr_result = self.extract_text(image_path)
        raw_text = ocr_result['raw_text']
        
        # Auto-detect document type if needed
        if document_type == 'auto':
            if re.search(self.patterns['pan'], raw_text):
                document_type = 'pan'
                print("\n🎯 Auto-detected: PAN Card")
            elif re.search(self.patterns['aadhaar'], raw_text):
                document_type = 'aadhaar'
                print("\n🎯 Auto-detected: Aadhaar Card")
            elif re.search(r'passport', raw_text.lower()):
                document_type = 'passport'
                print("\n🎯 Auto-detected: Passport")
            elif re.search(r'driving\s*licence|driving\s*license', raw_text.lower()):
                document_type = 'drivers_license'
                print("\n🎯 Auto-detected: Driver's License")
            elif re.search(r'election|voter', raw_text.lower()):
                document_type = 'voter_id'
                print("\n🎯 Auto-detected: Voter ID")
            else:
                document_type = 'unknown'
                print("\n⚠️  Could not auto-detect document type")
        
        # Extract specific details based on document type
        if document_type == 'pan':
            details = self.extract_pan_details(raw_text)
        elif document_type == 'aadhaar':
            details = self.extract_aadhaar_details(raw_text)
        elif document_type == 'passport':
            details = self.extract_passport_details(raw_text)
        elif document_type == 'drivers_license':
            details = self.extract_drivers_license_details(raw_text)
        elif document_type == 'voter_id':
            details = self.extract_voter_id_details(raw_text)
        else:
            details = {'document_type': 'unknown'}
        
        # Compile complete result
        result = {
            'success': True,
            'document_type': document_type,
            'extracted_details': details,
            'raw_text': raw_text,
            'ocr_confidence': ocr_result['confidence'],
            'preprocessed_image': ocr_result['preprocessed_image'],
            'timestamp': datetime.now().isoformat()
        }
        
        # Validate extracted data
        validation = self.validate_extraction(result)
        result['validation'] = validation
        
        print(f"\n{'='*60}")
        print(f"✅ PROCESSING COMPLETE")
        print(f"{'='*60}")
        
        return result
    
    def validate_extraction(self, result):
        """
        Validate the extracted data
        
        Returns validation status and any issues found
        """
        
        validation = {
            'is_valid': True,
            'issues': [],
            'confidence_level': 'high'
        }
        
        details = result['extracted_details']
        doc_type = result['document_type']
        
        # Check OCR confidence
        if result['ocr_confidence'] < 60:
            validation['issues'].append("Low OCR confidence - image quality may be poor")
            validation['confidence_level'] = 'low'
        elif result['ocr_confidence'] < 80:
            validation['confidence_level'] = 'medium'
        
        # Validate PAN
        if doc_type == 'pan':
            if not details.get('pan_number'):
                validation['is_valid'] = False
                validation['issues'].append("PAN number not found")
            elif not re.match(self.patterns['pan'], details['pan_number']):
                validation['is_valid'] = False
                validation['issues'].append("Invalid PAN format")
        
        # Validate Aadhaar
        elif doc_type == 'aadhaar':
            if not details.get('aadhaar_number'):
                validation['is_valid'] = False
                validation['issues'].append("Aadhaar number not found")
            elif len(details['aadhaar_number'].replace(' ', '')) != 12:
                validation['is_valid'] = False
                validation['issues'].append("Invalid Aadhaar format")
        
        return validation


# Test function
def test_ocr():
    """Test the OCR service with a sample image"""
    
    ocr = OCRService()
    
    print("\n" + "="*60)
    print("OCR SERVICE TEST")
    print("="*60)
    
    # Check if test image exists
    test_image = "test_pan.jpg"
    
    if not os.path.exists(test_image):
        print(f"\n⚠️  Test image '{test_image}' not found")
        print("Please provide a PAN card image for testing")
        return
    
    # Process the image
    result = ocr.process_document(test_image, document_type='auto')
    
    # Display results
    print("\n" + "="*60)
    print("EXTRACTION RESULTS")
    print("="*60)
    print(json.dumps(result['extracted_details'], indent=2))
    
    print("\n" + "="*60)
    print("VALIDATION")
    print("="*60)
    print(f"Valid: {result['validation']['is_valid']}")
    print(f"Confidence: {result['validation']['confidence_level']}")
    if result['validation']['issues']:
        print("Issues:")
        for issue in result['validation']['issues']:
            print(f"  - {issue}")

def extract_passport_details(self, text):
    """Extract Passport specific information"""
    
    print("\n🔎 Extracting Passport details...")
    
    details = {
        'document_type': 'PASSPORT',
        'passport_number': None,
        'name': None,
        'nationality': None,
        'date_of_birth': None,
        'date_of_issue': None,
        'date_of_expiry': None
    }
    
    # Passport number pattern (e.g., A1234567)
    passport_pattern = r'[A-Z]\d{7}'
    passport_match = re.search(passport_pattern, text)
    if passport_match:
        details['passport_number'] = passport_match.group(0)
        print(f"   ✓ Found Passport: {details['passport_number']}")
    
    # Extract dates
    date_matches = re.findall(self.patterns['date'], text)
    if len(date_matches) >= 2:
        details['date_of_birth'] = date_matches[0]
        details['date_of_issue'] = date_matches[1] if len(date_matches) > 1 else None
        details['date_of_expiry'] = date_matches[2] if len(date_matches) > 2 else None
        print(f"   ✓ Found DOB: {details['date_of_birth']}")
    
    # Extract nationality
    if 'indian' in text.lower():
        details['nationality'] = 'Indian'
        print(f"   ✓ Found Nationality: {details['nationality']}")
    
    return details

def extract_drivers_license_details(self, text):
    """Extract Driver's License specific information"""
    
    print("\n🔎 Extracting Driver's License details...")
    
    details = {
        'document_type': 'DRIVERS_LICENSE',
        'license_number': None,
        'name': None,
        'date_of_birth': None,
        'date_of_issue': None,
        'valid_until': None,
        'blood_group': None
    }
    
    # License number patterns (varies by state)
    # Example: MH01 20190012345
    license_pattern = r'[A-Z]{2}\d{2}\s?\d{11}'
    license_match = re.search(license_pattern, text)
    if license_match:
        details['license_number'] = license_match.group(0)
        print(f"   ✓ Found License: {details['license_number']}")
    
    # Extract dates
    date_matches = re.findall(self.patterns['date'], text)
    if date_matches:
        details['date_of_birth'] = date_matches[0] if len(date_matches) > 0 else None
        details['date_of_issue'] = date_matches[1] if len(date_matches) > 1 else None
        details['valid_until'] = date_matches[2] if len(date_matches) > 2 else None
    
    # Extract blood group
    blood_group_pattern = r'\b(A|B|AB|O)[+-]\b'
    blood_match = re.search(blood_group_pattern, text)
    if blood_match:
        details['blood_group'] = blood_match.group(0)
        print(f"   ✓ Found Blood Group: {details['blood_group']}")
    
    return details

def extract_voter_id_details(self, text):
    """Extract Voter ID specific information"""
    
    print("\n🔎 Extracting Voter ID details...")
    
    details = {
        'document_type': 'VOTER_ID',
        'epic_number': None,
        'name': None,
        'father_name': None,
        'date_of_birth': None,
        'gender': None
    }
    
    # EPIC number pattern (e.g., ABC1234567)
    epic_pattern = r'[A-Z]{3}\d{7}'
    epic_match = re.search(epic_pattern, text)
    if epic_match:
        details['epic_number'] = epic_match.group(0)
        print(f"   ✓ Found EPIC: {details['epic_number']}")
    
    # Extract date of birth
    date_matches = re.findall(self.patterns['date'], text)
    if date_matches:
        details['date_of_birth'] = date_matches[0]
        print(f"   ✓ Found DOB: {details['date_of_birth']}")
    
    # Extract gender
    if 'male' in text.lower():
        details['gender'] = 'Male' if 'female' not in text.lower() else 'Female'
        print(f"   ✓ Found Gender: {details['gender']}")
    
    return details
if __name__ == "__main__":
    import json
    test_ocr()