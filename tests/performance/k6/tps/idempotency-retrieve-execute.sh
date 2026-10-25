k6 run tests/performance/k6/tps/idempotency-retrieve-execute.tps.js  --env DURATION=60s

k6 run tests/performance/k6/tps/idempotency-retrieve.tps.js --env DURATION=60s

k6 run tests/performance/k6/tps/idempotency-execute.tps.js --env DURATION=60s



podman exec -e REDISCLI_AUTH="$REDISCLI_AUTH" arix-redis redis-cli FLUSHALL ASYNC
podman exec -e REDISCLI_AUTH="$REDISCLI_AUTH" arix-redis redis-cli --scan | head -n 10 | while IFS= read -r key; do   echo "KEY: $key";   podman exec -e REDISCLI_AUTH="$REDISCLI_AUTH" arix-redis redis-cli GET "$key"; done