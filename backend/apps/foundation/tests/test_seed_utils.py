from django.test import SimpleTestCase

from backend.apps.foundation.services.seed_utils import (
    VaultTransitFPEClient,
    build_idempotency_fingerprint,
    derive_factory_seed,
)


class SeedUtilsTest(SimpleTestCase):
    def test_factory_seed_is_stable(self) -> None:
        seed_a = derive_factory_seed("tenant-a", "staging", "1.0.0", "2025-q1")
        seed_b = derive_factory_seed("tenant-a", "staging", "1.0.0", "2025-q1")
        seed_c = derive_factory_seed("tenant-a", "staging", "1.0.1", "2025-q1")

        self.assertEqual(seed_a, seed_b)
        self.assertNotEqual(seed_a, seed_c)

    def test_idempotency_fingerprint_uses_all_parts(self) -> None:
        fingerprint = build_idempotency_fingerprint("t1", "staging", "abc", "deadbeef")
        self.assertEqual(len(fingerprint), 64)
        self.assertEqual(fingerprint, build_idempotency_fingerprint("t1", "staging", "abc", "deadbeef"))
        self.assertNotEqual(fingerprint, build_idempotency_fingerprint("t1", "staging", "xyz", "deadbeef"))

    def test_vault_transit_stub_masks_with_same_length(self) -> None:
        client = VaultTransitFPEClient(transit_path="transit/seeds/staging", salt_namespace="demo")
        masked = client.mask("12345678901", salt_version="2025-q1")
        masked_again = client.mask("12345678901", salt_version="2025-q1")

        self.assertEqual(masked, masked_again)
        self.assertEqual(len(masked), len("12345678901"))

    def test_mask_allows_none_values(self) -> None:
        client = VaultTransitFPEClient(transit_path="transit/seeds/staging")
        self.assertIsNone(client.mask(None, salt_version="2025-q1"))

    def test_unmask_requires_flag(self) -> None:
        client = VaultTransitFPEClient(transit_path="transit/seeds/staging")
        with self.assertRaises(NotImplementedError):
            client.unmask("123", salt_version="2025-q1")

    def test_unmask_allows_stub_when_flag_enabled(self) -> None:
        client = VaultTransitFPEClient(
            transit_path="transit/seeds/staging",
            allow_stub_decrypt=True,
        )
        self.assertEqual("abc", client.unmask("abc", salt_version="2025-q1"))
