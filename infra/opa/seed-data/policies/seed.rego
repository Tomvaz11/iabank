package iabank.seed_data

import future.keywords.in

resources := input.planned_values.root_module.resources

seed_buckets[bucket] {
	bucket := resources[_]
	bucket.type == "aws_s3_bucket"
	bucket.values.tags.purpose == "seed-data-worm"
}

seed_bucket_versioning[bucket_name] := ver {
	ver := resources[_]
	ver.type == "aws_s3_bucket_versioning"
	bucket_name := ver.values.bucket
}

seed_bucket_encryption[bucket_name] := enc {
	enc := resources[_]
	enc.type == "aws_s3_bucket_server_side_encryption_configuration"
	bucket_name := enc.values.bucket
}

seed_bucket_object_lock[bucket_name] := lock {
	lock := resources[_]
	lock.type == "aws_s3_bucket_object_lock_configuration"
	bucket_name := lock.values.bucket
}

seed_queues[queue] {
	queue := resources[_]
	queue.type == "aws_elasticache_replication_group"
	queue.values.tags.purpose == "seed-data-queue"
}

transit_mounts[mount] {
	mount := resources[_]
	mount.type == "vault_mount"
	contains(mount.values.path, "seed-data")
	mount.values.type == "transit"
}

transit_keys[key] {
	key := resources[_]
	key.type == "vault_transit_secret_backend_key"
}

vault_policies[pol] {
	pol := resources[_]
	pol.type == "vault_policy"
}

deny[msg] {
	count(seed_buckets) == 0
	msg := "Nenhum bucket WORM (purpose=seed-data-worm) encontrado."
}

deny[msg] {
	bucket := seed_buckets[_]
	not bucket.values.object_lock_enabled
	msg := sprintf("%s deve habilitar object_lock_enabled.", [bucket.address])
}

deny[msg] {
	bucket := seed_buckets[_]
	not has_required_tags(bucket.values.tags)
	msg := sprintf("%s precisa das tags obrigatórias (service/environment/tenant/off_peak_window_utc).", [bucket.address])
}

deny[msg] {
	bucket := seed_buckets[_]
	not valid_off_peak(bucket.values.tags.off_peak_window_utc)
	msg := sprintf("%s off_peak_window_utc inválido ou ausente.", [bucket.address])
}

deny[msg] {
	bucket := seed_buckets[_]
	not versioning_enabled(bucket.values.bucket)
	msg := sprintf("%s deve ter versioning habilitado.", [bucket.values.bucket])
}

deny[msg] {
	bucket := seed_buckets[_]
	not encryption_kms_enabled(bucket.values.bucket)
	msg := sprintf("%s deve usar SSE-KMS (aws:kms) com chave dedicada.", [bucket.values.bucket])
}

deny[msg] {
	bucket := seed_buckets[_]
	not lock_retention_ok(bucket.values.bucket)
	msg := sprintf("%s deve ter Object Lock COMPLIANCE >=365 dias.", [bucket.values.bucket])
}

deny[msg] {
	count(seed_queues) == 0
	msg := "Fila curta (Elasticache) para seeds não encontrada (purpose=seed-data-queue)."
}

deny[msg] {
	queue := seed_queues[_]
	not queue.values.at_rest_encryption_enabled
	msg := sprintf("%s deve ter at_rest_encryption_enabled=true.", [queue.address])
}

deny[msg] {
	queue := seed_queues[_]
	not queue.values.transit_encryption_enabled
	msg := sprintf("%s deve ter transit_encryption_enabled=true.", [queue.address])
}

deny[msg] {
	queue := seed_queues[_]
	not queue.values.automatic_failover_enabled
	msg := sprintf("%s deve habilitar automatic_failover_enabled.", [queue.address])
}

deny[msg] {
	queue := seed_queues[_]
	queue.values.snapshot_retention_limit < 1
	msg := sprintf("%s deve manter ao menos um snapshot para rollback.", [queue.address])
}

deny[msg] {
	queue := seed_queues[_]
	not maintenance_range_valid(queue.values.maintenance_window)
	msg := sprintf("%s maintenance_window inválido, use ddd:HH:MM-ddd:HH:MM.", [queue.address])
}

deny[msg] {
	queue := seed_queues[_]
	not valid_off_peak(queue.values.tags.off_peak_window_utc)
	msg := sprintf("%s off_peak_window_utc inválido ou ausente.", [queue.address])
}

deny[msg] {
	queue := seed_queues[_]
	off_peak := parse_off_peak(queue.values.tags.off_peak_window_utc)
	mw := maintenance_range(queue.values.maintenance_window)
	not time_in_window(off_peak, mw.start)
	msg := sprintf("%s maintenance_window fora da janela off-peak (%s).", [queue.address, queue.values.tags.off_peak_window_utc])
}

deny[msg] {
	queue := seed_queues[_]
	off_peak := parse_off_peak(queue.values.tags.off_peak_window_utc)
	mw := maintenance_range(queue.values.maintenance_window)
	not time_in_window(off_peak, mw.end)
	msg := sprintf("%s maintenance_window fora da janela off-peak (%s).", [queue.address, queue.values.tags.off_peak_window_utc])
}

deny[msg] {
	mount := transit_mounts[_]
	mount.values.default_lease_ttl_seconds > 3600
	msg := sprintf("%s default_lease_ttl_seconds deve ser <=3600 (fail-close).", [mount.address])
}

deny[msg] {
	key := transit_keys[_]
	key.values.exportable
	msg := sprintf("%s não deve ser exportable.", [key.address])
}

deny[msg] {
	key := transit_keys[_]
	key.values.deletion_allowed
	msg := sprintf("%s não deve permitir delete de chave.", [key.address])
}

deny[msg] {
	key := transit_keys[_]
	not key.values.convergent_encryption
	msg := sprintf("%s deve habilitar convergent_encryption para FPE determinístico.", [key.address])
}

deny[msg] {
	key := transit_keys[_]
	not key.values.derived
	msg := sprintf("%s deve ter derived=true para separar chaves por tenant/ambiente.", [key.address])
}

deny[msg] {
	pol := vault_policies[_]
	not policy_covers_paths(pol.values.policy)
	msg := sprintf("%s deve cobrir encrypt/decrypt/rewrap e leitura da chave Transit.", [pol.address])
}

has_required_tags(tags) {
	tags.service
	tags.environment
	tags.tenant
	tags.off_peak_window_utc
}

valid_off_peak(window) {
	regex.match(`^[0-2][0-9]:[0-5][0-9]-[0-2][0-9]:[0-5][0-9]$`, window)
}

versioning_enabled(bucket_name) {
	ver := seed_bucket_versioning[bucket_name]
	some cfg in ver.values.versioning_configuration
	lower(cfg.status) == "enabled"
}

encryption_kms_enabled(bucket_name) {
	enc := seed_bucket_encryption[bucket_name]
	some rule in enc.values.rule
	some def in rule.apply_server_side_encryption_by_default
	def.sse_algorithm == "aws:kms"
	def.kms_master_key_id != ""
}

lock_retention_ok(bucket_name) {
	lock := seed_bucket_object_lock[bucket_name]
	some r in lock.values.rule
	some dr in r.default_retention
	lower(dr.mode) == "compliance"
	dr.days >= 365
}

parse_off_peak(window) = {"start": s, "end": e} {
	valid_off_peak(window)
	parts := split(window, "-")
	s := hhmm_to_minutes(parts[0])
	e := hhmm_to_minutes(parts[1])
}

maintenance_range(window) = {"start": s, "end": e} {
	maintenance_range_valid(window)
	parts := split(window, "-")
	start_parts := split(parts[0], ":")
	end_parts := split(parts[1], ":")
	start_time := sprintf("%s:%s", [start_parts[1], start_parts[2]])
	end_time := sprintf("%s:%s", [end_parts[1], end_parts[2]])
	s := hhmm_to_minutes(start_time)
	e := hhmm_to_minutes(end_time)
}

maintenance_range_valid(window) {
	parts := split(window, "-")
	count(parts) == 2
	start_parts := split(parts[0], ":")
	end_parts := split(parts[1], ":")
	count(start_parts) == 3
	count(end_parts) == 3
}

hhmm_to_minutes(val) = total {
	segments := split(val, ":")
	hours := to_number(segments[0])
	minutes := to_number(segments[1])
	total := hours * 60 + minutes
}

time_in_window(off_peak, val) {
	start := off_peak.start
	end := off_peak.end
	start <= end
	val >= start
	val <= end
}

time_in_window(off_peak, val) {
	start := off_peak.start
	end := off_peak.end
	start > end
	val >= start
}

time_in_window(off_peak, val) {
	start := off_peak.start
	end := off_peak.end
	start > end
	val <= end
}

policy_covers_paths(policy) {
	contains(policy, "encrypt/")
	contains(policy, "decrypt/")
	contains(policy, "rewrap/")
	contains(policy, "keys/")
}
