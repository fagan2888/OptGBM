from typing import Callable
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

import lightgbm as lgb
import numpy as np
import optuna
import pytest

from sklearn.datasets import load_boston
from sklearn.datasets import load_breast_cancer
from sklearn.datasets import load_digits
from sklearn.datasets import load_iris
from sklearn.datasets import load_wine
from sklearn.model_selection import train_test_split
from sklearn.utils.estimator_checks import check_estimator

from optgbm.sklearn import OGBMClassifier
from optgbm.sklearn import OGBMRegressor

callback = lgb.reset_parameter(
    learning_rate=lambda iteration: 0.05 * (0.99 ** iteration)
)


def zero_one_loss(
    y_true: np.ndarray,
    y_pred: np.ndarray
) -> Tuple[str, float, bool]:
    return 'zero_one_loss', np.mean(y_true != y_pred), False


@pytest.mark.skip
def test_ogbm_classifier() -> None:
    check_estimator(OGBMClassifier)


@pytest.mark.skip
def test_ogbm_regressor() -> None:
    check_estimator(OGBMRegressor)


@pytest.mark.parametrize('reg_sqrt', [False, True])
def test_fit_with_params(reg_sqrt: bool) -> None:
    X, y = load_boston(return_X_y=True)

    reg = OGBMRegressor(reg_sqrt=reg_sqrt)

    reg.fit(X, y)


@pytest.mark.parametrize('callbacks', [None, [callback]])
@pytest.mark.parametrize('eval_metric', ['auc', zero_one_loss])
def test_fit_with_fit_params(
    callbacks: Optional[List[Callable]],
    eval_metric: Union[Callable, str]
) -> None:
    X, y = load_breast_cancer(return_X_y=True)

    clf = OGBMClassifier()

    clf.fit(X, y, callbacks=callbacks, eval_metric=eval_metric)


@pytest.mark.parametrize('n_jobs', [-1, 1])
def test_fit_twice_without_study(n_jobs: int) -> None:
    X, y = load_breast_cancer(return_X_y=True)

    clf = OGBMClassifier(n_jobs=n_jobs, random_state=0)

    clf.fit(X, y)

    y_pred = clf.predict(X)

    assert isinstance(y_pred, np.ndarray)
    assert y.shape == y_pred.shape

    clf = OGBMClassifier(n_jobs=n_jobs, random_state=0)

    clf.fit(X, y)

    assert np.array_equal(y_pred, clf.predict(X))


@pytest.mark.parametrize('storage', [None, 'sqlite:///:memory:'])
def test_fit_twice_with_study(storage: Optional[str]) -> None:
    X, y = load_breast_cancer(return_X_y=True)

    n_trials = 5
    study = optuna.create_study(storage=storage)
    clf = OGBMClassifier(n_trials=n_trials, study=study)

    clf.fit(X, y)

    assert len(study.trials) == n_trials

    clf.fit(X, y)

    assert len(study.trials) == 2 * n_trials


def test_refit() -> None:
    X, y = load_breast_cancer(return_X_y=True)

    clf = OGBMClassifier()

    clf.fit(X, y)

    clf.refit(X, y)


def test_score() -> None:
    load_functions = [load_breast_cancer, load_digits, load_iris, load_wine]

    for load_function in load_functions:
        X, y = load_function(return_X_y=True)
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            random_state=0
        )

        clf = lgb.LGBMClassifier(random_state=0)

        clf.fit(X_train, y_train)

        score = clf.score(X_test, y_test)

        clf = OGBMClassifier(random_state=0)

        clf.fit(X_train, y_train)

        assert score <= clf.score(X_test, y_test)


@pytest.mark.parametrize('n_jobs', [-1, 1])
def test_plot_importance(n_jobs: int) -> None:
    X, y = load_breast_cancer(return_X_y=True)

    clf = OGBMClassifier(n_jobs=n_jobs)

    clf.fit(X, y)

    assert isinstance(clf.feature_importances_, np.ndarray)

    lgb.plot_importance(clf)
