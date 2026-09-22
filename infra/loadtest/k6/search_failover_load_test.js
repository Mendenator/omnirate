import http from "k6/http";
import { check, sleep } from "k6";

// S-19: 500 RPS steady search load while a node is manually taken down
// partway through the run (see the companion runbook step in
// infra/dr/dr_drill.md "Search failover drill"). K8/K9 latency targets must
// hold, and the error rate during the failover window must stay <=0.1%.
export const options = {
  scenarios: {
    search_failover: {
      executor: "constant-arrival-rate",
      rate: 500,
      timeUnit: "1s",
      duration: "15m", // long enough to comfortably straddle a manual node-down/up
      preAllocatedVUs: 150,
      maxVUs: 600,
    },
  },
  thresholds: {
    "http_req_duration{name:search}": ["p(95)<150"], // K9
    "http_req_duration{name:autocomplete}": ["p(95)<80"], // K8
    http_req_failed: ["rate<0.001"], // <=0.1% acceptance
  },
};

const BASE_URL = __ENV.OMNIRATE_API_URL || "http://localhost:8000";
const QUERIES = ["ресторан", "эмнэлэг", "hool", "сургууль", "кафе"];

export default function () {
  const q = QUERIES[Math.floor(Math.random() * QUERIES.length)];

  const searchRes = http.get(`${BASE_URL}/api/v1/search?q=${encodeURIComponent(q)}`, { tags: { name: "search" } });
  check(searchRes, { "search status 200": (r) => r.status === 200 });

  const acRes = http.get(`${BASE_URL}/api/v1/search/autocomplete?q=${encodeURIComponent(q.slice(0, 3))}`, {
    tags: { name: "autocomplete" },
  });
  check(acRes, { "autocomplete status 200": (r) => r.status === 200 });

  sleep(0.1);
}
