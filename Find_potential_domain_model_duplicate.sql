-- Find potential domain model duplicates
SELECT
  a.name,
  COUNT(*) as duplicate_count,
  array_agg(a.file_name) as files
FROM
  python_code_chunks a
JOIN
  python_code_chunks b
ON
  a.name = b.name AND a.id != b.id
WHERE
  a.chunk_type = 'class' AND
  a.architectural_layer = 'Domain' AND
  b.architectural_layer = 'Domain' AND
  a.project_name = 'Inventory_scrape'
GROUP BY
  a.name
HAVING
  COUNT(*) > 1
ORDER BY
  COUNT(*) DESC;
