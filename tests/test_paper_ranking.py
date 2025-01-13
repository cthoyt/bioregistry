"""Test for checking the paper ranking model."""

import datetime
import json
import tempfile
import unittest
import unittest.mock
from pathlib import Path

from bioregistry.analysis.paper_ranking import runner
from bioregistry.constants import BIOREGISTRY_PATH, CURATED_PAPERS_PATH

HERE = Path(__file__).parent.resolve()
RESOURCES = HERE.joinpath("resources")
MOCK_DATA_PATH = RESOURCES.joinpath("mock_pubmed_data.json")
MOCK_SEARCH_PATH = RESOURCES.joinpath("mock_search.json")


class TestPaperRanking(unittest.TestCase):
    """Tests the paper ranking model."""

    @unittest.mock.patch("bioregistry.analysis.paper_ranking._get_metadata_for_ids")
    @unittest.mock.patch("bioregistry.analysis.paper_ranking._get_ids")
    def test_pipeline(self, mock_get_metadata_for_ids, mock_get_ids):
        """Smoke test to ensure pipeline runs successfully without error."""
        # set the data that gets returned by each of the INDRA-wrapping
        # funcs using JSON files in the tests/resources/ folder
        mock_get_metadata_for_ids.return_value = json.loads(MOCK_DATA_PATH.read_text())
        mock_get_ids.return_value = {}

        # these are dummy values, since we will mock
        # the functions that use them
        start_date = datetime.date.today().isoformat()
        end_date = datetime.date.today().isoformat()

        with tempfile.TemporaryDirectory() as directory:
            directory_ = Path(directory)

            runner(
                # TODO create test data
                bioregistry_file=BIOREGISTRY_PATH,
                # TODO create test data
                curated_papers_path=CURATED_PAPERS_PATH,
                start_date=start_date,
                end_date=end_date,
                include_remote=False,
                output_path=directory_,
            )

            # TODO ideally the tests check the actual functionality, and not the I/O,
            # using some test data instead of live real data, which changes over time

            # Check if the evaluation file was created
            evaluation_file = directory_.joinpath("evaluation.tsv")
            self.assertTrue(evaluation_file.exists(), f"{evaluation_file} was not created")

            # Check if the importances file was created
            importances_file = directory_.joinpath("importances.tsv")
            self.assertTrue(importances_file.exists(), f"{importances_file} was not created")


if __name__ == "__main__":
    unittest.main()
