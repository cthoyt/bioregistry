import requests
import json
import click
import pandas as pd
import logging
import matplotlib.pyplot as plt
from dateutil.parser import isoparse
from dateutil import tz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for the GitHub repository information and API URL
GITHUB_API_URL = "https://api.github.com"
REPO_OWNER = "biopragmatics"
REPO_NAME = "bioregistry"
BRANCH = "main"
FILE_PATH = "src/bioregistry/data/bioregistry.json"


def get_commit_before_date(date, owner, name, branch):
    """
    Get the commit before a given date.

    Args:
        date (datetime): The date to get the commit before.
        owner (str): The repository owner.
        name (str): The repository name.
        branch (str): The branch name.

    Returns:
        str: The SHA of the commit before the given date, or None if no commit is found.
    """
    url = f"{GITHUB_API_URL}/repos/{owner}/{name}/commits"
    params = {"sha": branch, "until": date.isoformat()}
    response = requests.get(url, params=params)
    response.raise_for_status()
    commits = response.json()
    if commits:
        first_commit = commits[0]
        if "sha" in first_commit:
            return first_commit["sha"]
        else:
            logger.warning("No 'sha' field found in the first commit.")
    else:
        logger.warning(f"No commits found before {date}")
    return None


def get_file_at_commit(owner, name, file_path, commit_sha):
    """
    Get the file content at a specific commit.

    Args:
        owner (str): The repository owner.
        name (str): The repository name.
        file_path (str): The file path in the repository.
        commit_sha (str): The commit SHA.

    Returns:
        dict: The file content as a dictionary.
    """
    url = f"{GITHUB_API_URL}/repos/{owner}/{name}/contents/{file_path}"
    params = {"ref": commit_sha}
    response = requests.get(url, params=params)
    response.raise_for_status()
    file_info = response.json()
    download_url = file_info["download_url"]
    file_content_response = requests.get(download_url)
    file_content_response.raise_for_status()
    return json.loads(file_content_response.text)


def compare_bioregistry(old_data, new_data):
    """
    Compare two versions of the bioregistry data.

    Args:
        old_data (dict): The old bioregistry data.
        new_data (dict): The new bioregistry data.

    Returns:
        tuple: Sets of added prefixes, deleted prefixes, and a count of updated prefixes, along with update details.
    """
    old_prefixes = set(old_data.keys())
    new_prefixes = set(new_data.keys())

    added_prefixes = new_prefixes - old_prefixes
    deleted_prefixes = old_prefixes - new_prefixes
    updated_prefixes = 0
    update_details = []

    for prefix in old_prefixes & new_prefixes:
        if old_data[prefix] != new_data[prefix]:
            updated_prefixes += 1
            changes = compare_entries(old_data[prefix], new_data[prefix])
            update_details.append((prefix, changes))

    return added_prefixes, deleted_prefixes, updated_prefixes, update_details


def compare_entries(old_entry, new_entry):
    """
    Compare individual entries for detailed changes.

    Args:
        old_entry (dict): The old entry data.
        new_entry (dict): The new entry data.

    Returns:
        dict: A dictionary of changes.
    """
    changes = {}
    for key in old_entry.keys() | new_entry.keys():
        if old_entry.get(key) != new_entry.get(key):
            changes[key] = (old_entry.get(key), new_entry.get(key))
    return changes


def get_all_mapping_keys(data):
    """
    Get all unique mapping keys from the bioregistry data.

    Args:
        data (dict): The bioregistry data.

    Returns:
        set: A set of all unique mapping keys.
    """
    mapping_keys = set()
    for prefix in data:
        if "mappings" in data[prefix]:
            mapping_keys.update(data[prefix]["mappings"].keys())
    return mapping_keys


def get_data(date1, date2):
    """
    Retrieve and compare bioregistry data between two dates.

    Args:
        date1 (str): The starting date in ISO format.
        date2 (str): The ending date in ISO format.

    Returns:
        tuple: Data on added, deleted, and updated prefixes, update details, and old and new bioregistry data.
    """
    date1 = isoparse(date1).astimezone(tz.tzutc())
    date2 = isoparse(date2).astimezone(tz.tzutc())

    old_commit = get_commit_before_date(date1, REPO_OWNER, REPO_NAME, BRANCH)
    new_commit = get_commit_before_date(date2, REPO_OWNER, REPO_NAME, BRANCH)

    if not old_commit:
        logger.error(f"Couldn't find commit before {date1}")
        return None, None, None, None, None

    if not new_commit:
        logger.error(f"Couldn't find commit before {date2}")
        return None, None, None, None, None

    old_bioregistry = get_file_at_commit(REPO_OWNER, REPO_NAME, FILE_PATH, old_commit)
    new_bioregistry = get_file_at_commit(REPO_OWNER, REPO_NAME, FILE_PATH, new_commit)

    added, deleted, updated, update_details = compare_bioregistry(old_bioregistry, new_bioregistry)

    old_mapping_keys = get_all_mapping_keys(old_bioregistry)
    new_mapping_keys = get_all_mapping_keys(new_bioregistry)
    all_mapping_keys = old_mapping_keys.union(new_mapping_keys)

    return (
        added,
        deleted,
        updated,
        update_details,
        old_bioregistry,
        new_bioregistry,
        all_mapping_keys,
    )


def summarize_changes(added, deleted, updated, update_details):
    """
    Summarize changes in the bioregistry data.

    Args:
        added (set): Set of added prefixes.
        deleted (set): Set of deleted prefixes.
        updated (int): Count of updated prefixes.
        update_details (list): List of update details.

    Returns:
        None
    """
    logger.info(f"Total Added Prefixes: {len(added)}")
    logger.info(f"Total Deleted Prefixes: {len(deleted)}")
    logger.info(f"Total Updated Prefixes: {updated}")


def visualize_changes(
    added, deleted, updated, update_details, start_date, end_date, all_mapping_keys
):
    """
    Visualize changes in the bioregistry data.

    Args:
        added (set): Set of added prefixes.
        deleted (set): Set of deleted prefixes.
        updated (int): Count of updated prefixes.
        update_details (list): List of update details.
        start_date (str): The starting date.
        end_date (str): The ending date.
        all_mapping_keys (set): Set of all mapping keys.

    Returns:
        None
    """

    main_fields = {}
    mapping_fields = {key: 0 for key in all_mapping_keys}

    if update_details:
        # Process mappings fields to exclude them
        for changes in update_details:
            for field, change in changes.items():
                if field == "mappings":
                    mappings = change[1] if isinstance(change[1], dict) else change[0]
                    if mappings:
                        for mapping_key in mappings.keys():
                            if mapping_key in mapping_fields:
                                mapping_fields[mapping_key] += 1

        # Process other fields, excluding mappings
        for changes in update_details:
            for field in changes.items():
                if field in mapping_fields or field == "mappings":
                    continue
                if field == "contributor" or field == "contributor_extras":
                    continue
                if field in main_fields:
                    main_fields[field] += 1
                else:
                    main_fields[field] = 1

        # Plot for main fields
        if main_fields:
            main_fields_df = pd.DataFrame(list(main_fields.items()), columns=["Field", "Count"])
            main_fields_df = main_fields_df.sort_values(by="Count", ascending=False)

            plt.figure(figsize=(15, 8))
            plt.bar(main_fields_df["Field"], main_fields_df["Count"], color="green")
            plt.title(f"Main Fields Updated from {start_date} to {end_date}")
            plt.ylabel("Count")
            plt.xlabel("Field")
            plt.xticks(rotation=45, ha="right")
            plt.grid(axis="y", linestyle="--", alpha=0.7)
            plt.tight_layout(pad=3.0)
            plt.show()

        # Plot for mapping fields
        if mapping_fields:
            mapping_fields_df = pd.DataFrame(
                list(mapping_fields.items()), columns=["Field", "Count"]
            )
            mapping_fields_df = mapping_fields_df.sort_values(by="Count", ascending=False)

            plt.figure(figsize=(15, 8))
            plt.bar(mapping_fields_df["Field"], mapping_fields_df["Count"], color="blue")
            plt.title(f"Mapping Fields Updated from {start_date} to {end_date}")
            plt.ylabel("Count")
            plt.xlabel("Field")
            plt.xticks(rotation=45, ha="right")
            plt.grid(axis="y", linestyle="--", alpha=0.7)
            plt.tight_layout(pad=3.0)
            plt.show()


@click.command()
@click.argument("date1")
@click.argument("date2")
def final(date1, date2):
    """
    This function processes and visualizes changes in Bioregistry data between two dates.

    Args:
        date1 (str): The starting date in the format YYYY-MM-DD.
        date2 (str): The ending date in the format YYYY-MM-DD.

    Returns:
        None
    """
    added, deleted, updated, update_details, old_data, new_data, all_mapping_keys = get_data(
        date1, date2
    )
    if added is not None and updated is not None:
        summarize_changes(added, deleted, updated, update_details)
        visualize_changes(added, deleted, updated, update_details, date1, date2, all_mapping_keys)


if __name__ == "__main__":
    final()
