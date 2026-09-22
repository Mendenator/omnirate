import http from "k6/http";
import { check } from "k6";
import { uuidv4 } from "https://jslib.k6.io/k6-utils/1.4.0/index.js";

// K1: POST /reviews p95 <= 250ms @ 200 RPS, 30 min.
export const options = {
  scenarios: {
    reviews_write: {
      executor: "constant-arrival-rate",
      rate: 200,
      timeUnit: "1s",
      duration: "30m",
      preAllocatedVUs: 100,
      maxVUs: 400,
    },
  },
  thresholds: {
    http_req_duration: ["p(95)<250"],
    http_req_failed: ["rate<0.01"],
  },
};

const BASE_URL = __ENV.OMNIRATE_API_URL || "http://localhost:8000";
const TOKEN = __ENV.OMNIRATE_TEST_TOKEN; // issued out-of-band against a seeded test user

export default function () {
  const entityId = __ENV.OMNIRATE_TEST_ENTITY_ID;
  const payload = JSON.stringify({
    entity_id: entityId,
    overall_score: 4 + Math.random(),
    criteria_scores: { taste: 4, service: 5 },
    body: "k6 synthetic review",
  });

  const res = http.post(`${BASE_URL}/api/v1/reviews`, payload, {
    headers: {
      "Content-Type": "application/json",
      "Idempotency-Key": uuidv4(),
      Authorization: `Bearer ${TOKEN}`,
    },
  });

  check(res, {
    "status is 201 or 409": (r) => r.status === 201 || r.status === 409,
  });
}
