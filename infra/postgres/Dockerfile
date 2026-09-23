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

# The base image's baked-in libxml2 (...u5) is actually NEWER than what
# archive.debian.org's frozen bullseye/main snapshot offers (...u4) — u5 was
# a point release that only ever shipped via debian-security, which isn't
# mirrored on archive.debian.org under that suite name at all (see above).
# libxml2-dev is only available at u4 from the snapshot and needs an exact
# version match, so satisfying it means *downgrading* the already-installed
# libxml2, not upgrading it. --allow-downgrades alone only permits that if
# apt's solver decides to do it, but nothing here requests libxml2 itself,
# so the solver never considers touching it — it has to be named explicitly,
# pinned to the exact version the archive snapshot carries, to force the
# downgrade. Safe here: libxml2 isn't something pg_jsonschema.so itself
# links against (it's a JSON Schema validator, not an XML tool) — it's only
# a transitive dependency of the build tooling in this discarded builder
# stage. (This pin is tied to archive.debian.org's bullseye/main snapshot,
# which is now frozen — Check-Valid-Until is disabled above precisely
# because that snapshot isn't expected to ever change.)
#
# DEBIAN_FRONTEND=noninteractive + the dpkg confold/confdef options guard
# against a separate issue: the base image ships a locally-modified
# /etc/postgresql-common/createcluster.conf, and touching postgresql-common
# would otherwise stop to ask (hanging forever on a build with no TTY)
# whether to keep it — force-confold says "always keep the version on disk."
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends --allow-downgrades \
    -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" \
    libxml2=2.9.10+dfsg-6.7+deb11u4 \
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

# cargo pgrx install names the built artifacts after the crate (pg_jsonschema),
# not the SQL extension it registers (jsonschema_is_valid() etc., used by
# apps/backend/alembic 0001's trigger) — pg_jsonschema.so /
# pg_jsonschema.control / pg_jsonschema--0.3.3.sql, all prefixed.
FROM postgis/postgis:16-3.4
COPY --from=builder /usr/lib/postgresql/16/lib/pg_jsonschema.so /usr/lib/postgresql/16/lib/
COPY --from=builder /usr/share/postgresql/16/extension/pg_jsonschema* /usr/share/postgresql/16/extension/

# pgvector (P2-10, alembic 0007) — unlike pg_jsonschema, PGDG ships a
# prebuilt package for this one (postgresql-16-pgvector), so no Rust/cargo
# build needed. A fresh FROM starts this stage's filesystem over from the
# unmodified base image, so it needs the same apt-source fix as the builder
# stage above (a separate stage, not inherited) before `apt-get update` will
# work at all — but NOT the libxml2 pin, which was specific to
# postgresql-server-dev-16's dependency chain and doesn't come up here.
# This does pull in a postgresql-16 point-release bump as a side effect
# (PGDG's pgvector build depends on a newer postgresql-16 than the base
# image shipped) — expected and compatible within the 16.x line.
RUN sed -i \
        -e '/debian-security/d' \
        -e 's|http://deb.debian.org/debian|http://archive.debian.org/debian|g' \
        /etc/apt/sources.list \
    && echo 'Acquire::Check-Valid-Until "false";' > /etc/apt/apt.conf.d/99no-check-valid-until \
    && DEBIAN_FRONTEND=noninteractive apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        postgresql-16-pgvector \
    && rm -rf /var/lib/apt/lists/*
