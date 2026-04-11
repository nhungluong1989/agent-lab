# Code Conventions

## Language & Runtime

- Python 3.10+
- PySpark for all ETL workloads
- Type hints required on all function signatures

## Naming Patterns

| Element | Convention | Example |
|---|---|---|
| Module / file | `snake_case` | `user_events.py` |
| Class | `PascalCase` | `OrderTransformer` |
| Function / method | `snake_case` | `read_raw_events()` |
| Variable | `snake_case` | `raw_df`, `user_id` |
| Constant | `UPPER_SNAKE_CASE` | `MAX_RETRY_COUNT` |
| Spark DataFrame | suffix `_df` | `orders_df`, `cleaned_df` |
| Spark temp view | `snake_case` string | `"raw_orders"` |
| ETL job file | `<domain>_<stage>.py` | `orders_transform.py` |

## File Organization

```
project/
├── src/
│   ├── jobs/               # entry points — one file per ETL job
│   │   └── orders_daily.py
│   ├── transforms/         # pure transformation logic (no I/O)
│   │   └── orders.py
│   ├── readers/            # data source abstractions
│   │   └── delta_reader.py
│   ├── writers/            # data sink abstractions
│   │   └── delta_writer.py
│   └── utils/              # shared helpers (schema, logging, config)
│       ├── schema.py
│       └── spark_session.py
├── tests/
│   ├── unit/
│   └── integration/
├── conf/                   # environment configs (YAML/TOML, no secrets)
└── notebooks/              # exploratory only, not production code
```

- `jobs/` files are thin orchestrators — they wire readers, transforms, and writers
- Business logic lives exclusively in `transforms/`
- No Spark logic in `utils/` except session creation

## Import Ordering

Follow PEP 8 + isort grouping, separated by blank lines:

```python
# 1. stdlib
import os
from datetime import date

# 2. third-party
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType

# 3. internal
from src.utils.spark_session import get_spark
from src.transforms.orders import clean_orders
```

- Always import `pyspark.sql.functions as F` — never use bare `col`, `lit`, etc.
- Never use wildcard imports (`from pyspark.sql.functions import *`)

## Spark ETL Patterns

### Job structure

```python
# src/jobs/orders_daily.py
from src.readers.delta_reader import read_delta
from src.transforms.orders import clean_orders, aggregate_orders
from src.writers.delta_writer import write_delta
from src.utils.spark_session import get_spark

def run(env: str) -> None:
    spark = get_spark(app_name="orders_daily")
    raw_df = read_delta(spark, path=f"s3://bucket/{env}/raw/orders")
    cleaned_df = clean_orders(raw_df)
    agg_df = aggregate_orders(cleaned_df)
    write_delta(agg_df, path=f"s3://bucket/{env}/curated/orders", mode="overwrite")

if __name__ == "__main__":
    run(env=os.getenv("ENV", "dev"))
```

### Transform functions

```python
# src/transforms/orders.py
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

def clean_orders(df: DataFrame) -> DataFrame:
    return (
        df
        .filter(F.col("status").isNotNull())
        .withColumn("order_date", F.to_date(F.col("order_ts")))
        .drop("_corrupt_record")
    )
```

- Each transform is a **pure function**: `DataFrame → DataFrame`
- No SparkSession references inside transforms
- Chain `.withColumn` / `.filter` calls using method chaining with parentheses

### SparkSession

```python
# src/utils/spark_session.py
from pyspark.sql import SparkSession

def get_spark(app_name: str) -> SparkSession:
    return SparkSession.builder.appName(app_name).getOrCreate()
```

- One `get_spark()` call per job entry point — never create sessions inside transforms
- Use `getOrCreate()` so tests can inject a pre-configured session

## Architectural Decisions

- **No SQL strings in transforms** — use DataFrame API; reserve Spark SQL for notebooks/exploration
- **Schema-on-read with explicit schemas** — define `StructType` for all external sources, never infer in production
- **Immutable DataFrames** — never reassign the same variable name after transformation; use descriptive names (`raw_df` → `cleaned_df` → `agg_df`)
- **Partitioning** — always specify `partitionBy` on writes for large tables; document partition columns in `conf/`
- **No `.collect()` in production** — only allowed in tests or for single-value aggregations

## Anti-Patterns to Avoid

```python
# ❌ bare function names from pyspark.sql.functions
from pyspark.sql.functions import col, lit
df.filter(col("id").isNotNull())

# ✅ always alias as F
from pyspark.sql import functions as F
df.filter(F.col("id").isNotNull())

# ❌ schema inference on external data
df = spark.read.json("s3://bucket/events/")

# ✅ explicit schema
df = spark.read.schema(EVENTS_SCHEMA).json("s3://bucket/events/")

# ❌ logic mixed into job entry point
def run():
    df = spark.read.parquet(...)
    df = df.filter(col("x") > 0).groupBy("y").count()  # transform logic here
    df.write.parquet(...)

# ✅ delegate to transforms/
def run():
    raw_df = read_parquet(spark, ...)
    result_df = aggregate_events(raw_df)
    write_parquet(result_df, ...)

# ❌ collect inside a loop
for row in df.collect():
    process(row)

# ✅ use Spark operations end-to-end
df.foreach(process)
```

## General Rules

- Max line length: 100 characters
- Use `black` for formatting, `ruff` for linting
- All public functions must have a docstring if logic is non-obvious
- No hardcoded paths, bucket names, or credentials — use `conf/` or environment variables
- Log at job boundaries (start, end, row counts) using Python `logging`, not `print`
