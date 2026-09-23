# Postgres 16 + PostGIS + pg_jsonschema.
#
# pg_jsonschema (https://github.com/supabase/pg_jsonschema) is a pgrx extension
# with no official prebuilt image for postgis/postgis, so we build it from
# source on top of the official PostGIS image. This is the image referenced by
# infra/terraform/modules/postgres for stage/prod, and by docker-compose.yml
# for local dev.
FROM postgis/postgis:16-3.4 AS builder

# postgis/postgis:16-3.4 is still Debian 11 (bullseye), which is old enough
# now that deb.debian.org has dropped it entirely (404s on every package).
# archive.debian.org mirrors EOL Debian releases indefinitely, but only the
# main archive — bullseye-security isn't published there under that suite
# name at all (404 on the Release file itself). That's fine here: this
# builder stage only exists to compile pg_jsonschema.so, which gets COPY'd
# into a fresh, unpatched postgis/postgis:16-3.4 final stage below anyway —
# security patches on throwaway build tools (curl, git, build-essential)
# don't change what ships. Repoint the main archive and drop -security.
RUN sed -i \
        -e '/debian-security/d' \
        -e 's|http://deb.debian.org/debian|http://archive.debian.org/debian|g' \
        /etc/apt/sources.list \
    && echo 'Acquire::Check-Valid-Until "false";' > /etc/apt/apt.conf.d/99no-check-valid-until

# archive.debian.org serves the *last* bullseye snapshot before EOL, which is
# newer than several packages already baked into this base image (e.g.
# libxml2) — apt-get install alone refuses to pull libxml2-dev because it
# can't upgrade the already-installed libxml2 to match as a side effect.
# `apt-get upgrade` first reconciles the base image with the archive
# snapshot so the subsequent install has no version conflicts to resolve.
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
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
