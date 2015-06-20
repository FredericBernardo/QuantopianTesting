# Use the previous 50 bars' movements to predict the next movement

# Use a random forest classifier. More here: http://scikit-learn.org/stable/user_guide.html
from sklearn import linear_model, metrics
from sklearn.cross_validation import train_test_split
from sklearn.neural_network import BernoulliRBM
from sklearn.pipeline import Pipeline


from collections import deque

import numpy as np

def initialize(context):
    context.security = sid(698) # Boeing
    context.window_length = 50 # Amount of prior bars to studyain

    logistic = linear_model.LogisticRegression()
    rbm = BernoulliRBM(random_state=0, verbose=True)


    rbm.learning_rate =  0.06
    rbm.n_iter = 30

    rbm.n_components = 150
    logistic.C = 6000.0
    context.classifier = Pipeline(steps=[('rbm', rbm), ('logistic', logistic)])

    #context.classifier = RandomForestClassifier() # Use a random forest classifier
    #context.classifier = ExtraTreesClassifier(n_estimators=10, max_depth=None, min_samples_split=1,random_state=0)

    # deques are lists with a maximum length where old entries are shifted out
    context.recent_prices = deque(maxlen=context.window_length+2) # Stores recent prices
    context.X = deque(maxlen=1000) # Independent, or input variables
    context.Y = deque(maxlen=1000) # Dependent, or output variable

    context.prediction = 0 # Stores most recent prediction

def handle_data(context, data):
    context.recent_prices.append(data[context.security].price) # Update the recent prices
    if len(context.recent_prices) == context.window_length+2: # If there's enough recent price data

        # Make a list of 1's and 0's, 1 when the price increased from the prior bar
        changes = np.diff(context.recent_prices) > 0

        context.X.append(changes[:-1]) # Add independent variables, the prior changes
        context.Y.append(changes[-1]) # Add dependent variable, the final change

        if len(context.Y) >= 200: # There needs to be enough data points to make a good model

            context.classifier.fit(context.X, context.Y) # Generate the model

            context.prediction = context.classifier.predict(changes[1:]) # Predict

            # If prediction = 1, buy all shares affordable, if 0 sell all shares
            order_target_percent(context.security, context.prediction)

            record(prediction=int(context.prediction))
