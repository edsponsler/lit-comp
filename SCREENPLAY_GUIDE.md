# Guide: Generating Screenplay Components

This guide explains how to use the screenplay generation tool to create screenplay components like a beat sheet or a detailed scene list from a novel.

## Overview

The screenplay workflow is an offline, batch process that takes the modern English translation of a novel and uses a generative AI model to create screenplay components.

-   **Input**: A `_prepared.json` file in Google Cloud Storage (GCS), which contains the modern English translation.
-   **Process**: The `run_screenplay_creation.py` script invokes an agent that can generate a high-level beat sheet or a detailed scene list for specific chapters.
-   **Output**: A new `.txt` file is saved to the same GCS bucket (e.g., `..._beatsheet.txt` or `..._scenes.txt`).

## Prerequisites

Before you can run the screenplay tool, you **must** have already run the book preparation workflow for the target novel. The screenplay tool depends on the `_prepared.json` file created by that process.

1.  **Set your environment**:
    ```bash
    source gcenv.sh lit-comp
    ```

2.  **Run the book preparation job**:
    ```bash
    ./run_book_prep_build.sh
    ```
    This will create the necessary `..._prepared.json` file in your GCS bucket.

## How to Run the Tool

Once the prerequisite is met, you can generate screenplay components by running the `run_screenplay_creation.py` script from the project's root directory.

First, ensure your environment is set. This configures the GCS bucket and file for the script to use.
```bash
source gcenv.sh lit-comp
```

The script requires an `--action` argument to specify what to generate.

### Generating a Beat Sheet

To generate a high-level, three-act beat sheet for the entire novel:
```bash
python -m scripts.run_screenplay_creation --action beatsheet
```
Upon completion, a new file named `..._beatsheet.txt` will be available in your GCS bucket.

### Generating a Scene List

To generate a detailed list of scenes for a specific part of the novel, use the `scenelist` action and provide a `--chapters` argument.
```bash
python -m scripts.run_screenplay_creation --action scenelist --chapters "Chapters 1 through 16"
```
Upon completion, a new file named `..._chapters_1_through_16_scenes.txt` will be available in your GCS bucket.