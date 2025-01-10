"""Utilities for processing tabular data in Pandas dataframes.

The following examples show how the entries in the widely used `Gene Ontology Annotations
<http://geneontology.org/docs/go-annotation-file-gaf-format-2.2/#>`_ database distributed
in the `GAF format <http://geneontology.org/docs/go-annotation-file-gaf-format-2.2/>`_ can
be loaded with :mod:`pandas` then normalized with the Bioregistry. It can be loaded in full
with the :func:`get_goa_example` function.
"""

import functools
import logging
import re
from typing import Callable, Dict, Optional, Pattern, Union, cast

import pandas as pd
from tabulate import tabulate
from tqdm.auto import tqdm

import bioregistry

__all__ = [
    "get_goa_example",
    # Normalization
    "normalize_prefixes",
    "normalize_curies",
    # Validation
    "validate_prefixes",
    "validate_curies",
    "validate_identifiers",
    # Conversion
    "identifiers_to_curies",
    "identifiers_to_iris",
    "curies_to_iris",
    "curies_to_identifiers",
    "iris_to_curies",
    "pd_collapse_to_curies",
]

logger = logging.getLogger(__name__)


class PrefixLocationError(ValueError):
    """Raised when not exactly one of prefix and prefix_column were given."""


def get_goa_example() -> pd.DataFrame:
    """Get the GOA file."""
    return pd.read_csv(
        "http://geneontology.org/gene-associations/goa_human.gaf.gz",
        sep="\t",
        comment="!",
        header=None,
    )


def _norm_column(df: pd.DataFrame, column: Union[int, str]) -> str:
    return column if isinstance(column, str) else df.columns[column]


def normalize_prefixes(
    df: pd.DataFrame, column: Union[int, str], *, target_column: Optional[str] = None
) -> None:
    """Normalize prefixes in a given column.

    :param df: A dataframe
    :param column: A column in the dataframe containing prefixes
    :param target_column: The target column to put the normalized prefixes. If not given,
        overwrites the given ``column`` in place

    .. code-block:: python

        import bioregistry.pandas as brpd
        import pandas as pd

        df = brpd.get_goa_example()

        # column 1: DB
        #  i.e., `UniProtKB` becomes `uniprot`
        brpd.normalize_prefixes(df, column=0)
    """
    column = _norm_column(df, column)
    if target_column is None:
        target_column = column
    df[target_column] = df[column].map(bioregistry.normalize_prefix, na_action="ignore")


def normalize_curies(
    df: pd.DataFrame, column: Union[int, str], *, target_column: Optional[str] = None
) -> None:
    """Normalize CURIEs in a given column.

    :param df: A dataframe
    :param column: The column of CURIEs to normalize
    :param target_column:
        The column to put the normalized CURIEs in. If not given, overwrites the given ``column`` in place.

    .. code-block:: python

        import bioregistry.pandas as brpd
        import pandas as pd

        df = brpd.get_goa_example()

        # column 5: GO ID - fix normalization of capitalization of prefix,
        #  i.e., `GO:0003993` becomes `go:0003993`
        brpd.normalize_curies(df, column=4)

        # column 6: DB:Reference (|DB:Reference) - fix synonym of prefix
        #  i.e., `PMID:2676709` becomes `pubmed:2676709`
        brpd.normalize_curies(df, column=5)

        # column 8: With (or) From
        #  i.e., `GO:0000346` becomes `go:0000346`
        brpd.normalize_curies(df, column=7)

        # column 13: Taxon(|taxon) - fix synonym of prefix
        #  i.e., `taxon:9606` becomes `ncbitaxon:9606`
        brpd.normalize_curies(df, column=12)
    """
    column = _norm_column(df, column)
    if target_column is None:
        target_column = column
    df[target_column] = df[column].map(bioregistry.normalize_curie, na_action="ignore")


def validate_prefixes(
    df: pd.DataFrame, column: Union[int, str], *, target_column: Optional[str] = None
) -> pd.Series:
    """Validate prefixes in a given column.

    :param df: A DataFrame
    :param column: The column of prefixes to validate
    :param target_column:
        The optional column to put the results of validation
    :returns:
        A pandas series corresponding to the validity of each row

    .. code-block:: python

        import bioregistry.pandas as brpd
        import pandas as pd

        df = brpd.get_goa_example()

        # column 1: DB
        #  i.e., `UniProtKB` entries are not standard, and are therefore false
        idx = brpd.validate_prefixes(df, column=0)

        # Slice the dataframe based on valid and invalid prefixes
        valid_prefix_df = df[idx]
        invalid_prefix_df = df[~idx]
    """
    column = _norm_column(df, column)
    results = df[column].map(lambda x: bioregistry.normalize_prefix(x) == x, na_action="ignore")
    if target_column:
        df[target_column] = results
    return results


def summarize_prefix_validation(df: pd.DataFrame, idx: pd.Series, column) -> None:
    """Provide a summary of prefix validation."""
    # TODO add suggestions on what to do next, e.g.:,
    #  1. can some be normalized? use normalization function
    #  2. slice out invalid content
    #  3. make new prefix request to Bioregistry
    count = (~idx).sum()
    unique = sorted(df[~idx][column].unique())

    print(  # noqa:T201
        f"{count:,} of {len(df.index):,} ({count / len(df.index):.0%})",
        "rows with the following prefixes need to be fixed:",
        unique,
    )
    normalizable = {
        prefix: norm_prefix
        for prefix, norm_prefix in (
            (prefix, bioregistry.normalize_prefix(prefix)) for prefix in unique
        )
        if norm_prefix
    }
    if normalizable:
        print(  # noqa:T201
            f"The following prefixes could be normalized using normalize_curies():"
            f"\n\n{tabulate(normalizable.items(), headers=['raw', 'standardized'], tablefmt='github')}"
        )


def validate_curies(
    df: pd.DataFrame, column: Union[int, str], *, target_column: Optional[str] = None
) -> pd.Series:
    """Validate CURIEs in a given column.

    :param df: A DataFrame
    :param column: The column of CURIEs to validate
    :param target_column:
        The optional column to put the results of validation.
    :returns:
        A pandas series corresponding to the validity of each row

    .. code-block:: python

        import bioregistry.pandas as brpd
        import pandas as pd

        df = brpd.get_goa_example()

        # column 5: GO ID - fix normalization of capitalization of prefix,
        #  i.e., `GO:0003993` is not standard and is therefore false
        idx = brpd.validate_curies(df, column=4)

        # Slice the dataframe
        valid_go_df = df[idx]
        invalid_go_df = df[~idx]
    """
    column = _norm_column(df, column)
    results = df[column].map(bioregistry.is_valid_curie, na_action="ignore")
    if target_column:
        df[target_column] = results
    return results


def summarize_curie_validation(df: pd.DataFrame, idx: pd.Series) -> None:
    """Provide a summary of CURIE validation."""
    count = (~idx).sum()
    unique = sorted(df[~idx][0].unique())
    print(  # noqa:T201
        f"{count:,} of {len(df.index):,} ({count / len(df.index):.0%})",
        "rows with the following CURIEs need to be fixed:",
        unique,
    )


def validate_identifiers(
    df: pd.DataFrame,
    column: Union[int, str],
    *,
    prefix: Optional[str] = None,
    prefix_column: Optional[str] = None,
    target_column: Optional[str] = None,
    use_tqdm: bool = False,
) -> pd.Series:
    """Validate local unique identifiers in a given column.

    Some data sources split the prefix and identifier in separate columns,
    so you can use the ``prefix_column`` argument instead of the ``prefix``
    argument like in the following example with the GO Annotation Database:

    :param df: A dataframe
    :param column: A column in the dataframe containing identifiers
    :param prefix:
        Specify the prefix if all identifiers in the given column are from
        the same namespace
    :param prefix_column:
        Specify the ``prefix_column`` if there is an additional column whose rows
        contain the prefix for each rows' respective identifiers.
    :param target_column:
        If given, stores the results of validation in this column
    :param use_tqdm:
        Should a progress bar be shown?
    :returns:
        A pandas series corresponding to the validity of each row
    :raises PrefixLocationError:
        If not exactly one of the prefix and prefix_column arguments are given
    :raises ValueError:
        If prefix_column is given and it contains no valid prefixes

    .. code-block:: python

        import bioregistry.pandas as brpd
        import pandas as pd

        df = brpd.get_goa_example()

        # Use a combination of column 1 (DB) and column 2 (DB Object ID) for validation
        idx = brpd.validate_identifiers(df, column=1, prefix_column=0)

        # Split the dataframe based on valid and invalid identifiers
        valid_df = df[idx]
        invalid_df = df[~idx]
    """
    column = _norm_column(df, column)
    if prefix_column is None and prefix is None:
        raise PrefixLocationError
    elif prefix_column is not None and prefix is not None:
        raise PrefixLocationError
    elif prefix is not None:
        return _help_validate_identifiers(df, column, prefix)
    else:  # prefix_column is not None
        prefixes = df[prefix_column].unique()
        if 0 == len(prefixes):
            raise ValueError(f"No prefixes found in column {prefix_column}")
        if 1 == len(prefixes):
            return _help_validate_identifiers(df, column, list(prefixes)[0])
        patterns: Dict[str, Optional[Pattern]] = {}
        for prefix in df[prefix_column].unique():
            if pd.isna(prefix):
                continue
            pattern = bioregistry.get_pattern(prefix)
            patterns[prefix] = re.compile(pattern) if pattern else None

        def _validate_lambda(_p: Optional[str], _i: str) -> Optional[bool]:
            if _p is None:
                return None
            _pattern = patterns.get(_p)
            if _pattern is None:
                return None
            return bool(_pattern.fullmatch(_i))

        results = _multi_column_map(
            df,
            [cast(str, prefix_column), column],
            _validate_lambda,
            use_tqdm=use_tqdm,
        )
    if target_column:
        df[target_column] = results
    return results


def _help_validate_identifiers(df: pd.DataFrame, column: str, prefix: str) -> pd.Series:
    norm_prefix = bioregistry.normalize_prefix(prefix)
    if norm_prefix is None:
        raise ValueError(
            f"Can't validate identifiers for {prefix} because it is not in the Bioregistry"
        )
    pattern = bioregistry.get_pattern(prefix)
    if pattern is None:
        raise ValueError(
            f"Can't validate identifiers for {prefix} because it has no pattern in the Bioregistry"
        )
    pattern_re = re.compile(pattern)
    return df[column].map(
        lambda s: bool(pattern_re.fullmatch(s)),
        na_action="ignore",
    )


def identifiers_to_curies(
    df: pd.DataFrame,
    column: Union[int, str],
    *,
    prefix: Optional[str] = None,
    prefix_column: Union[None, int, str] = None,
    target_column: Optional[str] = None,
    use_tqdm: bool = False,
    normalize_prefixes_: bool = True,
) -> None:
    """Convert a column of local unique identifiers to CURIEs.

    :param df: A dataframe
    :param column: A column in the dataframe containing identifiers
    :param prefix:
        Specify the prefix if all identifiers in the given column are from
        the same namespace
    :param prefix_column:
        Specify the ``prefix_column`` if there is an additional column whose rows
        contain the prefix for each rows' respective identifiers.
    :param target_column:
        If given, stores CURIEs in this column,
    :param use_tqdm:
        Should a progress bar be shown?
    :param normalize_prefixes_:
        Should the prefix column get auto-normalized if ``prefix_column`` is not None?
    :raises PrefixLocationError:
        If not exactly one of the prefix and prefix_column arguments are given
    :raises ValueError:
        If the given prefix is not normalizable

    .. code-block:: python

        import bioregistry.pandas as brpd
        import pandas as pd

        df = brpd.get_goa_example()

        # Use a combination of column 1 (DB) and column 2 (DB Object ID) for conversion
        brpd.identifiers_to_curies(df, column=1, prefix_column=0)
    """
    # FIXME do pattern check first so you don't get bananas
    column = _norm_column(df, column)
    if prefix_column is None and prefix is None:
        raise PrefixLocationError
    elif prefix_column is not None and prefix is not None:
        raise PrefixLocationError

    # valid_idx = validate_identifiers(df, column=column, prefix=prefix, prefix_column=prefix_column)
    target_column = target_column or column

    if prefix is not None:
        norm_prefix = bioregistry.normalize_prefix(prefix)
        if norm_prefix is None:
            raise ValueError

        df.loc[target_column] = df[column].map(
            functools.partial(bioregistry.curie_to_str, prefix=norm_prefix),
            na_action="ignore",
        )
    elif prefix_column is not None:
        prefix_column = _norm_column(df, prefix_column)
        if normalize_prefixes_:
            normalize_prefixes(df=df, column=prefix_column)
        df[target_column] = _multi_column_map(
            df, [prefix_column, column], bioregistry.curie_to_str, use_tqdm=use_tqdm
        )


def identifiers_to_iris(
    df: pd.DataFrame,
    column: Union[int, str],
    *,
    prefix: str,
    prefix_column: Optional[str] = None,
    target_column: Optional[str] = None,
    use_tqdm: bool = False,
) -> None:
    """Convert a column of local unique identifiers to IRIs.

    :param df: A dataframe
    :param column: A column in the dataframe containing identifiers
    :param prefix:
        Specify the prefix if all identifiers in the given column are from
        the same namespace
    :param prefix_column:
        Specify the ``prefix_column`` if there is an additional column whose rows
        contain the prefix for each rows' respective identifiers.
    :param target_column:
        If given, stores IRIs in this column
    :param use_tqdm:
        Should a progress bar be shown?

    :raises PrefixLocationError:
        If not exactly one of the prefix and prefix_column arguments are given
    :raises ValueError:
        If the given prefix is not normalizable

    .. code-block:: python

        import bioregistry.pandas as brpd
        import pandas as pd

        df = brpd.get_goa_example()

        # Use a combination of column 1 (DB) and column 2 (DB Object ID) for conversion
        brpd.identifiers_to_iris(df, column=1, prefix_column=0)
    """
    column = _norm_column(df, column)
    if prefix_column is None and prefix is None:
        raise PrefixLocationError
    elif prefix_column is not None and prefix is not None:
        raise PrefixLocationError
    elif prefix is not None:
        norm_prefix = bioregistry.normalize_prefix(prefix)
        if norm_prefix is None:
            raise ValueError
        df[target_column or column] = df[column].map(
            functools.partial(bioregistry.get_iri, prefix=norm_prefix), na_action="ignore"
        )
    else:  # prefix_column is not None
        prefix_column = _norm_column(df, prefix_column)
        df[target_column or column] = _multi_column_map(
            df, [prefix_column, column], bioregistry.get_iri, use_tqdm=use_tqdm
        )


def _multi_column_map(
    df: pd.DataFrame, columns: list[str], func: Callable, *, use_tqdm: bool = False
) -> pd.Series:
    rows = df[columns].values
    if use_tqdm:
        rows = tqdm(rows, unit_scale=True)
    return pd.Series(
        [func(*row) if all(pd.notna(cell) for cell in row) else None for row in rows],
        index=df.index,
    )


def curies_to_iris(
    df: pd.DataFrame, column: Union[int, str], *, target_column: Optional[str] = None
) -> None:
    """Convert a column of CURIEs to IRIs.

    :param df: A dataframe
    :param column: A column in the dataframe containing CURIEs
    :param target_column:
        If given, stores the IRIs in this column. Otherwise, overwrites the
        given column in place.

    .. seealso:: :func:`iris_to_curies`
    """
    column = _norm_column(df, column)
    df[target_column or column] = df[column].map(bioregistry.get_iri, na_action="ignore")


def curies_to_identifiers(
    df: pd.DataFrame,
    column: Union[int, str],
    *,
    target_column: Optional[str] = None,
    prefix_column_name: Optional[str] = None,
) -> None:
    """Split a CURIE column into a prefix and local identifier column.

    By default, the local identifier stays in the same column unless target_column is given.
    If prefix_column_name isn't given, it's derived from the target column (if labels available)
    or just appended to the end if not

    :param df: A dataframe
    :param column: A column in the dataframe containing CURIEs
    :param target_column:
        If given, stores identifiers in this column. Else, stores in the given column
    :param prefix_column_name:
        If given, stores prefixes in this column. Else, derives the column name from the
        target column name.
    :raises ValueError:
        If no prefix_column_name is given and the auto-generated name conflicts with a column
        already in the dataframe.

    .. code-block:: python

        import bioregistry.pandas as brpd
        import pandas as pd

        df = brpd.get_goa_example()

        # column 5: GO ID - convert CURIEs directly to IRIs
        #  i.e., `GO:0003993` becomes `http://amigo.geneontology.org/amigo/term/GO:0003993`
        brpd.curies_to_identifiers(df, column=4)
    """
    column = _norm_column(df, column)
    if target_column is None:
        target_column = column
    if prefix_column_name is None:
        prefix_column_name = f"{target_column}_prefix"
        if prefix_column_name in df.columns:
            raise ValueError(
                "auto-generated prefix column is already present. please specify explicitly."
            )

    prefixes, identifiers = zip(*df[column].map(bioregistry.parse_curie, na_action="ignore"))
    df[prefix_column_name] = prefixes
    df[target_column] = identifiers


def iris_to_curies(
    df: pd.DataFrame, column: Union[int, str], *, target_column: Optional[str] = None
) -> None:
    """Convert a column of IRIs to CURIEs.

    :param df: A dataframe
    :param column: A column in the dataframe containing IRIs
    :param target_column:
        If given, stores the CURIEs in this column. Otherwise, overwrites the
        given column in place.

    .. seealso:: :func:`curies_to_iris`
    """
    column = _norm_column(df, column)
    df[target_column or column] = df[column].map(bioregistry.curie_from_iri, na_action="ignore")


def pd_collapse_to_curies(df: pd.DataFrame, prefix_column: Union[int, str], identifier_column: Union[int, str], *, target_column: str) -> None:
    prefix_column = _norm_column(df, prefix_column)
    identifier_column = _norm_column(df, identifier_column)
    df[target_column] = [
        f"{prefix}:{identifier}"
        for prefix, identifier in df[[prefix_column, identifier_column]].values
    ]
    del df[prefix_column]
    del df[identifier_column]



