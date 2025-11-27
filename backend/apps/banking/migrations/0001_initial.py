import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tenancy', '0027_alter_tenant_options_alter_tenantthemetoken_managers'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccountCategory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('code', models.CharField(max_length=40)),
                ('description', models.CharField(max_length=255)),
                ('is_default', models.BooleanField(default=False)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='accountcategorys', to='tenancy.tenant')),
            ],
            options={
                'db_table': 'banking_account_category',
                'unique_together': {('tenant', 'code')},
            },
        ),
        migrations.CreateModel(
            name='BankAccount',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('agency', models.CharField(max_length=10)),
                ('account_number', models.CharField(max_length=20)),
                ('initial_balance', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('type', models.CharField(choices=[('CHECKING', 'Checking'), ('SAVINGS', 'Savings')], max_length=16)),
                ('status', models.CharField(choices=[('ACTIVE', 'Active'), ('BLOCKED', 'Blocked')], default='ACTIVE', max_length=16)),
            ],
            options={
                'db_table': 'banking_bank_account',
            },
        ),
        migrations.CreateModel(
            name='Consultant',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('balance', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='consultants', to='tenancy.tenant')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='consultant_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'banking_consultant',
            },
        ),
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('document_number', models.CharField(max_length=20)),
                ('birth_date', models.DateField(blank=True, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('phone', models.CharField(blank=True, max_length=20, null=True)),
                ('status', models.CharField(choices=[('ACTIVE', 'Active'), ('BLOCKED', 'Blocked'), ('DELINQUENT', 'Delinquent'), ('CANCELED', 'Canceled')], default='ACTIVE', max_length=16)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='customers', to='tenancy.tenant')),
            ],
            options={
                'db_table': 'banking_customer',
                'unique_together': {('tenant', 'document_number')},
            },
        ),
        migrations.CreateModel(
            name='Supplier',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('document_number', models.CharField(blank=True, max_length=20, null=True)),
                ('status', models.CharField(choices=[('ACTIVE', 'Active'), ('BLOCKED', 'Blocked')], default='ACTIVE', max_length=16)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='suppliers', to='tenancy.tenant')),
            ],
            options={
                'db_table': 'banking_supplier',
            },
        ),
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('zip_code', models.CharField(max_length=10)),
                ('street', models.CharField(max_length=255)),
                ('number', models.CharField(max_length=20)),
                ('complement', models.CharField(blank=True, max_length=100, null=True)),
                ('neighborhood', models.CharField(max_length=100)),
                ('city', models.CharField(max_length=100)),
                ('state', models.CharField(max_length=2)),
                ('is_primary', models.BooleanField(default=False)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='addresses', to='banking.customer')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='addresss', to='tenancy.tenant')),
            ],
            options={
                'db_table': 'banking_address',
            },
        ),
        migrations.AddField(
            model_name='bankaccount',
            name='customer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='bank_accounts', to='banking.customer'),
        ),
        migrations.AddField(
            model_name='bankaccount',
            name='tenant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bankaccounts', to='tenancy.tenant'),
        ),
        migrations.CreateModel(
            name='Loan',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('principal_amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('interest_rate', models.DecimalField(decimal_places=2, max_digits=5)),
                ('number_of_installments', models.PositiveSmallIntegerField()),
                ('contract_date', models.DateField()),
                ('first_installment_date', models.DateField()),
                ('status', models.CharField(choices=[('IN_PROGRESS', 'In progress'), ('PAID_OFF', 'Paid off'), ('IN_COLLECTION', 'In collection'), ('CANCELED', 'Canceled')], default='IN_PROGRESS', max_length=16)),
                ('iof_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('cet_annual_rate', models.DecimalField(decimal_places=4, max_digits=7)),
                ('cet_monthly_rate', models.DecimalField(decimal_places=4, max_digits=7)),
                ('consultant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='loans', to='banking.consultant')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='loans', to='banking.customer')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='loans', to='tenancy.tenant')),
            ],
            options={
                'db_table': 'banking_loan',
            },
        ),
        migrations.CreateModel(
            name='CreditLimit',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('current_limit', models.DecimalField(decimal_places=2, max_digits=12)),
                ('used_amount', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('status', models.CharField(choices=[('ACTIVE', 'Active'), ('FROZEN', 'Frozen'), ('CANCELED', 'Canceled')], default='ACTIVE', max_length=16)),
                ('effective_from', models.DateField(blank=True, null=True)),
                ('effective_through', models.DateField(blank=True, null=True)),
                ('bank_account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='credit_limits', to='banking.bankaccount')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='creditlimits', to='tenancy.tenant')),
            ],
            options={
                'db_table': 'banking_credit_limit',
            },
        ),
        migrations.CreateModel(
            name='Installment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('installment_number', models.PositiveSmallIntegerField()),
                ('due_date', models.DateField()),
                ('amount_due', models.DecimalField(decimal_places=2, max_digits=10)),
                ('amount_paid', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('payment_date', models.DateField(blank=True, null=True)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('PAID', 'Paid'), ('OVERDUE', 'Overdue'), ('PARTIALLY_PAID', 'Partially paid')], default='PENDING', max_length=16)),
                ('loan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='installments', to='banking.loan')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='installments', to='tenancy.tenant')),
            ],
            options={
                'db_table': 'banking_installment',
                'unique_together': {('loan', 'installment_number')},
            },
        ),
        migrations.CreateModel(
            name='FinancialTransaction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('description', models.CharField(max_length=255)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('transaction_date', models.DateField()),
                ('is_paid', models.BooleanField(default=False)),
                ('payment_date', models.DateField(blank=True, null=True)),
                ('type', models.CharField(choices=[('INCOME', 'Income'), ('EXPENSE', 'Expense')], max_length=16)),
                ('bank_account', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='transactions', to='banking.bankaccount')),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='transactions', to='banking.accountcategory')),
                ('installment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payments', to='banking.installment')),
                ('supplier', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='transactions', to='banking.supplier')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='financialtransactions', to='tenancy.tenant')),
            ],
            options={
                'db_table': 'banking_financial_transaction',
            },
        ),
        migrations.CreateModel(
            name='Contract',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('body', models.JSONField()),
                ('etag_payload', models.CharField(max_length=64)),
                ('version', models.CharField(max_length=32)),
                ('signed_at', models.DateTimeField()),
                ('status', models.CharField(choices=[('ACTIVE', 'Active'), ('REVOKED', 'Revoked'), ('EXPIRED', 'Expired')], default='ACTIVE', max_length=16)),
                ('pii_redacted', models.BooleanField(default=True)),
                ('bank_account', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contracts', to='banking.bankaccount')),
                ('customer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contracts', to='banking.customer')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contracts', to='tenancy.tenant')),
            ],
            options={
                'db_table': 'banking_contract',
            },
        ),
        migrations.AddConstraint(
            model_name='consultant',
            constraint=models.CheckConstraint(check=models.Q(('balance__gte', 0)), name='consultant_balance_non_negative'),
        ),
        migrations.AddConstraint(
            model_name='address',
            constraint=models.UniqueConstraint(condition=models.Q(('is_primary', True)), fields=('customer', 'is_primary'), name='banking_address_primary_unique'),
        ),
        migrations.AddConstraint(
            model_name='bankaccount',
            constraint=models.UniqueConstraint(fields=('tenant', 'account_number'), name='banking_bank_account_account_number_uniq'),
        ),
        migrations.AddConstraint(
            model_name='bankaccount',
            constraint=models.UniqueConstraint(fields=('tenant', 'agency', 'account_number'), name='banking_bank_account_agency_account_number_uniq'),
        ),
        migrations.AddConstraint(
            model_name='loan',
            constraint=models.CheckConstraint(check=models.Q(('number_of_installments__gt', 0)), name='loan_installments_positive'),
        ),
        migrations.AddConstraint(
            model_name='installment',
            constraint=models.CheckConstraint(check=models.Q(('amount_due__gte', 0)), name='installment_amount_due_positive'),
        ),
        migrations.AddConstraint(
            model_name='installment',
            constraint=models.CheckConstraint(check=models.Q(('amount_paid__gte', 0)), name='installment_amount_paid_positive'),
        ),
        migrations.AddConstraint(
            model_name='financialtransaction',
            constraint=models.CheckConstraint(check=models.Q(('amount__gte', 0)), name='financial_tx_amount_positive'),
        ),
        migrations.AddConstraint(
            model_name='financialtransaction',
            constraint=models.CheckConstraint(check=models.Q(('payment_date__isnull', True)) | models.Q(('is_paid', True)), name='financial_tx_payment_date_requires_paid'),
        ),
        migrations.AddConstraint(
            model_name='creditlimit',
            constraint=models.CheckConstraint(check=models.Q(('current_limit__gte', 0)), name='credit_limit_non_negative'),
        ),
        migrations.AddConstraint(
            model_name='creditlimit',
            constraint=models.CheckConstraint(check=models.Q(('used_amount__gte', 0)), name='credit_limit_used_non_negative'),
        ),
        migrations.AddConstraint(
            model_name='accountcategory',
            constraint=models.UniqueConstraint(condition=models.Q(('is_default', True)), fields=('tenant', 'is_default'), name='account_category_single_default'),
        ),
        migrations.AddConstraint(
            model_name='supplier',
            constraint=models.UniqueConstraint(condition=models.Q(('document_number__isnull', False)), fields=('tenant', 'document_number'), name='supplier_document_unique_per_tenant'),
        ),
        migrations.AddIndex(
            model_name='customer',
            index=models.Index(fields=['tenant', 'status'], name='banking_cust_status_idx'),
        ),
        migrations.AddIndex(
            model_name='address',
            index=models.Index(fields=['customer', 'is_primary'], name='banking_address_primary_idx'),
        ),
        migrations.AddIndex(
            model_name='bankaccount',
            index=models.Index(fields=['tenant', 'status'], name='bank_acct_status_idx'),
        ),
        migrations.AddIndex(
            model_name='bankaccount',
            index=models.Index(fields=['customer'], name='bank_acct_customer_idx'),
        ),
        migrations.AddIndex(
            model_name='loan',
            index=models.Index(fields=['tenant', 'status'], name='banking_loan_status_idx'),
        ),
        migrations.AddIndex(
            model_name='loan',
            index=models.Index(fields=['customer'], name='banking_loan_customer_idx'),
        ),
        migrations.AddIndex(
            model_name='loan',
            index=models.Index(fields=['consultant'], name='banking_loan_consultant_idx'),
        ),
        migrations.AddIndex(
            model_name='installment',
            index=models.Index(fields=['tenant', 'status'], name='banking_installment_status_idx'),
        ),
        migrations.AddIndex(
            model_name='installment',
            index=models.Index(fields=['loan', 'due_date'], name='banking_installment_due_idx'),
        ),
        migrations.AddIndex(
            model_name='financialtransaction',
            index=models.Index(fields=['tenant', 'type'], name='financial_tx_type_idx'),
        ),
        migrations.AddIndex(
            model_name='financialtransaction',
            index=models.Index(fields=['bank_account'], name='financial_tx_account_idx'),
        ),
        migrations.AddIndex(
            model_name='creditlimit',
            index=models.Index(fields=['tenant', 'status'], name='credit_limit_status_idx'),
        ),
        migrations.AddIndex(
            model_name='creditlimit',
            index=models.Index(fields=['bank_account'], name='credit_limit_account_idx'),
        ),
        migrations.AddIndex(
            model_name='accountcategory',
            index=models.Index(fields=['tenant', 'is_default'], name='account_category_default_idx'),
        ),
        migrations.AddIndex(
            model_name='contract',
            index=models.Index(fields=['tenant', 'status'], name='contract_status_idx'),
        ),
        migrations.AddConstraint(
            model_name='contract',
            constraint=models.UniqueConstraint(fields=('tenant', 'etag_payload'), name='contract_etag_unique_per_tenant'),
        ),
        migrations.RunSQL(
            sql='SELECT iabank.apply_tenant_rls_policies();',
            reverse_sql='SELECT iabank.revert_tenant_rls_policies();',
        ),
    ]
