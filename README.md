# Next Chapter

A calm, simple job-search page for one teacher near Brighton.

- `index.html` is the whole site (Home, Jobs, Schools, Ideas, Plan).
- `data/jobs.json` is refreshed five times a day by `.github/workflows/update-jobs.yml`,
  which runs `scripts/update_jobs.py` against the DfE Teaching Vacancies open API
  (Open Government Licence) and keeps full-time teaching/leading jobs within 20 miles.
- `data/schools.json` lists primary schools within 10 miles (DfE GIAS, Nov 2026).
- Ticks, saved jobs and "new since last visit" are kept in the browser only.

Run the update by hand: `python3 scripts/update_jobs.py`
