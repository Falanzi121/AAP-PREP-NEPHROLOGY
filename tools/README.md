# Tools

## build_exam_data.py

Parses raw PREP text dumps into structured JSON plus plain-text answer keys.

```
python tools/build_exam_data.py --years 2015 2016 2017 2019 2022
```

Outputs are written to `questions/prep_<year>.json` and `keys/prep_<year>_key.txt`. Update the `--years` list to process other files. Ensure the corresponding `raw_txt/prep_<year>.txt` inputs are available before running.
