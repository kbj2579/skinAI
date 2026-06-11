#!/usr/bin/env bash
set -euo pipefail

BUCKET="s3://acne-rag-solution-727847798739-20260525"
ZIP_NAME="acne_rag_solution_kcc_license_audit_20260606.zip"
WORKDIR="${HOME}/acne_rag_cloudshell_validation"

rm -rf "${WORKDIR}"
mkdir -p "${WORKDIR}"
cd "${WORKDIR}"

aws s3 cp "${BUCKET}/deliverables/${ZIP_NAME}" .
unzip -o "${ZIP_NAME}" >/dev/null

python3 -m unittest acne_rag_solution.tests.test_engine
python3 acne_rag_solution/scripts/run_class_examples.py --llm template | tee hierarchical_14node_demo_output.md

CLASS_COUNT="$(grep -Ec '^## .*\(' hierarchical_14node_demo_output.md)"
OK_COUNT="$(grep -c '^check: OK' hierarchical_14node_demo_output.md)"

echo "class_count=${CLASS_COUNT}"
echo "ok_count=${OK_COUNT}"

if [ "${CLASS_COUNT}" != "14" ] || [ "${OK_COUNT}" != "14" ]; then
  echo "Validation failed: expected 14 classes and 14 OK checks." >&2
  exit 1
fi

aws s3 cp hierarchical_14node_demo_output.md "${BUCKET}/reports/cloudshell_hierarchical_14node_demo_output.md"
echo "Uploaded: ${BUCKET}/reports/cloudshell_hierarchical_14node_demo_output.md"
