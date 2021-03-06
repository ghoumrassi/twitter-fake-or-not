from tfn.models.model import Model
from tfn.preprocess import split_binary_classes
from tfn.feature_extraction.tf_idf import get_tfidf_model

from sklearn.metrics.pairwise import cosine_similarity


class CosineSimilarity(Model):
    def fit(self, X, y):
        self.x0, self.y0, self.x1, self.y1 = split_binary_classes(X, y)

        self.vectorizer0, self.corpus_matrix0, _ = get_tfidf_model(self.x0)
        self.vectorizer1, self.corpus_matrix1, _ = get_tfidf_model(self.x1)
    
    def predict(self, X):
        y = []
        for x in X:
            score0 = sum(cosine_similarity(self.vectorizer0.transform([x]), self.corpus_matrix0)[0].tolist())
            score1 = sum(cosine_similarity(self.vectorizer1.transform([x]), self.corpus_matrix1)[0].tolist())

            y.append(self.y0[0] if score0 > score1 else self.y1[0])

        return y


if __name__ == '__main__':
    from tfn.preprocess import Dataset
    from sklearn.metrics import accuracy_score, roc_auc_score

    data = Dataset('twitter')

    cosine = CosineSimilarity()
    cosine.fit(data.X_train, data.y_train)

    y_pred = cosine.predict(data.X_test)

    print('TF-IDF + cosine-sim accuracy:', round(accuracy_score(data.y_test, y_pred), 4))
    print('TF-IDF + cosine-sim AUC:', round(roc_auc_score(data.y_test, y_pred), 4))

