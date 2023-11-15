"""empty message

Revision ID: ajp2023111301
Revises: 5e11ccbd47f3
Create Date: 2023-11-13 11:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

revision = "ajp2023111301"
down_revision = "5e11ccbd47f3"
branch_labels = None
depends_on = None

def upgrade():
    # Create the batch table
    op.create_table(
        "batch",
        sa.Column("id_batch", sa.VARCHAR(length=30), nullable=False),
        sa.Column("name_batch", sa.VARCHAR(length=50), nullable=False),
        sa.Column("date_batch", sa.DateTime(), nullable=False),
        sa.Column("instrument", sa.VARCHAR(length=250), nullable=False),
        sa.Column("primer", sa.VARCHAR(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id_batch"),
    )

    # Create the location table
    op.create_table(
        "location",
        sa.Column("id_location", sa.VARCHAR(length=25), nullable=False),
        sa.Column("continent", sa.VARCHAR(length=80), nullable=False),
        sa.Column("country", sa.VARCHAR(length=60), nullable=False),
        sa.Column("province", sa.VARCHAR(length=40), nullable=False),
        sa.Column("city", sa.VARCHAR(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id_location"),
    )

    # Create result1 table
    op.create_table(
        "result1",
        sa.Column("id_result1", sa.Integer(), nullable=False),
        sa.Column("qc", sa.VARCHAR(length=60), nullable=False),
        sa.Column("ql", sa.VARCHAR(length=60), nullable=False),
        sa.Column("description", sa.VARCHAR(length=250), nullable=False),
        sa.Column("snapper_variants", sa.Integer(), nullable=True),
        sa.Column("snapper_ignored", sa.Integer(), nullable=True),
        sa.Column("num_heterozygous", sa.Integer(), nullable=True),
        sa.Column("mean_depth", sa.Numeric(), nullable=True),
        sa.Column("coverage", sa.Numeric(), nullable=True),
        sa.PrimaryKeyConstraint("id_result1"),
    )

    # Create sample_project table
    op.create_table(
        "sample_project",
        sa.Column("id_sample", sa.VARCHAR(length=40), nullable=False),
        sa.Column("id_project", sa.VARCHAR(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id_sample", "id_project"),
    )

    # Culture table changes
    op.add_column(
        "culture", sa.Column("submitter_plate_id", sa.VARCHAR(length=60), nullable=True)
    )
    op.add_column(
        "culture",
        sa.Column("submitter_plate_well", sa.VARCHAR(length=60), nullable=True),
    )

    # Extraction table changes - confirmed, needs foreign key
    op.add_column(
        "extraction",
        sa.Column("submitter_plate_id", sa.VARCHAR(length=60), nullable=True),
    )
    op.add_column(
        "extraction",
        sa.Column("submitter_plate_well", sa.VARCHAR(length=60), nullable=True),
    )
    op.add_column(
        "extraction",
        sa.Column("elution_plate_id", sa.VARCHAR(length=60), nullable=True),
    )
    op.add_column(
        "extraction",
        sa.Column("elution_plate_well", sa.VARCHAR(length=60), nullable=True),
    )
    op.add_column(
        "extraction",
        sa.Column("nucleic_acid_concentration", sa.Numeric(), nullable=True),
    )

    # Read set table change
    op.add_column(
        "read_set",
        sa.Column("sequencing_institution", sa.VARCHAR(length=128), nullable=True),
    )

    # sample table changes
    op.add_column(
        "sample",
        sa.Column("sequencing_type_requested", sa.VARCHAR(length=60), nullable=True),
    )
    op.add_column(
        "sample", sa.Column("submitted_for_sequencing", sa.Boolean(), nullable=True)
    )
    op.add_column(
        "sample", sa.Column("submitter_plate_id", sa.VARCHAR(length=60), nullable=True)
    )
    op.add_column(
        "sample",
        sa.Column("submitter_plate_well", sa.VARCHAR(length=60), nullable=True),
    )

#    # Add an autoincrement to the result1 table primary key. - could also add by setting primary_key=True on id_result1
#    op.execute(
#        """
#     CREATE SEQUENCE result1_id_result1_seq
#        AS integer
#        START WITH 1
#        INCREMENT BY 1
#        NO MINVALUE
#        NO MAXVALUE
#        CACHE 1;
#  """
#    )
#
#    op.execute(
#        """
#    ALTER TABLE result1 ALTER COLUMN id_result1 SET DEFAULT nextval('result1_id_result1_seq');
#  """
#    )

    #op.create_foreign_key(
    #    "extraction_sample_culture_fkey",
    #    "extraction",
    #    "sample",
    #    ["sample_id"],
    #    ["id"],
    #    ondelete="CASCADE",
    #)
#
    #op.create_foreign_key(
    #    "extraction_sample_culture_fkey",
    #    "extraction",
    #    "culture",
    #    ["culture_id"],
    #    ["id"],
    #    ondelete="CASCADE",
    #)
#
    #op.create_check_constraint(
    #    "foreign_key_xor", "extraction", "((sample_id IS NULL) <> (culture_id IS NULL))"
    #)

def downgrade():
    op.drop_table("batch")
    op.drop_table("location")
    op.drop_table("result1")
    op.drop_table("sample_project")

    # Culture table changes
    op.drop_column("culture", "submitter_plate_id")
    op.drop_column("culture", "submitter_plate_well")

    # Extraction table changes
    op.drop_column("extraction", "submitter_plate_id")
    op.drop_column("extraction", "submitter_plate_well")
    op.drop_column("extraction", "elution_plate_id")
    op.drop_column("extraction", "elution_plate_well")
    op.drop_column("extraction", "nucleic_acid_concentration")

    # Raw sequencing table changes
    op.drop_column("raw_sequencing_illumina", "library_prep_method")
    op.drop_column("raw_sequencing_nanopore", "library_prep_method")

    # Read set table change
    op.drop_column("read_set", "sequencing_institution")

    # Tiling PCR table change
    op.drop_column("tiling_pcr", "protocol")

    # sample table changes
    op.drop_column("sample", "sequencing_type_requested")
    op.drop_column("sample", "submitted_for_sequencing")
    op.drop_column("sample", "submitter_plate_id")
    op.drop_column("sample", "submitter_plate_well")

    #op.drop_constraint("foreign_key_xor", "extraction")
    #op.drop_constraint(
    #    "extraction_sample_culture_fkey", "extraction", type_="foreignkey"
    #)