#!/usr/bin/env bash
set -euo pipefail
kubectl="${KUBECTL:-kubectl --context capstone}"
$kubectl -n eventhub exec eventhub-db-0 -- psql -U eventhub -d eventhub -At -F ' ' -c "
SELECT 'events=' || (SELECT count(*) FROM events),
       'registrations=' || (SELECT count(*) FROM registrations),
       'checksum=' || md5(COALESCE((SELECT string_agg(e::text, '|' ORDER BY id) FROM events e), '')
                       || COALESCE((SELECT string_agg(r::text, '|' ORDER BY id) FROM registrations r), ''))"
