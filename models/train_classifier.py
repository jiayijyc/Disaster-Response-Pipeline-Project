import sys
import nltk
nltk.download(['punkt', 'wordnet'])
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.multioutput import MultiOutputClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.grid_search import GridSearchCV
from sklearn.base import BaseEstimator, TransformerMixin
import pickle   

def load_data(database_filepath):
    save_path = 'sqlite:///' + database_filepath
    engine = create_engine(save_path)
    table_name = database_filepath.split('/')[-1].split('.')[0]
    df = pd.read_sql("SELECT * FROM "+table_name, engine)
    X = df.message.values
    Y = df.loc[:,'related':].values
    category_names=df.loc[:,'related':].columns
    return X,Y,category_names  


def tokenize(text):
    tokens = word_tokenize(text)
    lemmatizer = WordNetLemmatizer()

    clean_tokens = []
    for tok in tokens:
        clean_tok = lemmatizer.lemmatize(tok).lower().strip()
        clean_tokens.append(clean_tok)

    return clean_tokens


def build_model():
    pipeline = Pipeline([
        ('vect', CountVectorizer(tokenizer=tokenize)),
        ('tfidf', TfidfTransformer()),
        ('moc', MultiOutputClassifier(RandomForestClassifier()))
    ])
    parameters = {'moc__estimator__n_estimators':[10,20],'moc__estimator__min_samples_split':[2,3]}
    cv = GridSearchCV(pipeline, param_grid=parameters)
    return cv


def evaluate_model(model, X_test, Y_test, category_names):
    best_model=model.best_estimator_
    Y_pred = best_model.predict(X_test)
    for ind in range(len(category_names)):
        accuracy=classification_report(Y_test[:,ind],Y_pred[:,ind])
        print ('Accuracy Result of Column '+category_names[ind])
        print(accuracy)
    pass


def save_model(model, model_filepath):
    best_model=model.best_estimator_
    pickle.dump(best_model, open(model_filepath, 'wb'))
    pass


def main():
    if len(sys.argv) == 3:
        database_filepath, model_filepath = sys.argv[1:]
        print('Loading data...\n    DATABASE: {}'.format(database_filepath))
        X, Y, category_names = load_data(database_filepath)
        X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2)
        
        print('Building model...')
        model = build_model()
        
        print('Training model...')
        model.fit(X_train, Y_train)
        
        print('Evaluating model...')
        evaluate_model(model, X_test, Y_test, category_names)

        print('Saving model...\n    MODEL: {}'.format(model_filepath))
        save_model(model, model_filepath)

        print('Trained model saved!')

    else:
        print('Please provide the filepath of the disaster messages database '\
              'as the first argument and the filepath of the pickle file to '\
              'save the model to as the second argument. \n\nExample: python '\
              'train_classifier.py ../data/DisasterResponse.db classifier.pkl')


if __name__ == '__main__':
    main()