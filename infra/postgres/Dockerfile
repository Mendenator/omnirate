# Postgres 16 + PostGIS + pg_jsonschema.
#
# pg_jsonschema (https://github.com/supabase/pg_jsonschema) is a pgrx extension
# with no official prebuilt image for postgis/postgis, so we build it from
# source on top of the official PostGIS image. This is the image referenced by
# infra/terraform/modules/postgres for stage/prod, and by docker-compose.yml
# for local dev.
FROM postgis/postgis:16-3.4 AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl libssl-dev pkg-config git \
    postgresql-server-dev-16 \
    && rm -rf /var/lib/apt/lists/*

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

RUN cargo install --locked cargo-pgrx --version 0.12.6 \
    && cargo pgrx init --pg16 "$(which pg_config)"

RUN git clone --depth 1 --branch v0.3.3 https://github.com/supabase/pg_jsonschema.git /tmp/pg_jsonschema
WORKDIR /tmp/pg_jsonschema
RUN cargo pgrx install --release --pg-config "$(which pg_config)"

FROM postgis/postgis:16-3.4
COPY --from=builder /usr/lib/postgresql/16/lib/jsonschema.so /usr/lib/postgresql/16/lib/
COPY --from=builder /usr/share/postgresql/16/extension/jsonschema* /usr/share/postgresql/16/extension/
