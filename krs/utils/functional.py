# from difflib import SequenceMatcher
# import re, json
# from datetime import datetime

# class CustomJSONEncoder(json.JSONEncoder):
#     """JSON Encoder for complex objects not serializable by default json code."""
#     def default(self, obj):
#         if isinstance(obj, datetime):
#             # Format datetime object as a string in ISO 8601 format
#             return obj.isoformat()
#         # Let the base class default method raise the TypeError
#         return json.JSONEncoder.default(self, obj)

# def similarity(a, b):
#     return SequenceMatcher(None, a, b).ratio()

# def filter_similar_entries(log_entries):
#     unique_entries = list(log_entries)
#     to_remove = set()

#     # Compare each pair of log entries
#     for i in range(len(unique_entries)):
#         for j in range(i + 1, len(unique_entries)):
#             if similarity(unique_entries[i], unique_entries[j]) > 0.85:
#                 # Choose the shorter entry to remove, or either if they are the same length
#                 if len(unique_entries[i]) > len(unique_entries[j]):
#                     to_remove.add(unique_entries[i])
#                 else:
#                     to_remove.add(unique_entries[j])

#     # Filter out the highly similar entries
#     filtered_entries = {entry for entry in unique_entries if entry not in to_remove}
#     return filtered_entries

# def extract_log_entries(log_contents):
#     # Patterns to match different log formats
#     patterns = [
#         re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{6}Z\s+(warn|error)\s+\S+\s+(.*)', re.IGNORECASE),
#         re.compile(r'[WE]\d{4} \d{2}:\d{2}:\d{2}.\d+\s+\d+\s+(.*)'),
#         re.compile(r'({.*})')  
#     ]

#     log_entries = set()
#     # Attempt to match each line with all patterns
#     for line in log_contents.split('\n'):
#         for pattern in patterns:
#             match = pattern.search(line)
#             if match:
#                 if match.groups()[0].startswith('{'):
#                     # Handle JSON formatted log entries
#                     try:
#                         log_json = json.loads(match.group(1))
#                         if 'severity' in log_json and log_json['severity'].lower() in ['error', 'warning']:
#                             level = "Error" if log_json['severity'] == "ERROR" else "Warning"
#                             message = log_json.get('error', '') if 'error' in log_json.keys() else line
#                             log_entries.add(f"{level}: {message.strip()}")
#                         elif 'level' in log_json:
#                             level = "Error" if log_json['level'] == "error" else "Warning"
#                             message = log_json.get('msg', '')  + log_json.get('error', '')
#                             log_entries.add(f"{level}: {message.strip()}")
#                     except json.JSONDecodeError:
#                         continue  # Skip if JSON is not valid
#                 else:
#                     if len(match.groups()) == 2:
#                         level, message = match.groups()
#                     elif len(match.groups()) == 1:
#                         message = match.group(1)  # Assuming error as default
#                         level = "ERROR"  # Default if not specified in the log

#                     level = "Error" if "error" in level.lower() else "Warning"
#                     formatted_message = f"{level}: {message.strip()}"
#                     log_entries.add(formatted_message)
#                 break  # Stop after the first match

#     return filter_similar_entries(log_entries)

import json
import re
from difflib import SequenceMatcher
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CustomJSONEncoder(json.JSONEncoder):
    """JSON Encoder for complex objects not serializable by default json code."""
    def default(self, obj):
        if isinstance(obj, datetime):
            # Format datetime object as a string in ISO 8601 format
            return obj.isoformat()
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)

def similarity(a, b):
    """
    Compute the similarity ratio between two strings using SequenceMatcher.
    
    Args:
        a (str): First string to compare.
        b (str): Second string to compare.

    Returns:
        float: Similarity ratio between the two strings.
    """
    return SequenceMatcher(None, a, b).ratio()

def filter_similar_entries(log_entries):
    """
    Filter out highly similar log entries.

    Args:
        log_entries (set): Set of log entries.

    Returns:
        set: Filtered set of unique log entries.
    """
    unique_entries = list(log_entries)
    to_remove = set()

    # Compare each pair of log entries
    for i in range(len(unique_entries)):
        for j in range(i + 1, len(unique_entries)):
            if similarity(unique_entries[i], unique_entries[j]) > 0.85:
                # Choose the shorter entry to remove, or either if they are the same length
                if len(unique_entries[i]) > len(unique_entries[j]):
                    to_remove.add(unique_entries[i])
                else:
                    to_remove.add(unique_entries[j])

    # Filter out the highly similar entries
    filtered_entries = {entry for entry in unique_entries if entry not in to_remove}
    logging.info("Filtered similar entries: %d removed, %d remaining", len(to_remove), len(filtered_entries))
    return filtered_entries

def extract_log_entries(log_contents):
    """
    Extract log entries from log contents using predefined patterns.

    Args:
        log_contents (str): String containing the log contents.

    Returns:
        set: Set of extracted and filtered log entries.
    """
    patterns = [
        re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{6}Z\s+(warn|error)\s+\S+\s+(.*)', re.IGNORECASE),
        re.compile(r'[WE]\d{4} \d{2}:\d{2}:\d{2}.\d+\s+\d+\s+(.*)'),
        re.compile(r'({.*})')
    ]

    log_entries = set()
    # Attempt to match each line with all patterns
    for line in log_contents.split('\n'):
        for pattern in patterns:
            match = pattern.search(line)
            if match:
                if match.groups()[0].startswith('{'):
                    # Handle JSON formatted log entries
                    try:
                        log_json = json.loads(match.group(1))
                        severity = log_json.get('severity', '').lower()
                        level = "Error" if severity == "error" else "Warning" if severity == "warning" else None
                        if level:
                            message = log_json.get('msg', '') + log_json.get('error', '')
                            log_entries.add(f"{level}: {message.strip()}")
                    except json.JSONDecodeError as e:
                        logging.warning("Failed to decode JSON log entry: %s", e)
                        continue  # Skip if JSON is not valid
                else:
                    if len(match.groups()) == 2:
                        level, message = match.groups()
                    elif len(match.groups()) == 1:
                        message = match.group(1)  # Assuming error as default
                        level = "ERROR"  # Default if not specified in the log

                    level = "Error" if "error" in level.lower() else "Warning"
                    formatted_message = f"{level}: {message.strip()}"
                    log_entries.add(formatted_message)
                break  # Stop after the first match

    filtered_entries = filter_similar_entries(log_entries)
    logging.info("Extracted %d log entries", len(filtered_entries))
    return filtered_entries
