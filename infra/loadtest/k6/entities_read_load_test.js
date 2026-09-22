import http from "k6/http";
import { check } from "k6";

// K2: entity read p95 <= 120ms (cache hit) @ 1,000 RPS.
export const options = {
  scenarios: {
    entity_read: {
      executor: "constant-arrival-rate",
      rate: 1000,
      timeUnit: "1s",
      duration: "10m",
      preAllocatedVUs: 200,
      maxVUs: 1000,
    },
  },
  thresholds: {
    http_req_duration: ["p(95)<120"],
    http_req_failed: ["rate<0.01"],
  },
};

const BASE_URL = __ENV.OMNIRATE_API_URL || "http://localhost:8000";
// A small hot set of pre-seeded entity IDs, comma-separated, so the run
// exercises the Redis cache path rather than cold DB reads every time.
const ENTITY_IDS = (__ENV.OMNIRATE_TEST_ENTITY_IDS || "").split(",");

export default function () {
  const id = ENTITY_IDS[Math.floor(Math.random() * ENTITY_IDS.length)];
  const res = http.get(`${BASE_URL}/api/v1/entities/${id}`);
  check(res, { "status is 200": (r) => r.status === 200 });
}
