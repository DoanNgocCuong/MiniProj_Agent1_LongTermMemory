```python
python evaluate_retrieval.py --test

```

```
================================================================================
 📊 FINAL RETRIEVAL RESULTS
================================================================================

Overall Metrics:
   Recall@5:    4.06%
   Precision@5: 1.32%
   MRR:               0.057

Per-Category Recall@5:
   Single-hop     :  3.65% (32 questions)
   Temporal       :  5.41% (37 questions)
   Multi-hop      :  0.00% (13 questions)
   Open-domain    :  4.29% (70 questions)

Latency Statistics:
   Mean:  0.17s
   P50:   0.16s
   P95:   0.20s
   P99:   0.25s

================================================================================

💾 Results saved to: ./results/retrieval_results_20260105_110159.json

✅ Benchmark completed!


```

---

```
================================================================================
 Conversation conv-26 Summary:
   Avg Recall@5: 13.93%
   Found: 25/152
================================================================================


================================================================================
 📊 FINAL RETRIEVAL RESULTS
================================================================================

Overall Metrics:
   Recall@5:    13.93%
   Precision@5: 3.42%
   MRR:               0.099

Per-Category Recall@5:
   Single-hop     : 11.46% (32 questions)
   Temporal       : 16.22% (37 questions)
   Multi-hop      :  3.85% (13 questions)
   Open-domain    : 15.71% (70 questions)

Latency Statistics:
   Mean:  0.81s
   P50:   0.45s
   P95:   0.93s
   P99:   10.26s

================================================================================

💾 Results saved to: ./results/retrieval_results_20260105_113201.json

✅ Benchmark completed!
(.locust_env) PS D:\GIT\MemoryEvaluation_T1_2026> 
```
