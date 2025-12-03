"""
Sentiment Analysis Service for Review Comments
"""
import logging
from typing import Dict, Optional
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer as NLTKSentimentAnalyzer

# Download required NLTK data (run once)
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon', quiet=True)

try:
    nltk.data.find('punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """Sentiment analysis service using multiple algorithms"""
    
    def __init__(self):
        self.vader_analyzer = SentimentIntensityAnalyzer()
        try:
            self.nltk_analyzer = NLTKSentimentAnalyzer()
        except:
            self.nltk_analyzer = None
            logger.warning("NLTK Sentiment Analyzer not available")
    
    def analyze_sentiment(self, text: str) -> Dict[str, any]:
        """
        Analyze sentiment of text using multiple methods
        Returns comprehensive sentiment analysis results
        """
        if not text or not text.strip():
            return self._get_neutral_sentiment()
        
        try:
            # TextBlob Analysis
            textblob_sentiment = self._analyze_with_textblob(text)
            
            # VADER Analysis
            vader_sentiment = self._analyze_with_vader(text)
            
            # Combine results for final sentiment
            combined_sentiment = self._combine_sentiments(textblob_sentiment, vader_sentiment)
            
            return {
                "overall_sentiment": combined_sentiment["label"],
                "confidence": combined_sentiment["confidence"],
                "polarity_score": combined_sentiment["polarity"],
                "details": {
                    "textblob": textblob_sentiment,
                    "vader": vader_sentiment
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return self._get_neutral_sentiment()
    
    def _analyze_with_textblob(self, text: str) -> Dict[str, any]:
        """Analyze sentiment using TextBlob"""
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity  # -1 to 1
        subjectivity = blob.sentiment.subjectivity  # 0 to 1
        
        # Convert polarity to sentiment label
        if polarity > 0.1:
            label = "positive"
        elif polarity < -0.1:
            label = "negative"
        else:
            label = "neutral"
        
        return {
            "label": label,
            "polarity": polarity,
            "subjectivity": subjectivity,
            "confidence": abs(polarity)
        }
    
    def _analyze_with_vader(self, text: str) -> Dict[str, any]:
        """Analyze sentiment using VADER"""
        scores = self.vader_analyzer.polarity_scores(text)
        
        # Determine sentiment label based on compound score
        compound = scores['compound']
        if compound >= 0.05:
            label = "positive"
        elif compound <= -0.05:
            label = "negative"
        else:
            label = "neutral"
        
        return {
            "label": label,
            "compound": compound,
            "positive": scores['pos'],
            "negative": scores['neg'],
            "neutral": scores['neu'],
            "confidence": abs(compound)
        }
    
    def _combine_sentiments(self, textblob_result: Dict, vader_result: Dict) -> Dict[str, any]:
        """Combine TextBlob and VADER results for final sentiment"""
        
        # Weight the results (VADER is often better for social media text)
        textblob_weight = 0.4
        vader_weight = 0.6
        
        # Combine polarity scores
        textblob_polarity = textblob_result["polarity"]
        vader_polarity = vader_result["compound"]
        
        combined_polarity = (textblob_polarity * textblob_weight) + (vader_polarity * vader_weight)
        
        # Determine final sentiment label
        if combined_polarity > 0.1:
            final_label = "positive"
        elif combined_polarity < -0.1:
            final_label = "negative"
        else:
            final_label = "neutral"
        
        # Calculate confidence as average of individual confidences
        combined_confidence = (textblob_result["confidence"] * textblob_weight) + (vader_result["confidence"] * vader_weight)
        
        return {
            "label": final_label,
            "polarity": combined_polarity,
            "confidence": min(combined_confidence, 1.0)  # Cap at 1.0
        }
    
    def _get_neutral_sentiment(self) -> Dict[str, any]:
        """Return neutral sentiment for error cases or empty text"""
        return {
            "overall_sentiment": "neutral",
            "confidence": 0.0,
            "polarity_score": 0.0,
            "details": {
                "textblob": {"label": "neutral", "polarity": 0.0, "subjectivity": 0.0, "confidence": 0.0},
                "vader": {"label": "neutral", "compound": 0.0, "positive": 0.0, "negative": 0.0, "neutral": 1.0, "confidence": 0.0}
            }
        }

# Global instance
sentiment_analyzer = SentimentAnalyzer()

def analyze_review_sentiment(comment: str) -> Dict[str, any]:
    """
    Convenience function to analyze sentiment of a review comment
    """
    return sentiment_analyzer.analyze_sentiment(comment)
