from django.db import migrations


def seed_test_information(apps, schema_editor):
    TestInformation = apps.get_model('hospital_admin', 'Test_Information')

    seed_rows = [
        ("Complete Blood Count (CBC)", "500"),
        ("Basic Metabolic Panel (BMP)", "900"),
        ("Comprehensive Metabolic Panel (CMP)", "1200"),
        ("Lipid Profile", "900"),
        ("Liver Function Test (LFT)", "1000"),
        ("Renal/Kidney Function Test (KFT)", "1000"),
        ("Thyroid Stimulating Hormone (TSH)", "700"),
        ("Free T4", "700"),
        ("Hemoglobin A1c (HbA1c)", "1000"),
        ("Fasting Blood Glucose (FBG)", "250"),
        ("Oral Glucose Tolerance Test (OGTT)", "800"),
        ("Urinalysis (Routine Examination)", "300"),
        ("Serum Electrolytes (Na/K/Cl)", "800"),
        ("C-Reactive Protein (CRP)", "900"),
        ("Erythrocyte Sedimentation Rate (ESR)", "350"),
        ("Vitamin D (25-OH)", "1800"),
        ("Vitamin B12", "1500"),
        ("Serum Ferritin", "1400"),
        ("Prothrombin Time / INR (PT/INR)", "900"),
        ("Hepatitis B Surface Antigen (HBsAg)", "700"),
    ]

    existing_names = set(
        name for name in TestInformation.objects.values_list('test_name', flat=True) if name
    )

    to_create = []
    for test_name, test_price in seed_rows:
        if test_name in existing_names:
            continue
        to_create.append(TestInformation(test_name=test_name, test_price=test_price))

    if to_create:
        TestInformation.objects.bulk_create(to_create)


class Migration(migrations.Migration):

    dependencies = [
        ('hospital_admin', '0005_admin_information_hospital'),
    ]

    operations = [
        migrations.RunPython(seed_test_information, migrations.RunPython.noop),
    ]
