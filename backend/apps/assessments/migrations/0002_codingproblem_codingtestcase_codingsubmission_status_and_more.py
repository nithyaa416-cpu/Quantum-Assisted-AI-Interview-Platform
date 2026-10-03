# Hand-corrected migration — AddField(problem) moved before AddIndex(problem)

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('interview_sessions', '0002_interviewquestion_follow_up_reason_and_more'),
        ('assessments', '0001_initial'),
    ]

    operations = [
        # ── 1. Create CodingProblem ──────────────────────────────────────────
        migrations.CreateModel(
            name='CodingProblem',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255)),
                ('slug', models.SlugField(max_length=255, unique=True)),
                ('description', models.TextField()),
                ('difficulty', models.CharField(
                    choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')],
                    default='easy', max_length=10,
                )),
                ('input_format',  models.TextField(blank=True)),
                ('output_format', models.TextField(blank=True)),
                ('constraints',   models.JSONField(blank=True, default=list)),
                ('examples',      models.JSONField(blank=True, default=list)),
                ('starter_code',  models.JSONField(default=dict)),
                ('time_limit_seconds', models.FloatField(default=2.0)),
                ('memory_limit_mb',    models.IntegerField(default=256)),
                ('is_active',  models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name':        'Coding Problem',
                'verbose_name_plural': 'Coding Problems',
                'db_table': 'assessments_coding_problem',
                'ordering': ['difficulty', 'title'],
            },
        ),

        # ── 2. Create CodingTestCase (no FK yet) ─────────────────────────────
        migrations.CreateModel(
            name='CodingTestCase',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('input_data',       models.TextField()),
                ('expected_output',  models.TextField()),
                ('is_hidden',        models.BooleanField(default=False)),
                ('order',            models.PositiveIntegerField(default=0)),
                ('created_at',       models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name':        'Coding Test Case',
                'verbose_name_plural': 'Coding Test Cases',
                'db_table': 'assessments_coding_test_case',
                'ordering': ['order'],
            },
        ),

        # ── 3. Add status field to CodingSubmission ──────────────────────────
        migrations.AddField(
            model_name='codingsubmission',
            name='status',
            field=models.CharField(
                blank=True,
                choices=[
                    ('accepted',              'Accepted'),
                    ('wrong_answer',          'Wrong Answer'),
                    ('compilation_error',     'Compilation Error'),
                    ('runtime_error',         'Runtime Error'),
                    ('time_limit_exceeded',   'Time Limit Exceeded'),
                    ('memory_limit_exceeded', 'Memory Limit Exceeded'),
                    ('internal_error',        'Internal Error'),
                    ('pending',               'Pending'),
                ],
                default='pending',
                max_length=30,
            ),
        ),

        # ── 4. Allow session to be nullable on CodingSubmission ──────────────
        migrations.AlterField(
            model_name='codingsubmission',
            name='session',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='coding_submissions',
                to='interview_sessions.interviewsession',
            ),
        ),

        # ── 5. Add problem FK to CodingSubmission (BEFORE the index!) ────────
        migrations.AddField(
            model_name='codingsubmission',
            name='problem',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='submissions',
                to='assessments.codingproblem',
            ),
        ),

        # ── 6. Add index on problem (AFTER the field exists) ─────────────────
        migrations.AddIndex(
            model_name='codingsubmission',
            index=models.Index(fields=['problem'], name='assessments_problem_706ee5_idx'),
        ),

        # ── 7. Add problem FK to CodingTestCase ──────────────────────────────
        migrations.AddField(
            model_name='codingtestcase',
            name='problem',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='test_cases',
                to='assessments.codingproblem',
            ),
        ),
    ]
