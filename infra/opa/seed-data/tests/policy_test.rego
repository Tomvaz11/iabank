package iabank.seed_data

import future.keywords.in

test_valid_plan_passes {
	denies := data.iabank.seed_data.deny with input as data.seed_plan
	count(denies) == 0
}

test_live_plan_passes {
	plan := data.seed_plan_live
	plan != null
	denies := data.iabank.seed_data.deny with input as plan
	count(denies) == 0
}

test_generated_plan_allows_window_wraparound {
	denies := data.iabank.seed_data.deny with input as data.seed_plan_wraparound
	count(denies) == 0
}

test_invalid_plan_raises_denies {
	denies := data.iabank.seed_data.deny with input as data.seed_plan_invalid
	count(denies) > 0
}

test_invalid_plan_reports_object_lock {
	denies := data.iabank.seed_data.deny with input as data.seed_plan_invalid
	some msg in denies
	contains(msg, "Object Lock")
}

test_missing_resources_fail_close {
	denies := data.iabank.seed_data.deny with input as data.seed_plan_no_resources
	msg_buckets := "Nenhum bucket WORM (purpose=seed-data-worm) encontrado."
	msg_queue := "Fila curta (Elasticache) para seeds não encontrada (purpose=seed-data-queue)."
	msg_buckets in denies
	msg_queue in denies
}

test_bucket_off_peak_invalid_detected {
	denies := data.iabank.seed_data.deny with input as data.seed_plan_invalid_bucket_offpeak
	some msg in denies
	contains(msg, "off_peak_window_utc inválido")
}

test_queue_off_peak_and_maintenance_invalid_detected {
	denies := data.iabank.seed_data.deny with input as data.seed_plan_invalid_queue
	msg_offpeak := "off_peak_window_utc inválido ou ausente."
	msg_maintenance := "maintenance_window inválido, use ddd:HH:MM-ddd:HH:MM."
	some m1 in denies
	some m2 in denies
	contains(m1, msg_offpeak)
	contains(m2, msg_maintenance)
}
