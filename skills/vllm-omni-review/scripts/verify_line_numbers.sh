#!/usr/bin/env bash
# verify_line_numbers.sh — Verify inline comment line numbers before posting.
#
# Usage: echo '<review_json>' | ./verify_line_numbers.sh <pr_number>
#
# Reads a review JSON (with comments array) from stdin, fetches the PR diff,
# and checks that each comment's line number points to a line in the diff
# that contains code related to the comment.
#
# Exits 0 if all lines are valid diff lines, 1 if any are outside diff hunks.

set -euo pipefail

REPO="vllm-project/vllm-omni"
PR_NUM="${1:?Usage: $0 <pr_number>}"

REVIEW_JSON=$(cat)
DIFF=$(gh pr diff "$PR_NUM" --repo "$REPO")

ERRORS=0

echo "$REVIEW_JSON" | jq -c '.comments[]' | while read -r comment; do
  FILE=$(echo "$comment" | jq -r '.path')
  LINE=$(echo "$comment" | jq -r '.line')
  BODY=$(echo "$comment" | jq -r '.body[:60]')
  
  # Extract the file's diff
  FILE_DIFF=$(echo "$DIFF" | sed -n "/^diff --git a\/${FILE//\//\/}/,/^diff --git/p" | head -n -1)
  
  if [ -z "$FILE_DIFF" ]; then
    echo "ERROR: File not in diff: ${FILE}" >&2
    ERRORS=$((ERRORS + 1))
    continue
  fi
  
  # Check if the line falls within any hunk
  IN_HUNK=false
  while IFS= read -r hunk_header; do
    # Parse @@ -old_start,old_count +new_start,new_count @@
    NEW_START=$(echo "$hunk_header" | grep -oP '\+\K[0-9]+')
    NEW_COUNT=$(echo "$hunk_header" | grep -oP '\+[0-9]+,\K[0-9]+' || echo "1")
    NEW_END=$((NEW_START + NEW_COUNT - 1))
    
    if [ "$LINE" -ge "$NEW_START" ] && [ "$LINE" -le "$NEW_END" ]; then
      IN_HUNK=true
      break
    fi
  done < <(echo "$FILE_DIFF" | grep '^@@')
  
  if [ "$IN_HUNK" = false ]; then
    echo "ERROR: Line ${LINE} in ${FILE} is outside all diff hunks" >&2
    echo "  Comment: ${BODY}..." >&2
    ERRORS=$((ERRORS + 1))
  else
    echo "OK: ${FILE}:${LINE} — ${BODY}..." >&2
  fi
done

exit $ERRORS
