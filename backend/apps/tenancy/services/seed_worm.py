from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal
from http import HTTPStatus
from pathlib import Path
from typing import Any, Mapping, MutableMapping, Sequence

from django.utils import timezone

from backend.apps.tenancy.managers import use_tenant
from backend.apps.tenancy.models import EvidenceWORM, SeedRun
from backend.apps.tenancy.services.seed_runs import ProblemDetail

DEFAULT_CHECKLIST_PATH = Path(__file__).resolve().parents[4] / 'observabilidade' / 'checklists' / 'seed-worm-checklist.json'


@dataclass
class WormSignature:
    signature: str
    algorithm: str
    key_id: str
    key_version: str


@dataclass
class SeedWormOutcome:
    report: dict[str, Any]
    evidence: EvidenceWORM | None
    problem: ProblemDetail | None


class WormSigner:
    def sign(self, *, digest: str) -> WormSignature:
        raise NotImplementedError

    def verify(self, *, digest: str, signature: WormSignature) -> bool:
        raise NotImplementedError


class LocalWormSigner(WormSigner):
    """
    Stub de assinatura determinística para ambientes de teste/offline.
    """

    def __init__(self, *, key_id: str = 'local-seeds-worm', key_version: str = 'v1', algorithm: str = 'LOCAL-SHA256') -> None:
        self.key_id = key_id
        self.key_version = key_version
        self.algorithm = algorithm

    def sign(self, *, digest: str) -> WormSignature:
        salted = f'{digest}:{self.key_id}:{self.key_version}'
        signature = hashlib.sha256(salted.encode('utf-8')).hexdigest()
        return WormSignature(signature=signature, algorithm=self.algorithm, key_id=self.key_id, key_version=self.key_version)

    def verify(self, *, digest: str, signature: WormSignature) -> bool:
        expected = self.sign(digest=digest)
        return (
            expected.signature == signature.signature
            and expected.algorithm == signature.algorithm
            and expected.key_id == signature.key_id
            and expected.key_version == signature.key_version
        )


class WormStorage:
    def upload(self, *, content: bytes, retention_days: int, metadata: Mapping[str, str]) -> str:
        raise NotImplementedError

    def retrieve(self, url: str) -> bytes:
        raise NotImplementedError


class InMemoryWormStorage(WormStorage):
    """
    Armazena evidências em memória; adequado para testes/unitários.
    """

    def __init__(self) -> None:
        self._store: dict[str, bytes] = {}

    def upload(self, *, content: bytes, retention_days: int, metadata: Mapping[str, str]) -> str:
        suffix = metadata.get('seed_run_id') or f'{len(self._store) + 1}'
        url = f'worm://{suffix}'
        self._store[url] = bytes(content)
        return url

    def retrieve(self, url: str) -> bytes:
        if url not in self._store:
            raise FileNotFoundError(f'Evidência WORM não encontrada para {url}')
        return self._store[url]


class SeedWormService:
    """
    Gera relatório WORM assinado, valida checklist automatizado e verifica integridade pós-upload.
    """

    def __init__(
        self,
        *,
        storage: WormStorage | None = None,
        signer: WormSigner | None = None,
        min_retention_days: int = 365,
        enforce_on_dry_run: bool = False,
        checklist_path: Path | None = None,
    ) -> None:
        self.storage = storage or InMemoryWormStorage()
        self.signer = signer or LocalWormSigner()
        self.min_retention_days = min_retention_days
        self.enforce_on_dry_run = enforce_on_dry_run
        self.checklist_template = self._load_checklist_template(checklist_path or DEFAULT_CHECKLIST_PATH)

    def emit(
        self,
        *,
        seed_run: SeedRun,
        manifest: Mapping[str, Any] | None,
        checklist_results: Mapping[str, bool],
        retention_days: int,
        cost_estimated_brl: float | Decimal = 0,
        cost_actual_brl: float | Decimal = 0,
        cost_model_version: str = '',
        extra_metadata: Mapping[str, Any] | None = None,
    ) -> SeedWormOutcome:
        """
        Constrói, assina, persiste e verifica o relatório WORM.
        Retorna ProblemDetail em caso de falha (fail-close).
        """
        if seed_run.dry_run and not self.enforce_on_dry_run:
            report = self._build_report(
                seed_run=seed_run,
                manifest=manifest,
                checklist=self._checklist_payload(checklist_results),
                status='skipped',
                cost_estimated_brl=cost_estimated_brl,
                cost_actual_brl=cost_actual_brl,
                cost_model_version=cost_model_version,
                extra_metadata=extra_metadata or {},
            )
            return SeedWormOutcome(report=report, evidence=None, problem=None)

        if retention_days < self.min_retention_days:
            problem = ProblemDetail(
                status=HTTPStatus.SERVICE_UNAVAILABLE,
                title='worm_retention_too_low',
                detail=f'Retenção WORM abaixo do mínimo exigido ({retention_days}d < {self.min_retention_days}d).',
                type='https://iabank.local/problems/seed/worm-retention',
            )
            return SeedWormOutcome(report={}, evidence=None, problem=problem)

        checklist = self._checklist_payload(checklist_results)
        status_label = 'failed' if checklist['summary']['failed'] else 'succeeded'
        report = self._build_report(
            seed_run=seed_run,
            manifest=manifest,
            checklist=checklist,
            status=status_label,
            cost_estimated_brl=cost_estimated_brl,
            cost_actual_brl=cost_actual_brl,
            cost_model_version=cost_model_version,
            extra_metadata=extra_metadata or {},
        )

        digest = self._hash(report)
        signature = self.signer.sign(digest=digest)
        serialized = json.dumps(report, sort_keys=True, ensure_ascii=False).encode('utf-8')
        url = self.storage.upload(
            content=serialized,
            retention_days=retention_days,
            metadata={
                'seed_run_id': str(seed_run.id),
                'environment': seed_run.environment,
                'tenant_id': str(seed_run.tenant_id),
            },
        )

        stored_bytes = self.storage.retrieve(url)
        stored_digest = self._hash(json.loads(stored_bytes.decode('utf-8')))
        verified_signature = self.signer.verify(digest=stored_digest, signature=signature)
        integrity_ok = stored_digest == digest and verified_signature

        evidence_status = (
            EvidenceWORM.IntegrityStatus.VERIFIED if integrity_ok else EvidenceWORM.IntegrityStatus.INVALID
        )
        with use_tenant(seed_run.tenant_id):
            evidence, _ = EvidenceWORM.objects.update_or_create(
                seed_run=seed_run,
                defaults={
                    'tenant': seed_run.tenant,
                    'report_url': url,
                    'signature_hash': digest,
                    'signature_algo': signature.algorithm,
                    'key_id': signature.key_id,
                    'key_version': signature.key_version,
                    'worm_retention_days': retention_days,
                    'integrity_status': evidence_status,
                    'integrity_verified_at': timezone.now(),
                    'cost_model_version': cost_model_version,
                    'cost_estimated_brl': Decimal(str(cost_estimated_brl or 0)),
                    'cost_actual_brl': Decimal(str(cost_actual_brl or 0)),
                },
            )

        problem = None
        if not integrity_ok:
            problem = ProblemDetail(
                status=HTTPStatus.SERVICE_UNAVAILABLE,
                title='worm_integrity_failed',
                detail='Hash ou assinatura do relatório WORM não pôde ser verificada.',
                type='https://iabank.local/problems/seed/worm-integrity',
            )
        elif checklist['summary']['failed']:
            failed_ids = ','.join(sorted(checklist['summary']['failed_ids']))
            problem = ProblemDetail(
                status=HTTPStatus.FORBIDDEN,
                title='worm_checklist_failed',
                detail=f'Itens de checklist reprovados: {failed_ids}.',
                type='https://iabank.local/problems/seed/worm-checklist',
            )

        return SeedWormOutcome(report=report, evidence=evidence, problem=problem)

    def _build_report(
        self,
        *,
        seed_run: SeedRun,
        manifest: Mapping[str, Any] | None,
        checklist: Mapping[str, Any],
        status: str,
        cost_estimated_brl: float | Decimal,
        cost_actual_brl: float | Decimal,
        cost_model_version: str,
        extra_metadata: Mapping[str, Any],
    ) -> dict[str, Any]:
        manifest_hash = ''
        if isinstance(manifest, Mapping):
            integrity = manifest.get('integrity')
            if isinstance(integrity, Mapping):
                manifest_hash = str(integrity.get('manifest_hash') or '')

        now = timezone.now()
        return {
            'seed_run_id': str(seed_run.id),
            'tenant_id': str(seed_run.tenant_id),
            'environment': seed_run.environment,
            'mode': seed_run.mode,
            'profile_version': seed_run.profile_version,
            'manifest_hash': manifest_hash or seed_run.manifest_hash_sha256,
            'status': status,
            'dry_run': seed_run.dry_run,
            'trace': {'trace_id': seed_run.trace_id, 'span_id': seed_run.span_id},
            'rate_limit_usage': seed_run.rate_limit_usage or {},
            'budget': {
                'cost_model_version': cost_model_version,
                'estimated_brl': float(cost_estimated_brl or 0),
                'actual_brl': float(cost_actual_brl or 0),
            },
            'checklist': checklist,
            'metadata': {
                'manifest_path': seed_run.manifest_path,
                **extra_metadata,
            },
            'generated_at': now.isoformat(),
        }

    def _hash(self, payload: Mapping[str, Any]) -> str:
        canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
        return hashlib.sha256(canonical.encode('utf-8')).hexdigest()

    def _checklist_payload(self, results: Mapping[str, bool]) -> dict[str, Any]:
        items: list[MutableMapping[str, Any]] = []
        failed: list[str] = []
        template = self.checklist_template or []

        for item in template:
            item_id = str(item.get('id'))
            passed = bool(results.get(item_id, False))
            items.append(
                {
                    'id': item_id,
                    'description': item.get('description', ''),
                    'category': item.get('category', ''),
                    'severity': item.get('severity', 'high'),
                    'passed': passed,
                }
            )
            if not passed:
                failed.append(item_id)

        summary = {
            'total': len(items),
            'passed': len(items) - len(failed),
            'failed': len(failed),
            'failed_ids': failed,
        }
        return {'items': items, 'summary': summary}

    def _load_checklist_template(self, path: Path) -> Sequence[dict[str, Any]]:
        if path.exists():
            try:
                raw = path.read_text(encoding='utf-8')
                data = json.loads(raw)
                items = data.get('items') if isinstance(data, Mapping) else None
                if isinstance(items, list):
                    return [item for item in items if isinstance(item, Mapping)]
            except (OSError, json.JSONDecodeError):
                pass

        # Fallback mínimo para não bloquear em caso de arquivo ausente
        return [
            {'id': 'pii_masked', 'description': 'PII mascarada via Vault Transit', 'category': 'pii', 'severity': 'critical'},
            {'id': 'rls_enforced', 'description': 'RLS/ABAC aplicados', 'category': 'security', 'severity': 'critical'},
            {'id': 'contracts_aligned', 'description': 'Contratos/serializers compatíveis', 'category': 'governance', 'severity': 'high'},
            {'id': 'idempotency_reused', 'description': 'Idempotency-Key registrada com TTL e hash', 'category': 'resilience', 'severity': 'high'},
            {'id': 'rate_limit_respected', 'description': 'RateLimit/backoff aplicados', 'category': 'performance', 'severity': 'medium'},
            {'id': 'slo_met', 'description': 'SLO/SLO budget atendidos', 'category': 'observability', 'severity': 'medium'},
        ]
