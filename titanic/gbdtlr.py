# coding:utf-8
import pandas as pd
import numpy as np

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder
from sklearn.cross_validation import train_test_split
from sklearn.metrics import roc_auc_score

from preprocess_data import preprocess_data
from conf import conf

if __name__ == '__main__':
    train, train_target = preprocess_data(pd.read_csv(conf.train))

    X_train, X_val, Y_train, Y_val = train_test_split(train, train_target, \
                        test_size=conf.test_size)

    print 'transform feature ...'


    dt = RandomForestClassifier(min_samples_leaf=10, max_depth=5, n_estimators=200,\
                                max_features=3,  random_state=conf.random_state)
    dt.fit(X_train, Y_train)

    #print dt.apply(X_train).shape

    print ' Random Forest model '
    print '====' * 10
    print 'Train score', dt.score(X_train, Y_train)
    print 'Test score', dt.score(X_val, Y_val)

    onehot = OneHotEncoder()
    Xf_train = onehot.fit_transform(dt.apply(X_train).reshape((X_train.shape[0],-1)))
    Xf_val = onehot.transform(dt.apply(X_val).reshape((X_val.shape[0],-1)))

    print 'before DT:', X_train.shape[1], 'after DT:', Xf_train.shape[1]
    # Xf_train = X_train
    # Xf_val = X_val

    best_C = 0
    best_val_auc = 0
    best_val_score = 0
    for C in [0.1]: #[1e-2, 3e-2, 1e-1, 3e-1, 1, 3, 10, 1e2, 3e2, 1e3, 3e3]:
    #for C in [1e-2, 3e-3, 1e-3, 3e-4, 1e-4, 3e-5, 1e-5, 3e-6, 1e-6]:
        print 'C:', C
        lr = LogisticRegression( penalty='l1', n_jobs=-1, C=C, random_state=conf.random_state)
        lr.fit(Xf_train, Y_train)

        #save_obj(lr, 'dt_lr.mod')
        pred =  lr.predict_proba(Xf_train)[:,1]

        print 'train score:', lr.score(Xf_train, Y_train), 'AUC:', roc_auc_score(Y_train, pred)


        score = lr.score(Xf_val, Y_val)
        pred =  lr.predict_proba(Xf_val)[:,1]
        val_auc = roc_auc_score(Y_val, pred)
        print 'validate score:', score, 'AUC:', val_auc

        if val_auc > best_val_auc :
            best_C = C
            best_val_auc = val_auc
            best_val_score = score


    print 'Best C:', best_C, 'Best AUC:', best_val_auc, 'Best score:', best_val_score
    lr = LogisticRegression( penalty='l1', n_jobs=-1, C=best_C)
    lr.fit(Xf_train, Y_train)

    df = pd.read_csv(conf.test)
    test = preprocess_data(df, label=False)
    X_test = onehot.transform(dt.apply(test).reshape((test.shape[0],-1)))
    pred = lr.predict(X_test)
    df_out = pd.DataFrame({'PassengerId': df.PassengerId, 'Survived': pred})
    df_out.to_csv('gbdt_lr_pred.csv', index=False)
