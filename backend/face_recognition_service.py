"""
Face Recognition Service using OpenCV DNN

This service handles:
1. Face detection using OpenCV's deep learning models
2. Face comparison using feature extraction
3. Age-aware similarity scoring
4. Intelligent verification with context
"""

import cv2
import numpy as np
from PIL import Image
import os
from datetime import datetime
import json

class FaceRecognitionService:
    """
    Face Recognition and Comparison Service using OpenCV
    """
    
    def __init__(self):
        """Initialize face recognition service with OpenCV models"""
        
        # Download pre-trained models if not present
        self.model_dir = 'models'
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)
        
        # Paths to model files
        self.face_proto = os.path.join(self.model_dir, 'deploy.prototxt')
        self.face_model = os.path.join(self.model_dir, 'res10_300x300_ssd_iter_140000.caffemodel')
        
        # Download models if not present
        self._download_models()
        
        # Load face detection model
        try:
            self.face_net = cv2.dnn.readNetFromCaffe(self.face_proto, self.face_model)
            print("✅ Face detection model loaded successfully")
        except Exception as e:
            print(f"⚠️  Error loading models: {str(e)}")
            print("   Face detection will use Haar Cascades as fallback")
            self.face_net = None
            # Load Haar Cascade as backup
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
        
        # Thresholds for different scenarios
        self.thresholds = {
            'strict': {
                'strong_match': 0.85,
                'good_match': 0.75,
                'review': 0.65
            },
            'age_adjusted': {
                'strong_match': 0.75,
                'good_match': 0.65,
                'review': 0.55
            }
        }
        
        print("✅ Face Recognition Service initialized (OpenCV)")
    
    def _download_models(self):
        """Download face detection models if not present"""
        
        if os.path.exists(self.face_proto) and os.path.exists(self.face_model):
            return
        
        print("📥 Downloading face detection models...")
        
        import urllib.request
        
        # URLs for the models
        proto_url = "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt"
        model_url = "https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel"
        
        try:
            # Download prototxt
            if not os.path.exists(self.face_proto):
                print("   Downloading deploy.prototxt...")
                urllib.request.urlretrieve(proto_url, self.face_proto)
                print("   ✓ deploy.prototxt downloaded")
            
            # Download model (this is ~10MB, might take a minute)
            if not os.path.exists(self.face_model):
                print("   Downloading model (10MB, please wait)...")
                urllib.request.urlretrieve(model_url, self.face_model)
                print("   ✓ Model downloaded")
            
            print("✅ Models downloaded successfully!")
            
        except Exception as e:
            print(f"⚠️  Error downloading models: {str(e)}")
            print("   Will use Haar Cascade fallback")
    
    def detect_faces(self, image_path):
        """Detect all faces in an image using OpenCV DNN"""
        
        print(f"\n🔍 Detecting faces in: {image_path}")
        
        try:
            # Load image
            image = cv2.imread(image_path)
            
            if image is None:
                raise ValueError("Could not read image file")
            
            (h, w) = image.shape[:2]
            print(f"   Image size: {w}x{h}")
            
            # Detect faces
            if self.face_net is not None:
                faces = self._detect_faces_dnn(image)
            else:
                faces = self._detect_faces_haar(image)
            
            if len(faces) == 0:
                print("   ❌ No faces detected")
                return {
                    'success': False,
                    'num_faces': 0,
                    'message': 'No faces detected in image'
                }
            
            print(f"   ✅ Found {len(faces)} face(s)")
            
            # Extract features for each face
            faces_data = []
            for i, (x, y, w, h) in enumerate(faces):
                # Extract face region
                face_roi = image[y:y+h, x:x+w]
                
                # Extract features
                features = self._extract_face_features(face_roi)
                
                # Estimate age (basic heuristic)
                estimated_age = self._estimate_age(face_roi)
                
                face_info = {
                    'face_number': int(i + 1),
                    'location': {
                        'x': int(x),
                        'y': int(y),
                        'width': int(w),
                        'height': int(h)
                    },
                    'features': [float(f) for f in features],  # Convert to Python float
                    'estimated_age': int(estimated_age),
                    'size': int(w * h)
                }
                
                faces_data.append(face_info)
                print(f"   Face {i+1}: Location ({x}, {y}, {w}, {h}), Est. Age: {estimated_age}")
            
            # Sort by size (largest face first)
            faces_data.sort(key=lambda x: x['size'], reverse=True)
            
            # Assess image quality
            image_quality = self._assess_image_quality(image)
            
            return {
                'success': True,
                'num_faces': int(len(faces)),
                'faces': faces_data,
                'image_quality': float(image_quality),
                'primary_face': faces_data[0] if faces_data else None
            }
        
        except Exception as e:
            print(f"   ❌ Error detecting faces: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'num_faces': 0,
                'message': f'Error detecting faces: {str(e)}'
            }
    
    def _detect_faces_dnn(self, image):
        """Detect faces using DNN model"""
        
        (h, w) = image.shape[:2]
        
        # Prepare image for DNN
        blob = cv2.dnn.blobFromImage(
            cv2.resize(image, (300, 300)), 
            1.0, 
            (300, 300),
            (104.0, 177.0, 123.0)
        )
        
        # Pass through network
        self.face_net.setInput(blob)
        detections = self.face_net.forward()
        
        faces = []
        
        # Process detections
        for i in range(0, detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            
            # Filter weak detections
            if confidence > 0.5:
                # Get bounding box
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")
                
                # Ensure box is within image bounds
                startX = max(0, startX)
                startY = max(0, startY)
                endX = min(w, endX)
                endY = min(h, endY)
                
                width = endX - startX
                height = endY - startY
                
                if width > 0 and height > 0:
                    faces.append((startX, startY, width, height))
        
        return faces
    
    def _detect_faces_haar(self, image):
        """Detect faces using Haar Cascade (fallback)"""
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        return faces
    
    def _extract_face_features(self, face_image):
        """Extract features from face region"""
        
        # Resize to standard size
        face_resized = cv2.resize(face_image, (128, 128))
        
        # Convert to grayscale
        gray = cv2.cvtColor(face_resized, cv2.COLOR_BGR2GRAY)
        
        # Calculate HOG features
        win_size = (128, 128)
        block_size = (16, 16)
        block_stride = (8, 8)
        cell_size = (8, 8)
        nbins = 9
        
        hog = cv2.HOGDescriptor(win_size, block_size, block_stride, cell_size, nbins)
        hog_features = hog.compute(gray)
        
        # Calculate color histogram features
        hist_b = cv2.calcHist([face_resized], [0], None, [32], [0, 256])
        hist_g = cv2.calcHist([face_resized], [1], None, [32], [0, 256])
        hist_r = cv2.calcHist([face_resized], [2], None, [32], [0, 256])
        
        # Normalize histograms
        hist_b = cv2.normalize(hist_b, hist_b).flatten()
        hist_g = cv2.normalize(hist_g, hist_g).flatten()
        hist_r = cv2.normalize(hist_r, hist_r).flatten()
        
        # Combine features
        features = np.concatenate([
            hog_features.flatten(),
            hist_b,
            hist_g,
            hist_r
        ])
        
        return features
    
    def compare_faces(self, image1_path, image2_path, context=None):
        """Compare faces in two images"""
        
        print(f"\n{'='*60}")
        print(f"👥 FACE COMPARISON")
        print(f"{'='*60}")
        print(f"Image 1: {image1_path}")
        print(f"Image 2: {image2_path}")
        
        # Detect faces in both images
        faces1 = self.detect_faces(image1_path)
        faces2 = self.detect_faces(image2_path)
        
        # Check if faces were detected
        if not faces1['success']:
            return {
                'success': False,
                'error': 'No face detected in first image (document photo)',
                'image1_analysis': faces1
            }
        
        if not faces2['success']:
            return {
                'success': False,
                'error': 'No face detected in second image (selfie)',
                'image2_analysis': faces2
            }
        
        # Warnings
        warnings = []
        if faces1['num_faces'] > 1:
            warnings.append(f"Multiple faces ({faces1['num_faces']}) detected in document. Using largest face.")
        if faces2['num_faces'] > 1:
            warnings.append(f"Multiple faces ({faces2['num_faces']}) detected in selfie. Using largest face.")
        
        # Get primary faces
        face1 = faces1['primary_face']
        face2 = faces2['primary_face']
        
        # Compare features
        features1 = np.array(face1['features'])
        features2 = np.array(face2['features'])
        
        # Calculate similarity using cosine similarity
        similarity = self._calculate_similarity(features1, features2)
        
        print(f"\n📊 Similarity Score: {similarity:.4f}")
        print(f"   (0.0 = completely different, 1.0 = identical)")
        
        # Age analysis
        age1 = face1['estimated_age']
        age2 = face2['estimated_age']
        age_gap = abs(age1 - age2)
        age_gap_detected = age_gap > 10
        
        print(f"\n👤 Age Analysis:")
        print(f"   Image 1 estimated age: ~{age1} years")
        print(f"   Image 2 estimated age: ~{age2} years")
        print(f"   Age gap: ~{age_gap} years")
        
        if age_gap_detected:
            print(f"   ⚠️  Significant age difference detected!")
        
        # Get verification result
        verification = self._verify_with_context(
            similarity,
            age_gap_detected,
            faces1['image_quality'],
            faces2['image_quality']
        )
        
        # Feature comparison
        feature_comparison = self._compare_feature_regions(features1, features2)
        
        # Compile result - ENSURE ALL VALUES ARE JSON SERIALIZABLE
        result = {
            'success': True,
            'comparison': {
                'similarity': float(similarity),
                'similarity_percentage': float(similarity * 100),
                'is_match': bool(verification['is_match']),
                'match_level': str(verification['match_level']),
                'confidence': int(verification['confidence'])
            },
            'image1_analysis': {
                'num_faces': int(faces1['num_faces']),
                'estimated_age': int(age1),
                'image_quality': float(faces1['image_quality'])
            },
            'image2_analysis': {
                'num_faces': int(faces2['num_faces']),
                'estimated_age': int(age2),
                'image_quality': float(faces2['image_quality'])
            },
            'age_analysis': {
                'age_gap': int(age_gap),
                'significant_gap': bool(age_gap_detected),
                'threshold_adjusted': bool(age_gap_detected)
            },
            'feature_comparison': feature_comparison,
            'verification': {
                'verdict': str(verification['verdict']),
                'message': str(verification['message']),
                'recommendation': str(verification['recommendation'])
            },
            'warnings': [str(w) for w in warnings],
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"\n{'='*60}")
        print(f"✅ VERIFICATION COMPLETE")
        print(f"{'='*60}")
        print(f"Verdict: {verification['verdict']}")
        print(f"Similarity: {result['comparison']['similarity_percentage']:.1f}%")
        print(f"Match Level: {verification['match_level']}")
        
        return result
    
    def _calculate_similarity(self, features1, features2):
        """Calculate cosine similarity between feature vectors"""
        
        # Normalize features
        features1_norm = features1 / (np.linalg.norm(features1) + 1e-6)
        features2_norm = features2 / (np.linalg.norm(features2) + 1e-6)
        
        # Calculate cosine similarity
        similarity = np.dot(features1_norm, features2_norm)
        
        # Ensure similarity is between 0 and 1
        similarity = max(0, min(1, float(similarity)))
        
        return similarity
    
    def _compare_feature_regions(self, features1, features2):
        """Compare different regions of features"""
        
        # Divide features into regions
        total_len = len(features1)
        region_size = total_len // 5
        
        regions = {
            'eye_region': (0, region_size),
            'nose_region': (region_size, region_size * 2),
            'mouth_region': (region_size * 2, region_size * 3),
            'face_shape': (region_size * 3, region_size * 4),
            'overall_structure': (region_size * 4, total_len)
        }
        
        comparison = {}
        
        for name, (start, end) in regions.items():
            region1 = features1[start:end]
            region2 = features2[start:end]
            
            similarity = self._calculate_similarity(region1, region2)
            
            # ENSURE JSON SERIALIZABLE - convert numpy types to Python types
            comparison[name] = {
                'similarity': float(similarity * 100),
                'match': bool(similarity > 0.7)
            }
        
        return comparison
    
    def _verify_with_context(self, similarity, age_gap_detected, quality1, quality2):
        """Intelligent verification with context-aware thresholds"""
        
        thresholds = self.thresholds['age_adjusted'] if age_gap_detected else self.thresholds['strict']
        
        low_quality = quality1 < 50 or quality2 < 50
        
        if similarity >= thresholds['strong_match']:
            match_level = "STRONG_MATCH"
            is_match = True
            confidence = 95 if not age_gap_detected else 90
            
            if age_gap_detected:
                verdict = "✅ STRONG MATCH"
                message = "Excellent facial structure match despite age difference"
                recommendation = "APPROVE - High confidence match with age-adjusted threshold"
            else:
                verdict = "✅ PERFECT MATCH"
                message = "All facial features align perfectly"
                recommendation = "AUTO-APPROVE - Definite same person"
        
        elif similarity >= thresholds['good_match']:
            match_level = "GOOD_MATCH"
            is_match = True
            confidence = 80 if not age_gap_detected else 75
            
            if age_gap_detected:
                verdict = "✅ LIKELY MATCH"
                message = "Good facial structure match with detected age difference"
                recommendation = "APPROVE - Age difference detected but key features match well"
            else:
                verdict = "✅ STRONG MATCH"
                message = "Strong similarity across facial features"
                recommendation = "APPROVE - Same person with high confidence"
        
        elif similarity >= thresholds['review']:
            match_level = "MODERATE_MATCH"
            is_match = False
            confidence = 65 if not age_gap_detected else 60
            
            if age_gap_detected:
                verdict = "⚠️ REVIEW REQUIRED"
                message = "Moderate similarity with significant age difference"
                recommendation = "MANUAL REVIEW - Age gap and moderate match require human verification"
            elif low_quality:
                verdict = "⚠️ REVIEW REQUIRED"
                message = "Moderate similarity with low image quality"
                recommendation = "MANUAL REVIEW - Poor image quality affects confidence"
            else:
                verdict = "⚠️ REVIEW REQUIRED"
                message = "Moderate similarity - additional verification needed"
                recommendation = "MANUAL REVIEW - Borderline match requires human judgment"
        
        else:
            match_level = "MISMATCH"
            is_match = False
            confidence = 30 if not low_quality else 20
            
            if low_quality:
                verdict = "❌ POOR QUALITY"
                message = "Low similarity with poor image quality"
                recommendation = "REJECT - Request better quality images and retry"
            else:
                verdict = "❌ MISMATCH"
                message = "Significant differences in facial structure"
                recommendation = "REJECT - Likely different person or fraudulent attempt"
        
        return {
            'match_level': match_level,
            'is_match': is_match,
            'confidence': confidence,
            'verdict': verdict,
            'message': message,
            'recommendation': recommendation
        }
    
    def _assess_image_quality(self, image):
        """Assess image quality (0-100 score)"""
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        height, width = gray.shape
        resolution_score = min(100, (height * width) / 10000)
        
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        sharpness_score = min(100, laplacian_var / 10)
        
        mean_brightness = np.mean(gray)
        brightness_score = 100 - abs(mean_brightness - 128) / 1.28
        
        contrast = gray.std()
        contrast_score = min(100, contrast / 0.5)
        
        quality = (
            resolution_score * 0.3 +
            sharpness_score * 0.4 +
            brightness_score * 0.15 +
            contrast_score * 0.15
        )
        
        return float(quality)
    
    def _estimate_age(self, face_image):
        """Estimate age from face (basic heuristic)"""
        
        gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
        texture = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        if texture > 500:
            age = 25
        elif texture > 300:
            age = 35
        else:
            age = 45
        
        return int(age)
    
    def create_comparison_image(self, image1_path, image2_path, output_path):
        """Create side-by-side comparison image"""
        
        try:
            img1 = Image.open(image1_path)
            img2 = Image.open(image2_path)
            
            target_height = 400
            img1 = img1.resize((int(img1.width * target_height / img1.height), target_height))
            img2 = img2.resize((int(img2.width * target_height / img2.height), target_height))
            
            total_width = img1.width + img2.width + 20
            combined = Image.new('RGB', (total_width, target_height), 'white')
            
            combined.paste(img1, (0, 0))
            combined.paste(img2, (img1.width + 20, 0))
            
            combined.save(output_path)
            
            return output_path
        
        except Exception as e:
            print(f"Error creating comparison image: {str(e)}")
            return None