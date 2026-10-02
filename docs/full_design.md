# Full design vs prototype

What the prototype simplifies or leaves out, and how the full system would do it.
Base for the "architecture" and "design discussion" parts of the presentation.

| Area | Prototype | Full design | Why simplified |
|---|---|---|---|
| Channels | Web ratings and support chats only | Add mobile app reviews and post-checkout surveys: one raw table each, one more branch in the `clean.feedback` union | Two channels already show text of different shapes (short comment, multi-turn chat) |
| Source data | Synthetic files from `data_gen/` | Daily exports from the web store, support platform and order system | No access to real systems |
| File landing | Loader uploads local files to GCS | Source systems write to the GCS landing bucket (directly, via API pull job on Cloud Run, or Storage Transfer Service) | Upload step simulates the sources |
| Load trigger | Manual run | Cloud Scheduler, or a GCS object event (Eventarc) starting the load | Scheduling is a non-goal |
| Real time | Daily batch load jobs | Pub/Sub to BigQuery (subscription or Storage Write API) replaces the load jobs; enrichment triggered per message | Daily freshness is enough for the users |
| Modeling | Clean layer as views; one orders file | Incremental, date-partitioned tables; separate customers and products tables; possibly dbt | Thousands of rows per day, views are fast enough |
| Invalid rows | Excluded in the clean views | Written to a quarantine table with the rejection reason, counted in monitoring | Keeps the clean layer simple |
| Enrichment run | Manual script, one LLM call per item | Scheduled Cloud Run Job; Vertex AI batch prediction for high volumes | Low volume |
| LLM quality | Manual spot check of a sample | Labelled set built from workbench corrections; accuracy tracked per prompt version and model | LLM accuracy eval is a non-goal |
| Human in the loop | Correct a tag only | Also re-run the LLM on selected items from the workbench (the app calls the enrichment step, which appends a new row) | One action meets the requirement; avoids the only direct call between components |
| Workbench | Streamlit run locally, no login | Deployed on Cloud Run behind IAP; `corrected_by` from the user identity | Deployment and authentication are non-goals |
| Analytics | No aggregated dashboards | Looker Studio on top of the clean views; a `product_returns` view with return rate per product over all orders | Workbench focuses on exploring single items |
| Monitoring | None | Metrics: rows loaded and rejected per source, enrichment errors and latency, share of items not enriched, share of corrected tags. Alerts via Cloud Monitoring on failed loads or error spikes | Monitoring is a non-goal |
| Operations | Resources created by hand | Terraform for bucket, datasets and IAM; CI/CD running lint and tests | Not needed for a single-user prototype |
