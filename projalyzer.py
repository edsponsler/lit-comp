import os
import subprocess
import re
from datetime import datetime

def get_git_log():
    """
    Fetches the git log with a specific format.
    Returns a list of commit messages.
    """
    try:
        # Using a format that's easy to parse: hash, author, relative date, subject
        log_format = "--pretty=format:%H|%an|%ar|%s"
        result = subprocess.run(
            ["git", "log", log_format],
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8'
        )
        # Corrected the split method with a closing quote
        return result.stdout.strip().split('\n')
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error getting git log: {e}")
        return []

def find_entry_points():
    """
    Scans the repository for common application entry points.
    Returns a list of potential entry point files.
    """
    common_entry_points = [
        "app.py", "main.py", "index.js", "server.js", "manage.py"
    ]
    found_entry_points = []
    for root, _, files in os.walk("."):
        if ".git" in root:
            continue
        for file in files:
            if file in common_entry_points:
                found_entry_points.append(os.path.join(root, file))
    return found_entry_points

def read_relevant_files():
    """
    Reads README.md and ARCHITECTURE.md if they exist.
    Returns a dictionary with the file contents.
    """
    files_to_read = ["README.md", "ARCHITECTURE.md"]
    content = {}
    for file_name in files_to_read:
        if os.path.exists(file_name):
            try:
                with open(file_name, 'r', encoding='utf-8') as f:
                    content[file_name] = f.read()
            except Exception as e:
                print(f"Error reading {file_name}: {e}")
    return content

def analyze_files_for_resources():
    """
    Scans all files in the repository for keywords related to Google Cloud services.
    Returns a set of identified services.
    """
    services = set()
    gcp_regex = re.compile(
        r'\b(GCS|Google Cloud Storage|BigQuery|Cloud Run|Vertex AI|Cloud Functions|Compute Engine|GKE|Google Kubernetes Engine)\b',
        re.IGNORECASE
    )
    for root, _, files in os.walk("."):
        if ".git" in root:
            continue
        for file in files:
            if file.endswith(('.py', '.md', '.yaml', '.yml', '.json', '.txt')):
                try:
                    with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                        content = f.read()
                        matches = gcp_regex.findall(content)
                        for match in matches:
                            if "storage" in match.lower() or "gcs" in match.lower():
                                services.add("Google Cloud Storage")
                            elif "bigquery" in match.lower():
                                services.add("BigQuery")
                            elif "run" in match.lower():
                                services.add("Cloud Run")
                            elif "vertex" in match.lower():
                                services.add("Vertex AI")
                            elif "functions" in match.lower():
                                services.add("Cloud Functions")
                            elif "compute" in match.lower() or "gce" in match.lower():
                                services.add("Compute Engine")
                            elif "kubernetes" in match.lower() or "gke" in match.lower():
                                services.add("Google Kubernetes Engine")
                except (IOError, UnicodeDecodeError):
                    # Ignore files that can't be read or have decoding errors
                    pass
    return list(services)

def generate_report(commit_logs, file_contents, entry_points, resources):
    """
    Generates the final markdown report.
    """
    report = f"# Project Analysis Report ({datetime.now().strftime('%Y-%m-%d')})\n\n"

    report += "## Project Overview\n\n"
    if "README.md" in file_contents:
        report += "### From README.md\n\n"
        report += f"{file_contents['README.md']}\n\n"
    else:
        report += "No README.md found.\n\n"

    if "ARCHITECTURE.md" in file_contents:
        report += "### From ARCHITECTURE.md\n\n"
        report += f"{file_contents['ARCHITECTURE.md']}\n\n"

    report += "## Repository Structure\n\n"
    report += "### Entry Points\n\n"
    if entry_points:
        report += "Potential entry points found:\n"
        for entry in entry_points:
            report += f"- `{entry}`\n"
    else:
        report += "No common entry points found.\n"
    report += "\n"

    report += "### Resources and Services\n\n"
    if resources:
        report += "The following Google Cloud services appear to be used:\n"
        for resource in resources:
            report += f"- {resource}\n"
    else:
        report += "No Google Cloud services detected in the codebase.\n"
    report += "\n"

    report += "## Commit History\n\n"
    if commit_logs:
        report += "### Commit Narrative\n\n"
        report += "The project's development history, as told by the commit messages, is as follows:\n\n"
        for log in reversed(commit_logs):
            parts = log.split('|', 3)
            if len(parts) == 4:
                _, author, date, message = parts
                report += f"- **{date}**: {message.strip()} (by *{author}*)\n"
    else:
        report += "No commit history found.\n"

    with open("projalyzer_out.md", "w", encoding="utf-8") as f:
        f.write(report)

    print("Analysis complete. Report saved to projalyzer_out.md")

def main():
    """
    Main function to run the repository analysis.
    """
    print("Analyzing Git repository...")
    logs = get_git_log()
    print(f"Found {len(logs)} commits.")
    files = read_relevant_files()
    print(f"Found {len(files)} relevant files: {list(files.keys())}")
    entry_points = find_entry_points()
    print(f"Found {len(entry_points)} potential entry points.")
    resources = analyze_files_for_resources()
    print(f"Found {len(resources)} potential resources.")
    generate_report(logs, files, entry_points, resources)

if __name__ == "__main__":
    main()