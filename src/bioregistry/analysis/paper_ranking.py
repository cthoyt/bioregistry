# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "bioregistry[paper-ranking]",
# ]
#
# [tool.uv.sources]
# bioregistry = { path = "../../../" }
# ///

"""Train a TF-IDF classifier and use it to score the relevance of new PubMed papers to the Bioregistry.

Run with:

1. ``python -m bioregistry.analysis.paper_ranking``
2. ``tox -e paper-ranking``
3. ``uv run --script paper_ranking.py``
"""

from __future__ import annotations

import datetime
import json
import logging
import textwrap
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any, NamedTuple, Optional, Union

import click
import numpy as np
import pandas as pd
from more_itertools import chunked
from numpy.typing import NDArray
from sklearn.base import ClassifierMixin
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.linear_model._base import LinearClassifierMixin
from sklearn.metrics import matthews_corrcoef, roc_auc_score
from sklearn.model_selection import cross_val_predict, train_test_split
from sklearn.svm import SVC, LinearSVC
from sklearn.tree import DecisionTreeClassifier
from tqdm import tqdm
from typing_extensions import TypeAlias

from bioregistry.constants import BIOREGISTRY_PATH, CURATED_PAPERS_PATH

logger = logging.getLogger(__name__)

HERE = Path(__file__).parent.resolve()
ROOT = HERE.parent.parent.parent.resolve()

DIRECTORY = ROOT.joinpath("exports", "analyses", "paper_ranking")
DIRECTORY.mkdir(exist_ok=True, parents=True)

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRPtP-tcXSx8zvhCuX6fqz_QvHowyAoDahnkixARk9rFTe0gfBN9GfdG6qTNQHHVL0i33XGSp_nV9XM/pub?output=csv"

XTrain: TypeAlias = NDArray[np.float64]
YTrain: TypeAlias = NDArray[np.float64]
XTest: TypeAlias = NDArray[np.str_]
YTest: TypeAlias = NDArray[np.str_]

ClassifierHint: TypeAlias = Union[ClassifierMixin, LinearClassifierMixin]
Classifiers: TypeAlias = list[tuple[str, ClassifierHint]]

DEFAULT_SEARCH_TERMS = [
    "database",
    "ontology",
    "resource",
    "vocabulary",
    "nomenclature",
]


def get_publications_from_bioregistry(path: Optional[Path] = None) -> pd.DataFrame:
    """Load bioregistry data from a JSON file, extracting publication details and fetching abstracts if missing.

    :param path: Path to the bioregistry JSON file.
    :return: DataFrame containing publication details.
    """
    if path is None:
        path = BIOREGISTRY_PATH

    records = json.loads(path.read_text(encoding="utf-8"))
    publications = []
    pubmeds = set()
    for record in records.values():
        # TODO replace with usage of bioregistry code, this is duplicate logic
        #  see Resource.get_publications()
        for publication in record.get("publications", []):
            pubmed = publication.get("pubmed")
            if pubmed:
                pubmeds.add(pubmed)
            publications.append({"pubmed": pubmed, "title": publication.get("title"), "label": 1})

    pubmed_to_metadata = _get_metadata_for_ids(sorted(pubmeds))
    for publication in publications:
        publication["abstract"] = pubmed_to_metadata.get(publication["pubmed"], {}).get(
            "abstract", ""
        )

    logger.info(f"Got {len(publications):,} publications from the bioregistry")

    return pd.DataFrame(publications)


def load_curated_papers(file_path: Path = CURATED_PAPERS_PATH) -> pd.DataFrame:
    """Load curated papers data from TSV file, and fetch titles and abstracts for PMIDs.

    :param file_path: Path to the curated_papers.tsv file.
    :return: DataFrame containing curated publication details.
    """
    curated_df = pd.read_csv(file_path, sep="\t")
    curated_df = curated_df.rename(columns={"pmid": "pubmed", "relevant": "label"})
    curated_df["title"] = ""
    curated_df["abstract"] = ""

    pubmeds = curated_df["pubmed"].tolist()
    fetched_metadata = _get_metadata_for_ids(pubmeds)

    for index, row in curated_df.iterrows():
        if row["pubmed"] in fetched_metadata:
            curated_df.at[index, "title"] = fetched_metadata[row["pubmed"]].get("title", "")
            curated_df.at[index, "abstract"] = fetched_metadata[row["pubmed"]].get("abstract", "")

    click.echo(f"Got {len(curated_df)} curated publications from the curated_papers.tsv file")
    return curated_df


def _get_metadata_for_ids(pubmed_ids: Iterable[Union[int, str]]) -> dict[str, dict[str, Any]]:
    """Get metadata for articles in PubMed, wrapping the INDRA client."""
    from indra.literature import pubmed_client

    fetched_metadata = {}
    for chunk in chunked(
        tqdm(pubmed_ids, unit="article", unit_scale=True, desc="Getting metadata"), 200
    ):
        fetched_metadata.update(pubmed_client.get_metadata_for_ids(chunk, get_abstracts=True))
    return fetched_metadata


def _get_ids(term: str, use_text_word: bool, relative_date: int) -> set[str]:
    from indra.literature import pubmed_client

    return {
        str(pubmed_id)
        for pubmed_id in pubmed_client.get_ids(
            term, use_text_word=use_text_word, reldate=relative_date
        )
    }


def _search(
    terms: list[str], pubmed_ids_to_filter: set[str], relative_date: int
) -> dict[str, list[str]]:
    paper_to_terms: defaultdict[str, list[str]] = defaultdict(list)
    for term in tqdm(terms, desc="Searching PubMed", unit="search term", leave=False):
        for pubmed_id in _get_ids(term, use_text_word=True, relative_date=relative_date):
            if pubmed_id not in pubmed_ids_to_filter:
                paper_to_terms[pubmed_id].append(term)
    return dict(paper_to_terms)


def fetch_pubmed_papers(*, pubmed_ids_to_filter: set[str], relative_date: int) -> pd.DataFrame:
    """Fetch PubMed papers from the last 30 days using specific search terms, excluding curated papers.

    :param pubmed_ids_to_filter: List containing already curated PMIDs
    :param relative_date: the number of recent days to search
    :return: DataFrame containing PubMed paper details.
    """
    paper_to_terms = _search(
        DEFAULT_SEARCH_TERMS, pubmed_ids_to_filter=pubmed_ids_to_filter, relative_date=relative_date
    )

    papers = _get_metadata_for_ids(paper_to_terms)

    records = []
    for pubmed_id, paper in papers.items():
        title = paper.get("title")
        abstract = paper.get("abstract", "")

        if title and abstract:
            records.append(
                {
                    "pubmed": pubmed_id,
                    "title": title,
                    "abstract": abstract,
                    "year": paper.get("publication_date", {}).get("year"),
                    "search_terms": paper_to_terms[pubmed_id],
                }
            )

    click.echo(f"{len(records):,} records fetched from PubMed")
    return pd.DataFrame(records)


def load_google_curation_df() -> pd.DataFrame:
    """Download and load curation data from a Google Sheets URL.

    :return: DataFrame containing curated publication details.
    """
    click.echo("Downloading curation sheet")
    df = pd.read_csv(URL)
    df["label"] = df["relevant"].map(_map_labels)
    df = df[["pubmed", "title", "abstract", "label"]]

    pmids_to_fetch = df[df["abstract"] == ""].pubmed.tolist()
    fetched_metadata = _get_metadata_for_ids(pmids_to_fetch)

    for index, row in df.iterrows():
        if row["pubmed"] in fetched_metadata:
            df.at[index, "abstract"] = fetched_metadata[row["pubmed"]].get("abstract", "")

    click.echo(f"Got {df.label.notna().sum()} curated publications from Google Sheets")
    return df


def _map_labels(s: str) -> Optional[int]:
    """Map labels to binary values.

    :param s: Label value.
    :return: Mapped binary label value.
    """
    if s in {"1", "1.0", 1}:
        return 1
    if s in {"0", "0.0", 0}:
        return 0
    return None


def train_classifiers(x_train: XTrain, y_train: YTrain) -> Classifiers:
    """Train multiple classifiers on the training data.

    :param x_train: Training features.
    :param y_train: Training labels.
    :return: List of trained classifiers.
    """
    classifiers = [
        ("rf", RandomForestClassifier()),
        ("lr", LogisticRegression()),
        ("dt", DecisionTreeClassifier()),
        ("svc", LinearSVC()),
        ("svm", SVC(kernel="rbf", probability=True)),
    ]
    for _, clf in tqdm(classifiers, desc="Training classifiers"):
        clf.fit(x_train, y_train)
    return classifiers


def generate_meta_features(
    classifiers: Classifiers, x_train: XTrain, y_train: YTrain, cv: int = 5
) -> pd.DataFrame:
    """Generate meta-features for training a meta-classifier using cross-validation predictions.

    .. todo:: explain what this approach is doing and why. What is a meta-feature?

    :param classifiers: List of trained classifiers.
    :param x_train: Training features.
    :param y_train: Training labels.
    :return: DataFrame containing meta-features.
    """
    df = pd.DataFrame()
    for name, clf in classifiers:
        df[name] = _cross_val_predict(clf, x_train, y_train, cv=cv)
    return df


def _cross_val_predict(
    clf: ClassifierHint, x_train: XTrain, y_train: YTrain, cv: int
) -> NDArray[np.float64]:
    if not hasattr(clf, "predict_proba"):
        return cross_val_predict(clf, x_train, y_train, cv=cv, method="decision_function")
    return cross_val_predict(clf, x_train, y_train, cv=cv, method="predict_proba")[:, 1]


def _predict(clf: ClassifierHint, x: NDArray[np.float64]) -> NDArray[np.float64]:
    if hasattr(clf, "predict_proba"):
        return clf.predict_proba(x)[:, 1]
    else:
        return clf.decision_function(x)


class MetaClassifierEvaluationResults(NamedTuple):
    """A tuple for meta classifier results."""

    mcc: float
    roc_auc: float


def _evaluate_meta_classifier(
    meta_clf: ClassifierMixin, x_test_meta: XTest, y_test: YTest
) -> MetaClassifierEvaluationResults:
    """Evaluate meta-classifier using MCC and AUC-ROC scores.

    :param meta_clf: Trained meta-classifier.
    :param x_test_meta: Test meta-features.
    :param y_test: Test labels.
    :return: MCC and AUC-ROC scores.
    """
    y_pred = meta_clf.predict(x_test_meta)
    mcc = matthews_corrcoef(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, _predict(meta_clf, x_test_meta))
    return MetaClassifierEvaluationResults(mcc, roc_auc)


def predict_and_save(
    df: pd.DataFrame,
    vectorizer: TfidfVectorizer,
    classifiers: Classifiers,
    meta_clf: ClassifierMixin,
    path: str | Path,
) -> None:
    """Predict and save scores for new data using trained classifiers and meta-classifier.

    :param df: DataFrame containing new data.
    :param vectorizer: Trained TF-IDF vectorizer.
    :param classifiers: List of trained classifiers.
    :param meta_clf: Trained meta-classifier.
    :param path: Path to save the predictions.
    """
    x_meta = pd.DataFrame()
    x_transformed = vectorizer.transform(df.title + " " + df.abstract)
    for name, clf in classifiers:
        x_meta[name] = _predict(clf, x_transformed)

    df["meta_score"] = _predict(meta_clf, x_meta)
    df = df.sort_values(by="meta_score", ascending=False)
    df["abstract"] = df["abstract"].apply(lambda x: textwrap.shorten(x, 25))
    path = Path(path).resolve()
    df.to_csv(path, sep="\t", index=False)
    click.echo(f"Wrote predicted scores to {path}")


def _first_of_month() -> str:
    today = datetime.date.today()
    return datetime.date(today.year, today.month, 1).isoformat()


def _get_meta_results(
    classifiers: Classifiers, x_train: XTrain, x_test: XTest, y_train: YTrain, y_test: YTest
) -> tuple[LogisticRegression, MetaClassifierEvaluationResults]:
    meta_features = generate_meta_features(classifiers, x_train, y_train)
    meta_clf = LogisticRegression()
    meta_clf.fit(meta_features, y_train)

    x_test_meta = pd.DataFrame()
    for name, clf in classifiers:
        x_test_meta[name] = _predict(clf, x_test)

    return meta_clf, _evaluate_meta_classifier(meta_clf, x_test_meta.to_numpy(), y_test)


def _get_evaluation_df(
    classifiers: Classifiers, x_train: XTrain, x_test: XTest, y_train: YTrain, y_test: YTest
) -> tuple[LogisticRegression, pd.DataFrame]:
    scores = []
    for name, clf in tqdm(classifiers, desc="evaluating"):
        y_pred = clf.predict(x_test)
        try:
            mcc = matthews_corrcoef(y_test, y_pred)
        except ValueError as e:
            tqdm.write(click.style(f"{clf} failed to calculate MCC: {e}", fg="yellow"))
            mcc = None
        roc_auc = roc_auc_score(y_test, _predict(clf, x_test))
        if not mcc and not roc_auc:
            continue
        scores.append((name, mcc or float("nan"), roc_auc or float("nan")))

    meta_clf, meta_clf_results = _get_meta_results(
        classifiers, x_train=x_train, y_train=y_train, x_test=x_test, y_test=y_test
    )
    scores.append(("meta_classifier", meta_clf_results.mcc, meta_clf_results.roc_auc))

    evaluation_df = pd.DataFrame(scores, columns=["classifier", "mcc", "auc_roc"]).round(3)
    return meta_clf, evaluation_df


@click.command()
@click.option(
    "--bioregistry-file",
    type=Path,
    help="Path to the bioregistry.json file",
    default=BIOREGISTRY_PATH,
)
@click.option(
    "--start-date",
    required=True,
    help="Start date of the period",
    default=_first_of_month,
)
@click.option(
    "--end-date",
    required=True,
    help="End date of the period",
    default=datetime.date.today().isoformat(),
)
def main(bioregistry_file: Path, start_date: str, end_date: str) -> None:
    """Load data, train classifiers, evaluate models, and predict new data.

    :param bioregistry_file: Path to the bioregistry JSON file.
    :param start_date: The start date of the period for which papers are being ranked.
    :param end_date: The end date of the period for which papers are being ranked.
    """
    runner(
        bioregistry_file=bioregistry_file,
        curated_papers_path=CURATED_PAPERS_PATH,
        start_date=start_date,
        end_date=end_date,
        output_path=DIRECTORY,
    )


def runner(
    *,
    bioregistry_file: Path,
    curated_papers_path: Path,
    start_date: str,
    end_date: str,
    include_remote: bool = True,
    output_path: Path,
) -> None:
    """Run functionality directly."""
    publication_df = get_publications_from_bioregistry(bioregistry_file)
    curated_papers_df = load_curated_papers(curated_papers_path)

    curated_dfs = [curated_papers_df]
    if include_remote:
        curated_dfs.append(load_google_curation_df())

    df = pd.concat([publication_df, *curated_dfs])
    df["abstract"] = df["abstract"].fillna("")
    df["title_abstract"] = df["title"] + " " + df["abstract"]

    vectorizer = TfidfVectorizer(stop_words="english")
    vectorizer.fit(df.title_abstract)

    annotated_df = df[df.label.notna()]
    x = vectorizer.transform(annotated_df.title_abstract)
    y = annotated_df.label

    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.33, random_state=42, shuffle=True
    )

    classifiers = train_classifiers(x_train, y_train)

    meta_clf, evaluation_df = _get_evaluation_df(
        classifiers, x_train=x_train, y_train=y_train, x_test=x_test, y_test=y_test
    )
    click.echo(evaluation_df.to_markdown(index=False))
    evaluation_path = output_path.joinpath("evaluation.tsv")
    click.echo(f"Writing evaluation to {evaluation_path}")
    evaluation_df.to_csv(evaluation_path, sep="\t", index=False)

    random_forest_clf = classifiers[0][1]
    lr_clf = classifiers[1][1]
    importances_df = (
        pd.DataFrame(
            zip(
                vectorizer.get_feature_names_out(),
                vectorizer.idf_,
                random_forest_clf.feature_importances_,
                lr_clf.coef_[0],
            ),
            columns=["word", "idf", "rf_importance", "lr_importance"],
        )
        .sort_values("rf_importance", ascending=False, key=abs)
        .round(4)
    )
    click.echo(importances_df.head(15).to_markdown(index=False))
    importance_path = output_path.joinpath("importances.tsv")
    click.echo(f"Writing feature (word) importances to {importance_path}")
    importances_df.to_csv(importance_path, sep="\t", index=False)

    # These have already been curated and will therefore be filtered out
    curated_pubmed_ids: set[str] = {str(pubmed) for pubmed in df["pubmed"] if pd.notna(pubmed)}

    # FIXME the fetch_pubmed_papers function should
    #  take into account the start and end date. as
    predictions_df = fetch_pubmed_papers(pubmed_ids_to_filter=curated_pubmed_ids, relative_date=30)
    if not predictions_df.empty:
        # TODO update the way naming this file works, see discussion on
        #  https://github.com/biopragmatics/bioregistry/pull/1350
        predictions_path = output_path.joinpath(f"predictions_{start_date}_to_{end_date}.tsv")
        predict_and_save(predictions_df, vectorizer, classifiers, meta_clf, predictions_path)


if __name__ == "__main__":
    main()
