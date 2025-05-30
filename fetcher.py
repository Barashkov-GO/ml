CONN_STR = """
    host={}
    port={}
    dbname={}
    user={}
    password={}
    target_session_attrs=read-write
"""

READ_CSV_KEYS = {
    "sep",
    "delimiter",
    "header",
    "names",
    "index_col",
    "usecols",
    "dtype",
    "engine",
    "converters",
    "true_values",
    "false_values",
    "skiprows",
    "nrows",
    "na_values",
    "keep_default_na",
    "na_filter",
    "skip_blank_lines",
    "parse_dates",
    "infer_datetime_format",
    "dayfirst",
    "cache_dates",
    "iterator",
    "chunksize",
    "compression",
    "thousands",
    "decimal",
    "lineterminator",
    "quotechar",
    "quoting",
    "doublequote",
    "escapechar",
    "comment",
    "encoding",
    "encoding_errors",
    "dialect",
    "error_bad_lines",
    "warn_bad_lines",
    "on_bad_lines",
    "delim_whitespace",
    "low_memory",
    "memory_map",
    "float_precision",
}


class Fetcher:
    def __init__(
        self, creds_file_path, sqls_path, host="gp.data.lmru.tech", port=5432, db="adb"
    ):
        with open(creds_file_path, "r") as file:
            self.user, self.pswd = file.read().split("\n")

        self.sql_path = sqls_path

        self.conn_str = CONN_STR.format(host, port, db, self.user, self.pswd)
        self.ch_conn = {
            "host": host,
            "port": port,
            "user": self.user,
            "password": self.pswd,
            "connect_timeout": 10,
        }
        if len(db) > 0:
            self.ch_conn["database"] = db

    def __reloc_kwargs(self, **kwargs):
        return (
            {k: v for k, v in kwargs.items() if k in READ_CSV_KEYS},
            {k: v for k, v in kwargs.items() if k not in READ_CSV_KEYS},
        )

    def pg_test_conn(self):
        import psycopg2

        try:
            with psycopg2.connect(self.conn_str, connect_timeout=10) as conn:
                print("Успешное подключение к базе данных!")
        except psycopg2.Error as e:
            print(f"Ошибка подключения к базе данных: {e}")

    def ch_test_conn(self):
        import clickhouse_connect

        try:
            client = clickhouse_connect.get_client(**self.ch_conn)
            client.query("SELECT 1")
            print("Успешное подключение к базе данных!")
        except Exception as e:
            print(f"Ошибка подключения к базе данных: {e}")

    def pg_exec_query_w_return(self, filename, **kwargs):
        import psycopg2
        import pandas as pd
        import tempfile

        read_csv_kwargs, fmt_kwargs = self.__reloc_kwargs(**kwargs)

        with open(f"{self.sql_path}/{filename}", "r") as file:
            query = file.read().format(**fmt_kwargs).rstrip().rstrip(";")

        with psycopg2.connect(self.conn_str) as conn:
            cur = conn.cursor()
            cur.execute(query)
            with tempfile.TemporaryFile() as tmpfile:
                head = "HEADER"
                copy_sql = f"COPY ({query}) TO STDOUT WITH CSV {head}"
                cur.copy_expert(copy_sql, tmpfile)
                tmpfile.seek(0)
                df = pd.read_csv(tmpfile, **read_csv_kwargs)
            conn.commit()
            cur.close()
        conn.close()

        return df

    def ch_exec_query_w_return(self, filename, d_type=[], **kwargs):
        import clickhouse_connect
        import pandas as pd

        read_csv_kwargs, fmt_kwargs = self.__reloc_kwargs(**kwargs)

        with open(f"{self.sql_path}/{filename}", "r") as file:
            query = file.read().format(**fmt_kwargs).rstrip().rstrip(";")

        client = clickhouse_connect.get_client(**self.ch_conn)
        result = client.query(query)
        result_rows = result.result_rows
        df = pd.DataFrame(result_rows, columns=result.column_names)

        if d_type:
            df = df.astype(d_type)

        return df

    def pg_exec_many_queries(
        self,
        filenames_prep,
        filename,
        filename_close,
        d_type=[],
        parse_dates=None,
        **kwargs,
    ):
        import psycopg2
        import pandas as pd
        import tempfile

        read_csv_kwargs, fmt_kwargs = self.__reloc_kwargs(**kwargs)

        with psycopg2.connect(self.conn_str) as conn:
            cur = conn.cursor()
            if filenames_prep:
                for filename_sub in filenames_prep:
                    with open(f"{self.sql_path}/{filename_sub}", "r") as file:
                        query = file.read().format(**fmt_kwargs)
                        cur.execute(query)
                        conn.commit()
            with tempfile.TemporaryFile() as tmpfile:
                head = "HEADER"
                with open(f"{self.sql_path}/{filename}", "r") as file:
                    query = file.read().format(**fmt_kwargs).rstrip().rstrip(";")
                copy_sql = f"COPY ({query}) TO STDOUT WITH CSV {head}"
                cur.copy_expert(copy_sql, tmpfile)
                tmpfile.seek(0)
                df = pd.read_csv(tmpfile, **read_csv_kwargs)
            if filename_close:
                with open(f"{self.sql_path}/{filename_close}", "r") as file:
                    query = file.read().format(**fmt_kwargs)
                    cur.execute(query)
            conn.commit()
            cur.close()

        return df

    def ch_exec_many_queries(
        self, filenames_prep, filename, filename_close, d_type=[], **kwargs
    ):
        import clickhouse_connect
        import pandas as pd

        read_csv_kwargs, fmt_kwargs = self.__reloc_kwargs(**kwargs)

        client = clickhouse_connect.get_client(**self.ch_conn)

        for filename in filenames_prep:
            with open(f"{self.sql_path}/{filename}", "r") as file:
                query = file.read().format(**fmt_kwargs)
                client.command(query)

        with open(f"{self.sql_path}/{filename}", "r") as file:
            query = file.read().format(**fmt_kwargs).rstrip().rstrip(";")

        result = client.query(query)
        result_rows = result.result_rows
        df = pd.DataFrame(result_rows, columns=result.column_names)

        if d_type:
            df = df.astype(d_type)

        with open(f"{self.sql_path}/{filename_close}", "r") as file:
            query = file.read().format(**fmt_kwargs)
            client.command(query)

        return df
