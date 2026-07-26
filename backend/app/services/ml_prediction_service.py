from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from app.services.priority_service import calculate_priority, detect_category


@dataclass
class MLPredictionModel:
    vectorizer: TfidfVectorizer
    priority_model: LogisticRegression
    category_model: LogisticRegression
    trained: bool = False


class MLPredictionSingleton:
    _instance: "MLPredictionSingleton | None" = None

    def __init__(self):
        self.model = MLPredictionModel(
            vectorizer=TfidfVectorizer(max_features=2000, ngram_range=(1, 2)),
            priority_model=LogisticRegression(max_iter=500),
            category_model=LogisticRegression(max_iter=500),
            trained=False,
        )

    @classmethod
    def instance(cls) -> "MLPredictionSingleton":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def train(self, texts: list[str], priority_labels: list[str], category_labels: list[str]) -> bool:
        if len(texts) < 5:
            self.model.trained = False
            return False

        transformed = self.model.vectorizer.fit_transform(texts)
        self.model.priority_model.fit(transformed, priority_labels)
        self.model.category_model.fit(transformed, category_labels)
        self.model.trained = True
        return True

    def predict(self, title: str, description: str) -> tuple[float, str, str]:
        text = f"{title} {description}"

        if self.model.trained:
            transformed = self.model.vectorizer.transform([text])
            predicted_priority = self.model.priority_model.predict(transformed)[0]
            predicted_category = self.model.category_model.predict(transformed)[0]

            score_map = {
                "Low": 0.2,
                "Medium": 0.5,
                "High": 0.75,
                "Critical": 1.0,
                "low": 0.2,
                "medium": 0.5,
                "high": 0.75,
                "critical": 1.0,
            }
            score = score_map.get(str(predicted_priority), 0.2)
            return score, str(predicted_priority).title(), str(predicted_category).lower()

        fallback_category = detect_category(title, description)
        score, level = calculate_priority(title, description, fallback_category)
        return score, level, fallback_category
