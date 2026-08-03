## 1. Fix merge payload truncation in classifier.py

- [x] 1.1 Replace `payload[:30000]` byte-level slice with a function that truncates at the last complete JSON object boundary (`},`) when the 100,000 character limit is exceeded
- [x] 1.2 After clean truncation, close the JSON array with `]` and append a note to the user message indicating how many items were omitted
- [x] 1.3 Increase the safe payload limit from 30,000 to 100,000 characters

## 2. Add merge response validation in merger.py

- [x] 2.1 After parsing the merge LLM response, validate that expected top-level keys (`specs`, `loop_engineering`, `harness_engineering`) exist and are dicts
- [x] 2.2 Log a warning when a key is missing or of wrong type, using empty `{}` as fallback for that key only
- [x] 2.3 If ALL three categories are empty or missing after validation, log an error and trigger the programmatic fallback

## 3. Implement programmatic merge fallback

- [x] 3.1 Add a fallback function that concatenates all `ChunkItem.items` into the output structure without LLM-based deduplication
- [x] 3.2 Set `meta.merge_fallback: true` in the output when the fallback is used
- [x] 3.3 Wire the fallback into the merge flow when the LLM merge produces no useful output

## 4. Verify the fix

- [x] 4.1 Re-run `harness sources/.` with the same 139-page PDF and confirm harness.json has non-empty categories
- [x] 4.2 Run existing tests to ensure no regressions
