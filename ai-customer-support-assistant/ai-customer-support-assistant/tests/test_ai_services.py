from app.services.intent_classifier import IntentClassifier
from app.services.sentiment_analyzer import SentimentAnalyzer


def test_intent_classifier_predicts_billing():
    classifier = IntentClassifier()
    prediction = classifier.predict("I want a refund for my last payment")
    assert prediction.intent == "billing_inquiry"
    assert prediction.confidence > 0


def test_intent_classifier_predicts_technical_support():
    classifier = IntentClassifier()
    prediction = classifier.predict("the website is showing an error page")
    assert prediction.intent == "technical_support"


def test_intent_classifier_predicts_cancellation():
    classifier = IntentClassifier()
    prediction = classifier.predict("please cancel my membership right away")
    assert prediction.intent == "cancellation_request"


def test_sentiment_analyzer_detects_negative():
    analyzer = SentimentAnalyzer()
    result = analyzer.analyze("This is terrible, I hate this service and I'm furious")
    assert result.label == "negative"
    assert result.compound < 0


def test_sentiment_analyzer_detects_positive():
    analyzer = SentimentAnalyzer()
    result = analyzer.analyze("Thank you so much, this was fantastic and really helpful!")
    assert result.label == "positive"
    assert result.compound > 0


def test_sentiment_analyzer_detects_neutral():
    analyzer = SentimentAnalyzer()
    result = analyzer.analyze("I would like to update my shipping address")
    assert result.label in {"neutral", "positive"}
