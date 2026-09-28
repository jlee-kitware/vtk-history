#!/bin/bash
# Extract review examples from the mirrored MRs, then label them on the Spark.
cd "$(dirname "$0")/.."
set -e
echo "extract start $(date)"
python3 -u extract/extract_reviews.py
echo "extract done $(date)"
python3 -u label/label_reviews.py
echo "label done $(date)"
